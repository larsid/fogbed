import threading
import time
from typing import List, Optional, Set, Tuple

import pytest

from fogbed.exceptions import ContainerNotFound, FailInjectionError
from fogbed.fails.agent import FailAgent
from fogbed.fails.events import NodeState
from fogbed.fails.models import (
    AvailabilityFail,
    AvailabilityMode,
    CrashFail,
    DisconnectFail,
    FailModel,
    SelectionMethod,
    SplitMethod
)
from fogbed.fails.operators import NodeOperator
from fogbed.fails.plan import FailPlan, FailTarget, NodeSpec, TargetKind


class FakeOperator(NodeOperator):
    def __init__(self, broken: Optional[Set[str]] = None):
        self.calls: List[Tuple[str, str]] = []
        self.broken = broken or set()
        self._lock = threading.Lock()

    def _call(self, action: str, node: NodeSpec):
        if(node.name in self.broken):
            raise RuntimeError(f'{node.name} is broken')
        with self._lock:
            self.calls.append((action, node.name))

    def crash(self, node: NodeSpec): self._call('crash', node)
    def recover(self, node: NodeSpec): self._call('recover', node)
    def disconnect(self, node: NodeSpec): self._call('disconnect', node)
    def reconnect(self, node: NodeSpec): self._call('reconnect', node)
    def exists(self, name: str) -> bool: return True


def node_target(name: str, model: FailModel) -> FailTarget:
    return FailTarget(TargetKind.NODE, name, model, [NodeSpec(name, 's1')])


def instance_target(name: str, model: FailModel, nodes: List[str]) -> FailTarget:
    return FailTarget(TargetKind.INSTANCE, name, model, [NodeSpec(node, 's1') for node in nodes])


def wait_for(condition, timeout: float = 2.0):
    deadline = time.time() + timeout
    while(time.time() < deadline):
        if(condition()): return
        time.sleep(0.01)
    raise AssertionError('condition not reached')


def transitions(agent: FailAgent, node: str) -> List[NodeState]:
    return [event.state for event in agent.events() if event.node == node]


@pytest.fixture
def operator() -> FakeOperator:
    return FakeOperator()


@pytest.fixture
def agent(operator):
    instance = FailAgent(operator, source='worker1')
    yield instance
    instance.stop()


def test_node_crash_happens_after_life_time_and_is_restored_on_stop(agent, operator):
    agent.load(FailPlan([node_target('d1', CrashFail(life_time=0.1))]))
    agent.start()

    assert operator.calls == []
    wait_for(lambda: operator.calls == [('crash', 'd1')])
    assert agent.status()['nodes'] == {'d1': 'off'}

    agent.stop()

    assert operator.calls == [('crash', 'd1'), ('recover', 'd1')]
    assert [(event.state, event.action, event.source) for event in agent.events()] == [
        (NodeState.OFF, 'crash', 'worker1'),
        (NodeState.ON, 'recover', 'worker1')
    ]
    assert agent.status()['nodes'] == {'d1': 'on'}
    assert not agent.is_running


def test_instance_disconnect_selects_nodes_by_split_and_selection(agent, operator):
    model = DisconnectFail(fail_rate=0.5, split_method=SplitMethod.UP, life_time=0, selection_method=SelectionMethod.SEQUENTIAL)
    agent.load(FailPlan([instance_target('edge', model, ['d1', 'd2', 'd3'])]))
    agent.start()

    wait_for(lambda: len(operator.calls) == 2)
    assert operator.calls == [('disconnect', 'd1'), ('disconnect', 'd2')]

    agent.stop()
    assert sorted(operator.calls[2:]) == [('reconnect', 'd1'), ('reconnect', 'd2')]


def test_node_availability_alternates_states(agent, operator):
    model = AvailabilityFail(availability=0.5, slot_time=0.05, availability_mode=AvailabilityMode.DISCONNECT)
    agent.load(FailPlan([node_target('d1', model)]))
    agent.start()

    wait_for(lambda: len(agent.events()) >= 5)
    agent.stop()

    states = transitions(agent, 'd1')
    assert states[0] == NodeState.OFF
    assert all(previous != current for previous, current in zip(states, states[1:]))
    assert states[-1] == NodeState.ON
    assert {action for action, _ in operator.calls} == {'disconnect', 'reconnect'}


def test_instance_availability_keeps_failed_nodes_within_target(agent, operator):
    model = AvailabilityFail(availability=0.5, slot_time=0.05, availability_mode=AvailabilityMode.CRASH)
    agent.load(FailPlan([instance_target('edge', model, ['d1', 'd2'])], seed=1))
    agent.start()

    observed = []
    deadline = time.time() + 0.6
    while(time.time() < deadline):
        observed.append(sum(state == 'off' for state in agent.status()['nodes'].values()))
        time.sleep(0.01)
    agent.stop()

    assert max(observed) <= 1
    assert {action for action, _ in operator.calls} == {'crash', 'recover'}


