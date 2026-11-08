import sys
import time

from fogbed import (
    AvailabilityFail, AvailabilityMode, 
    Container, CrashFail, 
    FailController, FogbedDistributedExperiment, 
    setLogLevel
)

setLogLevel('info')

worker1_ip = sys.argv[1] if(len(sys.argv) > 1) else '192.168.0.151'
worker2_ip = sys.argv[2] if(len(sys.argv) > 2) else '192.168.0.152'

exp = FogbedDistributedExperiment()

fog  = exp.add_virtual_instance('fog')
edge = exp.add_virtual_instance('edge', fail_model=AvailabilityFail(
    availability=0.5, slot_time=2, availability_mode=AvailabilityMode.DISCONNECT))

gw = Container('gw')
d1 = Container('d1', fail_model=CrashFail(life_time=20))
d2 = Container('d2')

exp.add_docker(gw, fog)
exp.add_docker(d1, edge)
exp.add_docker(d2, edge)

worker1 = exp.add_worker(ip=worker1_ip)
worker2 = exp.add_worker(ip=worker2_ip)

worker1.add(fog, reachable=True)
worker2.add(edge, reachable=True)
exp.add_tunnel(worker1, worker2)

fails = FailController(exp, seed=42)

try:
    exp.start()
    fails.start()
    time.sleep(60)

    for event in fails.events():
        print(event)
    for metrics in fails.metrics().values():
        print(metrics.to_dict())

except Exception as ex: 
    print(ex)
finally:
    try:
        fails.stop()
    finally:
        exp.stop()
