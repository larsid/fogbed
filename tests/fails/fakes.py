import threading
import time
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from fogbed.exceptions import ContainerNotFound
from fogbed.fails.operators import NodeOperator
from fogbed.fails.plan import NodeSpec


class FakeNode:
    def __init__(self, name: str):
        self.name = name
        self.configured = False
        self.detached: List['FakeInterface'] = []
        self.ports: Dict['FakeInterface', int] = {}
        self.vsctl_calls: List[Tuple[str, ...]] = []

    def MAC(self) -> str:
        return f'00:00:00:00:00:{len(self.name):02d}'

    def configDefault(self):
        self.configured = True

    def detach(self, interface: 'FakeInterface'):
        self.detached.append(interface)

    def vsctl(self, *args: str) -> str:
        self.vsctl_calls.append(args)
        if(args[0] == 'get'):
            return f'{self.ports.get(self._interface(args[2]), 0) + 10}\n'
        return ''

    def _interface(self, name: str) -> 'FakeInterface':
        return next(interface for interface in self.ports if interface.name == name)


class FakeInterface:
    def __init__(self, node: FakeNode, port: int):
        self.node = node
        self.name = f'{node.name}-eth{port}'
        self.status: List[str] = []
        node.ports[self] = port

    def ifconfig(self, status: str):
        self.status.append(status)


class FakeLink:
    def __init__(self, node1: FakeNode, node2: FakeNode, port2: Optional[int] = None):
        self.intf1 = FakeInterface(node1, len(node1.ports))
        self.intf2 = FakeInterface(node2, len(node2.ports) + 1 if(port2 is None) else port2)


class FakeNet:
    def __init__(self, switches: Sequence[str] = ('s2',)):
        self.is_running = True
        self.nodes: Dict[str, FakeNode] = {name: FakeNode(name) for name in switches}
        self.links: List[FakeLink] = []
        self.calls: List[Any] = []

    def __contains__(self, name: str) -> bool:
        return name in self.nodes

    def __getitem__(self, name: str) -> FakeNode:
        return self.nodes[name]

    def addDocker(self, name: str, **params: Any):
        self.calls.append(('addDocker', name, params))
        self.nodes[name] = FakeNode(name)

    def removeDocker(self, name: str):
        self.calls.append(('removeDocker', name))
        self.nodes.pop(name)

    def addLink(self, node1: str, node2: str, **params: Any):
        self.calls.append(('addLink', node1, node2, params))
        self.links.append(FakeLink(self.nodes[node1], self.nodes[node2], params.get('port2')))

    def removeLink(self, node1: str, node2: str):
        self.calls.append(('removeLink', node1, node2))
        for link in self.linksBetween(self.nodes[node1], self.nodes[node2]):
            link.intf1.node.ports.pop(link.intf1)
            link.intf2.node.ports.pop(link.intf2)
            self.links.remove(link)

    def linksBetween(self, node1: FakeNode, node2: FakeNode) -> List[FakeLink]:
        return [link for link in self.links if {link.intf1.node, link.intf2.node} == {node1, node2}]


class FakeOperator(NodeOperator):
    def __init__(self, broken: Optional[Set[str]] = None, missing: Optional[Set[str]] = None, delay: float = 0.0):
        self.calls: List[Tuple[str, str]] = []
        self.broken = broken or set()
        self.missing = missing or set()
        self.delay = delay
        self._lock = threading.Lock()

    def _call(self, action: str, node: NodeSpec):
        time.sleep(self.delay)
        if(node.name in self.missing):
            raise ContainerNotFound(f'Container {node.name} not found.')
        if(node.name in self.broken):
            raise RuntimeError(f'{node.name} is broken')
        with self._lock:
            self.calls.append((action, node.name))

    def crash(self, node: NodeSpec): self._call('crash', node)
    def recover(self, node: NodeSpec): self._call('recover', node)
    def disconnect(self, node: NodeSpec): self._call('disconnect', node)
    def reconnect(self, node: NodeSpec): self._call('reconnect', node)
    def exists(self, name: str) -> bool: return True
