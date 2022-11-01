# Fogbed

Fogbed is a framework and toolset integration for rapid prototyping of fog components in virtual-ized environments using a desktop approach. Its design meets the postulated requirements of low cost, flexible setup and compatibility with real world technologies. The components are based on Mininet network emulator with Docker container instances as fog virtual nodes.

## Install

Before installing Fogbed it is necessary to install some dependencies and Containernet, as shown in the steps below:

#### 1. Installing required dependencies

```
sudo apt-get install autoconf screen build-essential sysstat uuid-runtime ansible
```



#### 2. Install Containernet

```
git clone https://github.com/containernet/containernet.git
```

```
sudo ansible-playbook -i "localhost," -c local containernet/ansible/install.yml
```


#### 3. Install Fogbed
```
sudo pip install -U git+https://github.com/EsauM10/fogbed.git
```