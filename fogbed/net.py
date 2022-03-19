from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI

from fogbed.emulation import EmulationCore
from fogbed.node import VirtualInstance


class FogTopo(Containernet):
    def __init__(self, max_cpu=1.0, max_mem=512) -> None:
        Containernet.__init__(self)
        self.addController('c0', controller=Controller)
        EmulationCore(max_cpu, max_mem)


    def addVirtualInstance(self, label:str):
        if(label in EmulationCore.nodes()):
            raise Exception(f"Data center label already exists: {label}")

        datacenter = VirtualInstance(label)
        datacenter.net = self  # set reference to network
        EmulationCore.register(datacenter)
        datacenter.create()
        return datacenter
        

    def addLink(self, node1, node2, **params):
        assert node1 is not None
        assert node2 is not None
        
        if(isinstance(node1, VirtualInstance)): node1 = node1.switch
        if(isinstance(node2, VirtualInstance)): node2 = node2.switch

        link = Containernet.addLink(self, node1, node2, **params)
        return link
            
    
    def startCLI(self):
        CLI(self)

        