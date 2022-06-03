from typing import Dict
from fogbed.node import VirtualInstance

CPU_PERIOD = 1000000
MAX_CPU = 1.0
MAX_MEM = 512

NODES: Dict[str, VirtualInstance] = {}

class EmulationCore:
    '''Essa classe possibilita o acesso das variaveis globais do ambiente de emulacao'''
    def __init__(self, max_cpu:float, max_mem:int) -> None:
        global MAX_CPU, MAX_MEM
        MAX_CPU = max_cpu
        MAX_MEM = max_mem

    @staticmethod
    def register(datacenter: VirtualInstance):
        '''Registra uma nova instancia virtual'''
        NODES[datacenter.label] = datacenter
    
    @staticmethod
    def nodes() -> Dict[str, VirtualInstance]:
        '''Retorna todas as instancias virtuais do ambiente de emulacao'''
        return NODES

    @staticmethod
    def cpu_period() -> float:
        '''Retorna a quantidade total de CPU time em microsegundos'''
        return CPU_PERIOD

    @staticmethod
    def max_cpu() -> float:
        '''Retorna o percentual de CPU disponivel para emulacao'''
        return MAX_CPU
    
    @staticmethod
    def max_memory() -> int:
        return MAX_MEM

    @staticmethod
    def get_all_compute_units() -> float:
        '''Retorna a soma de CUs disponivel nos datacenters'''
        return sum([dc.getComputeUnits() for dc in NODES.values()])

    @staticmethod
    def get_all_memory_units() -> int:
        '''Retorna a soma da memoria disponivel nos datacenters'''
        return sum([dc.getMemoryUnits() for dc in NODES.values()])