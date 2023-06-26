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

    For the worker `ip` parameter, you can provide an IP address or hostname, and Fogbed will automatically resolve it.

To run that example, start a service in each worker with:
```
sudo RunWorker -p=5000
```
copy and save the code to a file and run it with:
```
python3 topology.py
```

## Setting Controller Address
By default, Fogbed runs an OpenFlow Controller on the machine that executes the experiment. You can manually run a controller and pass the address to the experiment.
```py

from fogbed import (
    FogbedDistributedExperiment
)

exp = FogbedDistributedExperiment(
    controller_ip='192.168.0.150',
    controller_port=6633
)
```
!!! tip
    For the `controller_ip` parameter, you can provide an IP address or hostname, and Fogbed will automatically resolve it.

To start a controller, run the command `controller -v ptcp:6633` on the target machine. You can also use other controllers, such as the <a href="https://github.com/noxrepo/pox">POX Controller</a>.


## Limiting CPU and Memory
To limit CPU and memory within the workers, use the `FogbedDistributedExperiment` class to set the `max_cpu` and `max_memory` parameters based on the number of workers in the topology.
```py
from fogbed import FogbedDistributedExperiment

workers = 3
exp     = FogbedDistributedExperiment(max_cpu=workers * 0.5, max_memory=workers * 512)
```

* `max_cpu` - sets the maximum percentage of CPU usage that can be consumed by the emulation.
* `max_memory` - defines the maximum amount of memory in megabytes that the emulation can utilize.


## Helper methods
The `FogbedDistributedExperiment` class offers some helper methods like:

<b>`add_docker`</b>
<i>(container: Container, datacenter: VirtualInstance)

* Adds a container to a virtual instance.
* Raises a `ContainerAlreadyExists` exception if name or ip already exists.
</i>


<b>`add_tunnel`</b>
<i>(worker1: Worker, worker2: Worker, **params: Any)

* Adds a tunnel between two workers.
</i>


<b>`add_virtual_instance`</b>
<i>(name: str, resource_model: Optional[ResourceModel] = None) -> VirtualInstance

* Creates a virtual instance.
* Raises a `VirtualInstanceAlreadyExists` exception if name already exists.
</i>


<b>`add_worker`</b>
<i>(ip: str, port: int = 5000, controller: Optional[Controller] = None) -> Worker

* Creates a worker.
* Raises a `WorkerAlreadyExists` exception if ip already exists.
</i>


<b>`get_containers`</b>
<i>() -> List[Container]

* Returns all containers of the emulation.
</i>


<b>`get_docker`</b>
<i>(name: str) -> Container

* Returns a container by name. 
* Raises a `ContainerNotFound` exception if name doesn't exist.
</i>


<b>`get_virtual_instance`</b>
<i>(name: str) -> VirtualInstance

* Returns a virtual instance by name.
* Raises a `VirtualInstanceNotFound` exception if name doesn't exist.
</i>


<b>`get_virtual_instances`</b>
<i>() -> List[VirtualInstance]

* Returns all virtual instances of the emulation.
</i>


<b>`get_worker`</b>
<i>(ip: str) -> Worker

* Returns a worker by ip/hostname.
* Raises a `WorkerNotFound` exception if ip/hostname doesn't exist.
</i>


<b>`remove_docker`</b>
<i>(name: str)

* Removes a container by name. 
* Raises a `ContainerNotFound` exception if name doesn't exist.
</i>


<b>`start`</b>
<i>()

* Starts the experiment. 
</i>


<b>`stop`</b>
<i>()

* Stops the experiment. 
</i>