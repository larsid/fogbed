from typing import Any, Dict, Optional

from fogbed.node.services import DockerService

from mininet.util import ipAdd

class Container:
    IP_COUNTER = 0

    def __init__(self, 
        name: str, 
        ip: Optional[str] = None, 
        **params
    ):
        self.name    = name
        self.ip      = self._get_ip(ip)
        self._params = params
        self._service: Optional[DockerService] = None
    

    def cmd(self, command: str) -> str:
        if(self._service is None):
            raise Exception(f'Docker container {self.name} was not started')
        return self._service.run_command(command)

    def start(self):
        if(self._service is None):
            raise Exception(f'Docker container {self.name} was not started')
        self._service.start()

    def stop(self):
        if(self._service is None):
            raise Exception(f'Docker container {self.name} was not started')
        self._service.stop()

    def set_docker(self, service: DockerService):
        self._service = service

    def update_cpu(self, cpu_quota: int, cpu_period: int):
        if(self._service is not None):
            self._service.update_cpu(cpu_quota, cpu_period)

        self._params['cpu_quota'] = cpu_quota
        self._params['cpu_period'] = cpu_period

    def update_memory(self, memory_limit: int):
        if(self._service is not None):
            self._service.update_memory(memory_limit)

        self._params['mem_limit'] = memory_limit

    def _get_ip(self, ip: Optional[str]) -> str:
        if(ip is None):
            Container.IP_COUNTER += 1
            return ipAdd(Container.IP_COUNTER)
        
        return ip

    @property
    def cpu_period(self) -> int:
        cpu_period = self._params.get('cpu_period')
        return -1 if(cpu_period is None) else cpu_period

    @property
    def cpu_quota(self) -> int:
        cpu_quota = self._params.get('cpu_quota')
        return -1 if(cpu_quota is None) else cpu_quota

    @property
    def mem_limit(self) -> int:
        mem_limit = self._params.get('mem_limit')
        return -1 if(mem_limit is None) else mem_limit

    @property
    def resources(self) -> 'Dict[str, Any] | None':
        return self._params.get('resources')
    
    @property
    def compute_units(self) -> float:
        resources = self.resources
        return 0.0 if(resources is None) else resources['cu']
    
    @property
    def memory_units(self) -> int:
        resources = self.resources
        return 0 if(resources is None) else resources['mu']

    @property
    def params(self) -> Dict[str, Any]:
        self._params['ip'] = self.ip
        return self._params

    def __repr__(self) -> str:
        cpu_quota  = self.cpu_quota
        cpu_period = self.cpu_period
        return f'Container(name={self.name}, cpu_quota={cpu_quota}, cpu_period={cpu_period})'
    
    def __eq__(self, other: object) -> bool:
        if(not isinstance(other, Container)): return False
        return self.name == other.name
