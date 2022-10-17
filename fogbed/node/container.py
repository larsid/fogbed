from typing import Any, Dict, Optional

from mininet.node import Docker

class Container:
    def __init__(self, name: str, **params) -> None:
        self.name   = name
        self.params = params
        self._docker: Optional[Docker] = None
    
    def cmd(self, command: str) -> str:
        if(self._docker is None):
            raise Exception(f'Docker container {self.name} was not started')
        return self._docker.cmd(command)

    def start(self):
        if(self._docker is None):
            raise Exception(f'Docker container {self.name} was not started')
        self._docker.start()

    def stop(self):
        if(self._docker is None):
            raise Exception(f'Docker container {self.name} was not started')
        self._docker.stop()

    def set_docker(self, docker: Docker):
        self._docker = docker

    def update_cpu(self, cpu_quota: int, cpu_period: int):
        if(self._docker is not None):
            self._docker.updateCpuLimit(cpu_quota, cpu_period)

        self.params['cpu_quota'] = cpu_quota
        self.params['cpu_period'] = cpu_period

    def update_memory(self, memory_limit: int):
        if(self._docker is not None):
            self._docker.updateMemoryLimit(memory_limit)

        self.params['mem_limit'] = memory_limit

    @property
    def cpu_period(self) -> int:
        cpu_period = self.params.get('cpu_period')
        return -1 if(cpu_period is None) else cpu_period

    @property
    def cpu_quota(self) -> int:
        cpu_quota = self.params.get('cpu_quota')
        return -1 if(cpu_quota is None) else cpu_quota

    @property
    def mem_limit(self) -> int:
        mem_limit = self.params.get('mem_limit')
        return -1 if(mem_limit is None) else mem_limit

    @property
    def resources(self) -> 'Dict[str, Any] | None':
        return self.params.get('resources')
    
    @property
    def compute_units(self) -> float:
        resources = self.resources
        return 0.0 if(resources is None) else resources['cu']
    
    @property
    def memory_units(self) -> int:
        resources = self.resources
        return 0 if(resources is None) else resources['mu']
    
    @property
    def ip(self) -> str:
        return self._docker.IP() if(self._docker is not None) else ''


    @staticmethod
    def from_dict(params: Dict[str, Any]):
        required_params = ['name', 'dimage', 'cpu_period', 'cpu_quota', 'mem_limit']
        
        for param in required_params:
            if(params.get(param) is None):
                raise Exception(f'Missing param container.{param}')
        
        return Container(**params) 

    def __repr__(self) -> str:
        cpu_quota  = self.cpu_quota
        cpu_period = self.cpu_period
        return f'Container(name={self.name}, cpu_quota={cpu_quota}, cpu_period={cpu_period})'
    
    def __eq__(self, other: object) -> bool:
        if(not isinstance(other, Container)): return False
        return self.name == other.name
