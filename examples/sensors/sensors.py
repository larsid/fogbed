from typing import List

from fogbed import (
    FogbedExperiment, Container, VirtualInstance, setLogLevel
)

setLogLevel('info')

exp = FogbedExperiment()

def create_devices(number: int) -> List[VirtualInstance]:
    return [exp.add_virtual_instance(f'edge{i+1}') for i in range(number)]

def create_sensors(devices: List[VirtualInstance], server_url: str):
    for i, device in enumerate(devices):
        name = f'User{i+1}'

        sensor_container = Container(
            name=name, 
            dcmd='python3 device.py',
            dimage='larsid/covid-device:latest',
            environment={'UID': name, 'URL': server_url}
        )
        sensor_container.environment['BIND_IP'] = sensor_container.ip
        exp.add_docker(
            container=sensor_container, 
            datacenter=device
        )

def create_links(cloud: VirtualInstance, devices: List[VirtualInstance]):
    for device in devices:
        exp.add_link(device, cloud)


if(__name__=='__main__'):
    cloud   = exp.add_virtual_instance('cloud')
    devices = create_devices(5)

    server = Container(
        name='server', 
        dimage='larsid/covid-api:latest',
        dcmd='python3 app.py',
        port_bindings={8000: 8000},
    )

    react_app = Container(
        name='monitor',
        dcmd='npm start',
        dimage='larsid/covid-monitor:latest',
        environment={'REACT_APP_API_URL': 'http://localhost:8000'},
        port_bindings={3000: 3000},
    )

    exp.add_docker(server, cloud)
    exp.add_docker(react_app, cloud)
    create_sensors(devices, server_url=f'http://{server.ip}:8000')
    create_links(cloud, devices)

    try:
        exp.start() 
        input('Press any key...')
    except Exception as ex: 
        print(ex)
    finally:
        exp.stop()
