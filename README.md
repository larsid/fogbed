![](https://img.shields.io/badge/python-3.8+-blue.svg)
![](https://img.shields.io/badge/Ubuntu-20.04-orange.svg)
# Fogbed

Fogbed is a framework and toolset integration for rapid prototyping of fog components in virtualized environments using a desktop or distributed approach. Its design meets the postulated requirements of low cost, flexible setup and compatibility with real world technologies. The components are based on Mininet network emulator with Docker container instances as fog virtual nodes.

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
sudo pip install fogbed
```

## Get Started
After having installed fogbed you can start an example topology, copy the example in `examples/sensors/sensors.py` and run with:
```
sudo python3 sensors.py
```
Then access the url `http://localhost:3000` on your browser to visualize a React application consuming a REST API what monitor some devices which send health random data.

![monitor](https://user-images.githubusercontent.com/33939999/202031666-45889ae0-49ee-4a5e-a7a6-94f1705a8a08.jpeg)

## Documentation
Project documentation is available at https://larsid.github.io/fogbed/

## Publications
A. Coutinho, U. Damasceno, E. Mascarenhas, A. C. Santos, J. E. B. T. da Silva and F. Greve, "[Rapid-Prototyping of Integrated Edge/Fog and DLT/Blockchain Systems with Fogbed](https://ieeexplore.ieee.org/document/10279234)," ICC 2023 - IEEE International Conference on Communications, Rome, Italy, 2023, pp. 622-627, doi: 10.1109/ICC45041.2023.10279234.
