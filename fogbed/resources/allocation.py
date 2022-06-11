from mininet.node import Docker

from typing import Callable
from fogbed.emulation import EmulationCore

class CPUAllocator:
    def __init__(self, compute_single_cu: Callable[[], float]) -> None:
        self.compute_single_cu = compute_single_cu


    def allocate(self, container: Docker, requested_cu: float):
        cpu_quota    = self.calculate_cpu_quota(requested_cu)
        cpu_period   = EmulationCore.cpu_period_in_microseconds()
        container.updateCpuLimit(cpu_quota, cpu_period)    

    def calculate_cpu_quota(self, requested_cu: float) -> int:
        single_cu      = self.compute_single_cu()
        cpu_percentage = single_cu * requested_cu
        cpu_period = EmulationCore.cpu_period_in_microseconds()
        cpu_quota  = cpu_period * cpu_percentage

        if(cpu_quota < 1000): cpu_quota = 1000
        return int(cpu_quota)


class MemoryAllocator:
    def __init__(self, compute_single_mu: Callable[[], float]) -> None:
        self.compute_single_mu = compute_single_mu

    def allocate(self, container: Docker, requested_mu: int):
        memory_limit = self.calculate_memory_limit(requested_mu)
        container.updateMemoryLimit(mem_limit=memory_limit)

    def calculate_memory_limit(self, requested_mu: int) -> int:
        single_mu      = self.compute_single_mu()
        memory_limit   = single_mu * requested_mu

        if(memory_limit < 4): memory_limit = 4
        return int(memory_limit * 1024 * 1024)