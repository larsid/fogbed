from typing import Dict, List
from fogbed.exceptions import ContainerNotFound
from fogbed.node.container import Container
from fogbed.node.instance import VirtualInstance

CPU_PERIOD = 1000000
MAX_CPU = 1.0
MAX_MEM = 512

nodes: Dict[str, VirtualInstance] = {}

class Services:
    def __init__(self, max_cpu: float, max_mem: int) -> None:
        global MAX_CPU, MAX_MEM
        MAX_CPU = max_cpu
        MAX_MEM = max_mem

    @staticmethod
    def add_virtual_instance(datacenter: VirtualInstance):
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
    
    @staticmethod
    def get_virtual_instance_by_container(name: str) -> VirtualInstance:
        for datacenter in nodes.values():
            if(name in datacenter.containers):
                return datacenter
        raise ContainerNotFound(f'Container {name} not found.')
    
    @staticmethod
    def get_virtual_instance_by_name(name: str) -> 'VirtualInstance | None':
        return nodes.get(name)

    @staticmethod
    def get_container_by_ip(ip: str) -> 'Container | None':
        for container in Services.get_all_containers():
            if(container.ip == ip):
                return container
        return None
    
    @staticmethod
    def get_container_by_name(name: str) -> 'Container | None':
        for container in Services.get_all_containers():
            if(container.name == name):
                return container
        return None
    