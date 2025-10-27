#!/usr/bin/env python3
"""
Script para verificar se um IP está disponível no container.
Útil para debug de problemas de bind.
"""

import socket
import sys
import os


def get_all_local_ips():
    """
    Retorna todos os IPs configurados no sistema.
    """
    hostname = socket.gethostname()
    local_ips = []
    
    try:
        # Obtém todos os IPs associados ao hostname
        addr_info = socket.getaddrinfo(hostname, None)
        for info in addr_info:
            ip = info[4][0]
            if ip not in local_ips:
                local_ips.append(ip)
    except Exception as e:
        print(f"Erro ao obter IPs: {e}")
    
    return local_ips


def test_bind(ip, port=0):
    """
    Testa se é possível fazer bind em um IP específico.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((ip, port))
        sock.close()
        return True
    except OSError as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("VERIFICAÇÃO DE IPs DISPONÍVEIS NO CONTAINER")
    print("=" * 60)
    
    # Mostra o hostname
    hostname = socket.gethostname()
    print(f"\nHostname: {hostname}")
    
    # Mostra todos os IPs locais
    print("\nIPs encontrados no sistema:")
    local_ips = get_all_local_ips()
    for ip in local_ips:
        print(f"  - {ip}")
    
    # Verifica o IP da variável de ambiente BIND_IP
    bind_ip = os.getenv('BIND_IP')
    
    if bind_ip:
        print(f"\nVariável BIND_IP configurada: {bind_ip}")
        
        # Testa se o IP está disponível
        result = test_bind(bind_ip)
        
        if result is True:
            print(f"✓ O IP {bind_ip} está disponível e pode ser usado para bind")
        else:
            print(f"✗ O IP {bind_ip} NÃO está disponível para bind")
            print(f"  Erro: {result[1]}")
            print(f"\n  SOLUÇÃO:")
            print(f"  Execute no host:")
            print(f"    docker exec {hostname} ip addr add {bind_ip}/24 dev eth0")
    else:
        print("\nVariável BIND_IP não configurada")
    
    # Testa bind em 0.0.0.0 (qualquer interface)
    print(f"\nTeste de bind em 0.0.0.0 (qualquer interface):")
    result = test_bind('0.0.0.0')
    if result is True:
        print(f"✓ Bind em 0.0.0.0 funciona")
    else:
        print(f"✗ Bind em 0.0.0.0 falhou: {result[1]}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()

