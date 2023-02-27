from typing import List
from fogbed import (
    FogbedDistributedExperiment, 
    VirtualInstance, Container, Worker
)

exp = FogbedDistributedExperiment()

def create_devices(number: int) -> List[VirtualInstance]:
    return [exp.add_virtual_instance(f'edge{i+1}') for i in range(number)]


def create_sensors(devices: List[VirtualInstance], server_url: str):
    for i, device in enumerate(devices):
        name = f'User{i+1}'
        exp.add_docker(
            container=Container(
                name=name, 
                dcmd='python3 device.py',
                dimage='esaum/device:latest',
                environment={'UID': name, 'URL': server_url}
            ), 
            datacenter=device)


def add_datacenters_to_worker(worker: Worker, datacenters: List[VirtualInstance]):
    for device in datacenters:
        worker.add(device, reachable=True)



if(__name__=='__main__'):
    cloud   = exp.add_virtual_instance('cloud')
    devices = create_devices(3)    

    server = Container(
        name='server', 
        dimage='esaum/covid-api:latest',
        dcmd='python3 app.py',
        ports=[8000],
        port_bindings={8000: 8000},
    )
    react_app = Container(
        name='monitor',
        dcmd='npm start',
        dimage='esaum/covid-monitor:latest',
        environment={'REACT_APP_API_URL': f'http://localhost:8000'},
        ports=[3000],
        port_bindings={3000: 3000},
    )

    exp.add_docker(server, cloud)
    exp.add_docker(react_app, cloud)
    create_sensors(devices, server_url=f'http://{server.ip}:8000')
    
    worker1 = exp.add_worker(ip='192.168.0.152')
    worker2 = exp.add_worker(ip='192.168.0.192')

    add_datacenters_to_worker(worker1, [cloud])
    add_datacenters_to_worker(worker2, devices)
    exp.add_tunnel(worker1, worker2)

    try:
        exp.start() 
        input('Press any key to continue...')
    except Exception as ex: 
        print(ex)
    finally:
        exp.stop()
