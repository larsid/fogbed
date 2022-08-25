from typing import Dict, List
from fogbed.node.container import Container
from fogbed.node.instance import VirtualInstance

CPU_PERIOD = 1000000
MAX_CPU = 1.0
MAX_MEM = 512

nodes: Dict[str, VirtualInstance] = {}

class EmulationCore:
    def __init__(self, max_cpu:float, max_mem:int) -> None:
        global MAX_CPU, MAX_MEM
        MAX_CPU = max_cpu
        MAX_MEM = max_mem

    @staticmethod
    def register(datacenter: VirtualInstance):
        nodes[datacenter.label] = datacenter
    
    @staticmethod
    def virtual_instances() -> Dict[str, VirtualInstance]:
        return nodes

    @staticmethod
    def cpu_period_in_microseconds() -> int:
        return CPU_PERIOD

    @staticmethod
    def cpu_percentage() -> float:
        return MAX_CPU
    
    @staticmethod
    def memory_in_megabytes() -> int:
        return MAX_MEM

    @staticmethod
    def get_all_compute_units() -> float:
        return sum([dc.compute_units for dc in nodes.values()])

    @staticmethod
    def get_all_memory_units() -> int:
        return sum([dc.memory_units for dc in nodes.values()])
    
    @staticmethod
    def get_all_containers() -> List[Container]:
        return [
            container
            for datacenter in nodes.values()
            for container in datacenter
        ]
        