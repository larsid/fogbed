from fogbed.helpers import resolve_ip


class Controller:
    def __init__(self, ip: str, port: int) -> None:
        self.ip = resolve_ip(ip)
        self.port = port
    
    def __str__(self) -> str:
        return f'Controller(ip={self.ip}, port={self.port})'