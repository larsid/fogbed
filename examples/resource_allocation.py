from mininet.log import setLogLevel
from fogbed.net import Fogbed
from fogbed.resources import ResourceModel
from fogbed.resources.models import CloudResourceModel, EdgeResourceModel

setLogLevel('info')

net = Fogbed(max_cpu=0.5, max_mem=512)#500 000 us

try:  
    edge = net.addVirtualInstance('edge')
    cloud = net.addVirtualInstance('cloud')

    edge.assignResourceModel(EdgeResourceModel(max_cu=2, max_mu=256))
    cloud.assignResourceModel(CloudResourceModel(max_cu=2, max_mu=512))
    
    edge.addDocker('d1', resources=ResourceModel.SMALL)
    edge.addDocker('d2', resources=ResourceModel.SMALL)
    edge.addDocker('d3', resources=ResourceModel.SMALL)
    
    cloud.addDocker('d4', resources=ResourceModel.SMALL)
    cloud.addDocker('d5', resources=ResourceModel.SMALL)
    cloud.addDocker('d6', resources=ResourceModel.SMALL)
    cloud.addDocker('d7', resources=ResourceModel.SMALL)
    
    print(edge)
    print(cloud)

    net.addLink(edge, cloud, delay='100ms', bw=1)
    net.start()
    net.startCLI()
except Exception as ex: print(ex)
finally: 
    net.stop()