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
        self._node_locks: Dict[str, threading.RLock] = {}
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
            self._specs = {**{name: self._specs[name] for name in self._failures}, **plan.node_specs}
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

            self._stop_event = threading.Event()
            self._running = True
            self.started_at = start_at
            self.stopped_at = None
            self._threads = {
                target_owner(target): threading.Thread(
                    target=self._run_target,
                    args=(target, start_at, self._stop_event),
                    name=f'fail-{target_owner(target)}',
                    daemon=True
                )
                for target in self._plan.targets
            }

            for thread in self._threads.values():
                thread.start()

    def stop(self):
        with self._lock:
            if(self._running):
                self.stopped_at = self.clock()
            stop_event = self._stop_event
            threads = list(self._threads.values())

        stop_event.set()
        deadline = time.monotonic() + self.join_timeout

        for thread in threads:
            thread.join(max(0.0, deadline - time.monotonic()))

        errors = self._restore_failed_nodes()

        with self._lock:
            self._running = False

        if(errors):
            raise FailInjectionError(f'Could not restore nodes: {"; ".join(errors)}')

    def fail_node(self, name: str, mode: str, owner: Optional[str] = None, spec: Optional[NodeSpec] = None) -> bool:
        if(mode not in RECOVERY_ACTIONS):
            raise ValueError(f'Unknown fail mode: {mode}')

        with self._lock:
            node = self._get_spec(name, spec)

        with self._get_node_lock(name):
            failure = self._failures.get(name)

            if(failure is not None and not (mode == CRASH and failure.mode == DISCONNECT)):
                return False

            if(mode == CRASH):
                self.operator.crash(node)
            else:
                self.operator.disconnect(node)

            with self._lock:
                self._failures[name] = NodeFailure(mode, owner)
            self._record(name, NodeState.OFF, mode)
            return True

    def recover_node(self, name: str, owner: Optional[str] = None) -> bool:
        with self._lock:
            node = self._get_spec(name)

        with self._get_node_lock(name):
            failure = self._failures.get(name)

            if(failure is None):
                return False
            if(owner is not None and failure.owner != owner):
                return False

            if(failure.mode == CRASH):
                self.operator.recover(node)
            else:
                self.operator.reconnect(node)

            with self._lock:
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

    def _get_node_lock(self, name: str) -> threading.RLock:
        with self._lock:
            return self._node_locks.setdefault(name, threading.RLock())

    def _restore_failed_nodes(self) -> List[str]:
        errors: List[str] = []

        with self._lock:
            names = list(self._failures)

        for name in names:
            try:
                self.recover_node(name)
            except Exception as ex:
                with self._get_node_lock(name), self._lock:
                    self._failures.pop(name, None)
                    message = f'{name}: {ex}'
                    self._errors.append(f'stop: {message}')
                errors.append(message)

        return errors

    def _fail_owned_node(self, name: str, mode: str, owner: str, stop_event: threading.Event) -> bool:
        with self._get_node_lock(name):
            if(stop_event.is_set()):
                return False
            return self.fail_node(name, mode, owner)

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

    def _wait_until(self, moment: float, stop_event: threading.Event) -> bool:
        delay = moment - self.clock()
        if(delay <= 0):
            return not stop_event.is_set()
        return not stop_event.wait(delay)

    def _create_seed(self, owner: str) -> Optional[str]:
        return None if(self._plan.seed is None) else f'{self._plan.seed}:{owner}'

    def _run_target(self, target: FailTarget, start_at: float, stop_event: threading.Event):
        owner = target_owner(target)
        model = target.fail_model

        if(isinstance(model, AvailabilityFail)):
            self._run_availability(target, model, owner, start_at, stop_event)
        elif(isinstance(model, TimedFail)):
            self._run_timed(target, model, owner, start_at, stop_event)

    def _run_timed(self,
        target: FailTarget,
        model: TimedFail,
        owner: str,
        start_at: float,
        stop_event: threading.Event
    ):
        if(not self._wait_until(start_at + model.life_time, stop_event)):
            return

        rng = random.Random(self._create_seed(owner))

        names = target.node_names
        if(target.kind == TargetKind.INSTANCE):
            amount = split_amount(len(names), model.fail_rate, model.split_method, rng)
            names = select_nodes(names, amount, model.selection_method, rng)

        mode = CRASH if(isinstance(model, CrashFail)) else DISCONNECT
        for name in names:
            if(stop_event.is_set()):
                return
            self._safely(owner, lambda: self._fail_owned_node(name, mode, owner, stop_event))

    def _run_availability(self,
        target: FailTarget,
        model: AvailabilityFail,
        owner: str,
        start_at: float,
        stop_event: threading.Event
    ):
        names = target.node_names
        mode = model.availability_mode.value
        down_nodes = self._create_down_nodes(target, model, self._create_seed(owner))
        slot = 0

        while(self._wait_until(start_at + slot * model.slot_time, stop_event)):
            down = down_nodes(slot)

            for name in names:
                if(name not in down and not stop_event.is_set()):
                    self._safely(owner, lambda: self.recover_node(name, owner))

            for name in names:
                if(name in down):
                    self._safely(owner, lambda: self._fail_owned_node(name, mode, owner, stop_event))

            elapsed_slots = math.floor((self.clock() - start_at) / model.slot_time)
            slot = max(slot + 1, elapsed_slots)

    def _create_down_nodes(self, target: FailTarget, model: AvailabilityFail, seed: Optional[str]) -> Callable[[int], Set[str]]:
        names = target.node_names

        if(target.kind == TargetKind.NODE):
            schedule = NodeAvailabilitySchedule(model.availability)
            return lambda slot: set() if(schedule.is_on(slot)) else set(names)

        return InstanceAvailabilitySchedule(names, model.availability, seed).down_nodes
