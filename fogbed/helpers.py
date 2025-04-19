import socket
import subprocess


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