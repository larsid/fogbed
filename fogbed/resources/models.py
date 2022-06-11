from mininet.node import Docker

from fogbed.emulation import EmulationCore
from fogbed.resources import NotEnoughResourcesAvailable, ResourceModel
from fogbed.resources.allocation import CPUAllocator, MemoryAllocator


class EdgeResourceModel(ResourceModel):
    def __init__(self, max_cu=32, max_mu=512) -> None:
        super().__init__(max_cu, max_mu)

        self.cpu_allocator = CPUAllocator(
            compute_single_cu=self.calculate_cpu_percentage)

        self.memory_allocator = MemoryAllocator(
            compute_single_mu=self.calculate_memory_percentage)


    def allocate_cpu(self, container: Docker):
        requested_cu = self.get_compute_units(container)
        
        if(requested_cu + self.allocated_cu > self.max_cu):
            raise NotEnoughResourcesAvailable()
        
        self.allocated_cu += requested_cu
        self.cpu_allocator.allocate(container, requested_cu)
    

    def free_cpu(self, container: Docker):
        requested_cu = self.get_compute_units(container)
        self.allocated_cu -= requested_cu


    def allocate_memory(self, container: Docker):
        requested_mu = self.get_memory_units(container)

        if(requested_mu + self.allocated_mu > self.max_mu):
            raise NotEnoughResourcesAvailable()

        self.allocated_mu += requested_mu
        self.memory_allocator.allocate(container, requested_mu)


    def free_memory(self, container: Docker):
        requested_mu = self.get_memory_units(container)
        self.allocated_mu -= requested_mu

    def calculate_cpu_percentage(self) -> float:
        return EmulationCore.cpu_percentage() / EmulationCore.get_all_compute_units()

    def calculate_memory_percentage(self) -> float:
        return EmulationCore.memory_in_megabytes() / EmulationCore.get_all_memory_units()
    



# ================================================================================== #
class CloudResourceModel(EdgeResourceModel):
    def __init__(self, max_cu=32, max_mu=1024) -> None:
        super().__init__(max_cu, max_mu)


    def allocate_cpu(self, container: Docker):
        requested_cu = self.get_compute_units(container)
        self.allocated_cu += requested_cu
        self._update_cpu_for_all_containers()

    def free_cpu(self, container: Docker):
        super().free_cpu(container)
        self._update_cpu_for_all_containers()


    def allocate_memory(self, container: Docker):
        requested_mu = self.get_memory_units(container)
        self.allocated_mu += requested_mu
        self._update_memory_for_all_containers()


    def free_memory(self, container: Docker):
        super().free_memory(container)
        self._update_memory_for_all_containers()

    
    def calculate_cpu_percentage(self) -> float:
        e_cpu = EmulationCore.cpu_percentage()
        all_compute_units = EmulationCore.get_all_compute_units()
        cpu_op_factor = self._cpu_over_provisioning_factor()
        return (e_cpu / all_compute_units) * cpu_op_factor


    def _cpu_over_provisioning_factor(self) -> float:
        return float(self.max_cu) / max(self.max_cu, self.allocated_cu)


    def calculate_memory_percentage(self) -> float:
        memory_factor = float(self.max_mu) / max(self.max_mu, self.allocated_mu)
        return super().calculate_memory_percentage() * memory_factor


    def _update_cpu_for_all_containers(self):
        for container in self.allocated_containers:
            requested_cu = self.get_compute_units(container)
            self.cpu_allocator.allocate(container, requested_cu)
    
    def _update_memory_for_all_containers(self):
        for container in self.allocated_containers:
            requested_mu = self.get_memory_units(container)
            self.memory_allocator.allocate(container, requested_mu)