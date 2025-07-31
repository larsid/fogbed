from fogbed.emulation import Services
from fogbed.experiment.local import FogbedExperiment
from fogbed.node.container import Container
from fogbed.resources.flavors import Resources
from fogbed.resources.models import CloudResourceModel, EdgeResourceModel, FogResourceModel

from mininet.log import setLogLevel

setLogLevel('info')

Services(max_cpu=0.5, max_mem=512)
exp = FogbedExperiment()

cloud = exp.add_virtual_instance('cloud', CloudResourceModel(max_cu=8, max_mu=1024))
fog   = exp.add_virtual_instance('fog',   FogResourceModel(max_cu=4, max_mu=512))
edge  = exp.add_virtual_instance('edge',  EdgeResourceModel(max_cu=2, max_mu=256))

d1 = Container('d1', ip='10.0.0.1', dimage='ubuntu:trusty', resources=Resources.SMALL)
d2 = Container('d2', ip='10.0.0.2', dimage='ubuntu:trusty', resources=Resources.SMALL)
d3 = Container('d3', ip='10.0.0.3', dimage='ubuntu:trusty', resources=Resources.SMALL)
d4 = Container('d4', ip='10.0.0.4', dimage='ubuntu:trusty', resources=Resources.SMALL)
d5 = Container('d5', ip='10.0.0.5', dimage='ubuntu:trusty', resources=Resources.SMALL)
d6 = Container('d6', ip='10.0.0.6', dimage='ubuntu:trusty', resources=Resources.SMALL)
d7 = Container('d7', ip='10.0.0.7', dimage='ubuntu:trusty', resources=Resources.SMALL)

exp.add_docker(d1, cloud)

exp.add_docker(d2, fog)
exp.add_docker(d3, fog)
exp.add_docker(d4, fog)

exp.add_docker(d5, edge)
exp.add_docker(d6, edge)
exp.add_docker(d7, edge)

exp.add_link(cloud, fog)
exp.add_link(fog, edge)

try:
    exp.start()
    
    print(d1.cmd('ifconfig'))
    print(d1.cmd(f'ping -c 4 {d6.ip}'))
    
    exp.start_cli()
except Exception as ex: 
    print(ex)
finally:
    exp.stop()
