import time

import httpx
import pytest
from flask import Flask

from fogbed.exceptions import ContainerNotFound, FailInjectionError
from fogbed.fails.agent import FailAgent
from fogbed.fails.events import NodeState
from fogbed.fails.models import DisconnectFail
from fogbed.fails.plan import FailPlan, FailTarget, NodeSpec, TargetKind
from fogbed.fails.remote.client import FailWorkerClient
from fogbed.fails.remote.routes import create_fails_blueprint
from fakes import FakeOperator


@pytest.fixture
def operator() -> FakeOperator:
    return FakeOperator(missing={'ghost'})


@pytest.fixture
def agent(operator):
    instance = FailAgent(operator, source='worker1')
    yield instance
    instance.stop()


@pytest.fixture
def client(agent) -> FailWorkerClient:
    app = Flask(__name__)
    app.register_blueprint(create_fails_blueprint(lambda: agent))
    transport = httpx.WSGITransport(app=app)
    return FailWorkerClient('http://worker1:5000/', client=httpx.Client(transport=transport))


def test_client_runs_plan_and_reads_events(client, operator):
    target = FailTarget(TargetKind.NODE, 'd1', DisconnectFail(life_time=0), [NodeSpec('d1', 's1')])
    client.load_plan(FailPlan([target]))
    client.start(start_at=time.time())

    deadline = time.time() + 2
    while(client.status()['nodes'] != {'d1': 'off'} and time.time() < deadline):
        time.sleep(0.01)
    assert client.status()['nodes'] == {'d1': 'off'}

    client.stop()
    events = client.events()

    assert [(event.node, event.state, event.action) for event in events] == [
        ('d1', NodeState.OFF, 'disconnect'),
        ('d1', NodeState.ON, 'reconnect')
    ]
    assert operator.calls == [('disconnect', 'd1'), ('reconnect', 'd1')]


def test_client_immediate_fail_and_recover(client):
    spec = NodeSpec('d2', 's1', {'ip': '10.0.0.2'})

    assert client.fail_node('d2', 'crash', spec)
    assert not client.fail_node('d2', 'crash')
    assert client.recover_node('d2')
    assert not client.recover_node('d2')


def test_client_maps_errors(client):
    with pytest.raises(ContainerNotFound):
        client.fail_node('d9', 'crash')
    with pytest.raises(ContainerNotFound):
        client.fail_node('ghost', 'crash', NodeSpec('ghost', 's1'))
    with pytest.raises(FailInjectionError):
        client.fail_node('d9', 'explode', NodeSpec('d9', 's1'))

    target = FailTarget(TargetKind.NODE, 'd1', DisconnectFail(life_time=10), [NodeSpec('d1', 's1')])
    client.load_plan(FailPlan([target]))
    client.start()
    with pytest.raises(FailInjectionError):
        client.start()


def test_client_reports_unreachable_worker():
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError('connection refused', request=request)

    client = FailWorkerClient('http://10.0.0.99:5000', client=httpx.Client(transport=httpx.MockTransport(refuse)))

    with pytest.raises(FailInjectionError) as error:
        client.status()
    assert '10.0.0.99' in str(error.value)
