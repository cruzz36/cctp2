#!/usr/bin/env python3
"""
Script para iniciar a Nave-Mãe no CORE.

Uso: python3 start_nms.py
"""

import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import NMS_Server
import threading
import time

def main():
    print("="*60)
    print("NAVE-MÃE - Iniciando...")
    print("="*60)
    
    try:
        server = NMS_Server.NMS_Server()
        
        # Iniciar MissionLink (UDP 8080) em thread
        ml_thread = threading.Thread(target=server.recvMissionLink, daemon=True)
        ml_thread.start()
        print("[OK] MissionLink (UDP:8080) iniciado")
        time.sleep(0.5)  # Pequeno delay para garantir inicialização
        
        # Iniciar TelemetryStream (TCP 8081) em thread
        ts_thread = threading.Thread(target=server.recvTelemetry, daemon=True)
        ts_thread.start()
        print("[OK] TelemetryStream (TCP:8081) iniciado")
        time.sleep(0.5)
        
        # Iniciar API de Observação (HTTP 8082) em thread
        if server.observation_api:
            server.startObservationAPI()
            print("[OK] API de Observação (HTTP:8082) iniciada")
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
    
    except Exception as e:
        print(f"\n[ERRO] Erro ao iniciar Nave-Mãe: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

