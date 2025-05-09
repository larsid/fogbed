from fogbed.emulation import Services
from fogbed.node.container import Container
from fogbed.experiment.local import FogbedExperiment
from fogbed.resources.flavors import Resources
from fogbed.resources.models import CloudResourceModel, EdgeResourceModel
from fogbed.fails.controller import FailController
from fogbed.fails.models.disconnect import DisconnectFail

from mininet.log import setLogLevel
import time

setLogLevel('info')

# Define os recursos máximos disponíveis para os containers
Services(max_cpu=0.5, max_mem=512)

# Inicia o experimento
exp = FogbedExperiment()

# Adiciona instâncias virtuais com modelos de recurso
cloud = exp.add_virtual_instance('cloud', CloudResourceModel(max_cu=8, max_mu=1024))
edge = exp.add_virtual_instance('edge', EdgeResourceModel(max_cu=2, max_mu=256))

# Define containers
print('[INFO] Criando containers...')
d1 = Container('d1', ip='10.0.0.1', dimage='ubuntu:trusty', resources=Resources.SMALL)

# Container com falha de desconexão após 15 segundos
d2 = Container(
    'd2',
    ip='10.0.0.2',
    dimage='ubuntu:trusty',
    resources=Resources.SMALL,
    fail_model=DisconnectFail(life_time=10)  # Desconecta após 15s
)

# Adiciona containers às instâncias
print('[INFO] Atribuindo containers aos nós...')
exp.add_docker(d1, cloud)
exp.add_docker(d2, edge)

# Conecta os nós com um link de rede
print('[INFO] Conectando instâncias cloud e edge...')
exp.add_link(cloud, edge)

# Cria o controlador de falhas
fail_controller = FailController(exp)

try:
    print('[INFO] Iniciando o experimento...')
    exp.start()

    print('[INFO] Iniciando controlador de falhas...')
    fail_controller.start()

    # Testa comunicação antes da falha
    print(f'[TESTE] Testando ping de d1 ({d1.ip}) para d2 ({d2.ip}) antes da falha:')
    print(d1.cmd(f'ping -c 4 {d2.ip}'))

    print('[INFO] Aguardando 15 segundos para a falha ocorrer...')
    time.sleep(20)

    # Testa comunicação depois que o d2 se desconecta
    print(f'[TESTE] Testando ping de d1 para d2 após desconexão:')
    print(d1.cmd(f'ping -c 4 {d2.ip}'))

    print('[INFO] Você pode usar o CLI para interagir com os nós...')
    exp.start_cli()

except Exception as ex:
    print('[ERRO] Ocorreu uma exceção durante o experimento:')
    print(ex)

finally:
    print('[INFO] Encerrando controlador de falhas e experimento...')
    fail_controller.stop()
    exp.stop()
