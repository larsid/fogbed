import time

from fogbed import (
    AvailabilityFail, AvailabilityMode, 
    Container, CrashFail, 
    FailController, FogbedExperiment, 
    setLogLevel
)

setLogLevel('info')

exp = FogbedExperiment()

fog  = exp.add_virtual_instance('fog')
edge = exp.add_virtual_instance('edge', fail_model=AvailabilityFail(
    availability=0.5, slot_time=2, availability_mode=AvailabilityMode.DISCONNECT))

gw = Container('gw')
d1 = Container('d1', fail_model=CrashFail(life_time=20))
d2 = Container('d2')

exp.add_docker(gw, fog)
exp.add_docker(d1, edge)
exp.add_docker(d2, edge)
exp.add_link(fog, edge)

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
    fails.stop()
    exp.stop()
