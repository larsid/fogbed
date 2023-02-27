import socket
import subprocess
from fogbed.emulation import Services
from fogbed.exceptions import ContainerAlreadyExists, VirtualInstanceAlreadyExists

def verify_if_container_ip_exists(ip: str):
    if(Services.get_container_by_ip(ip) is not None):
        raise ContainerAlreadyExists(f'Container with ip={ip} already exists.')

def verify_if_container_name_exists(name: str):
    if(Services.get_container_by_name(name) is not None):
        raise ContainerAlreadyExists(f'Container with name={name} already exists.')

def verify_if_datacenter_exists(name: str):
    if(name in Services.virtual_instances()):
        raise VirtualInstanceAlreadyExists(f'Datacenter {name} already exists.')

def get_ip_address() -> str:
    output = subprocess.check_output(['hostname', '--all-ip-addresses'], text=True)
    return output.split(' ')[0]

def start_openflow_controller(ip: str, port: int):
    hostname = socket.gethostname()
    code = subprocess.call(['controller', '-D', f'ptcp:{port}'])

    if(code == 0):
        print(f'[{hostname}]: OpenFlow controller listening on: {ip}:{port}')