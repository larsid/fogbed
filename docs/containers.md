## Container Params
<b>`fogbed.Container`</b>
<i>(
    name: str, 
    ip: Optional[str] = None, 
    dcmd: str = '/bin/bash', 
    dimage: str = 'ubuntu:trusty', 
    environment: Dict[str, Any] = {}, 
    port_bindings: Dict[int, int] = {}, 
    volumes: List[str] = [],
    resources: HardwareResources = Resources.SMALL,
    link_params: Dict[str, Any] = {},
    **params: Any
)
</i>

## Containers IP
By default containers IP are created using the net `10.0.0.x`. You can provide custom IPs 
setting the `ip` param for all containers of the emulation.
```py
d1 = Container('d1', ip='250.10.0.1')
d2 = Container('d2', ip='182.1.0.12')
```

## Environment Variables
```py
from fogbed import Container

d1 = Container(
    name='d1', 
    environment={
        'VAR1': 'value',
        'VAR2': 10,
        'VAR3': True
    }
)
```

## Creating Volumes
```py
from fogbed import Container

d1 = Container(
    name='d1', 
    volumes=['/host/directory:/container/directory']
)
```

## Mapping Ports
The format to pass port bindings is opposite to that of the Docker CLI. For example, to open the container port `80` and map it to the host port `3000`, you should use:
```py
from fogbed import Container

d1 = Container(
    name='d1', 
    port_bindings={80: 3000}
)
```

## Limiting Resources
To limit containers CPU and memory set the `resources` param on constructor:
```py
from fogbed import Container, HardwareResources, Resources

d1 = Container('d1', resources=Resources.MEDIUM)
d2 = Container('d2', resources=HardwareResources(cu=2.0, mu=128))
```
See all available <a href="https://larsid.github.io/fogbed/resource_models/#predefined-resources">Resources</a>.

!!! note
    To enable the limiting resources feature on containers see 
    <a href="https://larsid.github.io/fogbed/local_emulation/#setting-a-resource-model">Setting a Resource Model.</a>

## Running Commands
After an experiment starts, you can interact with a container through the `cmd` method.
```py
...

key = '0x63746963616c2062797'
print(d1.cmd('ls'))
d1.cmd(f'echo {key} >> /tmp/data/key.pub')
print(d1.cmd('cat /tmp/data/key.pub'))
```


## Building Images
To run an container image within Fogbed, first it's necessary to install some packages:
``` dockerfile
FROM ubuntu:focal

RUN apt-get update \
    && apt-get install -y \
    net-tools \
    iputils-ping \
    iproute2 

```

build it with `sudo docker build -t <TAG> .` and then pass in a container:
```py
from fogbed import Container

d1 = Container(name='d1', dimage='TAG:latest')
```
For a complete reference about container requirements visit the <a href="https://github.com/containernet/containernet/wiki" target="_blank">Containernet Wiki.</a>


## Customizing links
Sometimes you may want to customize the links to enable fine-grained control over the link characteristics between an instance’s internal switch and its associated containers.

This can be done by passing the `link_params`, where you can define a `dict` with the link configuration, just like in 
<a href="https://github.com/mininet/mininet/wiki/Introduction-to-Mininet#setting-performance-parameters" target="_blank">
Mininet.
</a>

```py
from fogbed import Container

d1 = Container(
    name='d1', 
    link_params={
        'bw': 10, 
        'delay': '5ms', 
        'loss': 10, 
        'max_queue_size': 1000, 
        'use_htb': True
    }
)
```
!!! tip
    To apply the same link configuration to all containers within an instance, you can pass these parameters when creating the link between instances.

    ```py
    exp.add_link(cloud, edge, delay='50ms')
    ```