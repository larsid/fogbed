
from mininet.log import setLogLevel
from fogbed.net import Fogbed
from fogbed.resources import ResourceModel
from fogbed.resources.models import CloudResourceModel, EdgeResourceModel

setLogLevel('info')

if(__name__=='__main__'):
    net = Fogbed(max_cpu=0.5)#500 000 us

    try:  
        edge = net.addVirtualInstance('edge')
        cloud = net.addVirtualInstance('cloud')

        edge.assignResourceModel(EdgeResourceModel(max_cu=2))
        cloud.assignResourceModel(CloudResourceModel(max_cu=2))
        
        edge.addDocker('d1', resources=ResourceModel.SMALL)
        edge.addDocker('d2', resources=ResourceModel.SMALL)
        edge.addDocker('d3', resources=ResourceModel.SMALL)
        
        cloud.addDocker('d4', resources=ResourceModel.SMALL)
        cloud.addDocker('d5', resources=ResourceModel.SMALL)
        cloud.addDocker('d6', resources=ResourceModel.SMALL)
        cloud.addDocker('d7', resources=ResourceModel.SMALL)
        
        #print(edge.getStatus())
        #print(cloud.getStatus())

        net.addLink(edge, cloud, delay='100ms', bw=1)
        net.start()
        net.startCLI()
    except Exception as ex: print(ex)
    finally: 
        net.stop()