import socket
import subprocess
import sys
from typing import List

UBUNTU_2004 = 'Ubuntu20.04'

def resolve_ip(ip: str) -> str:
    return socket.gethostbyname(ip)

def get_tunnel_command(port: str, interface: str, ip: str) -> str:
    return f'ovs-vsctl add-port {port} {interface} -- set interface {interface} type=gre options:remote_ip={ip} options:df_default=false'

def get_ip_address() -> str:
    output = subprocess.check_output(['hostname', '--all-ip-addresses'], text=True)
    return output.split(' ')[0]

def get_os_version() -> str:
    distro = subprocess.run(['lsb_release', '-irs'], capture_output=True, text=True)
    return distro.stdout.replace('\n', '')

def start_openflow_controller(ip: str, port: int):
    hostname = socket.gethostname()
    code = subprocess.call(['controller', '-D', f'ptcp:{port}'])

    if(code == 0):
        print(f'[{hostname}]: OpenFlow controller listening on: {ip}:{port}')

def run_command(commands: List[str]):
    subprocess.call(commands)

def run_pip_install(package: str):
    if(get_os_version() == UBUNTU_2004):
        run_command(['sudo', 'pip', 'install', package])
    else:
        run_command(['pip', 'install', package])

def run_python_file(filename: str):
    run_command(['sudo', sys.executable, filename])


def get_experiment_template_code(filename: str) -> str:
    return f'''
from fogbed import setLogLevel
from fogbed.parsing.builder import ExperimentBuilder   

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