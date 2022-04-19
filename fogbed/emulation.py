from typing import Dict
from fogbed.node import VirtualInstance


_emulation_core = {
    'cpu_period': 1000000,
    'max_cpu': 1.0,
    'max_mem': 512,
}

_nodes: 'dict[str, VirtualInstance]' = {}

class EmulationCore:
    '''Essa classe possibilita o acesso das variaveis globais do ambiente de emulacao'''
    def __init__(self, max_cpu:float, max_mem:int) -> None:
        global _emulation_core
        _emulation_core['max_cpu'] = max_cpu
        _emulation_core['max_mem'] = max_mem

    @staticmethod
    def register(datacenter: VirtualInstance):
        '''Registra uma nova instancia virtual'''
        _nodes[datacenter.label] = datacenter
    
    @staticmethod
    def nodes() -> Dict[str, VirtualInstance]:
        '''Retorna todas as instancias virtuais do ambiente de emulacao'''
        return _nodes

    @staticmethod
    def cpu_period() -> float:
        '''Retorna a quantidade total de CPU time em microsegundos'''
        return _emulation_core['cpu_period']

    @staticmethod
    def e_cpu() -> float:
        '''Retorna o percentual de CPU disponivel para emulacao'''
        return _emulation_core['max_cpu']

    @staticmethod
    def compute_units() -> float:
        '''Retorna a quantidade total de CUs disponivel nos datacenters'''
        return sum([dc.getComputeUnits() for dc in _nodes.values()])