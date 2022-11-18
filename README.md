![](https://img.shields.io/badge/python-3.8+-blue.svg)
# Fogbed

Fogbed is a framework and toolset integration for rapid prototyping of fog components in virtual-ized environments using a desktop approach. Its design meets the postulated requirements of low cost, flexible setup and compatibility with real world technologies. The components are based on Mininet network emulator with Docker container instances as fog virtual nodes.

## Install

Before installing Fogbed it is necessary to install some dependencies and Containernet, as shown in the steps below:


#### 1. Install Containernet
```
sudo apt-get install ansible
```

```
git clone https://github.com/containernet/containernet.git
```

```
sudo ansible-playbook -i "localhost," -c local containernet/ansible/install.yml
```

#### 2. Install Fogbed
```
sudo pip install -U git+https://github.com/EsauM10/fogbed.git
```

## Get Started
After having installed fogbed you can start an example topology, copy the example in `examples/sensors/sensors.py` and run with:
```
sudo python3 sensors.py
```
Then access the url `http://localhost:3000` on your browser to visualize a React application consuming a REST API what monitor some devices which send health random data.

![monitor](https://user-images.githubusercontent.com/33939999/202031666-45889ae0-49ee-4a5e-a7a6-94f1705a8a08.jpeg)

### Local emulation
```python
from fogbed.emulation import Services
from fogbed.experiment.local import FogbedExperiment
from fogbed.node import Container
from fogbed.resources import Resources
from fogbed.resources.models import CloudResourceModel, EdgeResourceModel, FogResourceModel

from mininet.log import setLogLevel

setLogLevel('info')

Services(max_cpu=0.5, max_mem=512)
exp = FogbedExperiment()

cloud = exp.add_virtual_instance('cloud', CloudResourceModel(max_cu=8, max_mu=1024))
fog   = exp.add_virtual_instance('fog',   FogResourceModel(max_cu=4, max_mu=512))
edge  = exp.add_virtual_instance('edge',  EdgeResourceModel(max_cu=2, max_mu=256))

d1 = Container('d1', ip='10.0.0.1', dimage='ubuntu:trusty', resources=Resources.SMALL)
d2 = Container('d2', ip='10.0.0.2', dimage='ubuntu:trusty', resources=Resources.SMALL)
d3 = Container('d3', ip='10.0.0.3', dimage='ubuntu:trusty', resources=Resources.SMALL)
d4 = Container('d4', ip='10.0.0.4', dimage='ubuntu:trusty', resources=Resources.SMALL)
d5 = Container('d5', ip='10.0.0.5', dimage='ubuntu:trusty', resources=Resources.SMALL)
d6 = Container('d6', ip='10.0.0.6', dimage='ubuntu:trusty', resources=Resources.SMALL)
d7 = Container('d7', ip='10.0.0.7', dimage='ubuntu:trusty', resources=Resources.SMALL)

exp.add_docker(d1, cloud)

exp.add_docker(d2, fog)
exp.add_docker(d3, fog)
exp.add_docker(d4, fog)

exp.add_docker(d5, edge)
exp.add_docker(d6, edge)
exp.add_docker(d7, edge)

exp.add_link(cloud, fog)
exp.add_link(fog, edge)

try:
    exp.start()
    
    print(d1.cmd('ifconfig'))
    print(d1.cmd(f'ping -c 4 {d6.ip}'))
    
    exp.start_cli()
except Exception as ex: 
    print(ex)
finally:
    exp.stop()

```
Here we have the instantiation of a fog topology, used by fogbed, followed by the definition of 3 Virtual Instances. A `VirtualInstance` in the context of fogbed is a unit that can have one or more hosts linked together by a single switch. Each Virtual Instance has a resource model associated with it that defines how many resources that instance have so that they can be distributed among it’s containers.


The resource model use is based on the proposed in [son-emu](https://github.com/sonata-nfv/son-emu), each resource model has a `max_cu` and `max_mu` value, representing the maximum computing and memory units the Virtual Instance that assigns it has.

### Containers
You can also create containers with custom resource restrictions like in [Containernet](https://github.com/containernet/containernet/wiki#method-containernetadddocker)

```python
from fogbed.node import Container

d1 = Container('d1', ip='10.0.0.1', dimage='ubuntu:trusty', dcmd='/bin/bash')
d2 = Container('d2', ip='10.0.0.2', dimage='ubuntu:focal', mac='00:00:00:00:00:02')
d3 = Container('d3', ip='10.0.0.3', environment={'var1': 'value'})
```
On Fogbed, each container determines how much `cu` and `mu` they have, representing how many parts of the total of it’s Virtual Instance is available to the container. These values are converted to real cpu time and memory limit.

Example: if a container `c1` is assigned 4 computing units and container `c2` 2 computing units, and they are both in the same Virtual Instance, container `c1` has twice more cpu time than container `c2`.

The `resources` field describe how much of the Virtual Instance resources that container should take. If it isn’t specified, the predefined `ResourceModel.SMALL` is chosen. Below is the list of the predefined resources:

```python
Resources.TINY   => HardwareResources(cu=0.5,  mu=32)
Resources.SMALL  => HardwareResources(cu=1.0,  mu=128)
Resources.MEDIUM => HardwareResources(cu=4.0,  mu=256)
Resources.LARGE  => HardwareResources(cu=8.0,  mu=512)
Resources.XLARGE => HardwareResources(cu=16.0, mu=1024)
```
If none of the predefined resources is suitable for your application, you can pass a custom one like:

```python
from fogbed.resources.flavors import HardwareResources

d1 = Container('d1', ip='10.0.0.1', resources=HardwareResources(cu=2.0, mu=128))
```


