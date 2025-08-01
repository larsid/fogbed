"""
Patch para corrigir compatibilidade com cgroups v2
Este arquivo contém métodos para substituir os comandos cgroups v1 por cgroups v2
"""

import os
import subprocess
from mininet.log import debug, error


def cgroupSet_v2(self, param, value, resource='cpu'):
    """
    Versão atualizada do cgroupSet para cgroups v2
    """
    # Mapear parâmetros do cgroups v1 para v2
    param_mapping = {
        'cfs_quota_us': 'cpu.max',
        'cfs_period_us': 'cpu.max', 
        'shares': 'cpu.weight',
        'limit_in_bytes': 'memory.max'
    }
    
    container_id = self.did
    
    # Caminho do cgroup v2 para o container
    cgroup_path = f"/sys/fs/cgroup/system.slice/docker-{container_id}.scope"
    
    try:
        if param in ['cfs_quota_us', 'cfs_period_us']:
            # Para cpu.max, precisamos ler o valor atual e combinar quota/period
            cpu_max_file = os.path.join(cgroup_path, 'cpu.max')
            if os.path.exists(cpu_max_file):
                with open(cpu_max_file, 'r') as f:
                    current = f.read().strip().split()
                
                if param == 'cfs_quota_us':
                    # Formato: "quota period" ou "max period"
                    period = current[1] if len(current) > 1 else "100000"
                    new_value = f"{value} {period}" if value > 0 else f"max {period}"
                elif param == 'cfs_period_us':
                    quota = current[0] if len(current) > 0 else "max"
                    new_value = f"{quota} {value}"
                
                with open(cpu_max_file, 'w') as f:
                    f.write(new_value)
                    
                debug(f"cgroups v2: wrote {new_value} to {cpu_max_file}\n")
                return value
                
        elif param == 'shares' and resource == 'cpu':
            # Converter cpu shares para cpu weight (cgroups v2)
            # weight = (shares * 10000) / 1024, clamped to 1-10000
            weight = max(1, min(10000, (value * 10000) // 1024))
            cpu_weight_file = os.path.join(cgroup_path, 'cpu.weight')
            if os.path.exists(cpu_weight_file):
                with open(cpu_weight_file, 'w') as f:
                    f.write(str(weight))
                debug(f"cgroups v2: wrote {weight} to {cpu_weight_file}\n")
                return weight
                
        elif param == 'limit_in_bytes' and resource == 'memory':
            memory_max_file = os.path.join(cgroup_path, 'memory.max')
            if os.path.exists(memory_max_file):
                with open(memory_max_file, 'w') as f:
                    f.write(str(value))
                debug(f"cgroups v2: wrote {value} to {memory_max_file}\n")
                return value
                
    except Exception as e:
        # Fallback para o comportamento original se cgroups v2 falhar
        debug(f"cgroups v2 failed, trying original method: {e}\n")
        return original_cgroupSet(self, param, value, resource)
    
    return value


def cgroupGet_v2(self, param, resource='cpu'):
    """
    Versão atualizada do cgroupGet para cgroups v2
    """
    container_id = self.did
    cgroup_path = f"/sys/fs/cgroup/system.slice/docker-{container_id}.scope"
    
    try:
        if param in ['cfs_quota_us', 'cfs_period_us']:
            cpu_max_file = os.path.join(cgroup_path, 'cpu.max')
            if os.path.exists(cpu_max_file):
                with open(cpu_max_file, 'r') as f:
                    values = f.read().strip().split()
                    if param == 'cfs_quota_us':
                        return int(values[0]) if values[0] != 'max' else -1
                    else:  # cfs_period_us
                        return int(values[1]) if len(values) > 1 else 100000
                        
        elif param == 'shares' and resource == 'cpu':
            cpu_weight_file = os.path.join(cgroup_path, 'cpu.weight')
            if os.path.exists(cpu_weight_file):
                with open(cpu_weight_file, 'r') as f:
                    weight = int(f.read().strip())
                    # Converter weight de volta para shares
                    return (weight * 1024) // 10000
                    
        elif param == 'limit_in_bytes' and resource == 'memory':
            memory_max_file = os.path.join(cgroup_path, 'memory.max')
            if os.path.exists(memory_max_file):
                with open(memory_max_file, 'r') as f:
                    value = f.read().strip()
                    return int(value) if value != 'max' else -1
                    
    except Exception as e:
        debug(f"cgroups v2 get failed: {e}\n")
        return 0
    
    return 0


def patch_docker_cgroups():
    """
    Aplica o patch para usar cgroups v2 na classe Docker do mininet
    """
    from mininet.node import Docker
    
    # Salvar métodos originais
    global original_cgroupSet, original_cgroupGet
    original_cgroupSet = Docker.cgroupSet
    original_cgroupGet = Docker.cgroupGet
    
    # Substituir pelos métodos v2
    Docker.cgroupSet = cgroupSet_v2
    Docker.cgroupGet = cgroupGet_v2
    
    debug("cgroups v2 patch aplicado com sucesso!\n")


def unpatch_docker_cgroups():
    """
    Remove o patch e volta aos métodos originais
    """
    from mininet.node import Docker
    
    if 'original_cgroupSet' in globals():
        Docker.cgroupSet = original_cgroupSet
        Docker.cgroupGet = original_cgroupGet
        debug("cgroups v2 patch removido!\n")
