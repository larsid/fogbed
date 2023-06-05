# Distributed Emulation
A topology can be partitioned across different machines using the `FogbedDistributedExperiment` class. This class enables centralized control of a cluster of remote machines.

Unlike the `FogbedExperiment`, now we need to add the virtual instances within `Worker` objects. These workers can be connected using tunnels through the Fogbed API to allow the comunication between distributed containers.
```py
from fogbed import (
    FogbedDistributedExperiment, 
    Container
)

exp   = FogbedDistributedExperiment()

cloud = exp.add_virtual_instance('cloud')
fog   = exp.add_virtual_instance('fog')
edge  = exp.add_virtual_instance('edge')

d1 = Container('d1')
d2 = Container('d2')
d3 = Container('d3')

exp.add_docker(d1, cloud)
exp.add_docker(d2, fog)
exp.add_docker(d3, edge)

worker1 = exp.add_worker(ip='192.168.0.151', port=5000)
worker2 = exp.add_worker(ip='192.168.0.152', port=5000)

worker1.add(cloud, reachable=True)

worker2.add(fog, reachable=True)
worker2.add(edge)
worker2.add_link(fog, edge, delay='10ms')

exp.add_tunnel(worker1, worker2)

try:
    exp.start()
    print(d1.cmd(f'ping -c 4 {d3.ip}'))

except Exception as ex: 
    print(ex)
finally:
    exp.stop()
```

In this example, 3 virtual instances are distributed among 2 workers. The `cloud` instance has been added to `worker1`, while the `fog` and `edge` were added to `worker2`.

!!! note
    The `reachable` parameter establishes a connection between the virtual 
    instance and a switch gateway present in each worker. Through this gateway,
    the virtual instances can be reached by others.

Subsequently, the workers are connected using the `add_tunnel` method.

!!! tip
    Make sure the machines are connected and that the IP addresses and ports 
    are configured according to the experiment script.

To run that example, start a service in each worker with:
```
sudo RunWorker -p=5000
```
copy and save the code to a file and run it with:
```
python3 topology.py
```
