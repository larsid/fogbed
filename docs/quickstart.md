After having installed fogbed you can start an example topology. Copy the example below and save to a file:

```py
from fogbed import (
    FogbedExperiment, Container, setLogLevel
)

setLogLevel('info')

exp = FogbedExperiment()

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
```
and then run it with:
```
sudo python3 example.py
```

In this example we are checking the command `ifconfig` inside the host `d1` that is inside the Virtual Instance `cloud`, and running the ping command to test the reachability between `d1` and `d3`.