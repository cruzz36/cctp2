## Guia curtinho CORE (ficheiro: `/home/core/Downloads/cctp2-main/tp2/`)

### 0) Onde está o código
- No CORE, ir para `/home/core/Downloads/cctp2-main/tp2/`.

### 1) IPs
- Nave-Mãe (n1): `10.0.1.10` (rovers) e `10.0.0.11` (GC).
- Ground Control (n2): `10.0.0.10`.
- Rover1 (n3): `10.0.3.10`. Rover2 (n4): `10.0.2.10`.
- Satélite (n5): `10.0.3.1 / 10.0.2.1 / 10.0.1.1`.

### 2) Pôr código em cada nó (escolher UM método)
- Diretório partilhado: montar esta pasta em `/tmp/nms` (Core → File Transfer → Source `/home/core/Downloads/cctp2-main/tp2/`, Destination `/tmp/nms` em cada nó).
- Zip (manual): no **host CORE** correr  
  `tar -czf nms_code.tar.gz protocol server client otherEntities *.py requirements.txt --exclude='__pycache__' --exclude='*.pyc'`  
  Depois, Core → Tools → File Transfer → enviar `nms_code.tar.gz` para cada nó.  
  No **terminal de cada nó**:  
  `mkdir -p /tmp/nms && cd /tmp/nms && tar -xzf /tmp/nms_code.tar.gz`
- Script (automático, no **host CORE**):  
  `cd /home/core/Downloads/cctp2-main/tp2`  
  `python3 copy_to_core.py`  
  (Se falhar, usar o método Zip acima).
- Sem File Transfer (via vcmd, no **host CORE**, um nó de cada vez) — usar os nomes reais dos nós (NaveMae, GroundControl, Rover1, Rover2):
  1) Guardar sessão: `SESSION=$(ls -d /tmp/pycore.* | head -1)`  
  2) Copiar para NaveMae:  
     `sudo sh -c "cat /home/core/Downloads/cctp2-main/tp2/nms_code.tar.gz | vcmd -c $SESSION/NaveMae -- sh -c 'mkdir -p /tmp/nms && cat > /tmp/nms_code.tar.gz && cd /tmp/nms && tar -xzf /tmp/nms_code.tar.gz && rm /tmp/nms_code.tar.gz'"`  
  3) Copiar para GroundControl: trocar `/NaveMae` por `/GroundControl`  
  4) Copiar para Rover1: trocar por `/Rover1`  
  5) Copiar para Rover2: trocar por `/Rover2`
  - Se der “No such file or directory” no SESSION, volta a correr o passo 1).
  - Para abrir terminal de cada nó: botão direito no nó → Shell (no GUI do CORE).

### 3) Instalar deps (em CADA nó, no terminal desse nó)
```
cd /tmp/nms
pip3 install -r requirements.txt
```

### 4) Arrancar (onde correr cada comando)
- **Nave-Mãe (n1)**  
  `cd /tmp/nms`  
  `python3 start_nms.py`

- **Rover1 (n3)**  
  `cd /tmp/nms`  
  `python3 start_rover.py 10.0.1.10 r1`

- **Rover2 (n4)**  
  `cd /tmp/nms`  
  `python3 start_rover.py 10.0.1.10 r2`

- **Ground Control (n2)**  
  `cd /tmp/nms`  
  `python3 start_ground_control.py`  
  (só dashboard: `python3 GroundControl.py --dashboard --api http://10.0.1.10:8082`)

### 5) Testar
- Em qualquer nó: `cd /tmp/nms && python3 test_core_automated.py auto`
- Em qualquer nó: `cd /tmp/nms && chmod +x test_core_integration.sh && ./test_core_integration.sh`
- API (do GC ou n1): `curl http://10.0.1.10:8082/rovers`

### 6) Se der erro
- “Module not found”: confirma `/tmp/nms` e `__init__.py`.
- Porta ocupada: `pkill -f start_nms.py` ou `pkill -f start_rover.py`.
- GC não liga: usa `--api http://10.0.1.10:8082`.
- Falhou cópia: reenviar `nms_code.tar.gz` ou montar diretório partilhado.

### 7) O que é cada coisa
- MissionLink → missões/progresso (UDP 8080).
...***
