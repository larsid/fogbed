You can create custom topologies and run locally with Containernet through from `FogbedExperiment` class.
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

* `resource_model` - If defined, Fogbed enable the limiting resources feature on containers.


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