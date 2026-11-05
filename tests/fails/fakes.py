import threading
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from fogbed.exceptions import ContainerNotFound
from fogbed.fails.operators import NodeOperator
from fogbed.fails.plan import NodeSpec


class FakeNode:
    def __init__(self, name: str):
        self.name = name
        self.configured = False
        self.detached: List['FakeInterface'] = []

    def configDefault(self):
        self.configured = True

    def detach(self, interface: 'FakeInterface'):
        self.detached.append(interface)


class FakeInterface:
    def __init__(self, node: FakeNode):
        self.node = node
        self.status: List[str] = []

    def ifconfig(self, status: str):
        self.status.append(status)


class FakeLink:
    def __init__(self, node1: FakeNode, node2: FakeNode):
        self.intf1 = FakeInterface(node1)
        self.intf2 = FakeInterface(node2)


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
        self.links.append(FakeLink(self.nodes[node1], self.nodes[node2]))

    def removeLink(self, node1: str, node2: str):
        self.calls.append(('removeLink', node1, node2))
        self.links = [link for link in self.links if {link.intf1.node.name, link.intf2.node.name} != {node1, node2}]

    def linksBetween(self, node1: FakeNode, node2: FakeNode) -> List[FakeLink]:
        return [link for link in self.links if {link.intf1.node, link.intf2.node} == {node1, node2}]


class FakeOperator(NodeOperator):
    def __init__(self, broken: Optional[Set[str]] = None, missing: Optional[Set[str]] = None):
        self.calls: List[Tuple[str, str]] = []
        self.broken = broken or set()
        self.missing = missing or set()
        self._lock = threading.Lock()

    def _call(self, action: str, node: NodeSpec):
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
