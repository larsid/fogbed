from mininet.node import Docker
from mininet.log import info

from fogbed.emulation import EmulationCore
from fogbed.resources import NotEnoughResourcesAvailable, ResourceModel


class EdgeResourceModel(ResourceModel):
    def __init__(self, max_cu=32, max_mu=512) -> None:
        super().__init__(max_cu, max_mu)
        self.raise_no_cpu_resources_left = True
        self.cpu_op_factor = 1.0
        

    def allocate(self, container: Docker):
        self.allocated_containers[container.name] = container
        self._allocate_cpu(container)
        self._allocate_memory(container)
        self._apply_limits(container)


    def _allocate_cpu(self, container: Docker):
        requested_cu = self.get_compute_units(container)
        
        if(requested_cu + self.allocated_cu > self.max_cu and self.raise_no_cpu_resources_left):
            raise NotEnoughResourcesAvailable('Not enough compute resources left.')
        self.allocated_cu += requested_cu
    
    
    def _apply_limits(self, container:Docker):
        single_cu      = self._compute_single_cu()
        requested_cu   = self.get_compute_units(container)
        cpu_percentage = single_cu * requested_cu
        cpu_period, cpu_quota = self._calculate_cpu_cfs(cpu_percentage)

        if(not self.raise_no_cpu_resources_left):
            self._update_all_containers(cpu_period, cpu_quota)
        else:
            self._update_cpu_limit(container, cpu_period, cpu_quota)

    
    def _compute_single_cu(self)->float:
        return EmulationCore.e_cpu() / EmulationCore.compute_units()
        

    def _calculate_cpu_cfs(self, cpu_percentage:float):
        cpu_period = EmulationCore.cpu_period()
        cpu_quota = cpu_period * cpu_percentage

        if(cpu_quota < 1000):
            cpu_quota = 1000
            info('Increased CPU quota to avoid system error.')
        return int(cpu_period), int(cpu_quota)


    def _update_cpu_limit(self, container: Docker, cpu_period:int, cpu_quota: int):
        if(container.resources['cpu_period'] != cpu_period or container.resources['cpu_quota'] != cpu_quota):
            container.updateCpuLimit(cpu_quota=cpu_quota, cpu_period=cpu_period)
            info(f"{container.name}: update cpu_quota={cpu_quota}, cpu_op_factor={self.cpu_op_factor}\n\n")
    

    def _update_all_containers(self, cpu_period: int, cpu_quota: int):
        info('\n*** Updating all containers\n')
        for container in self.allocated_containers.values():
            self._update_cpu_limit(container, cpu_period, cpu_quota)
        


    def _allocate_memory(self, container: Docker):
        pass



# ================================================================================== #
class CloudResourceModel(EdgeResourceModel):
    def __init__(self, max_cu=32, max_mu=1024) -> None:
        super().__init__(max_cu, max_mu)
        self.raise_no_cpu_resources_left = False


    def _compute_single_cu(self) -> float:
        e_cpu = EmulationCore.e_cpu()
        compute_units = EmulationCore.compute_units()
        self.cpu_op_factor = self._cpu_over_provisioning_factor()
        return (e_cpu / compute_units) * self.cpu_op_factor

    def _cpu_over_provisioning_factor(self)->float:
        return float(self.max_cu) / max(self.max_cu, self.allocated_cu)