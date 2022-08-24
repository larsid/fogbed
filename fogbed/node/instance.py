from itertools import chain
from typing import Dict, Optional
from fogbed.exceptions import ContainerAlreadyExists, NotEnoughResourcesAvailable, ResourceModelNotFound

from fogbed.node.container import Container
from fogbed.resources import ResourceModel

from mininet.log import info
from mininet.node import Docker
from mininet.topo import Topo


class VirtualInstance(object):
    COUNTER = 0

    def __init__(self, name: str, topology: Topo) -> None:
        self.label    = name
        self.topology = topology
        self.switch   = self.create_switch()
        self.containers: Dict[str, Container] = {}
        self.resource_model: Optional[ResourceModel] = None
        
    
    def assignResourceModel(self, resource_model: ResourceModel):
        self.resource_model = resource_model
    

    def addDocker(self, name: str, **params):
        if(name in self.topology.hosts()):
            raise ContainerAlreadyExists(f'Container {name} already exists.')
        
        container = Container(name, **params)
        try:
            self.create_container(container)
        except NotEnoughResourcesAvailable:
            info(f'{name}: Allocation of container was blocked by resource model.\n\n')
    
    
    def create_container(self, container: Container):
        if(self.resource_model is None):
            raise ResourceModelNotFound('Assign a resource model to this virtual instance.')
        
        self.set_default_params(container)
        self.resource_model.allocate(container)
        self.containers[container.name] = container

    
    def create_switch(self) -> str:
        VirtualInstance.COUNTER += 1
        return self.topology.addSwitch(f's{VirtualInstance.COUNTER}')
    
    def set_default_params(self, container: Container):
        if(container.params.get('dimage') is None):
            container.params['dimage'] = 'ubuntu:trusty'

        if(container.resources is None):
            container.params['resources'] = ResourceModel.TINY
    
    def create_topology(self) -> Topo:
        topology = Topo()
        topology.addSwitch(self.switch)
        
        for container in self.containers.values():
            topology.addHost(container.name, cls=Docker, **container.params)
            topology.addLink(container.name, self.switch)
        return topology

    @property
    def compute_units(self) -> float:
        if(self.resource_model is None): return 0.0
        return self.resource_model.max_cu
    
    @property
    def memory_units(self) -> int:
        if(self.resource_model is None): return 0
        return self.resource_model.max_mu

    def __repr__(self) -> str:
        containers = [repr(container) for container in self.containers.values()]
        header = f'[{self.label}]\n'
        return header + '\n'.join(containers)

    def __iter__(self):
        for container in chain(self.containers.values()):
            yield container
