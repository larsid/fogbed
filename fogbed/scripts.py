import argparse
import os
from pathlib import Path
import tempfile
import sys

from fogbed.helpers import (
    get_experiment_template_code,
    run_command,
    run_pip_install,
    run_python_file
)


def build(filename: str):
    if(filename.endswith('.py')):
        run_python_file(filename)
        return
    
    code = get_experiment_template_code(filename=os.path.abspath(filename))

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as file:
        file.write(code)
        temp_filename = file.name
    
    try:
        run_python_file(temp_filename)
    finally:
        os.remove(temp_filename)


def install_containernet(branch: str):
    print('Installing Containernet...')
    unzipped_folder = f'containernet-{branch}'
    containernet_folder = os.path.join(Path.home(), 'containernet')

    run_command(['sudo', 'apt-get', 'install', 'ansible'])
    run_command(
        ['wget', f'https://github.com/containernet/containernet/archive/refs/heads/{branch}.zip'])
    run_command(['unzip', f'{branch}.zip'])
    run_command(['mv', unzipped_folder, containernet_folder])
    run_command([
        'sudo', 
        'ansible-playbook', 
        '-i', '"localhost,"', 
        '-c', 'local',
        f'{containernet_folder}/ansible/install.yml'])
    run_command(['rm', '-rf', f'{branch}.zip'])
    run_pip_install('git+https://github.com/containernet/containernet.git')


def run_worker(port: int):
    run_worker_path = os.path.join(sys.prefix, 'bin', 'RunWorker')
    run_command(['sudo', run_worker_path, f'-p={port}'])


def main():
    global_parser = argparse.ArgumentParser(prog='fogbed')
    subparsers    = global_parser.add_subparsers(dest='command', title='commands')

    install_parser = subparsers.add_parser('install', help='install Containernet')
    install_parser.add_argument('-b', '--branch', type=str, default='master', help='Containernet branch name to install')

    run_parser = subparsers.add_parser('run', help='run a topology especified in a file .yml or .py')
    run_parser.add_argument('file', type=str, help='topology file') 

    worker_parser = subparsers.add_parser('worker', help='run a worker')
    worker_parser.add_argument('-p', '--port', type=int, default=5000, help='run server on especified port (default: 5000)')

    args = global_parser.parse_args()
    
    if(args.command == 'run'):
        build(filename=args.file)
    elif(args.command == 'install'):
        install_containernet(branch=args.branch)
    elif(args.command == 'worker'):
        run_worker(port=int(args.port))
    else:
        global_parser.print_help()
