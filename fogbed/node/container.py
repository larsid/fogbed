from typing import Any, Dict, List, Optional

from fogbed.node.services import DockerService
from fogbed.resources.flavors import HardwareResources, Resources

from mininet.util import ipAdd

class Container:
    IP_COUNTER = 0

    def __init__(self, 
        name: str, 
        ip: Optional[str] = None,
        dcmd: str = '/bin/bash',
        dimage: str = 'ubuntu:trusty',
        environment: Dict[str, Any] = {},
        port_bindings: Dict[int, int] = {},
        volumes: List[str] = [],
        resources: HardwareResources = Resources.SMALL,
        **params: Any
    ):
        self.name        = name
        self.ip          = self._get_ip(ip)
        self.dcmd        = dcmd
        self.dimage      = dimage
        self.environment = environment.copy()
        self.bindings    = port_bindings.copy()
        self.ports       = list(self.bindings.keys())
        self.volumes     = volumes.copy()
        self.resources   = resources
        self._params     = params
        self._service: Optional[DockerService] = None
    

    def cmd(self, command: str) -> str:
        if(self._service is None):
            raise Exception(f'Container {self.name} was not started')
        return self._service.run_command(command)

    def start(self):
        if(self._service is None):
            raise Exception(f'Container {self.name} was not started')
        self._service.start()

    def stop(self):
        if(self._service is None):
            raise Exception(f'Container {self.name} was not started')
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
    def compute_units(self) -> float:
        return self.resources.compute_units
    
    @property
    def memory_units(self) -> int:
        return self.resources.memory_units

    @property
    def params(self) -> Dict[str, Any]:
        self._params['ip'] = self.ip
        self._params['dcmd'] = self.dcmd
        self._params['dimage'] = self.dimage
        self._params['environment'] = self.environment
        self._params['ports'] = self.ports
        self._params['port_bindings'] = self.bindings
        self._params['volumes'] = self.volumes        
        return self._params

    def __repr__(self) -> str:
        cpu_quota  = self.cpu_quota
        cpu_period = self.cpu_period
        return f'Container(name={self.name}, cpu_quota={cpu_quota}, cpu_period={cpu_period})'
    
    def __eq__(self, other: object) -> bool:
        if(not isinstance(other, Container)): return False
        return self.name == other.name
