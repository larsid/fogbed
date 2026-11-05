import math
import random
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set

from fogbed.exceptions import ContainerNotFound, FailInjectionError
from fogbed.fails.events import EventLog, FailEvent, NodeState
from fogbed.fails.models import AvailabilityFail, CrashFail, TimedFail
from fogbed.fails.operators import NodeOperator
from fogbed.fails.plan import FailPlan, FailTarget, NodeSpec, TargetKind
from fogbed.fails.schedule import InstanceAvailabilitySchedule, NodeAvailabilitySchedule
from fogbed.fails.selection import select_nodes, split_amount

from mininet.log import info

CRASH = 'crash'
DISCONNECT = 'disconnect'
RECOVERY_ACTIONS = {CRASH: 'recover', DISCONNECT: 'reconnect'}


@dataclass(frozen=True)
class NodeFailure:
    mode: str
    owner: Optional[str]


def target_owner(target: FailTarget) -> str:
    return f'{target.kind.value}:{target.name}'


class FailAgent:
    def __init__(self,
        operator: NodeOperator,
        source: str = 'local',
        clock: Callable[[], float] = time.time,
        join_timeout: float = 30.0
    ):
        self.operator     = operator
        self.source       = source
        self.clock        = clock
        self.join_timeout = join_timeout
        self.started_at: Optional[float] = None
        self.stopped_at: Optional[float] = None
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._running = False
        self._plan = FailPlan()
        self._threads: Dict[str, threading.Thread] = {}
        self._specs: Dict[str, NodeSpec] = {}
        self._failures: Dict[str, NodeFailure] = {}
        self._errors: List[str] = []
        self._events = EventLog()

    @property
    def is_running(self) -> bool:
        return self._running

    def load(self, plan: FailPlan):
        with self._lock:
            if(self._running):
                raise FailInjectionError('A fail plan is already running')

            self._plan = plan
            self._specs.update(plan.node_specs)
            self._threads = {}
            self._errors.clear()
            self._events.clear()
            self.started_at = None
            self.stopped_at = None

    def start(self, start_at: Optional[float] = None):
        with self._lock:
            if(self._running):
                raise FailInjectionError('A fail plan is already running')

            if(start_at is None):
                start_at = self._plan.start_at
            if(start_at is None):
                start_at = self.clock()

            self._stop_event.clear()
            self._running = True
            self.started_at = start_at
            self.stopped_at = None
            self._threads = {
                target_owner(target): threading.Thread(
                    target=self._run_target,
                    args=(target, start_at),
                    name=f'fail-{target_owner(target)}',
                    daemon=True
                )
                for target in self._plan.targets
            }

            for thread in self._threads.values():
                thread.start()

    def stop(self):
        self._stop_event.set()

        for thread in list(self._threads.values()):
            thread.join(self.join_timeout)

        with self._lock:
            for name in list(self._failures):
                self._safely('stop', lambda: self.recover_node(name))

            if(self._running):
                self.stopped_at = self.clock()
            self._running = False

    def fail_node(self, name: str, mode: str, owner: Optional[str] = None, spec: Optional[NodeSpec] = None) -> bool:
        if(mode not in RECOVERY_ACTIONS):
            raise ValueError(f'Unknown fail mode: {mode}')

        with self._lock:
            node = self._get_spec(name, spec)
            failure = self._failures.get(name)

            if(failure is not None and not (mode == CRASH and failure.mode == DISCONNECT)):
                return False

            if(mode == CRASH):
                self.operator.crash(node)
            else:
                self.operator.disconnect(node)

            self._failures[name] = NodeFailure(mode, owner)
            self._record(name, NodeState.OFF, mode)
            return True

    def recover_node(self, name: str, owner: Optional[str] = None) -> bool:
        with self._lock:
            node = self._get_spec(name)
            failure = self._failures.get(name)

            if(failure is None):
                return False
            if(owner is not None and failure.owner != owner):
                return False

            if(failure.mode == CRASH):
                self.operator.recover(node)
            else:
                self.operator.reconnect(node)

            self._failures.pop(name)
            self._record(name, NodeState.ON, RECOVERY_ACTIONS[failure.mode])
            return True

    def events(self) -> List[FailEvent]:
        return self._events.list()

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'running': self._running,
                'time': self.clock(),
                'started_at': self.started_at,
                'stopped_at': self.stopped_at,
                'targets': [
                    {
                        'kind': target.kind.value,
                        'name': target.name,
                        'fail_model': target.fail_model.to_dict(),
                        'active': self._is_target_active(target)
                    }
                    for target in self._plan.targets
                ],
                'nodes': {
                    name: NodeState.OFF.value if(name in self._failures) else NodeState.ON.value
                    for name in self._specs
                },
                'failures': {name: failure.mode for name, failure in self._failures.items()},
                'errors': list(self._errors)
            }

    def _get_spec(self, name: str, spec: Optional[NodeSpec] = None) -> NodeSpec:
        if(spec is not None):
            if(spec.name != name):
                raise ValueError(f'Spec of {spec.name} does not match container {name}')
            self._specs[name] = spec

        node = self._specs.get(name)
        if(node is None):
            raise ContainerNotFound(f'Container {name} not found.')
        return node

    def _is_target_active(self, target: FailTarget) -> bool:
        thread = self._threads.get(target_owner(target))
        return thread is not None and thread.is_alive()

    def _record(self, name: str, state: NodeState, action: str):
        self._events.append(FailEvent(name, state, action, self.clock(), self.source))

    def _safely(self, owner: str, operation: Callable[[], Any]):
        try:
            operation()
        except Exception as ex:
            message = f'{owner}: {ex}'
            with self._lock:
                self._errors.append(message)
            info(f'*** Fail error on {message}\n')

    def _wait_until(self, moment: float) -> bool:
        delay = moment - self.clock()
        if(delay <= 0):
            return not self._stop_event.is_set()
        return not self._stop_event.wait(delay)

    def _create_rng(self, owner: str) -> random.Random:
        if(self._plan.seed is None):
            return random.Random()
        return random.Random(f'{self._plan.seed}:{owner}')

    def _run_target(self, target: FailTarget, start_at: float):
        owner = target_owner(target)
        rng = self._create_rng(owner)
        model = target.fail_model

        if(isinstance(model, AvailabilityFail)):
            self._run_availability(target, model, owner, start_at, rng)
        elif(isinstance(model, TimedFail)):
            self._run_timed(target, model, owner, start_at, rng)

    def _run_timed(self, target: FailTarget, model: TimedFail, owner: str, start_at: float, rng: random.Random):
        if(not self._wait_until(start_at + model.life_time)):
            return

        names = target.node_names
        if(target.kind == TargetKind.INSTANCE):
            amount = split_amount(len(names), model.fail_rate, model.split_method, rng)
            names = select_nodes(names, amount, model.selection_method, rng)

        mode = CRASH if(isinstance(model, CrashFail)) else DISCONNECT
        for name in names:
            self._safely(owner, lambda: self.fail_node(name, mode, owner))

    def _run_availability(self, target: FailTarget, model: AvailabilityFail, owner: str, start_at: float, rng: random.Random):
        names = target.node_names
        mode = model.availability_mode.value
        down_nodes = self._create_down_nodes(target, model, rng)
        slot = 0

        while(self._wait_until(start_at + slot * model.slot_time)):
            down = down_nodes(slot)

            for name in names:
                if(name not in down):
                    self._safely(owner, lambda: self.recover_node(name, owner))

            for name in names:
                if(name in down and not self._stop_event.is_set()):
                    self._safely(owner, lambda: self.fail_node(name, mode, owner))

            elapsed_slots = math.floor((self.clock() - start_at) / model.slot_time)
            slot = max(slot + 1, elapsed_slots)

    def _create_down_nodes(self, target: FailTarget, model: AvailabilityFail, rng: random.Random) -> Callable[[int], Set[str]]:
        names = target.node_names

        if(target.kind == TargetKind.NODE):
            schedule = NodeAvailabilitySchedule(model.availability)
            return lambda slot: set() if(schedule.is_on(slot)) else set(names)

        return InstanceAvailabilitySchedule(names, model.availability, rng).down_nodes
