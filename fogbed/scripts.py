import argparse
from fogbed import setLogLevel
from fogbed.parsing.builder import ExperimentBuilder

setLogLevel('info')

def build(filename: str):
    exp = ExperimentBuilder(filename).build()
    
    try:
        exp.start()
        input('\nPress Enter to exit...')
    except Exception as ex:
        print(ex)
    finally:
        exp.stop()


def main():
    parser = argparse.ArgumentParser('sudo fogbed')
    parser.add_argument('-c', '--config-file', type=str, help='run a topology especified in a file .yml')
    args = parser.parse_args()
    build(filename=args.config_file)

    