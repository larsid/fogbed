![](https://img.shields.io/badge/python-3.8+-blue.svg)
![](https://img.shields.io/badge/Ubuntu-20.04-orange.svg)

# Fogbed
Fogbed is a framework and toolset integration for rapid prototyping of fog components in virtualized environments using a desktop approach. Its design meets the postulated requirements of low cost, flexible setup and compatibility with real world technologies. The components are based on Mininet network emulator with Docker container instances as fog virtual nodes.

## Requirements
* [Ubuntu 20.04](https://releases.ubuntu.com/focal/)
* [Containernet](https://containernet.github.io/)
* [Python 3.8+](https://www.python.org/)


## Install
### 1. Install Containernet
```
sudo apt-get install ansible
```

```
git clone https://github.com/containernet/containernet.git
```

```
sudo ansible-playbook -i "localhost," -c local containernet/ansible/install.yml
```

### 2. Install Fogbed
```
sudo pip install -U git+https://github.com/larsid/fogbed.git
```
