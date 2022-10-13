from typing import List

from fogbed.emulation import EmulationCore
from fogbed.exceptions import VirtualInstanceAlreadyExists
from fogbed.node.instance import VirtualInstance

from mininet.topo import Topo


class FogTopo(Topo):
    def __init__(self) -> None:
        super().__init__()


    def addLink(self, node1: VirtualInstance, node2: VirtualInstance, **params) -> int:
        return Topo.addLink(self, node1.switch, node2.switch, **params)
    
    
    def addVirtualInstance(self, name: str) -> VirtualInstance:
        if(name in EmulationCore.virtual_instances()):
            raise VirtualInstanceAlreadyExists(f'Datacenter {name} already exists.')
        
        datacenter = VirtualInstance(name=name, topology=self)
        EmulationCore.add_virtual_instance(datacenter)
        return datacenter
    
    
    def create(self):
        datacenters = EmulationCore.virtual_instances()
        
        for datacenter in datacenters.values():
            for container in datacenter:
                super().addLink(container.name, datacenter.switch)
    

    def get_topologies(self) -> List[Topo]:
        datacenters = EmulationCore.virtual_instances()
        
        return [
            datacenter.create_topology()
            for datacenter in datacenters.values()
        ]
    

    def get_tunnels(self) -> List:
        return [
            [s1, s2, self.linkInfo(s1, s2)]
            for s1, s2 in self.links()  # type: ignore
        ]
