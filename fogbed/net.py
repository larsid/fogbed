from mininet.net import Containernet
from mininet.node import Controller, Link
from mininet.cli import CLI

from fogbed.emulation import EmulationCore
from fogbed.node import VirtualInstance


class Fogbed(Containernet):
    def __init__(self, max_cpu=1.0, max_mem=512) -> None:
        Containernet.__init__(self)
        self.addController('c0', controller=Controller)
        EmulationCore(max_cpu, max_mem)


    def addVirtualInstance(self, label:str) -> VirtualInstance:
        if(label in EmulationCore.virtual_instances()):
            raise Exception(f"Data center label already exists: {label}")

        datacenter = VirtualInstance(label, net=self)
        EmulationCore.register(datacenter)
        datacenter.create()
        return datacenter
        

    def addLink(self, node1, node2, **params) -> Link:
        assert node1 is not None
        assert node2 is not None
        
        if(isinstance(node1, VirtualInstance)): node1 = node1.switch
        if(isinstance(node2, VirtualInstance)): node2 = node2.switch

        link = Containernet.addLink(self, node1, node2, **params)
        return link
            
    
    def startCLI(self):
        CLI(self)

        