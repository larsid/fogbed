from abc import ABC, abstractmethod
from mininet.node import Docker


DEFAULT_RESOURCES = dict(
    tiny   = {'cu': 0.5,  'mu': 32},
    small  = {'cu': 1.0,  'mu': 128},
    medium = {'cu': 4.0,  'mu': 256},
    large  = {'cu': 8.0,  'mu': 512},
    xlarge = {'cu': 16.0, 'mu': 1024},
)


class ResourceModel(ABC):
    TINY   = DEFAULT_RESOURCES['tiny']
    SMALL  = DEFAULT_RESOURCES['small']
    MEDIUM = DEFAULT_RESOURCES['medium']
    LARGE  = DEFAULT_RESOURCES['large']
    XLARGE = DEFAULT_RESOURCES['xlarge']

    def __init__(self, max_cu: float, max_mu: int) -> None:
        self.max_cu = max_cu
        self.max_mu = max_mu
        self.allocated_cu = 0
        self.allocated_mu = 0
        self.allocated_containers: list[Docker] = []


    def allocate(self, container: Docker):
        self.allocated_containers.append(container)
        self.allocate_cpu(container)
        self.allocate_memory(container)

    @abstractmethod
    def allocate_cpu(self, container: Docker):
        pass

    @abstractmethod
    def allocate_memory(self, container: Docker):
        pass
    

    def free(self, container:Docker):
        self.allocated_containers.remove(container)
        self.free_cpu(container)
        self.free_memory(container)
    
    @abstractmethod
    def free_cpu(self, container: Docker):
        pass

    @abstractmethod
    def free_memory(self, container: Docker):
        pass


    def get_compute_units(self, container: Docker) -> float:
        return container.params['resources']['cu']
    
    def get_memory_units(self, container: Docker) -> int:
        return container.params['resources']['mu']

    def update_cpu_limit(self, container: Docker, cpu_period:int, cpu_quota: int):
        if(container.resources['cpu_period'] != cpu_period or container.resources['cpu_quota'] != cpu_quota):
            container.updateCpuLimit(cpu_quota=cpu_quota, cpu_period=cpu_period)
            #info(f"{container.name}: update cpu_quota={cpu_quota}, cpu_op_factor={self.cpu_op_factor}\n\n")
    

    
class NotEnoughResourcesAvailable(BaseException):
    pass