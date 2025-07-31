from fogbed.emulation import Services
from fogbed.node.container import Container
from fogbed.experiment.local import FogbedExperiment
from fogbed.resources.flavors import Resources
from fogbed.resources.models import CloudResourceModel, EdgeResourceModel
from fogbed.fails.controller import FailController
from fogbed.fails.models.disconnect import DisconnectFail
from fogbed.fails.models.availability import AvailabilityFail, AvailabilityMode
from time import sleep

from mininet.log import setLogLevel

setLogLevel('info')

# Define os recursos máximos disponíveis para os containers
Services(max_cpu=0.5, max_mem=512)

# Inicia o experimento
exp = FogbedExperiment()

availability_config = AvailabilityFail(
    availability=0.5,
    slot_time=2.0,
    availability_mode=AvailabilityMode.DISCONNECT
)

# Adiciona instâncias virtuais com modelos de recurso
edge = exp.add_virtual_instance('edge', EdgeResourceModel(max_cu=2, max_mu=256))
cloud = exp.add_virtual_instance('cloud', CloudResourceModel(max_cu=2, max_mu=512), availability_config)

# Define os containers
d1 = Container('d1', ip='10.0.0.1', dimage='ubuntu:trusty', resources=Resources.SMALL)

d2 = Container(
    'd2',
    ip='10.0.0.2',
    dimage='ubuntu:trusty',
    resources=Resources.SMALL,
)

d3 = Container('d3', ip='10.0.0.3', dimage='ubuntu:trusty', resources=Resources.SMALL)
d4 = Container('d4', ip='10.0.0.4', dimage='ubuntu:trusty', resources=Resources.SMALL)

# Adiciona containers às instâncias
exp.add_docker(d1, edge)
exp.add_docker(d2, edge)
exp.add_docker(d3, cloud)
exp.add_docker(d4, cloud)

# Conecta os nós com um link de rede
exp.add_link(cloud, edge)

# Cria o controlador de falhas
fail_controller = FailController(exp)

try:
    exp.start()
    fail_controller.start()

    exp.start_cli()

except Exception as ex:
    print('[ERRO] Ocorreu uma exceção durante o experimento:')
    print(ex)

finally:
    fail_controller.stop()
    exp.stop()
