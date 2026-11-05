import time
from typing import Dict, List

import httpx
import pytest
from flask import Flask

from fogbed import Container, FogbedDistributedExperiment, VirtualInstance
from fogbed.exceptions import FailInjectionError
from fogbed.fails.agent import FailAgent
from fogbed.fails.controller import FailController, RemoteFailController
from fogbed.fails.events import NodeState
from fogbed.fails.models import AvailabilityFail, AvailabilityMode, CrashFail
from fogbed.fails.remote.client import FailWorkerClient
from fogbed.fails.remote.routes import create_fails_blueprint
from fakes import FakeOperator

W1 = '192.168.0.151'
W2 = '192.168.0.152'


class FakeRemoteWorker:
    def __init__(self, ip: str):
        self.url = f'http://{ip}:5000'


class FakeWorker:
    def __init__(self, ip: str):
        self.net = FakeRemoteWorker(ip)


class FakeDistributedExperiment:
    def __init__(self, instances: Dict[str, List[VirtualInstance]]):
        self.is_running = True
        self.workers = {ip: FakeWorker(ip) for ip in instances}
        self.instances = [instance for group in instances.values() for instance in group]

        for ip, group in instances.items():
            for instance in group:
                instance.set_ip(ip)

    def get_virtual_instances(self) -> List[VirtualInstance]:
        return self.instances


class Cluster:
    def __init__(self, clocks: Dict[str, float]):
        self.operators = {ip: FakeOperator() for ip in clocks}
        self.agents = {
            ip: FailAgent(self.operators[ip], source=f'host-{ip}', clock=lambda offset=offset: time.time() + offset)
            for ip, offset in clocks.items()
        }
        self.apps = {}

        for ip, agent in self.agents.items():
            app = Flask(f'worker-{ip}')
            app.register_blueprint(create_fails_blueprint(lambda agent=agent: agent))
            self.apps[f'http://{ip}:5000'] = app

    def client_factory(self, url: str) -> FailWorkerClient:
        return FailWorkerClient(url, client=httpx.Client(transport=httpx.WSGITransport(app=self.apps[url])))

    def stop(self):
        for agent in self.agents.values():
            agent.stop()


@pytest.fixture
def cluster():
    instance = Cluster({W1: 0.0, W2: 0.0})
    yield instance
    instance.stop()


def create_experiment() -> FakeDistributedExperiment:
    fog = VirtualInstance('fog')
    fog.create_container(Container('gw'))
    edge = VirtualInstance('edge', fail_model=AvailabilityFail(0.5, 0.05, AvailabilityMode.DISCONNECT))
    edge.create_container(Container('d1', fail_model=CrashFail(life_time=0.1)))
    edge.create_container(Container('d2'))
    return FakeDistributedExperiment({W1: [fog], W2: [edge]})


def wait_for(condition, timeout: float = 3.0):
    deadline = time.time() + timeout
    while(time.time() < deadline):
        if(condition()): return
        time.sleep(0.01)
    raise AssertionError('condition not reached')


def test_remote_controller_sends_plans_only_to_workers_with_targets(cluster):
    controller = RemoteFailController(create_experiment(), seed=5, start_delay=0.2, client_factory=cluster.client_factory)
    before = time.time()
    controller.start()

    assert cluster.agents[W1].status()['targets'] == []
    targets = cluster.agents[W2].status()['targets']
    assert [(target['kind'], target['name']) for target in targets] == [('node', 'd1'), ('instance', 'edge')]
    assert cluster.agents[W2].started_at == pytest.approx(controller.started_at, abs=0.05)
    assert before + 0.2 <= controller.started_at <= time.time() + 0.2
    assert controller.nodes == ['d1', 'd2']


def test_remote_controller_merges_events_and_restores_on_stop(cluster):
    controller = RemoteFailController(create_experiment(), seed=5, start_delay=0.1, client_factory=cluster.client_factory)
    controller.start()

    wait_for(lambda: ('crash', 'd1') in cluster.operators[W2].calls)
    controller.stop()

    events = controller.events()
    assert events
    assert {event.source for event in events} == {W2}
    assert [event.timestamp for event in events] == sorted(event.timestamp for event in events)
    assert all(state == 'on' for state in cluster.agents[W2].status()['nodes'].values())

    d1_states = [event.state for event in events if event.node == 'd1']
    assert NodeState.OFF in d1_states and d1_states[-1] == NodeState.ON

    metrics = controller.metrics()
    assert set(metrics) == {'d1', 'd2'}
    assert metrics['d1'].failures >= 1


def test_remote_controller_routes_manual_actions_to_owner_worker(cluster):
    controller = RemoteFailController(create_experiment(), client_factory=cluster.client_factory)

    assert controller.fail('gw', 'disconnect')
    assert not controller.fail('gw', 'disconnect')
    assert controller.recover('gw')
    assert cluster.operators[W1].calls == [('disconnect', 'gw'), ('reconnect', 'gw')]
    assert cluster.operators[W2].calls == []


def test_remote_controller_requires_running_experiment(cluster):
    experiment = create_experiment()
    experiment.is_running = False

    with pytest.raises(FailInjectionError):
        RemoteFailController(experiment, client_factory=cluster.client_factory).start()


def test_remote_controller_rejects_unassigned_instances(cluster):
    experiment = create_experiment()
    orphan = VirtualInstance('cloud', fail_model=CrashFail())
    orphan.create_container(Container('c1'))
    experiment.instances.append(orphan)

    with pytest.raises(FailInjectionError):
        RemoteFailController(experiment, client_factory=cluster.client_factory).start()


def test_remote_controller_compensates_clock_offsets():
    cluster = Cluster({W1: 0.0, W2: 3.0})
    try:
        controller = RemoteFailController(create_experiment(), start_delay=0.1, client_factory=cluster.client_factory)
        controller.start()

        assert controller.clock_offsets[W1] == pytest.approx(0.0, abs=0.2)
        assert controller.clock_offsets[W2] == pytest.approx(3.0, abs=0.2)
        assert cluster.agents[W2].started_at == pytest.approx(controller.started_at + 3.0, abs=0.2)

        wait_for(lambda: ('crash', 'd1') in cluster.operators[W2].calls)
        controller.stop()
        crash = next(event for event in controller.events() if event.action == 'crash')

        assert controller.started_at + 0.05 <= crash.timestamp <= controller.stopped_at
    finally:
        cluster.stop()


def test_stop_reports_unreachable_workers(cluster):
    experiment = create_experiment()
    experiment.workers['10.0.0.99'] = FakeWorker('10.0.0.99')

    def factory(url: str) -> FailWorkerClient:
        if('10.0.0.99' in url):
            def refuse(request): raise httpx.ConnectError('refused', request=request)
            return FailWorkerClient(url, client=httpx.Client(transport=httpx.MockTransport(refuse)))
        return cluster.client_factory(url)

    with pytest.raises(FailInjectionError) as error:
        RemoteFailController(experiment, client_factory=factory).stop()
    assert '10.0.0.99' in str(error.value)


def test_fail_controller_selects_remote_backend_for_distributed_experiments():
    controller = FailController(FogbedDistributedExperiment(), seed=1, start_delay=5)

    assert isinstance(controller.backend, RemoteFailController)
    assert controller.backend.start_delay == 5
    assert controller.backend.seed == 1
