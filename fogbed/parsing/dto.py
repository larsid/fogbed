from typing import Any, Dict, List, Optional

from fogbed import (
    HardwareResources, Resources, CloudResourceModel, EdgeResourceModel, FogResourceModel
)
from fogbed.resources.protocols import ResourceModel

resources: Dict[str, HardwareResources] = {
    'tiny':   Resources.TINY,
    'small':  Resources.SMALL,
    'medium': Resources.MEDIUM,
    'large':  Resources.LARGE,
    'xlarge': Resources.XLARGE
}

def validate_invalid_fields(data: Dict[str, Any]):
    for value in data.values():
        if(value is None):
            raise Exception('Invalid value')


class LinkDTO:
    def __init__(self, node1: str, node2: str, **options) -> None:
        self.node1  = node1
        self.node2  = node2
        self.params = options
    
    @staticmethod
    def from_dict(link: str, options: Optional[Dict[str, Any]]):
        node1, node2 = link.split('_')
        if(options is None): 
            options = {}
        else:
            validate_invalid_fields(options)
        return LinkDTO(node1, node2, **options)


class TunnelDTO:
    def __init__(self, worker1: str, worker2: str) -> None:
        self.worker1 = worker1
        self.worker2 = worker2
    
    @staticmethod
    def from_dict(tunnel: str):
        worker1, worker2 = tunnel.split('_')
        return TunnelDTO(worker1, worker2)
        

class VirtualInstanceDTO:
    def __init__(self, 
        name: str, 
        containers: List[str],
        model: Optional[ResourceModel] = None, 
    ):
        self.name = name
        self.model = model
        self.containers = containers

    @staticmethod
    def parse_resource_model(options: Dict[str, Any]) -> 'ResourceModel | None':
        if(options.get('model') is None):
            return None
        
        model  = str(options['model']['type']).lower()
        max_cu = float(options['model']['max_cu'])
        max_mu = int(options['model']['max_mu'])
        
        if(not model in ['cloud', 'edge', 'fog']):
            raise Exception('Invalid Flavor')
        if(model == 'cloud'):
            return CloudResourceModel(max_cu, max_mu)
        if(model == 'edge'):
            return EdgeResourceModel(max_cu, max_mu)
        return FogResourceModel(max_cu, max_mu)
        

    @staticmethod
    def from_dict(name: str, data: Dict[str, Any]):
        validate_invalid_fields(data)
        return VirtualInstanceDTO(
            name=name,
            containers=list(data['containers']),
            model=VirtualInstanceDTO.parse_resource_model(data)
        )


class WorkerDTO:
    def __init__(self,
        ip: str, 
        instances: List[str],
        port: int,
        reachable_instances: List[str] = [],
        links: List[LinkDTO] = []
    ):
        self.ip   = ip
        self.port = port
        self.instances = instances
        self.reachable_instances = reachable_instances
        self.links = links
            
    def instance_is_reachable(self, name: str) -> bool:
        return name in self.reachable_instances

    @staticmethod
    def parse_links(data: Dict[str, Any]) -> List[LinkDTO]:
        return [
            LinkDTO.from_dict(link, options)
            for link, options in data.items()
        ]
    
    @staticmethod
    def from_dict(data: Dict[str, Any]):
        validate_invalid_fields(data)
        port = 5000 if(data.get('port') is None) else data['port']
        reachable_instances = [] if(data.get('reachable') is None) else data['reachable']
        links = {} if(data.get('links') is None) else data['links']

        return WorkerDTO(
            ip=str(data['ip']),
            port=int(port),
            instances=list(data['instances']),
            reachable_instances=list(reachable_instances),
            links=WorkerDTO.parse_links(links)
        )
    