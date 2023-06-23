from typing import Any, Dict, List, Optional

from clusternet.client.worker import RemoteWorker

from fogbed.exceptions import VirtualInstanceAlreadyExists, VirtualInstanceNotFound
from fogbed.helpers import get_tunnel_command, resolve_ip
from fogbed.node.controller import Controller
from fogbed.node.instance import VirtualInstance
from fogbed.node.link import Link
from fogbed.node.services.remote_docker import RemoteDocker


class Worker:
    def __init__(self, 
        ip: str, 
        port: int, 
        controller: Optional[Controller] = None
    ):
        self.ip = ip
        self.controller = controller
        self.datacenters: Dict[str, VirtualInstance] = {}
        self.tunnels: List[str] = []
        self.links: List[Link] = []
        self.net = RemoteWorker(ip, port)
        

    def add(self, datacenter: VirtualInstance, reachable: bool = False):
        if(datacenter.switch in self.datacenters):
            raise VirtualInstanceAlreadyExists(f'Datacenter {datacenter.label} already exists.')
        
        datacenter.set_ip(self.ip)
        datacenter.set_reachable(reachable)
        self.datacenters[datacenter.switch] = datacenter


    def add_link(self, node1: VirtualInstance, node2: VirtualInstance, **params: Any):
        if(not node1.switch in self.datacenters):
            raise VirtualInstanceNotFound(node1.label)
        if(not node2.switch in self.datacenters):
            raise VirtualInstanceNotFound(node2.label)
        self.links.append(Link(node1.switch, node2.switch, **params))


    def add_tunnel(self, destination_ip: str):
        if(destination_ip == self.ip):
            raise Exception('Tunnel loops are not allowed')
        if(destination_ip in self.tunnels):
            raise Exception(f'Already exist a tunnel to worker with ip={destination_ip}')
        self.tunnels.append(destination_ip)
    

    def _create_topology(self):
        for datacenter in self.datacenters.values():
            self.net.add_switch(datacenter.switch)

            for container in datacenter:
                self.net.add_docker(container.name, **container.params)
                self.net.add_link(container.name, datacenter.switch)
                service = RemoteDocker(container.name, self.net.url)
                container.set_docker(service)

        for link in self.links:
            self.net.add_link(**link.to_dict)


    def _get_valid_switchname(self) -> str:
        switch_indexes = [int(name[1:]) for name in self.datacenters.keys()]
        switch_indexes.sort()
        return f's{switch_indexes.pop() + 1}'
    

    def _create_links_to_gateway(self, gateway: str):
        self.net.add_switch(gateway)

        for datacenter in self.datacenters.values():
            if(datacenter.is_reachable):
                self.net.add_link(datacenter.switch, gateway)
    

    def _create_tunnels(self, gateway: str):
        for index, ip in enumerate(self.tunnels):
            interface = f'{gateway}-gre{index+1}'
            command = get_tunnel_command(port=gateway, interface=interface, ip=resolve_ip(ip))
            self.net.run_command(gateway, command)

    @property
    def is_running(self) -> bool:
        return self.net.is_running

    def start(self, controller_ip: str, controller_port: int):
        if(not self.datacenters):
            raise Exception(f'[{self.ip}]: Expecting at least 1 VirtualInstance')

        if(self.controller is None):
            self.controller = Controller(controller_ip, controller_port)

        self.net.add_controller('c0', self.controller.ip, self.controller.port)
        self._create_topology()
        
        gateway = self._get_valid_switchname()
        self._create_links_to_gateway(gateway)
        self.net.start()
        self._create_tunnels(gateway)
    
    def stop(self):
        self.net.stop()

    def __eq__(self, other: object) -> bool:
        if(not isinstance(other, Worker)): return False
        return self.ip == other.ip
