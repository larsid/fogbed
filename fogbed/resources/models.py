from fogbed.emulation import Services
from fogbed.exceptions import NotEnoughResourcesAvailable
from fogbed.node.container import Container
from fogbed.resources.protocols import ResourceModel
from fogbed.resources.allocation import CPUAllocator, MemoryAllocator


class EdgeResourceModel(ResourceModel):
    def __init__(self, max_cu: float=16, max_mu: int=512) -> None:
        super().__init__(max_cu, max_mu)

        self.cpu_allocator = CPUAllocator(
            compute_single_cu=self.calculate_cpu_percentage)

        self.memory_allocator = MemoryAllocator(
            compute_single_mu=self.calculate_memory_percentage)


    def allocate_cpu(self, container: Container):
        requested_cu = container.compute_units
        
        if(requested_cu + self.allocated_cu > self.max_cu):
            raise NotEnoughResourcesAvailable()
        
        self.allocated_cu += requested_cu
        self.cpu_allocator.allocate(container)
    

    def free_cpu(self, container: Container):
        self.allocated_cu -= container.compute_units


    def allocate_memory(self, container: Container):
        requested_mu = container.memory_units

        if(requested_mu + self.allocated_mu > self.max_mu):
            raise NotEnoughResourcesAvailable()

        self.allocated_mu += requested_mu
        self.memory_allocator.allocate(container)


    def free_memory(self, container: Container):
        self.allocated_mu -= container.memory_units

    def calculate_cpu_percentage(self) -> float:
        return Services.cpu_percentage() / Services.get_all_compute_units()

    def calculate_memory_percentage(self) -> float:
        return Services.memory_in_megabytes() / Services.get_all_memory_units()
    



# ================================================================================= #
class CloudResourceModel(EdgeResourceModel):
    def __init__(self, max_cu: float=32, max_mu: int=1024) -> None:
        super().__init__(max_cu, max_mu)
        self.allocated_containers: list[Container] = []

    def allocate_cpu(self, container: Container):
        self.allocated_containers.append(container)
        self.allocated_cu += container.compute_units
        self._update_cpu_for_all_containers()

    def free_cpu(self, container: Container):
        super().free_cpu(container)
        self.allocated_containers.remove(container)
        self._update_cpu_for_all_containers()


    def allocate_memory(self, container: Container):
        self.allocated_mu += container.memory_units
        self._update_memory_for_all_containers()


    def free_memory(self, container: Container):
        super().free_memory(container)
        self._update_memory_for_all_containers()

    
    def calculate_cpu_percentage(self) -> float:
        e_cpu = Services.cpu_percentage()
        all_compute_units = Services.get_all_compute_units()
        cpu_op_factor = self._cpu_over_provisioning_factor()
        return (e_cpu / all_compute_units) * cpu_op_factor


    def _cpu_over_provisioning_factor(self) -> float:
        return float(self.max_cu) / max(self.max_cu, self.allocated_cu)


    def calculate_memory_percentage(self) -> float:
        memory_factor = float(self.max_mu) / max(self.max_mu, self.allocated_mu)
        return super().calculate_memory_percentage() * memory_factor


    def _update_cpu_for_all_containers(self):
        for container in self.allocated_containers:
            self.cpu_allocator.allocate(container)
    
    def _update_memory_for_all_containers(self):
        for container in self.allocated_containers:
            self.memory_allocator.allocate(container)


class FogResourceModel(CloudResourceModel):
    def __init__(self, max_cu: float=32, max_mu: int=1024) -> None:
        super().__init__(max_cu, max_mu)
