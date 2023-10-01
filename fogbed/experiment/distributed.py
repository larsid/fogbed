from typing import Any, Dict, List, Optional

from clusternet import ClusterMonitoring

from fogbed.emulation import Services
from fogbed.exceptions import ContainerNotFound, NotEnoughResourcesAvailable, VirtualInstanceNotFound, WorkerAlreadyExists, WorkerNotFound
from fogbed.experiment import Experiment
from fogbed.helpers import (
    get_ip_address,
    start_openflow_controller,
    verify_if_container_ip_exists, 
    verify_if_container_name_exists,
    verify_if_datacenter_exists
)
from fogbed.node.container import Container
from fogbed.node.controller import Controller
from fogbed.node.instance import VirtualInstance
from fogbed.node.services.remote_docker import RemoteDocker
from fogbed.node.worker import Worker
from fogbed.resources.protocols import ResourceModel

from mininet.log import info

class FogbedDistributedExperiment(Experiment):
    def __init__(self, 
        controller_ip: Optional[str] = None, 
        controller_port: int = 6633,
        max_cpu: float = 1.0,
        max_memory: int = 512,
        metrics_enabled: bool = False
    ):
        Services(max_cpu, max_memory)
        self.controller_ip   = controller_ip
        self.controller_port = controller_port
        self.metrics_enabled = metrics_enabled
        self.workers: Dict[str, Worker] = {}
        self.is_running = False
        self.monitor = ClusterMonitoring(
            monitor_server=get_ip_address(),
            grafana_uid='fogbed'
        )


    def add_docker(self, container: Container, datacenter: VirtualInstance):
        verify_if_container_name_exists(container.name)
        verify_if_container_ip_exists(container.ip)

        try:
            datacenter.create_container(container)

            if(self.is_running):
                worker = self._get_worker_by_datacenter(datacenter)
                worker.net.add_docker(container.name, **container.params)
                worker.net.add_link(container.name, datacenter.switch)
                worker.net.config_default(container.name)
                service = RemoteDocker(container.name, worker.net.url)
                container.set_docker(service)

        except NotEnoughResourcesAvailable:
            info(f'{container.name}: Allocation of container was blocked by resource model.\n\n')

              

    def add_tunnel(self, worker1: Worker, worker2: Worker, **params: Any):
        worker1.add_tunnel(worker2.ip)
        worker2.add_tunnel(worker1.ip)
        

    def add_worker(self, ip: str, port: int = 5000, controller: Optional[Controller] = None) -> Worker:
        if(ip in self.workers):
            raise WorkerAlreadyExists(ip)

        worker = Worker(ip, port, controller)
        self.workers[worker.ip] = worker
        return worker
    

    def add_virtual_instance(self, name: str, resource_model: Optional[ResourceModel] = None) -> VirtualInstance:
        verify_if_datacenter_exists(name)
        datacenter = VirtualInstance(name, resource_model)
        Services.add_virtual_instance(datacenter)
        return datacenter


    def get_containers(self) -> List[Container]:
        return Services.get_all_containers()


    def get_docker(self, name: str) -> Container:
        container = Services.get_container_by_name(name)
        
        if(container is None):
            raise ContainerNotFound(f'Container {name} not found.')
        return container


    def get_virtual_instance(self, name: str) -> VirtualInstance:
        datacenter = Services.get_virtual_instance_by_name(name)
        if(datacenter is None):
            raise VirtualInstanceNotFound(name)
        return datacenter
    

    def get_virtual_instances(self) -> List[VirtualInstance]:
        return list(Services.virtual_instances().values())


    def get_worker(self, ip: str) -> Worker:
        if(self.workers.get(ip) is None):
            raise WorkerNotFound(ip)
        return self.workers[ip]


    def _get_worker_by_datacenter(self, datacenter: VirtualInstance) -> Worker:
        return self.workers[datacenter.get_ip()]


    def remove_docker(self, name: str):
        datacenter = Services.get_virtual_instance_by_container(name)
        datacenter.remove_container(name)

        if(self.is_running):
            worker = self._get_worker_by_datacenter(datacenter)
            worker.net.remove_link(name, datacenter.switch)
            worker.net.remove_docker(name)

    def _start_monitoring_service(self):
        if(self.metrics_enabled):
            workers = [worker.net for worker in self.workers.values()]
            self.monitor.workers = workers
            self.monitor.start()

    def start(self):
        if(self.controller_ip is None):
            self.controller_ip = get_ip_address()
            start_openflow_controller(self.controller_ip, self.controller_port)

        for worker in self.workers.values():
            worker.start(self.controller_ip, self.controller_port)
        self._start_monitoring_service()
        self.is_running = True

    
    def stop(self):
        for worker in self.workers.values():
            worker.stop()

        self.monitor.stop()
        self.is_running = False

