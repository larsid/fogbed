#!/bin/bash
echo "Fogbed installer"
echo ""
echo "This program installs Fogbed and all requirements to the home directory of your user"


echo "installing required dependencies."
sudo apt update
sudo snap install cmake --classic
sudo apt-get install git autoconf screen build-essential sysstat python-matplotlib uuid-runtime


# Install Containernet
sudo apt-get install ansible aptitude
# Patch config file if necessary
grep "localhost ansible_connection=local" /etc/ansible/hosts >/dev/null
if [ $? -ne 0 ]; then
echo "localhost ansible_connection=local" | sudo tee -a /etc/ansible/hosts
fi

cd ~
sudo rm -rf containernet &> /dev/null
sudo rm -rf oflops &> /dev/null
sudo rm -rf oftest &> /dev/null
sudo rm -rf openflow &> /dev/null
sudo rm -rf pox &> /dev/null
git clone https://github.com/containernet/containernet
cd containernet/ansible
sudo ansible-playbook install.yml


# Install Metis
cd ~
wget http://glaros.dtc.umn.edu/gkhome/fetch/sw/metis/metis-5.1.0.tar.gz
tar -xzf metis-5.1.0.tar.gz
rm metis-5.1.0.tar.gz
cd metis-5.1.0
make config
make
sudo make install
cd ~
rm -rf metis-5.1.0


# Install Pyro
sudo pip install Pyro4


# Install Fogbed
cd ~
cd fogbed
python3 setup.py install
mkdir -p /usr/local/share/MaxiNet
cp -rv maxinet/Frontend/examples /usr/local/share/MaxiNet/
chmod +x /usr/local/share/MaxiNet/examples/*
cp share/MaxiNet-cfg-sample /usr/local/share/MaxiNet/config.example
cp share/maxinet_plot.py /usr/local/share/MaxiNet/
cd ~
sudo rm -rf fogbed &> /dev/null