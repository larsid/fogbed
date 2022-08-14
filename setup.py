import os
import subprocess
from setuptools import setup, find_packages

def run_command(command: str):
    args = command.split(' ')
    subprocess.call(args)

def install_maxinet():
    run_command('git clone https://github.com/EsauM10/maxinet.git')
    os.chdir('maxinet')
    run_command('sudo python3 setup.py install')
    os.chdir('..')
    run_command('git clone https://github.com/noxrepo/pox.git')


setup(
    name="fogbed",
    version="1.0.0",
    description='Containernet fork that add Fogbed support.',
    long_description='Containernet fork that add Fogbed support.',
    keywords=['networking', 'emulator', 'protocol', 'Internet', 'OpenFlow', 'SDN', 'fog'],
    url='https://github.com/EsauM10/fogbed',
    author='Esaú Mascarenhas',
    author_email='esaumasc@gmail.com',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python 3.8',
        'Topic :: System :: Emulators'
        'Operating System :: Ubunbu OS'
    ],
    packages=find_packages(),
    include_package_data=True,
)

if(__name__=='__main__'):
    install_maxinet()