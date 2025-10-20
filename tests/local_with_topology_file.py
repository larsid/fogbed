from fogbed import ExperimentBuilder

exp = ExperimentBuilder(filename='topology.yml').build()

try:
    exp.start()
    node1 = exp.get_docker('node1')
    node3 = exp.get_docker('node3')
    print(node1.cmd(f'ping -c 4 {node3.ip}'))

    input('\nPress Enter to exit...')
except Exception as ex:
    print(ex)
finally:
    exp.stop()

# Run with: fogbed run tests/local_with_topology_file.py