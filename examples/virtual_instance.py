from fogbed.emulation import EmulationCore
from fogbed.experiment import FogbedExperiment
from fogbed.resources import ResourceModel
from fogbed.resources.models import CloudResourceModel, EdgeResourceModel
from fogbed.topo import FogTopo

from mininet.log import setLogLevel

setLogLevel('info')

EmulationCore(max_cpu=0.5, max_mem=512)
topo = FogTopo()

edge  = topo.addVirtualInstance('edge')
cloud = topo.addVirtualInstance('cloud')
topo.addLink(edge, cloud, delay='100ms', bw=1)

edge.assignResourceModel(EdgeResourceModel(max_cu=2, max_mu=256))
cloud.assignResourceModel(CloudResourceModel(max_cu=2, max_mu=512))

edge.addDocker('d1', resources=ResourceModel.SMALL)
edge.addDocker('d2', resources=ResourceModel.SMALL)
edge.addDocker('d3', resources=ResourceModel.SMALL)

cloud.addDocker('d4', resources=ResourceModel.SMALL)
cloud.addDocker('d5', resources=ResourceModel.SMALL)
cloud.addDocker('d6', resources=ResourceModel.SMALL)
cloud.addDocker('d7', resources=ResourceModel.SMALL)

print(f'{edge}\n')
print(f'{cloud}\n')

exp = FogbedExperiment(topo)

try:
    exp.start()
    
    d1 = exp.get_node('d1')
    d6 = exp.get_node('d6')
    
    print(d1.cmd(f'ping -c 5 {d6.IP()}'))

except Exception as ex: 
    print(ex)
finally:
    exp.stop()
