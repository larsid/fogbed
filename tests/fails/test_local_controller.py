import time
from typing import List

import pytest

from fogbed import Container, VirtualInstance
from fogbed.exceptions import ContainerNotFound, FailInjectionError
from fogbed.fails.controller import FailController, LocalFailController, build_targets
from fogbed.fails.models import AvailabilityFail, AvailabilityMode, CrashFail
from fogbed.fails.plan import TargetKind
from fogbed.node.services.local_docker import LocalDocker
from fakes import FakeNet


class FakeExperiment:
    def __init__(self, instances: List[VirtualInstance]):
        self.instances = instances
        self.net = FakeNet(switches=[instance.switch for instance in instances])

        for instance in instances:
            for container in instance:
                self.net.addDocker(container.name, **container.params)
                self.net.addLink(container.name, instance.switch)
        self.net.calls.clear()

    def get_virtual_instances(self) -> List[VirtualInstance]:
        return self.instances

    def get_docker(self, name: str) -> Container:
        for instance in self.instances:
            if(name in instance.containers):
                return instance.containers[name]
        raise ContainerNotFound(name)


def create_edge() -> VirtualInstance:
    edge = VirtualInstance('edge', fail_model=AvailabilityFail(0.5, 2, AvailabilityMode.DISCONNECT))
    edge.create_container(Container('d1', fail_model=CrashFail(life_time=20), link_params={'bw': 5}))
    edge.create_container(Container('d2'))
    return edge


def test_build_targets_creates_node_and_instance_targets():
    fog = VirtualInstance('fog')
    fog.create_container(Container('gw'))
    edge = create_edge()

    targets = build_targets([fog, edge])

    assert [(target.kind, target.name) for target in targets] == [
        (TargetKind.NODE, 'd1'),
        (TargetKind.INSTANCE, 'edge')
    ]
    assert targets[0].nodes[0].switch == edge.switch
    assert targets[0].nodes[0].params['ip'] == edge.containers['d1'].ip
    assert targets[0].nodes[0].link_params == {'bw': 5}
    assert targets[1].node_names == ['d1', 'd2']
    assert 'fail_model' not in targets[1].nodes[0].params


def test_local_controller_runs_plan_and_rebinds_recovered_dockers():
    edge = VirtualInstance('edge')
    edge.create_container(Container('d1', fail_model=CrashFail(life_time=0)))
    experiment = FakeExperiment([edge])
    controller = LocalFailController(experiment)

    controller.start()
    deadline = time.time() + 2
    while('d1' in experiment.net and time.time() < deadline):
        time.sleep(0.01)
    assert 'd1' not in experiment.net

    controller.stop()

    container = edge.containers['d1']
    assert 'd1' in experiment.net
    assert isinstance(container._service, LocalDocker)
    assert container._service.docker is experiment.net['d1']

    metrics = controller.metrics()['d1']
    assert metrics.failures == 1
    assert metrics.repairs == 0
    assert metrics.uptime + metrics.downtime == controller.stopped_at - controller.started_at


def test_local_controller_requires_running_experiment():
    experiment = FakeExperiment([create_edge()])
    experiment.net.is_running = False

    with pytest.raises(FailInjectionError):
        LocalFailController(experiment).start()


def test_local_controller_manual_fail_and_recover():
    experiment = FakeExperiment([create_edge()])
    controller = LocalFailController(experiment)

    assert controller.fail('d2', 'disconnect')
    assert controller.recover('d2')
    assert [event.state.value for event in controller.events()] == ['off', 'on']

    with pytest.raises(ContainerNotFound):
        controller.fail('d9')


def test_metrics_require_started_controller():
    with pytest.raises(FailInjectionError):
        LocalFailController(FakeExperiment([create_edge()])).metrics()


def test_fail_controller_rejects_unknown_experiment_type():
    with pytest.raises(TypeError):
        FailController(object())
