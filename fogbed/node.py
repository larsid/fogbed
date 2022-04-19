from mininet.net import Containernet
from mininet.node import Switch, Docker
from mininet.log import info

from fogbed.resources import ResourceModel, NotEnoughResourcesAvailable

DCDPID_BASE = 1000

class VirtualInstance(object):
    ''' Representa um ponto de presenca (PoP) onde e possivel adicionar 
        e remover containers e computar recursos em tempo de execucao
    '''
    COUNTER = 1

    def __init__(self, label:str) -> None:
        self.net:Containernet               = None
        self.label                          = label
        self.name                           = f'dc{VirtualInstance.COUNTER}'
        self.containers:dict[str, Docker]   = {}
        self.switch:Switch                  = None
        self._resource_model:ResourceModel  = None


    def create(self):
        VirtualInstance.COUNTER += 1
        self.switch = self.net.addSwitch(self.name, pid=hex(self._next_process_id())[2:])


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
        
        self.net.removeLink(link=None, node1=container, node2=self.switch)
        self.net.removeDocker(name)
        del self.containers[name]


    def assignResourceModel(self, resource_model: ResourceModel):
        self._resource_model = resource_model
    

    def getComputeUnits(self) -> float:
        if(self._resource_model is None): return 0.0
        return self._resource_model.max_cu


    def __str__(self) -> str:
        max_cu = self._resource_model.max_cu
        max_mu = self._resource_model.max_mu

        status = f'{self.label}: max_cu={max_cu}, max_mu={max_mu}\n'
        for container in self.containers.values():
            status += f'{container.name}: cpu_quota={container.resources["cpu_quota"]}\n'
        return status



    def _all_containers_names(self) -> 'list[str]':
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


    def _next_process_id(self):
        global DCDPID_BASE
        DCDPID_BASE += 1
        return DCDPID_BASE