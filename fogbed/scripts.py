import argparse
import os
import tempfile

from fogbed.helpers import (
    create_file,
    get_experiment_template_code, 
    read_file, 
    run_command
)


def build(filename: str):
    if(filename.endswith('.py')):
        run_command(['sudo', 'python3', filename])
        return
    
    code = get_experiment_template_code(filename=os.path.abspath(filename))

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as file:
        file.write(code)
        temp_filename = file.name
    
    try:
        run_command(['sudo', 'python3', temp_filename])
    finally:
        os.remove(temp_filename)


def install_containernet(branch: str):
    print('Installing Containernet...')
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
    
    run_command(['sudo', 'pip', 'install', 'git+https://github.com/containernet/containernet.git'])
    run_command(['rm', '-rf', f'{branch}.zip'])


def run_worker(port: int):
    run_command(['sudo', 'RunWorker', f'-p={port}'])


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
