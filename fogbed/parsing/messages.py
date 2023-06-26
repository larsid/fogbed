class YMLErrors:
    @staticmethod
    def invalid_container(container: str) -> str:
        return f'''
        \nProvide a valid container:
        \r{container}:
        \r  resources: tiny | small | medium | large | xlarge 
        '''

    @staticmethod
    def invalid_instance(instance: str) -> str:
        return f'''
        \nProvide a virtual instance on format:
        \r{instance}:
        \r  model:
        \r    type: cloud | fog | edge
        \r    max_cu: float
        \r    max_mu: int
        \r  containers: [<container1>, <container2>, ...]
        '''
    
    @staticmethod
    def invalid_link() -> str:
        return '''
        \nProvide a link on format:\n
        \rinstance1_instance2:
        \r  delay: 10ms
        \r  bw: 10
        '''
    
    @staticmethod
    def invalid_tunnel() -> str:
        return '''
        \nProvide a tunnel on format: 
        \rtunnels: [worker1_worker2, ...]
        '''

    @staticmethod
    def invalid_worker(worker: str) -> str:
        return f'''
        \nProvide a valid worker on format:
        \r{worker}:
        \r  ip: <HOSTNAME/IP>
        \r  port: <PORT>
        \r  reachable: [<instance1>, ...]
        \r  instances: [<instance1>, <instance2>, ...]
        \r  links:
        \r    instance1_instance2:
        \r      delay: 10ms
        \r      bw: 10
        \r    instance1_instance3:
        '''
