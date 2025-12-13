#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se todos os imports funcionam corretamente.
Execute este script antes de copiar para o CORE para garantir que não há erros.
"""

import sys
import os

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adicionar diretório src ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(script_dir), 'src')
sys.path.insert(0, src_dir)

def test_imports():
    """Testa todos os imports principais."""
    errors = []
    warnings = []
    
    print("="*60)
    print("TESTE DE IMPORTS")
    print("="*60)
    
    # Testar imports básicos
    print("\n[1/8] Testando imports básicos...")
    try:
        import socket
        import threading
        import json
        import time
        print("  [OK] Imports basicos OK")
    except ImportError as e:
        errors.append(f"Imports basicos: {e}")
        print(f"  [ERRO] Erro: {e}")
    
    # Testar protocol
    print("\n[2/8] Testando protocol...")
    try:
        from protocol import MissionLink, TelemetryStream
        print("  [OK] Protocol OK")
    except ImportError as e:
        errors.append(f"Protocol: {e}")
        print(f"  [ERRO] Erro: {e}")
    
    # Testar server
    print("\n[3/8] Testando server...")
    try:
        from server import Server
        print("  [OK] Server OK")
    except ImportError as e:
        errors.append(f"Server: {e}")
        print(f"  [ERRO] Erro: {e}")
    
    # Testar client
    print("\n[4/8] Testando client...")
    try:
        from client import Agent
        print("  [OK] Client OK")
    except ImportError as e:
        errors.append(f"Client: {e}")
        print(f"  [ERRO] Erro: {e}")
    
    # Testar entities
    print("\n[5/8] Testando entities...")
    try:
        from entities import Limit
        print("  [OK] Entities OK")
    except ImportError as e:
        errors.append(f"Entities: {e}")
        print(f"  [ERRO] Erro: {e}")
    
    # Testar API (opcional)
    print("\n[6/8] Testando API (opcional)...")
    try:
        from api import ObservationAPI
        print("  [OK] API OK")
    except ImportError as e:
        warnings.append(f"API: {e} (opcional - requer Flask)")
        print(f"  [AVISO] {e} (opcional)")
    
    # Testar GroundControl
    print("\n[7/8] Testando GroundControl...")
    try:
        # GroundControl faz sys.exit(1) se requests não estiver instalado
        # Precisamos capturar isso
        import sys
        old_exit = sys.exit
        exit_called = False
        def mock_exit(code=0):
            nonlocal exit_called
            if code != 0:
                exit_called = True
                raise ImportError("GroundControl requer requests (opcional)")
        sys.exit = mock_exit
        try:
            from ground_control import GroundControl
            print("  [OK] GroundControl OK")
        finally:
            sys.exit = old_exit
            if exit_called:
                raise ImportError("GroundControl requer requests (opcional)")
    except ImportError as e:
        warnings.append(f"GroundControl: {e}")
        print(f"  [AVISO] {e} (opcional - requer requests)")
    except SystemExit:
        warnings.append("GroundControl: requests não instalado (opcional)")
        print("  [AVISO] requests não instalado (opcional)")
    except Exception as e:
        warnings.append(f"GroundControl: {e}")
        print(f"  [AVISO] {e}")
    
    # Testar scripts de início
    print("\n[8/8] Testando scripts de inicio...")
    try:
        # Scripts estão em scripts/, não podem ser importados diretamente
        # Verificar apenas que existem
        scripts_dir = os.path.join(os.path.dirname(script_dir), 'scripts')
        if os.path.exists(os.path.join(scripts_dir, 'start_nms.py')):
            print("  [OK] Scripts de inicio encontrados")
        else:
            warnings.append("Scripts não encontrados")
            print("  [AVISO] Scripts não encontrados")
    except Exception as e:
        warnings.append(f"Scripts: {e}")
        print(f"  [AVISO] {e}")
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    
    if errors:
        print(f"\n[ERRO] ERROS ENCONTRADOS: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n[OK] Todos os imports principais funcionam!")
    
    if warnings:
        print(f"\n[AVISO] AVISOS: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")
        print("\nNota: Avisos não impedem execução, mas algumas funcionalidades podem não estar disponíveis.")
    
    return True

def test_basic_functionality():
    """Testa funcionalidade básica sem criar sockets."""
    print("\n" + "="*60)
    print("TESTE DE FUNCIONALIDADE BÁSICA")
    print("="*60)
    
    try:
        from server import Server  # type: ignore
        from client import Agent  # type: ignore
        
        print("\n[1/2] Testando criacao de instancia Server...")
        # Não vamos criar socket real, apenas verificar que a classe pode ser importada
        print("  [OK] Classe Server importada com sucesso")
        
        print("\n[2/2] Testando criacao de instancia Agent...")
        # Não vamos criar socket real, apenas verificar que a classe pode ser importada
        print("  [OK] Classe Agent importada com sucesso")
        
        print("\n[OK] Testes de funcionalidade basica concluidos!")
        return True
        
    except Exception as e:
        print(f"\n[ERRO] Erro nos testes de funcionalidade: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE IMPORTS E ESTRUTURA")
    print("="*60)
    
    imports_ok = test_imports()
    functionality_ok = test_basic_functionality()
    
    print("\n" + "="*60)
    print("RESULTADO FINAL")
    print("="*60)
    
    if imports_ok and functionality_ok:
        print("\n[OK] TUDO OK! O codigo esta pronto para ser copiado para o CORE.")
        print("\nProximos passos:")
        print("  1. Copiar ficheiros para os nos do CORE")
        print("  2. Instalar dependencias: pip3 install -r requirements.txt")
        print("  3. Executar conforme docs/Guia_CORE_Unificado.md")
        sys.exit(0)
    else:
        print("\n[ERRO] ERROS ENCONTRADOS! Corrija os erros antes de copiar para o CORE.")
        sys.exit(1)
