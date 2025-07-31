from abc import ABC, abstractmethod


class DockerService(ABC):
    @abstractmethod
    def run_command(self, command: str) -> str:
        pass
    
    @abstractmethod
    def get_ip(self) -> str:
        pass

    @abstractmethod
    def update_cpu(self, cpu_quota: int, cpu_period: int):
        pass
    
    @abstractmethod
    def update_memory(self, memory_in_bytes: int):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass