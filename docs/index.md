![](https://img.shields.io/badge/python-3.8+-blue.svg)
![](https://img.shields.io/badge/Ubuntu-20.04-orange.svg)

# Fogbed
Fogbed is a framework and toolset integration designed for rapid prototyping of fog components in virtualized environments using a desktop approach. It aims to meet the requirements of low cost, flexible setup, and compatibility with real-world technologies. The components are built upon the Mininet network emulator, leveraging Docker container instances as fog virtual nodes.

## Requirements
* [Ubuntu 20.04](https://releases.ubuntu.com/focal/)
* [Containernet](https://containernet.github.io/)
* [Python 3.8+](https://www.python.org/)


## Install

=== "Latest"
    Install Fogbed
    ```
    sudo pip install fogbed
    ```
    Install Containernet
    ```
    fogbed install 
    ```

=== "1.1.x"
    Install Containernet
    ```
    sudo apt-get install ansible
    ```

    ```
    git clone https://github.com/containernet/containernet.git
    ```

    ```
    sudo ansible-playbook -i "localhost," -c local containernet/ansible/install.yml
    ```

    Install Fogbed
    ```
    sudo pip install fogbed
    ```