from fogbed.emulation import Services
from fogbed.node.container import Container
from fogbed.experiment.local import FogbedExperiment
from fogbed.resources.flavors import Resources
from fogbed.resources.models import CloudResourceModel, EdgeResourceModel, FogResourceModel
from fogbed.fails.controller import FailController
from fogbed.fails.models.crash import CrashFail
from fogbed.fails.models.disconnect import DisconnectFail

from mininet.log import setLogLevel
import time

setLogLevel('info')

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
    exp.start()

    print('[INFO] Iniciando controlador de falhas...')
    fail_controller.start()
    
    # Testa comunicação antes da falha
    print(f'[TESTE] Testando ping de d1 ({d1.ip}) para d2 ({d2.ip}) antes da falha:')
    print(d1.cmd(f'ping -c 4 {d2.ip}'))

    print('[INFO] Aguardando 10 segundos para a falha crash ocorrer...')
    time.sleep(10)

    # Testa comunicação depois que o d2 se desconecta
    print(f'[TESTE] Testando ping de d1 para d2 após desconexão:')
    print(d1.cmd(f'ping -c 4 {d2.ip}'))

    print('[INFO] Mudando a falha de d2 para d4...')

    print('[INFO] Testando ping de d1 para d4 antes da falha disconnect ocorrer...')
    print(d1.cmd(f'ping -c 4 {d4.ip}'))


    print('[INFO] Aguardando 10 segundos para a falha disconnect ocorrer...')   
    time.sleep(10)

    # Testa comunicação depois que o d4 se desconecta
    print(f'[TESTE] Testando ping de d1 para d4 após desconexão:')
    print(d1.cmd(f'ping -c 4 {d4.ip}'))

    exp.start_cli()


except Exception as ex:
    print(ex)

finally:
    fail_controller.stop()
    exp.stop()

