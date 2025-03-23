import argparse

from fogbed.helpers import run_command

global_parser = argparse.ArgumentParser(prog='fogbed')
subparsers    = global_parser.add_subparsers(dest='command', title='commands')

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

def run_worker(port: int):
    print(f'Running Worker on port={port}')
    run_command(['sudo', 'RunWorker', f'-p={port}'])


def main():
    subparsers.add_parser('install', help='install Containernet')

    run_parser = subparsers.add_parser('run', help='run a topology especified in a file .yml')
    run_parser.add_argument('config_file', type=str, help='YML config file') 

    worker_parser = subparsers.add_parser('worker', help='run a worker')
    worker_parser.add_argument('-p', '--port', type=int, default=5000, help='run server on especified port (default: 5000)')

    args = global_parser.parse_args()
    
    if(args.command == 'run'):
        build(filename=args.config_file)
    elif(args.command == 'worker'):
        run_worker(port=int(args.port))
    else:
        global_parser.print_help()
