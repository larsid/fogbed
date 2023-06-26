from typing import Dict, List

from fogbed import Container, FogbedDistributedExperiment

from fogbed.parsing.dto import VirtualInstanceDTO, WorkerDTO, TunnelDTO
from fogbed.parsing.exceptions import ParseTunnelsException


class DistributedExperimentFactory:
    def __init__(self,
        containers: Dict[str, Container],
        instances: List[VirtualInstanceDTO],
        workers: Dict[str, WorkerDTO],
        tunnels: List[TunnelDTO]
    ):
        self.experiment = FogbedDistributedExperiment()
        self.containers = containers
        self.instances  = instances
        self.workers    = workers
        self.tunnels    = self._resolve_worker_ips(tunnels)


    def add_instances_to_worker(self, data: WorkerDTO):
        worker = self.experiment.workers[data.ip]
        for name in data.instances:
            reachable = data.instance_is_reachable(name)
            instance = self.experiment.get_virtual_instance(name)
            worker.add(instance, reachable)


    def create_links(self, data: WorkerDTO):
        worker = self.experiment.workers[data.ip]
        for link in data.links:
            node1 = self.experiment.get_virtual_instance(link.node1)
            node2 = self.experiment.get_virtual_instance(link.node2)
            worker.add_link(node1, node2, **link.params)
    

    def create_containers(self, data: VirtualInstanceDTO):
        for name in data.containers:
            container = self.containers[name]
            instance = self.experiment.get_virtual_instance(data.name)
            self.experiment.add_docker(container, instance)


    def create_virtual_instances(self):
        for data in self.instances:
            self.experiment.add_virtual_instance(data.name, data.model)
            self.create_containers(data)


    def create_workers(self):
        for data in self.workers.values():
            self.experiment.add_worker(data.ip, data.port)
            self.add_instances_to_worker(data)
            self.create_links(data)


    def _resolve_worker_ips(self, tunnels: List[TunnelDTO]) -> List[TunnelDTO]:
        try:
            return [
                TunnelDTO(
                    worker1=self.workers[tunnel.worker1].ip,
                    worker2=self.workers[tunnel.worker2].ip
                )
                for tunnel in tunnels
            ]
        except KeyError as ex:
            raise ParseTunnelsException(f'Worker {ex} was not defined.')


    def create_tunnels(self):
        for tunnel in self.tunnels:
            worker1 = self.experiment.get_worker(tunnel.worker1)
            worker2 = self.experiment.get_worker(tunnel.worker2)
            self.experiment.add_tunnel(worker1, worker2)


    def build(self) -> FogbedDistributedExperiment:
        self.create_virtual_instances()
        self.create_workers()
        self.create_tunnels()

        return self.experiment