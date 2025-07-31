from fogbed import (
    FogbedDistributedExperiment, 
    Container
)

exp   = FogbedDistributedExperiment(metrics_enabled=True)

cloud = exp.add_virtual_instance('cloud')
fog   = exp.add_virtual_instance('fog')
edge  = exp.add_virtual_instance('edge')

exp.add_docker(Container('d1'), cloud)
exp.add_docker(Container('d2'), fog)
exp.add_docker(Container('d3'), edge)

worker1 = exp.add_worker(ip='esau-vm1', port=5000)

worker1.add(cloud)
worker1.add(fog)
worker1.add(edge)
worker1.add_link(cloud, fog, delay='10ms')
worker1.add_link(fog, edge)

try:
    exp.start()
    
    d1 = exp.get_docker('d1')
    d3 = exp.get_docker('d3')
    
    print(d1.cmd('ifconfig'))
    print(d1.cmd(f'ping -c 4 {d3.ip}'))
    input('Press Enter to exit...')

except Exception as ex: 
    print(ex)
finally:
    exp.stop()

# Run a Worker with: sudo RunWorker
# Change the Worker IP with your machine ip adddress
#    ex: worker1 = exp.add_worker(ip='192.168.0.185', port=5000)
# Run this example with: sudo python3 tests/distributed_metrics_enabled.py 