from fogbed import (
    FogbedExperiment, 
    Container, Resources, 
    CloudResourceModel, EdgeResourceModel,
    setLogLevel
)

setLogLevel('info')

exp = FogbedExperiment(max_cpu=0.5, max_memory=512)

edge = exp.add_virtual_instance('edge', EdgeResourceModel(max_cu=2, max_mu=256))
cloud = exp.add_virtual_instance('cloud', CloudResourceModel(max_cu=2, max_mu=512))

d1 = Container('d1', resources=Resources.SMALL)
d2 = Container('d2', resources=Resources.SMALL)
d3 = Container('d3', resources=Resources.SMALL)
d4 = Container('d4', resources=Resources.SMALL)
d5 = Container('d5', resources=Resources.SMALL)
d6 = Container('d6', resources=Resources.SMALL)

exp.add_docker(d1, edge)
exp.add_docker(d2, edge)
exp.add_docker(d3, edge)

exp.add_docker(d4, cloud)
exp.add_docker(d5, cloud)
exp.add_docker(d6, cloud)

exp.add_link(cloud, edge)

try:
    exp.start()
    
    d7 = Container('d7', resources=Resources.SMALL)
    exp.add_docker(d7, cloud)
    print(d1.cmd(f'ping -c 4 {d7.ip}'))

except Exception as ex: 
    print(ex)
finally:
    exp.stop()
