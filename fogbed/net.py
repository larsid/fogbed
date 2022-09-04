from mininet.net import Containernet
from mininet.node import Host
from mininet.link import Link

from fogbed.node.instance import VirtualInstance

class Fogbed(Containernet):
    def __init__(self, **params):
        super().__init__(**params)
        self.is_running = False
    
    def addLink(self, node1, node2, **params) -> Link:
        assert node1 is not None
        assert node2 is not None
        
        if(isinstance(node1, VirtualInstance)): node1 = node1.switch
        if(isinstance(node2, VirtualInstance)): node2 = node2.switch

        return Containernet.addLink(self, node1, node2, **params)


    def removeLink(self, node1, node2, **params):
        assert node1 is not None
        assert node2 is not None
        
        if(isinstance(node1, VirtualInstance)): node1 = node1.switch
        if(isinstance(node2, VirtualInstance)): node2 = node2.switch

        return Containernet.removeLink(self, node1, node2, **params)

    def getHost(self, name: str) -> Host:
        return self[name]

    def start(self):
        self.is_running = True
        super().start()

    def stop(self):
        self.is_running = False
        super().stop()