from typing import Any, Dict, List
import yaml

from fogbed import Container
from fogbed.parsing.messages import YMLErrors
from fogbed.parsing.dto import (
    LinkDTO, TunnelDTO, VirtualInstanceDTO, WorkerDTO,
    resources
)
from fogbed.parsing.exceptions import (
    ParseContainersException, ParseLinksException, ParseTunnelsException, 
    ParseVirtualInstances, ParseWorkersException, SectionNotFound
)


Options = Dict[str, Any]
Links = Dict[str, 'Options | None']
ContainerPorts   = List[Dict[int, int]]
VirtualInstances = Dict[str, Options]
Workers = Dict[str, Options]


def load_yml_file(filename: str) -> Dict[str, Any]:
    with open(filename, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


class YMLParser:
    def __init__(self, filename: str) -> None:
        self.data = load_yml_file(filename)

    def get_containers(self) -> Dict[str, Container]:
        section = 'containers'
        if(not self.section_is_present(section)):
            raise SectionNotFound(section)
        
        return {
            name: self._parse_container(name, options)
            for name, options in self.data[section].items()}
        

    def get_instances(self) -> List[VirtualInstanceDTO]:
        section = 'instances'
        if(not self.section_is_present(section)):
            raise SectionNotFound(section)
        
        instances: VirtualInstances = self.data[section]
        return [
            self._parse_virtual_instance(name, options)
            for name, options in instances.items()]
        
    
    def get_links(self) -> List[LinkDTO]:
        section = 'links'
        if(not self.section_is_present(section)):
            raise SectionNotFound(section)
        
        try:
            links: Links = self.data[section]
            return [
                LinkDTO.from_dict(link, options)
                for link, options in links.items()]
        except:
            raise ParseLinksException(YMLErrors.invalid_link())


    def get_tunnels(self) -> List[TunnelDTO]:
        section = 'tunnels'
        if(not self.section_is_present(section)):
            return []
        
        try:
            tunnels: List[str] = self.data[section]
            return [
                TunnelDTO.from_dict(tunnel)
                for tunnel in tunnels]  
        except:
            raise ParseTunnelsException(YMLErrors.invalid_tunnel())


    def get_workers(self) -> Dict[str, WorkerDTO]:
        section = 'workers'
        if(not self.section_is_present(section)):
            raise SectionNotFound(section)
        
        data: Workers = self.data[section]
        return  {
            name: self._parse_worker(name, options)
            for name, options in data.items()
        }

    
    def experiment_is_distributed(self) -> bool:
        try:
            return self.data['is_distributed'] == True
        except: pass
        return False


    def section_is_present(self, section: str) -> bool:
        return self.data.get(section) != None


    def _parse_container(self, name: str, options: Options) -> Container:    
        try:
            self._parse_resources(options)
            if(options.get('ports') is not None): 
                options['port_bindings'] = self._parse_bindings(options['ports'])
            return Container(name, **options)
        except:
            raise ParseContainersException(YMLErrors.invalid_container(name))
    
    def _parse_bindings(self, ports: ContainerPorts) -> Dict[int, int]:
        port_bindings = {}
        for binding in ports:
            port_bindings.update(binding)
        return port_bindings    

    def _parse_resources(self, options: Options):
        flavor = options.get('resources')
        if(flavor is not None):
            flavor = str(flavor).lower()
            options['resources'] = resources[flavor]


    def _parse_virtual_instance(self, name: str, options: Options) -> VirtualInstanceDTO:
        try:
            return VirtualInstanceDTO.from_dict(name, options)
        except:
            raise ParseVirtualInstances(YMLErrors.invalid_instance(name))


    def _parse_worker(self, name: str, options: Options) -> WorkerDTO:
        try:
            return WorkerDTO.from_dict(options)
        except:
            raise ParseWorkersException(YMLErrors.invalid_worker(name))
    