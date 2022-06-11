from typing import Callable, Tuple
from fogbed.emulation import EmulationCore

class CPUAllocator:
    def __init__(self, compute_single_cu: Callable[[], float]) -> None:
        self.compute_single_cu = compute_single_cu

    
    def calculate(self, requested_cu: float) -> Tuple[int, int]:
        single_cu      = self.compute_single_cu()
        cpu_percentage = single_cu * requested_cu
        return self.__calculate_cpu_cfs(cpu_percentage)
    

    def __calculate_cpu_cfs(self, cpu_percentage:float) -> Tuple[int, int]:
        cpu_period = EmulationCore.cpu_period_in_microseconds()
        cpu_quota = cpu_period * cpu_percentage

        if(cpu_quota < 1000): cpu_quota = 1000
        return int(cpu_period), int(cpu_quota)


class MemoryAllocator:
    def __init__(self, compute_single_mu: Callable[[], float]) -> None:
        self.compute_single_mu = compute_single_mu

    def calculate(self, requested_mu: int) -> int:
        single_mu      = self.compute_single_mu()
        memory_limit   = single_mu * requested_mu

        if(memory_limit < 4): memory_limit = 4
        return int(memory_limit * 1024 * 1024)