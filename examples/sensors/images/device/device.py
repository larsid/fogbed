import os
import random
import time
from typing import Any, Dict
import uuid
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.connection import create_connection


class SourceAddressAdapter(HTTPAdapter):
    """
    Adapter customizado para fazer bind de um IP específico nas requisições HTTP.
    """
    def __init__(self, source_address, **kwargs):
        self.source_address = source_address
        super().__init__(**kwargs)
    
    def init_poolmanager(self, *args, **kwargs):
        """
        Configura o pool manager com o endereço de origem especificado.
        """
        kwargs['source_address'] = (self.source_address, 0)
        return super().init_poolmanager(*args, **kwargs)


class Device:
    def __init__(self, name: str, url: str, bind_ip: str = None) -> None:
        self.id   = 0
        self.name = name
        self.url  = url
        self.bind_ip = bind_ip
        
        # Cria uma sessão HTTP
        self.session = requests.Session()
        
        # Se um IP de bind foi especificado, configura o adapter customizado
        if self.bind_ip:
            adapter = SourceAddressAdapter(self.bind_ip)
            # Monta o adapter para http e https
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
            print(f'[{self.name}]: Configurado bind para IP {self.bind_ip}')


    def generate_data(self) -> Dict[str, Any]:
        return {               
            'name':             self.name,       
            'temperature':      round(random.uniform(35, 39), 1), 
            'heart_rate':       random.randrange(0, 120),    
            'blood_pressure':   random.randrange(5, 130),
            'respiratory_rate': random.randrange(5, 30)
        }

    def connect(self):
        while 1:
            try:
                response = self.session.get(url=f'{self.url}')

                if response.ok:
                    break
            except Exception as ex: 
                print(f'[{self.name}]: {ex}')
            time.sleep(1)
    

    def create_user(self):
        data = self.generate_data()
        response = self.session.post(url=f'{self.url}/users', json=data)
        self.id = int(response.json()['data']['id'])


    def update_user(self):
        data = self.generate_data()
        self.session.put(url=f'{self.url}/users/{self.id}', json=data)


    def run(self):
        self.connect()
        self.create_user()

        try:
            while 1:
                self.update_user()
                time.sleep(random.randrange(2, 6))
        except:
            self.session.delete(url=f'{self.url}/users/{self.id}')
        finally:
            # Fecha a sessão HTTP ao finalizar
            self.session.close()

        


if(__name__=='__main__'):
    uid = str(os.getenv('UID', uuid.uuid4()))
    url = os.getenv('URL', 'http://localhost:8000')
    bind_ip = os.getenv('BIND_IP', None)  # IP de bind da rede do emulador
    
    Device(name=uid, url=url, bind_ip=bind_ip).run()

