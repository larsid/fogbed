from abc import ABC, abstractmethod
from typing import List, Optional

from fogbed.node.container import Container
from fogbed.node.instance import VirtualInstance
from fogbed.resources.protocols import ResourceModel


class Experiment(ABC):
    @abstractmethod
    def add_virtual_instance(self, name: str, resource_model: Optional[ResourceModel] = None) -> VirtualInstance:
        pass
    
    @abstractmethod
    def add_docker(self, container: Container, datacenter: VirtualInstance):
        pass

    @abstractmethod
    def get_docker(self, name: str) -> Container:
        pass
    
    @abstractmethod
    def get_containers(self) -> List[Container]:
        pass

    @abstractmethod
    def get_virtual_instance(self, name: str) -> VirtualInstance:
        pass
    
    @abstractmethod
    def get_virtual_instances(self) -> List[VirtualInstance]:
        pass        

    @abstractmethod
    def remove_docker(self, name: str):            
        pass

    @abstractmethod
    def start(self):
        pass
    
    @abstractmethod
    def stop(self):
        pass
