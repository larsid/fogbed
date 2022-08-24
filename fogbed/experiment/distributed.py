from typing import List

from MaxiNet.Frontend.maxinet import Cluster, Experiment
from MaxiNet.Frontend.maxinet.node import DockerWrapper
from MaxiNet.Frontend.partitioner import Clustering

from mininet.topo import Topo

from fogbed.emulation import EmulationCore

class FogbedDistributedExperiment:
    def __init__(self, topology: Topo) -> None:
        clustering      = Clustering(
            topologies=self.get_topologies(),
            tunnels=self.get_tunnels(topology)
        )
        cluster         = Cluster()
        self.experiment = Experiment(cluster, clustering)
    

    def get_topologies(self) -> List[Topo]:
        datacenters = EmulationCore.virtual_instances()
        
        return [
            datacenter.create_topology()
            for datacenter in datacenters.values()
        ]
    

    def get_tunnels(self, topology: Topo) -> List:
        return [
            [s1, s2, topology.linkInfo(s1, s2)]
            for s1, s2 in topology.links()  # type: ignore
        ]

    def get_node(self, name: str) -> DockerWrapper:
        return self.experiment.get_docker(name)

    def start(self):
        self.experiment.setup()

    def start_cli(self):
        self.experiment.CLI(locals(), globals())

    def stop(self):
        self.experiment.stop()
