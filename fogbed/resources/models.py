from mininet.node import Docker
from mininet.log import info

from fogbed.emulation import EmulationCore
from fogbed.resources import NotEnoughResourcesAvailable, ResourceModel
from fogbed.resources.allocation import CPUAllocator


class EdgeResourceModel(ResourceModel):
    def __init__(self, max_cu=32, max_mu=512) -> None:
        super().__init__(max_cu, max_mu)

        self.cpu = CPUAllocator(
            compute_single_cu=self._compute_single_cu
        )


    def allocate_cpu(self, container: Docker):
        requested_cu = self.get_compute_units(container)
        
        if(requested_cu + self.allocated_cu > self.max_cu):
            raise NotEnoughResourcesAvailable('Not enough compute resources left.')
        
        self.allocated_cu += requested_cu
        cpu_period, cpu_quota = self.cpu.calculate(requested_cu)
        self.update_cpu_limit(container, cpu_period, cpu_quota)
    
    def free_cpu(self, container: Docker):
        requested_cu = self.get_compute_units(container)
        self.allocated_cu -= requested_cu


    def allocate_memory(self, container: Docker):
        pass

    def free_memory(self, container: Docker):
        pass

    
    def _compute_single_cu(self) -> float:
        return EmulationCore.e_cpu() / EmulationCore.compute_units()
        
    
    



# ================================================================================== #
class CloudResourceModel(EdgeResourceModel):
    def __init__(self, max_cu=32, max_mu=1024) -> None:
        super().__init__(max_cu, max_mu)

        self.cpu = CPUAllocator(
            compute_single_cu=self._compute_single_cu
        )

    def allocate_cpu(self, container: Docker):
        requested_cu = self.get_compute_units(container)
        self.allocated_cu += requested_cu
        self._update_all_containers()

    def free_cpu(self, container: Docker):
        requested_cu = self.get_compute_units(container)
        self.allocated_cu -= requested_cu
        self._update_all_containers()


    def allocate_memory(self, container: Docker):
        pass

    def free_memory(self, container: Docker):
        pass

    
    def _compute_single_cu(self) -> float:
        e_cpu = EmulationCore.e_cpu()
        compute_units = EmulationCore.compute_units()
        cpu_op_factor = self._cpu_over_provisioning_factor()
        return (e_cpu / compute_units) * cpu_op_factor

    def _cpu_over_provisioning_factor(self) -> float:
        return float(self.max_cu) / max(self.max_cu, self.allocated_cu)
    

    def _update_all_containers(self):
        info('\n*** Updating all containers\n')

        for container in self.allocated_containers:
            requested_cu = self.get_compute_units(container)
            cpu_period, cpu_quota = self.cpu.calculate(requested_cu)
            self.update_cpu_limit(container, cpu_period, cpu_quota)