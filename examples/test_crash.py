from fogbed.emulation import Services
from fogbed.experiment.local import FogbedExperiment
from fogbed.node.container import Container
from fogbed.resources.flavors import Resources
from fogbed.resources.models import CloudResourceModel, EdgeResourceModel
from fogbed.fails.controller import FailController
from fogbed.fails.models.crash import CrashFail
from mininet.log import setLogLevel
from fogbed.fails.models.availability import AvailabilityFail, AvailabilityMode

setLogLevel('info')

Services(max_cpu=0.5, max_mem=512)

exp = FogbedExperiment()

edge = exp.add_virtual_instance('edge',
    EdgeResourceModel(max_cu=2, max_mu=256))

# cloud = exp.add_virtual_instance('cloud',
#     CloudResourceModel(max_cu=2, max_mu=512), AvailabilityFail(availability=0.8, slot_time=1, 
#                                                                availability_mode=AvailabilityMode.CRASH))

cloud = exp.add_virtual_instance('cloud',
    CloudResourceModel(max_cu=2, max_mu=512))

d1 = Container('d1', resources=Resources.SMALL)
d2 = Container('d2',
    resources=Resources.SMALL,
    fail_model=CrashFail(life_time=15)
)
d3 = Container('d3', resources=Resources.SMALL)
d4 = Container('d4', resources=Resources.SMALL)


exp.add_docker(d1, edge)
exp.add_docker(d2, edge)
exp.add_docker(d3, cloud)
exp.add_docker(d4, cloud)

exp.add_link(cloud, edge)

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
