## Container Params
`fogbed.Container`<i>(name: str, ip: Optional[str] = None, dcmd: str = '/bin/bash', dimage: str = 'ubuntu:trusty', 
environment: Dict[str, Any] = {}, ports: List[int] = [], port_bindings: Dict[int, int] = {}, volumes: List[str] = [],
resources: HardwareResources = Resources.SMALL,
**params: Any)
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
    ports=[80],
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
See all available <a href="/resource_models/#predefined-resources">Resources</a>.

## Running Commands
After an experiment starts, you can interact with a container through the `cmd` method.
```py
...

key = '0x63746963616c2062797'
print(d1.cmd('ls'))
d1.cmd(f'echo >> {key} /tmp/data/keys.json')
print(d1.cmd('cat /tmp/data/keys.json'))
```


## Building Images
To run an container image within Fogbed, first its necessary to install some packages:
```
FROM ubuntu:latest

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