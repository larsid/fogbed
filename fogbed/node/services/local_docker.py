
from fogbed.node.services import DockerService

from mininet.node import Docker

class LocalDocker(DockerService):
    def __init__(self, docker: Docker) -> None:
        self.docker = docker
    
    def get_ip(self) -> str:
        return self.docker.IP()

    def run_command(self, command: str) -> str:
        return self.docker.cmd(command)
    
    def update_cpu(self, cpu_quota: int, cpu_period: int):
        self.docker.updateCpuLimit(cpu_quota, cpu_period)
    
    def update_memory(self, memory_in_bytes: int):
        self.docker.updateMemoryLimit(memory_in_bytes)
    
    def start(self):
        return self.docker.start()
    
    def stop(self):
        return self.docker.stop()