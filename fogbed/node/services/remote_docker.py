
from fogbed.node.services import DockerService
from clusternet.client.container import RemoteContainer

class RemoteDocker(DockerService):
    def __init__(self, name: str, url: str) -> None:
        self.docker = RemoteContainer(name, url)

    def get_ip(self) -> str:
        return self.docker.get_ip()
    
    def run_command(self, command: str) -> str:
        return self.docker.cmd(command)
    
    def update_cpu(self, cpu_quota: int, cpu_period: int):
        self.docker.update_cpu(cpu_quota, cpu_period)
    
    def update_memory(self, memory_in_bytes: int):
        self.docker.update_memory(memory_in_bytes)
    
    def start(self):
        self.docker.start()
    
    def stop(self):
        self.docker.stop()