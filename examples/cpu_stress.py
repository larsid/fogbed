import time
from fogbed.net import Fogbed
from fogbed.node import VirtualInstance
from fogbed.resources import ResourceModel
from fogbed.resources.models import EdgeResourceModel

def stress(datacenter: VirtualInstance):
    for container in datacenter.containers.values():
        container.sendCmd('./start.sh')
        time.sleep(1)



try:
    net = Fogbed(max_cpu=0.5)#500 000 us
    edge = net.addVirtualInstance('edge')
    edge.assignResourceModel(EdgeResourceModel(max_cu=4))
    
    edge.addDocker('d1', dimage='mpeuster/stress', resources=ResourceModel.SMALL)
    edge.addDocker('d2', dimage='mpeuster/stress', resources=ResourceModel.SMALL)
    edge.addDocker('d3', dimage='mpeuster/stress', resources=ResourceModel.SMALL)
    edge.addDocker('d4', dimage='mpeuster/stress', resources=ResourceModel.SMALL)
    print(edge)
    
    net.start()
    stress(edge)
    net.startCLI()
except Exception as ex: print(ex)
finally: 
    net.stop()