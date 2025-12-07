## Guia Único: Preparar, Executar e Testar no CORE

### 1) Pré‑requisitos
- CORE instalado e topologia `topologiatp2.imn`.
- Python 3 em todos os nós; instalar deps com `pip3 install -r requirements.txt`.
- Portas usadas: MissionLink UDP 8080, TelemetryStream TCP 8081, API HTTP 8082.

### 2) IPs da topologia
- Nave-Mãe (n1): `10.0.1.10`
- Ground Control (n2): `10.0.0.10`
- Rover1 (n3): `10.0.3.10`
- Rover2 (n4): `10.0.2.10`
- Satélite/router (n5): `10.0.3.1 / 10.0.2.1 / 10.0.1.1`

### 3) Copiar código para os nós (escolhe um método)
1. **Diretório partilhado (recomendado)**: em cada nó, serviço FileTransfer → Source `…/CC/tp2`, Destination `/tmp/nms`. Inicia a sessão → código fica disponível.
2. **Zip/Tar + File Transfer**:
   - No host: `cd …/CC/tp2`  
     `tar -czf nms_code.tar.gz protocol server client otherEntities *.py requirements.txt --exclude='__pycache__' --exclude='*.pyc'`
   - CORE → Tools → File Transfer → envia para cada nó (n1–n4) para `/tmp/`.
   - No nó: `mkdir -p /tmp/nms && cd /tmp/nms && tar -xzf /tmp/nms_code.tar.gz`
3. **Script automático**: `python3 copy_to_core.py` (gera tar e tenta copiar/descompactar via vcmd/scp).

Estrutura esperada em cada nó: `/tmp/nms/` com `protocol/`, `server/`, `client/`, `otherEntities/`, `start_nms.py`, `start_rover.py`, `start_ground_control.py`, `GroundControl.py`, `requirements.txt`, testes.

### 4) Instalar dependências
```
cd /tmp/nms
pip3 install -r requirements.txt
```

### 5) Sequência de arranque
1. **Nave-Mãe (n1)**  
   `cd /tmp/nms`  
   `python3 start_nms.py`
2. **Rovers (n3, n4)**  
   `cd /tmp/nms`  
   `python3 start_rover.py 10.0.1.10 r1` (n3)  
   `python3 start_rover.py 10.0.1.10 r2` (n4)
3. **Ground Control (n2, opcional)**  
   `cd /tmp/nms`  
   `python3 start_ground_control.py`  
   (ou `python3 GroundControl.py --dashboard --api http://10.0.1.10:8082`)

### 6) Testes no CORE
1. **Automatizado por nó**  
   `cd /tmp/nms`  
   `python3 test_core_automated.py auto`  
   (ou `nms` | `rover` | `ground_control` para forçar papel). Valida imports, estrutura, instâncias e rede.
2. **Integração rápida**  
   `cd /tmp/nms`  
   `chmod +x test_core_integration.sh && ./test_core_integration.sh`
3. **Verificações manuais úteis**  
   - API: `curl http://10.0.1.10:8082/rovers` | `/missions` | `/telemetry`  
   - Ground Control: no menu interativo (opções 1–9) ver dashboard, rovers, missões, telemetria.  
   - Tráfego: UDP 8080 (MissionLink), TCP 8081 (TelemetryStream), HTTP 8082 (API).

### 7) Dicas/Troubleshooting
- Se “Module not found”: confirme que está em `/tmp/nms` e que existe `__init__.py` em todas as pastas.
- Se “Address already in use”: `pkill -f start_nms.py` / `start_rover.py` e relance; verifique `netstat -tuln | grep 8080/8081/8082`.
- Se Ground Control não liga: confirme API ativa na Nave-Mãe e use `--api http://10.0.1.10:8082`.
- Se cópia falha: reenvie `nms_code.tar.gz` ou use diretório partilhado.

### 8) Referência rápida de funcionalidades implementadas
- MissionLink (UDP) com handshake 3-way, ACKs, retransmissão, envio/receção de missões e progresso.
- TelemetryStream (TCP) para telemetria contínua e armazenamento por rover.
- Observation API (Flask) expõe rovers, missões, telemetria e progresso.
- Ground Control CLI mostra dashboard completo, listas de rovers/missões, telemetria (global ou por rover) e atualizações automáticas.
