import argparse
import subprocess
from typing import List

def run_command(commands: List[str]):
    subprocess.call(commands)

def create_file(filename: str, data: str):
    with open(filename, mode='w') as file:
        file.write(data)

def read_file(filename: str) -> str:
    with open(filename, mode='r') as file:
        return file.read()



def build(filename: str):
    try:
        from fogbed.parsing.builder import ExperimentBuilder
    except:
        print('Containernet is not installed, run: fogbed install')

    exp = ExperimentBuilder(filename).build()
    
    try:
        exp.start()
        input('\nPress Enter to exit...')
    except Exception as ex:
        print(ex)
    finally:
        exp.stop()


def install_containernet():
    print('Installing Containernet...')
    branch = 'ubuntu_2004'
    unzipped_folder = f'containernet-{branch}'
    containernet_folder = 'containernet'

    run_command(['sudo', 'apt-get', 'install', 'ansible'])
    run_command(
        ['wget', f'https://github.com/containernet/containernet/archive/refs/heads/{branch}.zip'])
    run_command(['unzip', f'{branch}.zip'])
    run_command(['mv', unzipped_folder, containernet_folder])

    if(branch == 'ubuntu_2004'):
        filename = f'{containernet_folder}/util/install.sh'
        install_sh = read_file(filename)
        new_file = install_sh.replace('git://', 'https://')
        create_file(filename, data=new_file)

    run_command([
        'sudo', 
        'ansible-playbook', 
        '-i', '"localhost,"', 
        '-c', 'local',
        f'{containernet_folder}/ansible/install.yml'])
    run_command(['sudo', 'rm', '-rf', f'{branch}.zip'])


def run_worker(port: int):
    print(f'Running Worker on port={port}')
    run_command(['sudo', 'RunWorker', f'-p={port}'])


def main():
    global_parser = argparse.ArgumentParser(prog='fogbed')
    subparsers    = global_parser.add_subparsers(dest='command', title='commands')

    subparsers.add_parser('install', help='install Containernet')

    run_parser = subparsers.add_parser('run', help='run a topology especified in a file .yml')
    run_parser.add_argument('config_file', type=str, help='YML config file') 

    worker_parser = subparsers.add_parser('worker', help='run a worker')
    worker_parser.add_argument('-p', '--port', type=int, default=5000, help='run server on especified port (default: 5000)')

    args = global_parser.parse_args()
    
    if(args.command == 'run'):
        build(filename=args.config_file)
    elif(args.command == 'install'):
        install_containernet()
    elif(args.command == 'worker'):
        run_worker(port=int(args.port))
    else:
        global_parser.print_help()
