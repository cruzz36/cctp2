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
  1) Guardar sessão: `SESSION=$(ls -d /tmp/pycore.* | head -1)          SESSION=/tmp/pycore.36361`  
  2) Copiar para NaveMae:  
     `sudo sh -c "cat /home/core/Downloads/cctp2-main/tp2/nms_code.tar.gz | vcmd -c $SESSION/NaveMae -- sh -c 'mkdir -p /tmp/nms && cat > /tmp/nms_code.tar.gz && cd /tmp/nms && tar -xzf /tmp/nms_code.tar.gz && rm /tmp/nms_code.tar.gz'"`  
  3) Copiar para GroundControl: trocar `/NaveMae` por `/GroundControl`  
  4) Copiar para Rover1: trocar por `/Rover1`  
  5) Copiar para Rover2: trocar por `/Rover2`
  - Se der “No such file or directory” no SESSION, volta a correr o passo 1).
  - Para abrir terminal de cada nó: botão direito no nó → Shell (no GUI do CORE).
- Depois do `copy_to_core.py` (se a verificação por SSH falhar): abre o terminal de cada nó e confirma `ls /tmp/nms && test -f /tmp/nms/start_nms.py`. Se não existir, volta a extrair o tar no nó: `mkdir -p /tmp/nms && cd /tmp/nms && tar -xzf /tmp/nms_code.tar.gz`.

### 3) Instalar deps (em CADA nó, no terminal desse nó)
```
cd /tmp/nms
pip3 install -r requirements.txt
```
- Se não houver internet nos nós (erro de DNS/PyPI), faz offline a partir do host CORE:
  - Para saber o número da sessão CORE (para usar no vcmd): `ls -d /tmp/pycore.*` (ex.: `/tmp/pycore.41269`)
  1. No host: `mkdir -p /home/core/pkgs`
  2. No host: `pip3 download --dest /home/core/pkgs psutil==5.9.0 flask==1.1.1 itsdangerous==1.1.0 jinja2==2.10.1 markupsafe==1.1.1 werkzeug==0.16.1 click==7.0 requests==2.22.0`
  3. No host: `tar -czf /home/core/pkgs.tgz -C /home/core pkgs`
  4. Para cada nó (NaveMae/GroundControl/Rover1/Rover2, um de cada vez), no host:
     ```
     sudo sh -c "cat /home/core/pkgs.tgz | vcmd -c /tmp/pycore.XXXX/<NODE> -- sh -c 'tar -xzf - -C /tmp && pip3 install --no-index --find-links /tmp/pkgs flask==1.1.1 itsdangerous==1.1.0 jinja2==2.10.1 markupsafe==1.1.1 werkzeug==0.16.1 click==7.0 psutil==5.9.0 requests==2.22.0'"
     ```
     (Troca `XXXX` pelo número da sessão e `<NODE>` pelo nome real, ex.: NaveMae, fazer isto para todos)
  5. Confirmar num nó:  
     `sudo vcmd -c /tmp/pycore.XXXX/NaveMae -- sh -c "python3 - <<'PY'\nimport psutil, requests, flask\nprint('OK deps')\nPY"`

### 4) Arrancar (terminal de cada nó)
- ctrl-c/ctrl-v nos vcmd/XTerm: selecionar texto copia (depois e colar noutro terminal do core e copiar com ctrl-shift-c); para colar usar botão do meio (scroll-click).
- Ordem para evitar timeout na Nave-Mãe: arrancar NaveMae e logo a seguir os rovers (Rover1, Rover2); só depois o GroundControl. Se a thread do MissionLink cair por timeout, relança `start_nms.py` depois de subires os rovers.
- comando clear do vcmd : `TERM=vt100 clear`
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

### 7) Depois de dar pull (para tudo ficar igual nos nós)
- No host CORE (`/home/core/Downloads/cctp2-main/tp2`):
  1. `git pull`
  2. `python3 copy_to_core.py` (gera novo `nms_code.tar.gz`; se falhar, usa método Zip do passo 2)
- Em cada nó (NaveMae, GroundControl, Rover1, Rover2):
  3. Parar processos antigos: `pkill -f start_nms.py || true && pkill -f start_rover.py || true && pkill -f start_ground_control.py || true`
  4. Limpar cópia antiga: `rm -rf /tmp/nms`
  5. Receber nova cópia (via File Transfer ou vcmd, conforme passo 2) e extrair em `/tmp/nms`
  6. `cd /tmp/nms && pip3 install -r requirements.txt` (ou método offline do passo 3)
  7. Arrancar de novo (passo 4): NaveMae → rovers → GroundControl
- Não é obrigatório fechar os terminais vcmd; basta parar os processos e recarregar `/tmp/nms`. Se quiser, pode fechar/reabrir.
- Automático pós-pull (sem internet nos nós) — tudo no host CORE:
  ```bash
  # 1) Atualizar código e copiar para nós
  cd /home/core/Downloads/cctp2-main/tp2
  SESSION=$(ls -d /tmp/pycore.* | head -1)
  git pull
  python3 copy_to_core.py  # já envia o tar para NaveMae/GroundControl/Rover1/Rover2

  # 2) Preparar deps offline
  mkdir -p /home/core/pkgs
  pip3 download --dest /home/core/pkgs \
    psutil==5.9.0 \
    flask==2.3.3 itsdangerous==2.1.2 jinja2==3.1.2 markupsafe==2.1.5 werkzeug==2.3.7 click==8.1.7 \
    requests==2.31.0
  tar -czf /home/core/pkgs.tgz -C /home/core pkgs

  # 3) Em cada nó (loop), limpar /tmp/nms, extrair tar e instalar deps offline
  for NODE in NaveMae GroundControl Rover1 Rover2; do
    sudo sh -c "vcmd -c $SESSION/$NODE -- sh -c 'pkill -f start_nms.py || true; pkill -f start_rover.py || true; pkill -f start_ground_control.py || true; rm -rf /tmp/nms; mkdir -p /tmp/nms'"
    sudo sh -c "cat /home/core/Downloads/cctp2-main/tp2/nms_code.tar.gz | vcmd -c $SESSION/$NODE -- sh -c 'cd /tmp/nms && tar -xzf -'"
    sudo sh -c "cat /home/core/pkgs.tgz | vcmd -c $SESSION/$NODE -- sh -c 'tar -xzf - -C /tmp && pip3 install --no-index --find-links /tmp/pkgs flask==2.3.3 itsdangerous==2.1.2 jinja2==3.1.2 markupsafe==2.1.5 werkzeug==2.3.7 click==8.1.7 psutil==5.9.0 requests==2.31.0'"
  done
  echo "Pronto: arrancar (passo 4): NaveMae -> rovers -> GroundControl"
  ```