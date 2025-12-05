# Guia de Teste no CORE (Common Open Research Emulator)

Este guia explica como testar o código do projeto NMS (Nave-Mãe e Rovers) no CORE.

## Resumo Rápido

1. **Abrir topologia** `topologiatp2.imn` no CORE
2. **Copiar ficheiros** para todos os nós (ou usar diretório partilhado)
3. **Iniciar Nave-Mãe** no nó **n1**:
   ```bash
   python3 start_nms.py
   ```
4. **Iniciar Rovers** nos nós **n3** e **n4**:
   ```bash
   python3 start_rover.py 10.0.1.10 r1  # n3
   python3 start_rover.py 10.0.1.10 r2  # n4
   ```
5. **Iniciar Ground Control** no nó **n2** (opcional):
   ```bash
   python3 start_ground_control.py
   ```

**IPs importantes:**
- Nave-Mãe: `10.0.1.10`
- Ground Control: `10.0.0.10`
- Rover1: `10.0.3.10`
- Rover2: `10.0.2.10`

## Pré-requisitos

1. **CORE instalado** no sistema
2. **Python 3** instalado
3. **Dependências Python** instaladas:
   ```bash
   pip install -r requirements.txt
   ```

## Estrutura da Topologia

A topologia está definida em `topologiatp2.imn`. A estrutura inclui:

- **n1 - NaveMae** (servidor)
  - IP: `10.0.1.10` (eth1) e `10.0.0.11` (eth0)
  - Conectado a n2 (Ground Control) e n5 (Satélite)

- **n2 - GroundControl** (cliente da API)
  - IP: `10.0.0.10` (eth0)
  - Conectado a n1 (Nave-Mãe)

- **n3 - Rover1** (cliente)
  - IP: `10.0.3.10` (eth0)
  - Conectado a n5 (Satélite)

- **n4 - Rover2** (cliente)
  - IP: `10.0.2.10` (eth0)
  - Conectado a n5 (Satélite)

- **n5 - Satelite** (router)
  - IPs: `10.0.3.1`, `10.0.2.1`, `10.0.1.1`
  - Conecta rovers à Nave-Mãe

## Passo 1: Abrir Topologia no CORE

1. Abrir o **CORE**
2. **File → Open** → Selecionar `topologiatp2.imn`
3. A topologia será carregada com todos os nós

## Passo 2: Iniciar a Emulação

1. No CORE, clicar em **Start the session** (botão play ▶️)
2. Aguardar que todos os nós iniciem
3. Verificar que todas as interfaces de rede estão ativas

## Passo 3: Copiar Código para os Nós

### Opção A: Copiar Manualmente

1. **Nave-Mãe (servidor)**:
   - Clicar com botão direito no nó da Nave-Mãe
   - **Shell Window** ou **Terminal**
   - Copiar todos os ficheiros do projeto para o nó:
     ```bash
     # Criar diretório
     mkdir -p /tmp/nms
     cd /tmp/nms
     
     # Copiar ficheiros (ajustar caminho conforme necessário)
     # Pode usar scp, rsync, ou copiar manualmente via interface do CORE
     ```

### Opção B: Usar Script de Cópia (Recomendado)

Criar um script que copia automaticamente os ficheiros para todos os nós:

```bash
#!/bin/bash
# copy_to_core.sh

# Diretório do projeto
PROJECT_DIR="/caminho/para/CC/tp2"

# Nós do CORE (ajustar conforme topologia)
NODES=("n1" "n2" "n3" "n4" "n5")  # Exemplo

for node in "${NODES[@]}"; do
    echo "Copiando para $node..."
    # Usar vcmd do CORE para copiar ficheiros
    # Ajustar conforme método de cópia disponível
done
```

## Passo 4: Executar Nave-Mãe (Servidor)

1. **Abrir terminal** no nó **n1 (NaveMae)**
2. **Navegar** para o diretório do projeto:
   ```bash
   cd /tmp/nms
   # ou
   cd /home/user/nms  # ajustar conforme necessário
   ```
3. **Instalar dependências** (se necessário):
   ```bash
   pip3 install psutil flask requests
   ```
4. **Executar servidor** usando o script:
   ```bash
   python3 start_nms.py
   ```
   
   Ou manualmente:
   ```bash
   python3 -c "from server import NMS_Server; import threading; import time
   server = NMS_Server.NMS_Server()
   threading.Thread(target=server.recvMissionLink, daemon=True).start()
   threading.Thread(target=server.recvTelemetry, daemon=True).start()
   if server.observation_api:
       server.startObservationAPI()
   while True: time.sleep(1)
   "
   ```
   
   Ou criar um script de inicialização:
   ```python
   # start_server.py
   from server import NMS_Server
   import threading
   
   server = NMS_Server.NMS_Server()
   
   # Iniciar servidor MissionLink em thread
   ml_thread = threading.Thread(target=server.recvMissionLink, daemon=True)
   ml_thread.start()
   
   # Iniciar servidor TelemetryStream em thread
   ts_thread = threading.Thread(target=server.recvTelemetry, daemon=True)
   ts_thread.start()
   
   # Iniciar API de Observação em thread
   if server.observation_api:
       server.startObservationAPI()
   
   print("Nave-Mãe iniciada!")
   print("MissionLink (UDP) na porta 8080")
   print("TelemetryStream (TCP) na porta 8081")
   print("API de Observação (HTTP) na porta 8082")
   
   # Manter servidor a correr
   try:
       while True:
           import time
           time.sleep(1)
   except KeyboardInterrupt:
       print("\nA encerrar servidor...")
   ```

