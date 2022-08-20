from itertools import chain
from typing import Dict, Optional

from fogbed.node.container import Container
from fogbed.resources import NotEnoughResourcesAvailable, ResourceModel

from mininet.log import info
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
            raise Exception(f'Container {name} already exists.')
        
        self.set_default_params(params)
        self.create_container(name, **params)
    
    
    def create_container(self, name: str, **params):
        if(self.resource_model is None):
            return None
        
        container = Container(name, **params)
        
        try:
            self.resource_model.allocate(container)
        except NotEnoughResourcesAvailable:
            info(f'{name}: Allocation of container was blocked by resource model.\n\n')
        else:
            self.containers[name] = container
        
    
    def create_switch(self) -> str:
        VirtualInstance.COUNTER += 1
        return self.topology.addSwitch(f's{VirtualInstance.COUNTER}')
    
    def set_default_params(self, container_params: dict):
        if(container_params.get('dimage') is None):
            container_params['dimage'] = 'ubuntu:trusty'

        if(container_params.get('resources') is None):
            container_params['resources'] = ResourceModel.TINY
    

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

    def __iter__( self ):
        for container in chain(self.containers.values()):
            yield container
