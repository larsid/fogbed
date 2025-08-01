from fogbed.emulation import Services
from fogbed.node.container import Container
from fogbed.experiment.local import FogbedExperiment
from fogbed.resources.flavors import Resources
from fogbed.resources.models import CloudResourceModel, EdgeResourceModel, FogResourceModel
from fogbed.fails.controller import FailController
from fogbed.fails.models.crash import CrashFail
from fogbed.fails.models.disconnect import DisconnectFail
from fogbed.patches import patch_docker_cgroups

from mininet.log import setLogLevel
import time

setLogLevel('info')

# Aplicar patch para cgroups v2
patch_docker_cgroups()

Services(max_cpu=0.5, max_mem=512)

exp = FogbedExperiment()

cloud = exp.add_virtual_instance('cloud', CloudResourceModel(max_cu=8, max_mu=1024))
fog = exp.add_virtual_instance('fog', FogResourceModel(max_cu=4, max_mu=512))
edge = exp.add_virtual_instance('edge', EdgeResourceModel(max_cu=2, max_mu=256))

d1 = Container('d1', ip='10.0.0.1', dimage='ubuntu:trusty', resources=Resources.SMALL)
d2 = Container('d2', ip='10.0.0.2', dimage='ubuntu:trusty', resources=Resources.SMALL, 
               fail_model=CrashFail(life_time=10))
d3 = Container('d3', ip='10.0.0.3', dimage='ubuntu:trusty', resources=Resources.SMALL)
d4 = Container('d4', ip='10.0.0.4', dimage='ubuntu:trusty', resources=Resources.SMALL, 
               fail_model=DisconnectFail(life_time=30)) 
d5 = Container('d5', ip='10.0.0.5', dimage='ubuntu:trusty', resources=Resources.SMALL)
d6 = Container('d6', ip='10.0.0.6', dimage='ubuntu:trusty', resources=Resources.SMALL)
d7 = Container('d7', ip='10.0.0.7', dimage='ubuntu:trusty', resources=Resources.SMALL)

exp.add_docker(d1, cloud)

exp.add_docker(d2, fog)
exp.add_docker(d3, fog)
exp.add_docker(d4, fog)

exp.add_docker(d5, edge)
exp.add_docker(d6, edge)
exp.add_docker(d7, edge)

exp.add_link(cloud, fog)
exp.add_link(fog, edge)

fail_controller = FailController(exp)

try:
    print('Iniciando experimento...')
    exp.start()

    print('Iniciando controlador de falhas...')
    fail_controller.start()
    
    # Testa comunicação antes da falha
    print('Ping d1 → d2 (antes crash):')
    print(d1.cmd(f'ping -c 2 {d2.ip}'))

    print('Aguardando crash (10s)...')
    time.sleep(10)

    # Testa comunicação depois que o d2 crashou
    print('Ping d1 → d2 (após crash):')
    print(d1.cmd(f'ping -c 2 {d2.ip}'))

    print('Ping d1 → d4 (antes disconnect):')
    print(d1.cmd(f'ping -c 2 {d4.ip}'))

    print('Aguardando disconnect (10s)...')   
    time.sleep(10)

    # Testa comunicação depois que o d4 se desconectou
    print('Ping d1 → d4 (após disconnect):')
    print(d1.cmd(f'ping -c 2 {d4.ip}'))

    print('Teste concluído!')
    exp.start_cli()


except Exception as ex:
    print(f'Erro: {ex}')

finally:
    fail_controller.stop()
    exp.stop()
    print('Finalizado!')