## Passo 5: Executar Rovers (Clientes)

Para cada rover:

1. **Abrir terminal** no nó do rover:
   - **n3 (Rover1)**: IP `10.0.3.10`
   - **n4 (Rover2)**: IP `10.0.2.10`

2. **Navegar** para o diretório do projeto:
   ```bash
   cd /tmp/nms
   ```

3. **IP da Nave-Mãe**: `10.0.1.10` (conforme topologia)

4. **Executar rover** usando o script:
   ```bash
   # Para Rover1 (n3)
   python3 start_rover.py 10.0.1.10 r1
   
   # Para Rover2 (n4)
   python3 start_rover.py 10.0.1.10 r2
   ```
   
   Ou manualmente:
   ```bash
   python3 -c "from client import NMS_Agent; import threading; import time
   rover = NMS_Agent.NMS_Agent('10.0.4.10')  # IP da Nave-Mãe
   
   # Iniciar telemetria contínua
   rover.startContinuousTelemetry('10.0.4.10', interval=5)
   
   # Manter rover a correr
   try:
       while True:
           time.sleep(1)
   except KeyboardInterrupt:
       rover.stopContinuousTelemetry()
       print('Rover encerrado')
   "
   ```

   Ou criar um script:
   ```python
   # start_rover.py
   from client import NMS_Agent
   import threading
   import time
   import sys
   
   if len(sys.argv) < 2:
       print("Uso: python3 start_rover.py <IP_NAVE_MAE> [ROVER_ID]")
       sys.exit(1)
   
   nms_ip = sys.argv[1]
   rover_id = sys.argv[2] if len(sys.argv) > 2 else "r1"
   
   rover = NMS_Agent.NMS_Agent(nms_ip)
   rover.id = rover_id  # Definir ID do rover
   
   # Registo na Nave-Mãe
   print(f"Rover {rover_id} a registar-se na Nave-Mãe {nms_ip}...")
   rover.registerAgent(nms_ip)
   
   # Iniciar telemetria contínua
   rover.startContinuousTelemetry(nms_ip, interval=5)
   print(f"Rover {rover_id} iniciado!")
   print("Telemetria contínua ativa (intervalo: 5 segundos)")
   
   # Manter rover a correr
   try:
       while True:
           time.sleep(1)
   except KeyboardInterrupt:
       rover.stopContinuousTelemetry()
       print(f'\nRover {rover_id} encerrado')
   ```

## Passo 6: Executar Ground Control (Opcional)

1. **Abrir terminal** no nó **n2 (GroundControl)**
2. **Navegar** para o diretório do projeto:
   ```bash
   cd /tmp/nms
   ```
3. **Executar Ground Control** usando o script:
   ```bash
   python3 start_ground_control.py
   ```
   
   Ou manualmente:
   ```bash
   python3 GroundControl.py --api http://10.0.1.10:8082
   ```
   
   (IP da Nave-Mãe: `10.0.1.10` conforme topologia)

## Passo 7: Testar Funcionalidades

### Teste 1: Registo de Rovers

1. Executar rovers (Passo 5)
2. Verificar no servidor que aparecem mensagens:
   ```
   CONECTION ESTABLISHED
   ```
3. Verificar que rovers estão registados:
   - No servidor, verificar `self.agents` contém os IDs dos rovers

### Teste 2: Envio de Missões

1. No servidor, criar uma missão:
   ```python
   mission = {
       "mission_id": "M-001",
       "rover_id": "r1",
       "geographic_area": {"x1": 10.0, "y1": 20.0, "x2": 50.0, "y2": 60.0},
       "task": "capture_images",
       "duration_minutes": 30,
       "update_frequency_seconds": 120
   }
   server.sendMission("10.0.4.11", "r1", mission)  # IP do rover r1
   ```

2. Verificar no rover que recebe a missão

### Teste 3: Telemetria Contínua

1. Rovers devem enviar telemetria automaticamente
2. Verificar no servidor que recebe ficheiros de telemetria
3. Verificar organização por `rover_id` em subpastas

### Teste 4: API de Observação

1. No Ground Control (n2) ou via terminal:
   ```bash
   curl http://10.0.1.10:8082/rovers
   curl http://10.0.1.10:8082/missions
   curl http://10.0.1.10:8082/telemetry
   ```

2. Ou usar o Ground Control interativo (recomendado):
   ```bash
   python3 start_ground_control.py
   # Depois escolher opção 1 (Dashboard completo)
   ```

## Passo 8: Monitorização

### Ver Tráfego de Rede

