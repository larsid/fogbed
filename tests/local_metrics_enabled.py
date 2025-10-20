from fogbed import (
    FogbedExperiment, Container
)

exp = FogbedExperiment(metrics_enabled=True)

cloud = exp.add_virtual_instance('cloud')
fog   = exp.add_virtual_instance('fog')
edge  = exp.add_virtual_instance('edge')

d1 = Container('d1', ip='10.0.0.1', dimage='ubuntu:trusty')
d2 = Container('d2', ip='10.0.0.2', dimage='ubuntu:trusty')
d3 = Container('d3', ip='10.0.0.3', dimage='ubuntu:trusty')

exp.add_docker(d1, cloud)
exp.add_docker(d2, fog)
exp.add_docker(d3, edge)

exp.add_link(cloud, fog)
exp.add_link(fog, edge)

try:
    exp.start()

    print(d1.cmd('ifconfig'))
    print(d1.cmd(f'ping -c 4 {d3.ip}'))
    exp.start_cli()
    
except Exception as ex: 
    print(ex)
finally:
    exp.stop()

# Run with: fogbed run tests/local_metrics_enabled.py