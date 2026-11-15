import threading
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Tuple

from fogbed.exceptions import ContainerNotFound, FailInjectionError
from fogbed.fails.plan import NodeSpec

from mininet.link import TCLink


class NodeOperator(ABC):
    @abstractmethod
    def crash(self, node: NodeSpec):
        pass

    @abstractmethod
    def recover(self, node: NodeSpec):
        pass

    @abstractmethod
    def disconnect(self, node: NodeSpec):
        pass

    @abstractmethod
    def reconnect(self, node: NodeSpec):
        pass

    @abstractmethod
    def exists(self, name: str) -> bool:
        pass


class ContainernetOperator(NodeOperator):
    def __init__(self,
        net_provider: Callable[[], Any],
        on_recover: Optional[Callable[[NodeSpec, Any], None]] = None
    ):
        self.net_provider = net_provider
        self.on_recover   = on_recover
        self._macs: Dict[str, str] = {}
        self._ports: Dict[str, Tuple[Optional[int], Optional[str]]] = {}
        self._lock = threading.Lock()

    def exists(self, name: str) -> bool:
        return name in self.net_provider()

    def crash(self, node: NodeSpec):
        with self._lock:
            net = self._get_running_net()
            interface = self._get_switch_interface(net, node)
            switch = net[node.switch]

            self._ports[node.name] = (switch.ports.get(interface), self._get_ofport(switch, interface))
            self._macs[node.name] = net[node.name].MAC()

            if(hasattr(switch, 'detach')):
                switch.detach(interface)

            net.removeLink(node1=node.name, node2=node.switch)
            net.removeDocker(node.name)

    def recover(self, node: NodeSpec):
        with self._lock:
            net = self._get_running_net()

            if(node.switch not in net):
                raise FailInjectionError(f'Switch {node.switch} not found')
            if(node.name in net and net.linksBetween(net[node.name], net[node.switch])):
                raise FailInjectionError(f'Container {node.name} is already running')

            params = dict(node.params)
            if(node.name in self._macs):
                params.setdefault('mac', self._macs[node.name])

            port, ofport = self._ports.get(node.name, (None, None))
            link_params = dict(node.link_params)
            if(port is not None):
                link_params['port2'] = port

            if(node.name not in net):
                net.addDocker(node.name, **params)
            net.addLink(node.name, node.switch, cls=TCLink, **link_params)

            if(ofport is not None):
                interface = self._get_switch_interface(net, node)
                net[node.switch].vsctl('set', 'Interface', interface.name, f'ofport_request={ofport}')

            docker = net[node.name]
            docker.configDefault()

            if(self.on_recover is not None):
                self.on_recover(node, docker)

    def disconnect(self, node: NodeSpec):
        self._set_link_status(node, 'down')

    def reconnect(self, node: NodeSpec):
        self._set_link_status(node, 'up')

    def _set_link_status(self, node: NodeSpec, status: str):
        with self._lock:
            net = self._get_running_net()
            self._get_switch_interface(net, node).ifconfig(status)

    def _get_ofport(self, switch: Any, interface: Any) -> Optional[str]:
        if(not hasattr(switch, 'vsctl')):
            return None

        ofport = str(switch.vsctl('get', 'Interface', interface.name, 'ofport')).strip()
        return ofport if(ofport.isdigit()) else None

    def _get_running_net(self) -> Any:
        net = self.net_provider()
        if(not getattr(net, 'is_running', True)):
            raise FailInjectionError('Network is not running')
        return net

    def _get_switch_interface(self, net: Any, node: NodeSpec) -> Any:
        if(node.name not in net):
            raise ContainerNotFound(f'Container {node.name} not found.')
        if(node.switch not in net):
            raise FailInjectionError(f'Switch {node.switch} not found')

        links = net.linksBetween(net[node.name], net[node.switch])
        if(not links):
            raise FailInjectionError(f'No link between {node.name} and {node.switch}')

        link = links[0]
        return link.intf1 if(link.intf1.node.name == node.switch) else link.intf2
