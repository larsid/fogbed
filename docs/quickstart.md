After having installed fogbed you can start an example topology. Copy the example below and save to a file:

```py title="topology.py"
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
    
except Exception as ex: 
    print(ex)
finally:
    exp.stop()
```
and then run it with:
```
sudo python3 topology.py
```

Here we have the instantiation of a fog topology followed by the definition of 3 Virtual Instances. A `VirtualInstance` in the context of fogbed is a unit that can have one or more containers linked together by a single switch.

In this example we are checking the command `ifconfig` inside the host `d1` that is inside the Virtual Instance `cloud`, and running the ping command to test the reachability between `d1` and `d3`.

```py
>>> print(d1.cmd(f'ping -c 4 {d3.ip}'))
'''
PING 10.0.0.3 (10.0.0.3) 56(84) bytes of data.
64 bytes from 10.0.0.3: icmp_seq=1 ttl=64 time=16.1 ms
64 bytes from 10.0.0.3: icmp_seq=2 ttl=64 time=0.414 ms
64 bytes from 10.0.0.3: icmp_seq=3 ttl=64 time=0.050 ms
64 bytes from 10.0.0.3: icmp_seq=4 ttl=64 time=0.074 ms

--- 10.0.0.3 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3051ms
rtt min/avg/max/mdev = 0.050/4.161/16.108/6.899 ms
'''
```