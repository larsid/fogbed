from fogbed.emulation import Services
from fogbed.experiment.local import FogbedExperiment
from fogbed.node.container import Container
from fogbed.resources.flavors import Resources
from fogbed.resources.models import CloudResourceModel, EdgeResourceModel
from fogbed.fails.controller import FailController
from fogbed.fails.models.crash import CrashFail
from mininet.log import setLogLevel
import time

# Nível de log para acompanhar os eventos do Mininet
setLogLevel('info')

# Definindo os recursos máximos disponíveis no sistema
Services(max_cpu=0.5, max_mem=512)

# Criando o experimento principal
exp = FogbedExperiment()

# Criando instância EDGE (próxima do usuário, poucos recursos)
edge = exp.add_virtual_instance('edge',
    EdgeResourceModel(max_cu=2, max_mu=256))

# Criando instância CLOUD (mais distante, mais recursos)
cloud = exp.add_virtual_instance('cloud',
    CloudResourceModel(max_cu=2, max_mu=512))

# Criando os containers:

# d1: container comum sem falha
print('[CONTAINER] Criando container d1 (sem falha)...')
d1 = Container('d1', resources=Resources.SMALL)

# d2: container com falha CRASH (parará após 10 segundos)
print('[CONTAINER] Criando container d2 com falha CRASH (irá falhar após 10s)...')
d2 = Container('d2',
    resources=Resources.SMALL,
    fail_model=CrashFail(life_time=10)
)

# d3 e d4: containers comuns
print('[CONTAINER] Criando containers d3 e d4 (sem falhas)...')
d3 = Container('d3', resources=Resources.SMALL)
d4 = Container('d4', resources=Resources.SMALL)

# Alocando containers nas instâncias
print('[ALOCAÇÃO] Alocando d1 e d2 na EDGE...')
exp.add_docker(d1, edge)
exp.add_docker(d2, edge)

print('[ALOCAÇÃO] Alocando d3 e d4 na CLOUD...')
exp.add_docker(d3, cloud)
exp.add_docker(d4, cloud)

# Conectando as instâncias com um link de rede
print('[REDE] Conectando EDGE e CLOUD...')
exp.add_link(cloud, edge)

# Criando controlador de falhas
print('[FALHAS] Inicializando controlador de falhas...')
fail_controller = FailController(exp)

# Iniciando o experimento
try:
    print('[INÍCIO] Iniciando experimento Fogbed...')
    exp.start()

    print('[FALHAS] Iniciando controlador de falhas (falha CRASH será aplicada em d2)...')
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

# Encerrando tudo corretamente
finally:
    print('[ENCERRAMENTO] Finalizando controlador de falhas...')
    fail_controller.stop()

    print('[ENCERRAMENTO] Parando experimento Fogbed...')
    exp.stop()

    print('[ENCERRAMENTO] Tudo finalizado com sucesso.')
