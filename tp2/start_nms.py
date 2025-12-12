#!/usr/bin/env python3
"""
Script para iniciar a Nave-Mãe no CORE.

Uso: python3 start_nms.py
"""

import sys
import os
import subprocess
from datetime import datetime

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import NMS_Server
import threading
import time

class Tee:
    """
    Classe que permite escrever simultaneamente para stdout e para um ficheiro.
    Útil para guardar logs enquanto ainda mostra output no terminal.
    """
    def __init__(self, *files):
        self.files = files
    
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()  # Garantir que é escrito imediatamente
    
    def flush(self):
        for f in self.files:
            f.flush()

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
    # Configurar logging para ficheiro
    log_dir = "/tmp/nms/logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(log_dir, f"navemae_{timestamp}.log")
    
    try:
        log_file = open(log_file_path, 'w', encoding='utf-8')
        # Redirecionar stdout e stderr para ficheiro E terminal
        sys.stdout = Tee(sys.stdout, log_file)
        sys.stderr = Tee(sys.stderr, log_file)
        print(f"[INFO] Logs sendo guardados em: {log_file_path}")
    except Exception as e:
        print(f"[AVISO] Não foi possível criar ficheiro de log: {e}")
        print("[AVISO] Continuando sem guardar logs em ficheiro...")
    
    print("="*60)
    print("NAVE-MÃE - Iniciando...")
    print("="*60)
    
    try:
        cleanup_old_processes()
        server = NMS_Server.NMS_Server()
        
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
        
        # Iniciar API de Observação (HTTP 8082) em thread
        if server.observation_api:
            try:
                server.startObservationAPI()
                time.sleep(1)
                print("[OK] API de Observação (HTTP:8082) iniciada")
                print(f"[INFO] API acessível em: http://{server.IPADDRESS}:8082")
            except Exception as e:
                print(f"[ERRO] Falha ao iniciar API de Observação: {e}")
        else:
            print("[AVISO] API de Observação não disponível (Flask não instalado)")
        
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
            if 'log_file' in locals():
                print(f"[INFO] Logs guardados em: {log_file_path}")
    
    except Exception as e:
        print(f"\n[ERRO] Erro ao iniciar Nave-Mãe: {e}")
        import traceback
        traceback.print_exc()
        if 'log_file' in locals():
            print(f"[INFO] Logs guardados em: {log_file_path}")
        sys.exit(1)

if __name__ == '__main__':
    main()

