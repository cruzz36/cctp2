#!/usr/bin/env python3
"""
Script para iniciar a Nave-Mãe no CORE.

Uso: python3 scripts/start_nms.py (executar a partir do diretório raiz do projeto)
     ou: cd /tmp/nms && python3 scripts/start_nms.py
"""

import sys
import os
import subprocess

# Adicionar diretório src ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(script_dir), 'src')
sys.path.insert(0, src_dir)

# Import após modificar sys.path (o linter pode não resolver, mas funciona em runtime)
from server import Server  # type: ignore
import threading
import time

def cleanup_old_processes():
    """
    Liberta portas 8080/8081/8082 e termina processos antigos do NMS.
    Evita o erro "Address already in use" quando há instâncias penduradas.
    """
    print("[INFO] A limpar processos antigos e portas 8080/8081/8082...")
    cmds = [
        # Não matar o processo atual; apenas componentes antigos
        ["pkill", "-f", "MissionLink.py"],
        ["pkill", "-f", "TelemetryStream.py"],
        ["fuser", "-k", "8080/udp"],
        ["fuser", "-k", "8081/tcp"],
        ["fuser", "-k", "8082/tcp"],
    ]
    for cmd in cmds:
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            # Se pkill/fuser não existirem no ambiente, simplesmente ignora
            continue
        except Exception:
            continue
    time.sleep(0.5)

def main():
    print("="*60)
    print("NAVE-MÃE - Iniciando...")
    print("="*60)
    
    try:
        cleanup_old_processes()
        server = Server.Server()
        
        # Iniciar MissionLink (UDP 8080) em thread
        ml_thread = threading.Thread(target=server.recvMissionLink, daemon=True)
        ml_thread.start()
        print("[OK] MissionLink (UDP:8080) iniciado")
        time.sleep(0.5)
        
        # Iniciar TelemetryStream (TCP 8081) em thread
        ts_thread = threading.Thread(target=server.recvTelemetry, daemon=True)
        ts_thread.start()
        print("[OK] TelemetryStream (TCP:8081) iniciado")
        time.sleep(0.5)
        
        # Iniciar API de Observação (HTTP 8082) em thread (necessária para Ground Control)
        if server.observation_api:
            try:
                server.startObservationAPI()
                time.sleep(1)
                print("[OK] API de Observação iniciada (necessária para Ground Control)")
            except Exception as e:
                print(f"[ERRO] Falha ao iniciar API de Observação: {e}")
        else:
            print("[AVISO] API de Observação não disponível (Flask não instalado)")
            print("[AVISO] Ground Control não funcionará sem a API")
        
        print("="*60)
        print("Nave-Mãe pronta e a escutar!")
        print("="*60)
        print("\nAguardando conexões de rovers...")
        print("Pressione Ctrl+C para encerrar\n")
        
        # Manter servidor a correr
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nA encerrar Nave-Mãe...")
            print("Aguardando threads terminarem...")
            time.sleep(2)
            print("Nave-Mãe encerrada.")
    
    except Exception as e:
        print(f"\n[ERRO] Erro ao iniciar Nave-Mãe: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

