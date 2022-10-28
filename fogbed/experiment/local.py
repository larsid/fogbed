from typing import List, Type

from fogbed.emulation import EmulationCore
from fogbed.exceptions import ContainerAlreadyExists, ContainerNotFound, NotEnoughResourcesAvailable, VirtualInstanceAlreadyExists
from fogbed.experiment import Experiment
from fogbed.net import Fogbed
from fogbed.node.container import Container
from fogbed.node.instance import VirtualInstance
from fogbed.resources import ResourceModel

from mininet.cli import CLI
from mininet.log import info
from mininet.node import Controller, Docker, OVSSwitch, Switch
from mininet.topo import Topo


class FogbedExperiment(Experiment):
    def __init__(self, controller=Controller, switch: Type[Switch]=OVSSwitch) -> None:
        self.topology = Topo()
        self.net = Fogbed(topo=self.topology, build=False, controller=controller, switch=switch)
    

    def add_link(self, node1: VirtualInstance, node2: VirtualInstance, **params):
        self.topology.addLink(node1.switch, node2.switch, **params)


    def add_virtual_instance(self, name: str, resource_model: ResourceModel) -> VirtualInstance:
        if(name in EmulationCore.virtual_instances()):
            raise VirtualInstanceAlreadyExists(f'Datacenter {name} already exists.')
        
        datacenter = VirtualInstance(name)
        datacenter.assignResourceModel(resource_model)
        EmulationCore.add_virtual_instance(datacenter)
        self.topology.addSwitch(datacenter.switch)
        return datacenter
    

    def add_docker(self, container: Container, datacenter: VirtualInstance):
        if(container in self.get_containers()):
            raise ContainerAlreadyExists(f'Container {container.name} already exists.')
        
        try:
            datacenter.create_container(container)
        except NotEnoughResourcesAvailable:
            info(f'{container.name}: Allocation of container was blocked by resource model.\n\n')
        else:
            self.topology.addHost(container.name, cls=Docker, **container.params)
            self.topology.addLink(container.name, datacenter.switch)

            if(self.net.is_running):
                self.net.addDocker(container.name, **container.params)
                self.net.addLink(container.name, datacenter.switch)
                docker = self.net.getDocker(container.name)
                docker.configDefault()
                container.set_docker(self.net[container.name])


    def get_docker(self, name: str) -> Container:
        for container in self.get_containers():
            if(name == container.name): return container
        raise ContainerNotFound(f'Container {name} not found.')


    def get_containers(self) -> List[Container]:
        return EmulationCore.get_all_containers()


    def get_virtual_instances(self) -> List[VirtualInstance]:
        return list(EmulationCore.virtual_instances().values())


    def remove_docker(self, name: str):            
        datacenter = EmulationCore.get_virtual_instance_by_container(name)
        datacenter.remove_container(name)

        if(self.net.is_running):
            info(f'*** Removing container\n{name}\n')
            self.net.removeLink(name, datacenter.switch)
            self.net.removeDocker(name)


    def start_cli(self):
        CLI(self.net)

    def start(self):
        self.net.start()
        for container in self.get_containers():
            container.set_docker(self.net[container.name])

    def stop(self):
        self.net.stop()