1. No CORE, clicar com botão direito em uma ligação
2. **Wireshark** ou **tcpdump** para capturar pacotes
3. Verificar:
   - **UDP porta 8080**: MissionLink (handshake, missões)
   - **TCP porta 8081**: TelemetryStream (telemetria)
   - **HTTP porta 8082**: API de Observação

### Ver Logs

- **Servidor**: Verificar saída do terminal da Nave-Mãe
- **Rovers**: Verificar saída do terminal de cada rover
- **Ground Control**: Verificar saída do terminal do Ground Control

## Scripts de Inicialização Automática

### Script para Nave-Mãe

```python
# start_nms.py
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import NMS_Server
import threading
import time

def main():
    print("="*60)
    print("NAVE-MÃE - Iniciando...")
    print("="*60)
    
    server = NMS_Server.NMS_Server()
    
    # Iniciar MissionLink (UDP 8080)
    ml_thread = threading.Thread(target=server.recvMissionLink, daemon=True)
    ml_thread.start()
    print("[OK] MissionLink (UDP:8080) iniciado")
    
    # Iniciar TelemetryStream (TCP 8081)
    ts_thread = threading.Thread(target=server.recvTelemetry, daemon=True)
    ts_thread.start()
    print("[OK] TelemetryStream (TCP:8081) iniciado")
    
    # Iniciar API de Observação (HTTP 8082)
    if server.observation_api:
        server.startObservationAPI()
        print("[OK] API de Observação (HTTP:8082) iniciada")
    else:
        print("[AVISO] API de Observação não disponível (Flask não instalado)")
    
    print("="*60)
    print("Nave-Mãe pronta!")
    print("="*60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nA encerrar Nave-Mãe...")

if __name__ == '__main__':
    main()
```

### Script para Rover

```python
# start_rover.py
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client import NMS_Agent
import threading
import time

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 start_rover.py <IP_NAVE_MAE> [ROVER_ID]")
        sys.exit(1)
    
    nms_ip = sys.argv[1]
    rover_id = sys.argv[2] if len(sys.argv) > 2 else "r1"
    
    print("="*60)
    print(f"ROVER {rover_id} - Iniciando...")
    print(f"Nave-Mãe: {nms_ip}")
    print("="*60)
    
    rover = NMS_Agent.NMS_Agent(nms_ip)
    rover.id = rover_id
    
    # Registo
    print(f"[...] A registar-se na Nave-Mãe...")
    rover.registerAgent(nms_ip)
    print(f"[OK] Registado como {rover_id}")
    
    # Telemetria contínua
    rover.startContinuousTelemetry(nms_ip, interval=5)
    print(f"[OK] Telemetria contínua ativa (intervalo: 5s)")
    
    print("="*60)
    print(f"Rover {rover_id} pronto!")
    print("="*60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        rover.stopContinuousTelemetry()
        print(f"\nRover {rover_id} encerrado")

if __name__ == '__main__':
    main()
```

## Troubleshooting

### Problema: "Address already in use"

**Solução**: Verificar se porta já está em uso:
```bash
netstat -tuln | grep 8080  # MissionLink
netstat -tuln | grep 8081  # TelemetryStream
netstat -tuln | grep 8082  # API
```

### Problema: "Connection refused"

**Solução**: 
1. Verificar que servidor está a correr
2. Verificar IP/porta corretos
3. Verificar conectividade de rede no CORE

### Problema: "Module not found"

**Solução**: 
1. Verificar que todos os ficheiros foram copiados
2. Verificar `sys.path` inclui diretório do projeto
3. Verificar que `__init__.py` existe em cada pasta

### Problema: Rovers não se registam

**Solução**:
1. Verificar que servidor está a correr
2. Verificar IP da Nave-Mãe está correto
3. Verificar conectividade de rede
4. Verificar logs do servidor

## Exemplo de Teste Completo

### Sequência de Inicialização:

```bash
# 1. Terminal n1 (NaveMae) - IP: 10.0.1.10
cd /tmp/nms
python3 start_nms.py

# 2. Terminal n3 (Rover1) - IP: 10.0.3.10
cd /tmp/nms
python3 start_rover.py 10.0.1.10 r1

# 3. Terminal n4 (Rover2) - IP: 10.0.2.10
cd /tmp/nms
python3 start_rover.py 10.0.1.10 r2

# 4. Terminal n2 (GroundControl) - IP: 10.0.0.10
cd /tmp/nms
python3 start_ground_control.py
```

### Ordem Recomendada:

1. **Primeiro**: Iniciar Nave-Mãe (n1)
2. **Segundo**: Iniciar Rovers (n3, n4)
3. **Terceiro**: Iniciar Ground Control (n2)

## Verificação de Funcionamento

### Checklist

- [ ] Nave-Mãe inicia sem erros
- [ ] Rovers registam-se com sucesso
- [ ] Telemetria é enviada periodicamente
- [ ] Missões podem ser enviadas e recebidas
- [ ] API de Observação responde a pedidos
- [ ] Ground Control consegue conectar à API
- [ ] Tráfego UDP (8080) e TCP (8081) visível no Wireshark

---

**Nota**: Ajustar IPs e caminhos conforme a topologia específica do CORE.

