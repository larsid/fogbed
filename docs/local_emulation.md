You can create custom topologies and run locally with Containernet using the `FogbedExperiment` class.
```py
from fogbed import Container, FogbedExperiment

exp   = FogbedExperiment()
cloud = exp.add_virtual_instance('cloud')
edge  = exp.add_virtual_instance('edge')

d1 = Container('d1')
d2 = Container('d2')
exp.add_docker(container=d1, datacenter=cloud)
exp.add_docker(container=d2, datacenter=edge)

exp.add_link(cloud, edge, delay='50ms')

try:
    exp.start()
    print(d1.cmd(f'ping -c 4 {d2.ip}'))

except Exception as ex:
    print(ex)
finally:
    exp.stop()
```


## Limiting CPU and Memory
```py
from fogbed import FogbedExperiment

exp = FogbedExperiment(max_cpu=0.5, max_memory=512)
```

* `max_cpu` - sets the maximum percentage of CPU usage that can be consumed by the emulation.
* `max_memory` - defines the maximum amount of memory in megabytes that the emulation can utilize.


## Setting a Resource Model
Each `VirtualInstance` has an optional `resource_model` param that defines how many resources that instance have.
```py
from fogbed import (
    FogbedExperiment, Container, CloudResourceModel, EdgeResourceModel
)

exp   = FogbedExperiment()
cloud = exp.add_virtual_instance('cloud', resource_model=CloudResourceModel(max_cu=8.0, max_mu=1024))
edge  = exp.add_virtual_instance('edge', resource_model=EdgeResourceModel(max_cu=2.0, max_mu=256))
```

* `resource_model` - If defined, Fogbed enables the limiting resources feature on containers.


## Adding or removing containers in runtime
```py
from fogbed import Container, FogbedExperiment
...

try:
    exp.start()
    ...

    exp.add_docker(container=Container('d3'), datacenter=edge)
    print(exp.get_docker('d3').cmd(f'ping -c 4 {d1.ip}'))
    exp.remove_docker('d3')

except Exception as ex:
    print(ex)
finally:
    exp.stop()
```

## Helper methods
The `FogbedExperiment` class offers some helper methods like:

<b>`add_docker`</b>
<i>(container: Container, datacenter: VirtualInstance)

* Adds a container to a virtual instance.´
* Raises a `ContainerAlreadyExists` exception if name or ip already exists.
</i>


<b>`add_link`</b>
<i>(node1: VirtualInstance, node2: VirtualInstance, **params: Any)

* Adds a link between two virtual instances.
</i> 


<b>`add_virtual_instance`</b>
<i>(name: str, resource_model: Optional[ResourceModel] = None) -> VirtualInstance

* Creates a virtual instance.
* Raises a `VirtualInstanceAlreadyExists` exception if name already exists.
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


<b>`get_virtual_instances`</b>
<i>() -> List[VirtualInstance]

* Returns all virtual instances of the emulation.
</i>


<b>`remove_docker`</b>
<i>(name: str)

* Removes a container by name. 
* Raises a `ContainerNotFound` exception if name doesn't exist.
</i>


<b>`start_cli`</b>
<i>()

* Starts the Containernet Command Line Interface.
</i>


<b>`start`</b>
<i>()

* Starts the experiment. 
</i>


<b>`stop`</b>
<i>()

* Stops the experiment. 
</i>