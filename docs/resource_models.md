The Resource Models define the policy for allocating computational resources such as `cpu_quota` and `mem_limit` within containers.

Each resource model has `max_cu` and `max_mu` values, representing the maximum computing and memory units that the `VirtualInstance` can have.

There are three types of resource models in Fogbed: `EdgeResourceModel`, `FogResourceModel` and `CloudResourceModel`.
## EdgeResourceModel
The Edge resource model follows a fixed limit strategy. If a container requests resources, and all of them have already been allocated, an exception is raised to alert that no more resources can be allocated for new containers.
```py
from fogbed import (
    FogbedExperiment, Container, Resources, EdgeResourceModel
)
exp  = FogbedExperiment()

edge_model = EdgeResourceModel(max_cu=2, max_mu=256)
edge = exp.add_virtual_instance('edge',  edge_model)

exp.add_docker(Container('d1', resources=Resources.SMALL), datacenter=edge)
exp.add_docker(Container('d2', resources=Resources.SMALL), datacenter=edge)
exp.add_docker(Container('d3', resources=Resources.SMALL), datacenter=edge)
```

```
d3: Allocation of container was blocked by resource model.
```

## CloudResourceModel and FogResourceModel
The Fog and Cloud resource models are identical, employing an over-provisioning strategy. If a container requests `HardwareResources`, and all of the resources of the `VirtualInstance` have already been allocated to other containers, the new container starts regardless. Subsequently, the CPU time and memory limit for each container is recalculated.


## Predefined Resources
Below is the list of the predefined `HardwareResources`:
```py
from fogbed import Resources

>>> Resources.TINY
'HardwareResources(cu=0.5,  mu=32)'

>>> Resources.SMALL
'HardwareResources(cu=1.0,  mu=128)'

>>> Resources.MEDIUM
'HardwareResources(cu=4.0,  mu=256)'

>>> Resources.LARGE
'HardwareResources(cu=8.0,  mu=512)'

>>> Resources.XLARGE
'HardwareResources(cu=16.0, mu=1024)'
```