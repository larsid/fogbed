import time

import pytest
from flask import Flask

from fogbed.fails.agent import FailAgent
from fogbed.fails.models import CrashFail
from fogbed.fails.plan import FailPlan, FailTarget, NodeSpec, TargetKind
from fogbed.fails.remote.routes import create_fails_blueprint
from fakes import FakeOperator


def plan_dict(life_time: float = 0.0) -> dict:
    target = FailTarget(TargetKind.NODE, 'd1', CrashFail(life_time=life_time), [NodeSpec('d1', 's1', {'ip': '10.0.0.1'})])
    return FailPlan([target], seed=3).to_dict()


@pytest.fixture
def operator() -> FakeOperator:
    return FakeOperator(missing={'ghost'})


@pytest.fixture
def agent(operator):
    instance = FailAgent(operator, source='worker1')
    yield instance
    instance.stop()


@pytest.fixture
def client(agent):
    app = Flask(__name__)
    app.register_blueprint(create_fails_blueprint(lambda: agent))
    return app.test_client()


def wait_for(condition, timeout: float = 2.0):
    deadline = time.time() + timeout
    while(time.time() < deadline):
        if(condition()): return
        time.sleep(0.01)
    raise AssertionError('condition not reached')


def test_plan_lifecycle_through_routes(client, operator):
    response = client.post('/fails', json=plan_dict())
    assert response.status_code == 201
    assert '1 targets' in response.json['content']

    start_at = time.time()
    response = client.post('/fails/start', json={'start_at': start_at})
    assert response.status_code == 200

    wait_for(lambda: operator.calls == [('crash', 'd1')])

    status = client.get('/fails/status').json['content']
    assert status['running']
    assert status['started_at'] == start_at
    assert status['nodes'] == {'d1': 'off'}

    response = client.post('/fails/stop')
    assert response.status_code == 200
    assert operator.calls == [('crash', 'd1'), ('recover', 'd1')]

    events = client.get('/fails/events').json['content']
    assert [(event['node'], event['state'], event['source']) for event in events] == [
        ('d1', 'off', 'worker1'),
        ('d1', 'on', 'worker1')
    ]


def test_start_without_body_uses_plan_start_at(client, agent):
    data = plan_dict(life_time=10)
    data['start_at'] = 1234.5
    client.post('/fails', json=data)

    assert client.post('/fails/start').status_code == 200
    assert agent.started_at == 1234.5


@pytest.mark.parametrize('body', [
    {},
    {'targets': 'd1'},
    {'targets': [{'kind': 'node', 'name': 'd1', 'fail_model': {'kind': 'meteor'}, 'nodes': []}]}
])
def test_invalid_plan_returns_bad_request(client, body):
    response = client.post('/fails', json=body)

    assert response.status_code == 400
    assert 'error' in response.json


def test_invalid_start_at_returns_bad_request(client):
    client.post('/fails', json=plan_dict())
    assert client.post('/fails/start', json={'start_at': 'soon'}).status_code == 400


def test_running_plan_returns_conflict(client):
    client.post('/fails', json=plan_dict(life_time=10))
    client.post('/fails/start')

    assert client.post('/fails/start').status_code == 409
    assert client.post('/fails', json=plan_dict()).status_code == 409


def test_immediate_fail_and_recover(client, operator):
    spec = NodeSpec('d2', 's1', {'ip': '10.0.0.2'}).to_dict()

    response = client.post('/containers/d2/fail', json={'mode': 'disconnect', 'spec': spec})
    assert response.status_code == 200
    assert client.post('/containers/d2/fail', json={'mode': 'disconnect'}).status_code == 409

    assert client.post('/containers/d2/recover').status_code == 200
    assert client.post('/containers/d2/recover').status_code == 409
    assert operator.calls == [('disconnect', 'd2'), ('reconnect', 'd2')]


@pytest.mark.parametrize('body', [
    {},
    {'mode': 'explode'},
    {'mode': 'crash', 'spec': 'd2'},
    {'mode': 'crash', 'spec': {'name': 'd3', 'switch': 's1'}}
])
def test_invalid_immediate_fail_returns_bad_request(client, body):
    assert client.post('/containers/d2/fail', json=body).status_code == 400


def test_unknown_container_returns_not_found(client):
    assert client.post('/containers/d9/fail', json={'mode': 'crash'}).status_code == 404
    assert client.post('/containers/d9/recover').status_code == 404

    spec = NodeSpec('ghost', 's1').to_dict()
    response = client.post('/containers/ghost/fail', json={'mode': 'crash', 'spec': spec})
    assert response.status_code == 404
    assert 'ghost' in response.json['error']


def test_status_without_plan(client):
    status = client.get('/fails/status').json['content']

    assert not status['running']
    assert status['targets'] == []
    assert 'time' in status


def test_operator_failure_returns_server_error(agent, client, operator):
    operator.broken.add('d4')
    spec = NodeSpec('d4', 's1').to_dict()
    response = client.post('/containers/d4/fail', json={'mode': 'crash', 'spec': spec})

    assert response.status_code == 500
    assert 'd4 is broken' in response.json['error']