def test_availability_does_not_revive_nodes_owned_by_other_target(agent, operator):
    agent.load(FailPlan([node_target('d1', CrashFail(life_time=0)), node_target('d2', CrashFail(life_time=0))]))
    agent.fail_node('d1', 'crash', owner='node:d1')

    assert not agent.recover_node('d1', owner='instance:edge')
    assert operator.calls == [('crash', 'd1')]
    assert agent.recover_node('d1')
    assert operator.calls == [('crash', 'd1'), ('recover', 'd1')]


def test_failed_node_is_not_failed_again(agent, operator):
    agent.load(FailPlan([node_target('d1', CrashFail())]))

    assert agent.fail_node('d1', 'disconnect')
    assert not agent.fail_node('d1', 'crash')
    assert operator.calls == [('disconnect', 'd1')]


def test_manual_fail_registers_new_spec(agent, operator):
    assert agent.fail_node('d7', 'crash', spec=NodeSpec('d7', 's3', {'ip': '10.0.0.7'}))
    assert agent.recover_node('d7')
    assert operator.calls == [('crash', 'd7'), ('recover', 'd7')]


def test_unknown_node_and_mode_are_rejected(agent):
    with pytest.raises(ContainerNotFound):
        agent.fail_node('d9', 'crash')
    with pytest.raises(ContainerNotFound):
        agent.recover_node('d9')
    with pytest.raises(ValueError):
        agent.fail_node('d9', 'explode')
    with pytest.raises(ValueError):
        agent.fail_node('d9', 'crash', spec=NodeSpec('d8', 's1'))


def test_recovering_healthy_node_returns_false(agent, operator):
    agent.load(FailPlan([node_target('d1', CrashFail())]))
    assert not agent.recover_node('d1')
    assert operator.calls == []


def test_running_agent_rejects_new_plan_and_second_start(agent):
    agent.load(FailPlan([node_target('d1', CrashFail(life_time=10))]))
    agent.start()

    with pytest.raises(FailInjectionError):
        agent.load(FailPlan())
    with pytest.raises(FailInjectionError):
        agent.start()


def test_start_waits_for_start_at(agent, operator):
    agent.load(FailPlan([node_target('d1', CrashFail(life_time=0))], start_at=time.time() + 0.3))
    agent.start()

    time.sleep(0.1)
    assert operator.calls == []
    wait_for(lambda: operator.calls == [('crash', 'd1')])


def test_stop_before_start_at_cancels_everything(agent, operator):
    agent.load(FailPlan([node_target('d1', CrashFail(life_time=0))]))
    agent.start(start_at=time.time() + 0.3)
    agent.stop()

    time.sleep(0.4)
    assert operator.calls == []
    assert agent.events() == []


def test_operation_errors_are_reported_without_stopping_target():
    operator = FakeOperator(broken={'d1'})
    agent = FailAgent(operator)
    model = CrashFail(fail_rate=1, life_time=0)
    agent.load(FailPlan([instance_target('edge', model, ['d1', 'd2'])]))
    agent.start()

    wait_for(lambda: operator.calls == [('crash', 'd2')])
    agent.stop()

    errors = agent.status()['errors']
    assert len(errors) == 1
    assert 'instance:edge' in errors[0] and 'd1 is broken' in errors[0]


def test_seeded_instance_availability_is_reproducible():
    model = AvailabilityFail(availability=0.5, slot_time=0.02, availability_mode=AvailabilityMode.DISCONNECT)
    sequences = []

    for _ in range(2):
        operator = FakeOperator()
        agent = FailAgent(operator)
        agent.load(FailPlan([instance_target('edge', model, ['d1', 'd2', 'd3', 'd4'])], seed=7))
        agent.start()
        wait_for(lambda: len(operator.calls) >= 12)
        agent.stop()
        sequences.append(operator.calls[:12])

    assert sequences[0] == sequences[1]


def test_status_reports_targets_and_clock(agent):
    agent.load(FailPlan([node_target('d1', CrashFail(life_time=10))]))
    agent.start()
    status = agent.status()

    assert status['running']
    assert status['targets'] == [{
        'kind': 'node',
        'name': 'd1',
        'fail_model': CrashFail(life_time=10).to_dict(),
        'active': True
    }]
    assert abs(status['time'] - time.time()) < 1


def test_loading_new_plan_clears_previous_run(agent, operator):
    agent.load(FailPlan([node_target('d1', CrashFail(life_time=0))]))
    agent.start()
    wait_for(lambda: operator.calls == [('crash', 'd1')])
    agent.stop()
    agent.load(FailPlan())

    assert agent.events() == []
    assert agent.started_at is None
