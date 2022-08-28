from typing import Type
from MaxiNet.Frontend.maxinet import Cluster, Experiment
from MaxiNet.Frontend.maxinet.node import DockerWrapper
from MaxiNet.Frontend.partitioner import Clustering

from fogbed.emulation import EmulationCore
from fogbed.node.instance import VirtualInstance
from fogbed.node.container import Container
from fogbed.topo import FogTopo

from mininet.node import Docker, OVSSwitch, Switch


class FogbedDistributedExperiment:
    def __init__(self, topology: FogTopo, switch: Type[Switch]=OVSSwitch) -> None:
        clustering      = Clustering(
            topologies=topology.get_topologies(),
            tunnels=topology.get_tunnels()
        )
        cluster         = Cluster()
        self.experiment = Experiment(cluster, clustering, switch=switch)

    
    def add_docker(self, container: Container, datacenter: VirtualInstance): 
        worker_id = self.experiment.get_worker_id_by_nodename(datacenter.switch)
        
        try:
            datacenter.create_container(container)
            self.experiment.addHost(container.name, cls=Docker, wid=worker_id, **container.params)
            self.experiment.addLink(container.name, datacenter.switch, autoconf=True)
        except Exception as ex:
            print(ex)
        else:
            self.update_containers(datacenter)


    def get_node(self, name: str) -> DockerWrapper:
        return self.experiment.get_docker(name)

    def start(self):
        self.experiment.setup()
        for datacenter in EmulationCore.virtual_instances().values():
            self.update_containers(datacenter)

    def update_containers(self, datacenter: VirtualInstance):
        for container in datacenter:
            node = self.get_node(container.name)
            node.updateCpuLimit(container.cpu_quota, container.cpu_period)
            node.updateMemoryLimit(container.mem_limit)

    def start_cli(self):
        self.experiment.CLI(locals(), globals())

    def stop(self):
        self.experiment.stop()
