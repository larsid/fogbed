from typing import Any
from mininet.net import Containernet
from mininet.node import Docker
from mininet.link import TCLink

from fogbed.node.instance import VirtualInstance

class Fogbed(Containernet):
    def __init__(self, **params):
        super().__init__(link=TCLink, **params)
        self.is_running = False
    
    def addLink(self, node1, node2, **params: Any):
        assert node1 is not None
        assert node2 is not None
        
        if(isinstance(node1, VirtualInstance)): node1 = node1.switch
        if(isinstance(node2, VirtualInstance)): node2 = node2.switch

        super().addLink(node1, node2, **params)


    def removeLink(self, node1, node2, **params: Any):
        assert node1 is not None
        assert node2 is not None
        
        if(isinstance(node1, VirtualInstance)): node1 = node1.switch
        if(isinstance(node2, VirtualInstance)): node2 = node2.switch

        super().removeLink(node1=node1, node2=node2, **params)

    def getDocker(self, name: str) -> Docker:
        container_names = [docker.name for docker in self.hosts]
        if(not name in container_names):
            raise Exception(f'Container {name} not found.')
            
        return self[name]

    def start(self):
        self.is_running = True
        super().start()

    def stop(self):
        self.is_running = False
        super().stop()