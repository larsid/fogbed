from abc import ABC, abstractmethod

from fogbed.node.container import Container


PREDEFINED_RESOURCES = dict(
    tiny   = {'cu': 0.5,  'mu': 32},
    small  = {'cu': 1.0,  'mu': 128},
    medium = {'cu': 4.0,  'mu': 256},
    large  = {'cu': 8.0,  'mu': 512},
    xlarge = {'cu': 16.0, 'mu': 1024},
)


class ResourceModel(ABC):
    TINY   = PREDEFINED_RESOURCES['tiny']
    SMALL  = PREDEFINED_RESOURCES['small']
    MEDIUM = PREDEFINED_RESOURCES['medium']
    LARGE  = PREDEFINED_RESOURCES['large']
    XLARGE = PREDEFINED_RESOURCES['xlarge']

    def __init__(self, max_cu: float, max_mu: int) -> None:
        self.max_cu = max_cu
        self.max_mu = max_mu
        self.allocated_cu = 0
        self.allocated_mu = 0
        self.allocated_containers: list[Container] = []


    def allocate(self, container: Container):
        self.allocated_containers.append(container)
        self.allocate_cpu(container)
        self.allocate_memory(container)

    @abstractmethod
    def allocate_cpu(self, container: Container):
        pass

    @abstractmethod
    def allocate_memory(self, container: Container):
        pass
    

    def free(self, container: Container):
        self.allocated_containers.remove(container)
        self.free_cpu(container)
        self.free_memory(container)
    
    @abstractmethod
    def free_cpu(self, container: Container):
        pass

    @abstractmethod
    def free_memory(self, container: Container):
        pass
    

