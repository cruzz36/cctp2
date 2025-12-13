#!/bin/bash
# Script de teste de integração para executar no CORE
# Este script testa a comunicação entre nós

echo "============================================================"
echo "TESTE DE INTEGRAÇÃO NO CORE"
echo "============================================================"

HOSTNAME=$(hostname)
echo "Nó atual: $HOSTNAME"
echo "IP: $(hostname -I | awk '{print $1}')"
echo ""

# Verificar se estamos no diretório correto
if [ ! -d "src" ] || [ ! -d "scripts" ]; then
    echo "ERRO: Execute este script a partir do diretório /tmp/nms"
    exit 1
fi

# Testar imports Python
echo "Testando imports Python..."
python3 -c "
import sys
import os
script_dir = os.path.dirname(os.path.abspath('scripts/test_core_integration.sh'))
src_dir = os.path.join(os.path.dirname(script_dir), 'src')
sys.path.insert(0, src_dir)
try:
    from server import Server
    from client import Agent
    from protocol import MissionLink, TelemetryStream
    print('✓ Imports OK')
except Exception as e:
    print(f'✗ Erro nos imports: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "ERRO: Imports falharam"
    exit 1
fi

# Executar teste automatizado
echo ""
echo "Executando testes automatizados..."
python3 scripts/test_core_automated.py auto || python3 test_core_automated.py auto

exit $?
