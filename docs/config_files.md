Fogbed accepts a `topology.yml` file to build an `Experiment`.

To create a `FogbedExperiment`, define the following sections: `containers`, `instances`, and `links`. Furthermore, you have the option to create a single topology by setting the `is_distributed` section to control when the topology should be distributed across the workers.

??? example "See the example of a single topology:"
    ``` yaml title="topology.yml"
    is_distributed: false

    containers:
      node1:
        dimage: ubuntu:trusty
        dcmd: /bin/bash
        environment:
          DATA_PATH: /tmp/data
        ports:
          - 80: 8000
        resources: medium
      node2:
        dimage: ubuntu:trusty
      node3:
        dimage: ubuntu:trusty
      node4:
        dimage: ubuntu:trusty

    instances:
      cloud:
        model: 
          type: cloud
          max_cu: 32
          max_mu: 2048
        containers: ['node1']
          
      fog:
        model: 
          type: fog
          max_cu: 8
          max_mu: 512
        containers: ['node2']
      
      edge:
        model: 
          type: edge
          max_cu: 1
          max_mu: 128
        containers: ['node3', 'node4']

    links:
      cloud_fog: 
        delay: 10ms
      fog_edge: 

    workers:
      worker1:
        ip: hostname1
        port: 5000
        reachable: ['cloud']
        instances: ['cloud']
      
      worker2:
        ip: hostname2
        port: 5000
        reachable: ['fog']
        instances: ['fog', 'edge']
        links:
          fog_edge:

    tunnels: ['worker1_worker2']
    ```

To run that topology use the command:
```
sudo fogbed /path/to/topology.yml
```

!!! tip
    If you set `is_distributed: true` that example will run the experiment using two workers.

    Make sure the IP addresses and ports are configured according to the experiment script
    and run `sudo RunWorker` in each machine.

## Using the ExperimentBuilder
```py title="experiment.py"
from fogbed import ExperimentBuilder

if(__name__=='__main__'):
    exp = ExperimentBuilder(filename='topology.yml').build()
        
    try:
        exp.start()
        node1 = exp.get_docker('node1')
        node3 = exp.get_docker('node3')
        print(node1.cmd(f'ping -c 4 {node3.ip}'))

        input('\nPress Enter to exit...')
    except Exception as ex:
        print(ex)
    finally:
        exp.stop()
```

To run that experiment use the command:
```
sudo python3 experiment.py
```