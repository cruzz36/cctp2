#!/usr/bin/env python3
"""
Script para iniciar o Ground Control no CORE.

Uso: python3 start_ground_control.py [API_URL]

Exemplos:
  python3 start_ground_control.py
  python3 start_ground_control.py http://10.0.1.10:8082
"""

import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from GroundControl import GroundControl

def main():
    # IP padrão da Nave-Mãe na topologia: 10.0.1.10
    default_api = "http://10.0.1.10:8082"
    api_url = sys.argv[1] if len(sys.argv) > 1 else default_api
    
    print("="*60)
    print("GROUND CONTROL - Iniciando...")
    print(f"API de Observação: {api_url}")
    print("="*60)
    
    try:
        gc = GroundControl(api_url=api_url)
        
        # Verificar conexão
        print(f"\n[...] A conectar à API em {api_url}...")
        test_data = gc._make_request('/status')
        if test_data is None:
            print("\n[ERRO] Não foi possível conectar à API.")
            print("Certifique-se de que:")
            print("  1. A Nave-Mãe está a correr")
            print("  2. A API de Observação está ativa")
            print("  3. A URL está correta")
            sys.exit(1)
        
        print("[OK] Conexão estabelecida com sucesso!\n")
        
        # Executar interface interativa
        gc.run_interactive()
    
    except KeyboardInterrupt:
        print("\n\nGround Control encerrado.")
    except Exception as e:
        print(f"\n[ERRO] Erro no Ground Control: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

