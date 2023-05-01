from typing import Any, Dict

from fogbed.helpers import resolve_ip


class Controller:
    def __init__(self, ip: str, port: int) -> None:
        self.ip = resolve_ip(ip)
        self.port = port
    
    def __str__(self) -> str:
        return f'Controller(ip={self.ip}, port={self.port})'


class Link:
    def __init__(self, node1: str, node2: str, **params: Any):
        self.node1  = node1
        self.node2  = node2
        self.params = params

    @property
    def to_dict(self) -> Dict[str, Any]:
        self.params['node1'] = self.node1
        self.params['node2'] = self.node2
        return self.params
