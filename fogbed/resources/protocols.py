from abc import ABC, abstractmethod

from fogbed.node.container import Container


class ResourceModel(ABC):
    def __init__(self, max_cu: float, max_mu: int) -> None:
        self.max_cu = max_cu
        self.max_mu = max_mu
        self.allocated_cu = 0
        self.allocated_mu = 0


    def allocate(self, container: Container):
        self.allocate_cpu(container)
        self.allocate_memory(container)

    @abstractmethod
    def allocate_cpu(self, container: Container):
        pass

    @abstractmethod
    def allocate_memory(self, container: Container):
        pass
    

    def free(self, container: Container):
        self.free_cpu(container)
        self.free_memory(container)
    
    @abstractmethod
    def free_cpu(self, container: Container):
        pass

    @abstractmethod
    def free_memory(self, container: Container):
        pass
    