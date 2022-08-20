from typing import List, Optional

from mininet.net import Containernet
from mininet.node import Switch, Docker
from mininet.log import info

from fogbed.resources import ResourceModel, NotEnoughResourcesAvailable


class VirtualInstance(object):
    COUNTER = 0

    def __init__(self, label:str, net: Containernet) -> None:
        VirtualInstance.COUNTER             += 1
        self.net                             = net
        self.label                           = label
        self.name                            = f'dc{VirtualInstance.COUNTER}'
        self.switch: Switch                  = self.net.addSwitch(self.name)
        self.containers: dict[str, Docker]   = {}
        self.resource_model: Optional[ResourceModel] = None


    def addDocker(self, name:str, **params) -> 'Docker | None':
        self._verify_container_exists(name)
        self._set_default_params(params)
        
        container = self.net.addDocker(name, **params)
        container = self._update_container_resources(container)
        return container


    def removeDocker(self, name: str):
        if(name not in self.containers):
            raise Exception(f'Container with name {name} not found')
        
        container = self.containers[name]

        if(self._resource_model is not None):
            self._resource_model.free(container)
        
        self.net.removeLink(node1=container, node2=self.switch)
        self.net.removeDocker(name)
        del self.containers[name]


    def assignResourceModel(self, resource_model: ResourceModel):
        self._resource_model = resource_model
    

    def getComputeUnits(self) -> float:
        if(self._resource_model is None): return 0.0
        return self._resource_model.max_cu

    def getMemoryUnits(self) -> int:
        if(self._resource_model is None): return 0
        return self._resource_model.max_mu

    def __str__(self) -> str:
        max_cu = self._resource_model.max_cu
        max_mu = self._resource_model.max_mu

        status = f'{self.label}: max_cu={max_cu}, max_mu={max_mu}\n'
        for container in self.containers.values():
            cpu_quota = container.resources['cpu_quota']
            mem_limit = container.resources['mem_limit']
            status += f'{container.name}: cpu_quota={cpu_quota}, mem_limit={mem_limit/(1024*1024)} MB\n'
        return status



    def _all_containers_names(self) -> List[str]:
        host_is_docker = lambda host: isinstance(host, Docker)
        containers = list(filter(host_is_docker, self.net.hosts))
        return [c.name for c in containers]


    def _update_container_resources(self, container: Docker) -> 'Docker | None':
        if(self._resource_model is None): return
        
        try:
            self._resource_model.allocate(container)
        except NotEnoughResourcesAvailable:
            info(f'{container.name}: Allocation of container was blocked by resource model.\n\n')
            self.net.removeDocker(container.name)
            return None
        
        self.net.addLink(container, self.switch)
        self.containers[container.name] = container
        return container
    

    def _set_default_params(self, container_params: dict):
        if(container_params.get('dimage') is None):
            container_params['dimage'] = 'ubuntu:trusty'

        if(container_params.get('resources') is None):
            container_params['resources'] = ResourceModel.TINY


    def _verify_container_exists(self, name: str):
        if(name in self._all_containers_names()):
            raise Exception(f'Container {name} already exists')
