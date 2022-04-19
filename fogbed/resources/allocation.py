from typing import Callable
from fogbed.emulation import EmulationCore

class CPUAllocator:
    def __init__(self, compute_single_cu: Callable[[], float]) -> None:
        self.compute_single_cu = compute_single_cu

    
    def calculate(self, requested_cu: float):
        single_cu      = self.compute_single_cu()
        cpu_percentage = single_cu * requested_cu
        cpu_period, cpu_quota = self.calculate_cpu_cfs(cpu_percentage)

        return cpu_period, cpu_quota
    

    def calculate_cpu_cfs(self, cpu_percentage:float):
        cpu_period = EmulationCore.cpu_period()
        cpu_quota = cpu_period * cpu_percentage

        if(cpu_quota < 1000): cpu_quota = 1000
        return int(cpu_period), int(cpu_quota)