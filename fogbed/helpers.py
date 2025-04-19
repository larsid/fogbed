import socket
import subprocess
from typing import List


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


def run_command(commands: List[str]):
    subprocess.call(commands)

def create_file(filename: str, data: str):
    with open(filename, mode='w') as file:
        file.write(data)

def read_file(filename: str) -> str:
    with open(filename, mode='r') as file:
        return file.read()

def get_experiment_template_code(filename: str) -> str:
    return f'''
try:
    from fogbed import setLogLevel
    from fogbed.parsing.builder import ExperimentBuilder
except:
    print("Containernet is not installed, run: fogbed install")

setLogLevel("info")
exp = ExperimentBuilder("{filename}").build()

try:
    exp.start()
    input("Press Enter to exit...")
except Exception as ex:
    print(ex)
finally:
    exp.stop()
    '''