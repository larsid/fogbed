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

def resolve_ip(ip: str) -> str:
    return socket.gethostbyname(ip)

def get_tunnel_command(port: str, interface: str, ip: str) -> str:
    return f'ovs-vsctl add-port {port} {interface} -- set interface {interface} type=gre options:remote_ip={ip} options:df_default=false'

def get_ip_address() -> str:
    output = subprocess.check_output(['hostname', '--all-ip-addresses'], text=True)
    return output.split(' ')[0]

def start_openflow_controller(ip: str, port: int):
    hostname = socket.gethostname()
    code = subprocess.call(['controller', '-D', f'ptcp:{port}'])

    if(code == 0):
        print(f'[{hostname}]: OpenFlow controller listening on: {ip}:{port}')