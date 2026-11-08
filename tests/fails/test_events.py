import json
import threading

import pytest

from fogbed.fails.events import EventLog, FailEvent, NodeState, compute_metrics


def event(node: str, state: NodeState, timestamp: float) -> FailEvent:
    action = 'crash' if(state == NodeState.OFF) else 'recover'
    return FailEvent(node, state, action, timestamp)


def test_event_survives_json_round_trip():
    original = FailEvent('d1', NodeState.OFF, 'disconnect', 12.5, '10.0.0.2')
    restored = FailEvent.from_dict(json.loads(json.dumps(original.to_dict())))
    assert restored == original


@pytest.mark.parametrize('data', [
    {},
    {'node': 'd1', 'state': 'broken', 'action': 'crash', 'timestamp': 1},
    {'node': 'd1', 'state': 'on', 'action': 'crash', 'timestamp': None}
])
def test_invalid_event_is_rejected(data):
    with pytest.raises(ValueError):
        FailEvent.from_dict(data)


def test_event_log_is_thread_safe():
    log = EventLog()

    def append_many(node: str):
        for index in range(500):
            log.append(event(node, NodeState.OFF, index))

    threads = [threading.Thread(target=append_many, args=(f'd{i}',)) for i in range(4)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()

    assert len(log.list()) == 2000
    log.clear()
    assert log.list() == []


def test_metrics_for_alternating_node():
    events = [
        event('d1', NodeState.OFF, 10),
        event('d1', NodeState.ON, 15),
        event('d1', NodeState.OFF, 25),
        event('d1', NodeState.ON, 30)
    ]
    metrics = compute_metrics(events, start=0, end=40)['d1']

    assert metrics.uptime == 30
    assert metrics.downtime == 10
    assert metrics.failures == 2
    assert metrics.repairs == 2
    assert metrics.availability == 0.75
    assert metrics.mtbf == 15
    assert metrics.mttr == 5


def test_metrics_for_permanent_crash():
    metrics = compute_metrics([event('d1', NodeState.OFF, 20)], start=0, end=60)['d1']

    assert metrics.availability == pytest.approx(1 / 3)
    assert metrics.failures == 1
    assert metrics.repairs == 0
    assert metrics.mttr == 40


def test_metrics_include_nodes_without_events():
    metrics = compute_metrics([], start=0, end=10, nodes=['d2'])['d2']

    assert metrics.availability == 1
    assert metrics.mtbf is None
    assert metrics.mttr is None


def test_metrics_ignore_order_duplicates_and_clip_window():
    events = [
        event('d1', NodeState.ON, 70),
        event('d1', NodeState.OFF, 50),
        event('d1', NodeState.OFF, 55),
        event('d1', NodeState.OFF, -5)
    ]
    metrics = compute_metrics(events, start=0, end=60)['d1']

    assert metrics.failures == 1
    assert metrics.repairs == 0
    assert metrics.downtime == 60
    assert metrics.uptime == 0


def test_metrics_reject_inverted_window():
    with pytest.raises(ValueError):
        compute_metrics([], start=10, end=0)


def test_metrics_serialization_contains_derived_values():
    data = compute_metrics([event('d1', NodeState.OFF, 5)], start=0, end=10)['d1'].to_dict()
    assert data['availability'] == 0.5
    assert data['mtbf'] == 5
    assert data['mttr'] == 5
