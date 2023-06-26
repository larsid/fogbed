from typing import Dict, List
from fogbed import Container, FogbedExperiment

from fogbed.parsing.dto import LinkDTO, VirtualInstanceDTO


class LocalExperimentFactory:
    def __init__(self,
        containers: Dict[str, Container],
        instances: List[VirtualInstanceDTO],
        links: List[LinkDTO]
    ):
        self.experiment = FogbedExperiment()
        self.containers = containers
        self.instances  = instances
        self.links = links
    

    def create_containers(self, data: VirtualInstanceDTO):
        for name in data.containers:
            container = self.containers[name]
            instance = self.experiment.get_virtual_instance(data.name)
            self.experiment.add_docker(container, instance)


    def create_virtual_instances(self):
        for data in self.instances:
            self.experiment.add_virtual_instance(data.name, data.model)
            self.create_containers(data)

    def create_links(self):
        for link in self.links:
            node1 = self.experiment.get_virtual_instance(link.node1)
            node2 = self.experiment.get_virtual_instance(link.node2)
            self.experiment.add_link(node1, node2, **link.params)

    def build(self) -> FogbedExperiment:
        self.create_virtual_instances()
        self.create_links()
        return self.experiment