from typing import Any, List, Optional, Type

from clusternet import ClusterMonitoring

from fogbed.emulation import Services
from fogbed.exceptions import ContainerNotFound, NotEnoughResourcesAvailable, VirtualInstanceNotFound
from fogbed.experiment import Experiment
from fogbed.helpers import (
    get_ip_address,
    verify_if_container_ip_exists,
    verify_if_container_name_exists,
    verify_if_datacenter_exists
)
from fogbed.experiment.net import Fogbed
from fogbed.node.container import Container
from fogbed.node.instance import VirtualInstance
from fogbed.node.services.local_docker import LocalDocker
from fogbed.resources.protocols import ResourceModel

from mininet.cli import CLI
from mininet.log import info
from mininet.node import Controller, Docker, OVSSwitch, Switch
from mininet.topo import Topo


class FogbedExperiment(Experiment):
    def __init__(self, 
        controller=Controller, 
        switch: Type[Switch]=OVSSwitch,
        max_cpu: float = 1.0,
        max_memory: int = 512,
        metrics_enabled: bool = False
    ):
        Services(max_cpu, max_memory)
        self.metrics_enabled = metrics_enabled
        self.topology = Topo()
        self.net = Fogbed(topo=self.topology, build=False, controller=controller, switch=switch)
        self.monitor = ClusterMonitoring(
            monitor_server=get_ip_address(),
            grafana_uid='fogbed'
        )
    

    def add_link(self, node1: VirtualInstance, node2: VirtualInstance, **params: Any):
        self.topology.addLink(node1.switch, node2.switch, **params)


    def add_virtual_instance(self, name: str, resource_model: Optional[ResourceModel] = None) -> VirtualInstance:
        verify_if_datacenter_exists(name)
        datacenter = VirtualInstance(name, resource_model)
        Services.add_virtual_instance(datacenter)
        self.topology.addSwitch(datacenter.switch)
        return datacenter
    

    def add_docker(self, container: Container, datacenter: VirtualInstance):
        verify_if_container_name_exists(container.name)
        verify_if_container_ip_exists(container.ip)
        
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
                container.set_docker(LocalDocker(docker))
    

    def get_docker(self, name: str) -> Container:
        container = Services.get_container_by_name(name)
        
        if(container is None):
            raise ContainerNotFound(f'Container {name} not found.')
        return container


    def get_containers(self) -> List[Container]:
        return Services.get_all_containers()

    def get_virtual_instance(self, name: str) -> VirtualInstance:
        datacenter = Services.get_virtual_instance_by_name(name)
        if(datacenter is None):
            raise VirtualInstanceNotFound(name)
        return datacenter

    def get_virtual_instances(self) -> List[VirtualInstance]:
        return list(Services.virtual_instances().values())


    def remove_docker(self, name: str):            
        datacenter = Services.get_virtual_instance_by_container(name)
        datacenter.remove_container(name)

        if(self.net.is_running):
            info(f'*** Removing container\n{name}\n')
            self.net.removeLink(name, datacenter.switch)
            self.net.removeDocker(name)


    def start_cli(self):
        CLI(self.net)

    def _set_docker_services(self):
        for container in self.get_containers():
            docker = self.net.getDocker(container.name)
            container.set_docker(LocalDocker(docker))

    def start(self):
        self.net.start()
        self._set_docker_services()
        if(self.metrics_enabled):
            self.monitor.start()

    def stop(self):
        self.net.stop()  
        self.monitor.stop()
