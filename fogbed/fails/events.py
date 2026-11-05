import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional


class NodeState(Enum):
    ON = 'on'
    OFF = 'off'


@dataclass(frozen=True)
class FailEvent:
    node: str
    state: NodeState
    action: str
    timestamp: float
    source: str = 'local'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'node': self.node,
            'state': self.state.value,
            'action': self.action,
            'timestamp': self.timestamp,
            'source': self.source
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'FailEvent':
        try:
            return FailEvent(
                node=str(data['node']),
                state=NodeState(data['state']),
                action=str(data['action']),
                timestamp=float(data['timestamp']),
                source=str(data.get('source', 'local'))
            )
        except (KeyError, TypeError) as ex:
            raise ValueError(f'Invalid fail event: {ex}')


class EventLog:
    def __init__(self):
        self._lock = threading.Lock()
        self._events: List[FailEvent] = []

    def append(self, event: FailEvent):
        with self._lock:
            self._events.append(event)

    def list(self) -> List[FailEvent]:
        with self._lock:
            return list(self._events)

    def clear(self):
        with self._lock:
            self._events.clear()


@dataclass(frozen=True)
class NodeMetrics:
    node: str
    uptime: float
    downtime: float
    failures: int
    repairs: int

    @property
    def availability(self) -> Optional[float]:
        total = self.uptime + self.downtime
        return self.uptime / total if(total > 0) else None

    @property
    def mtbf(self) -> Optional[float]:
        return self.uptime / self.failures if(self.failures > 0) else None

    @property
    def mttr(self) -> Optional[float]:
        return self.downtime / self.failures if(self.failures > 0) else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'node': self.node,
            'uptime': self.uptime,
            'downtime': self.downtime,
            'failures': self.failures,
            'repairs': self.repairs,
            'availability': self.availability,
            'mtbf': self.mtbf,
            'mttr': self.mttr
        }


def _node_metrics(node: str, events: List[FailEvent], start: float, end: float) -> NodeMetrics:
    state = NodeState.ON
    last_time = start
    uptime = downtime = 0.0
    failures = repairs = 0

    for event in events:
        timestamp = min(max(event.timestamp, start), end)
        if(event.state == state):
            continue

        if(state == NodeState.ON):
            uptime += timestamp - last_time
            failures += 1
        else:
            downtime += timestamp - last_time
            repairs += 1

        state = event.state
        last_time = timestamp

    if(state == NodeState.ON):
        uptime += end - last_time
    else:
        downtime += end - last_time

    return NodeMetrics(node, uptime, downtime, failures, repairs)


def compute_metrics(
    events: Iterable[FailEvent],
    start: float,
    end: float,
    nodes: Optional[Iterable[str]] = None
) -> Dict[str, NodeMetrics]:
    if(end < start):
        raise ValueError('end must not be before start')

    by_node: Dict[str, List[FailEvent]] = {name: [] for name in (nodes or [])}

    for event in sorted(events, key=lambda event: event.timestamp):
        by_node.setdefault(event.node, []).append(event)

    return {
        node: _node_metrics(node, node_events, start, end)
        for node, node_events in by_node.items()
    }
