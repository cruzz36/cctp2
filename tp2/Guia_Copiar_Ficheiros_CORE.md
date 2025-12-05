# Guia Detalhado: Como Copiar Ficheiros para o CORE

Este guia explica **passo a passo** como copiar os ficheiros do projeto para os nós do CORE.

## Método Recomendado: File Transfer do CORE (Mais Fácil)

Este é o método mais simples e funciona na maioria dos casos.

### Passo 1: Preparar Ficheiros no Sistema Host

1. **No seu computador** (fora do CORE), navegar para o diretório do projeto:
   ```bash
   cd C:\Users\jdosp\OneDrive\Ambiente de Trabalho\uni\3ano1sem\CC\tp2
   # ou o caminho onde está o projeto
   ```

2. **Criar arquivo compactado** com todos os ficheiros:
   ```bash
   # Windows (PowerShell)
   Compress-Archive -Path protocol,server,client,otherEntities,*.py,requirements.txt -DestinationPath nms_code.zip -Force
   
   # Linux/Mac
   tar -czf nms_code.tar.gz protocol/ server/ client/ otherEntities/ *.py requirements.txt --exclude='__pycache__' --exclude='*.pyc'
   ```

   **Ou usar o script Python:**
   ```bash
   python3 copy_to_core.py
   # Isto cria automaticamente nms_code.tar.gz
   ```

### Passo 2: Abrir CORE e Iniciar Sessão

1. **Abrir CORE**
2. **File → Open** → Selecionar `topologiatp2.imn`
3. **Clicar em Start the session** (botão play ▶️)
4. **Aguardar** que todos os nós iniciem (verificar que todos têm cor verde)

### Passo 3: Usar File Transfer do CORE

#### Opção A: Via Interface Gráfica

1. **No CORE, menu Tools → File Transfer**
   - Abre janela de transferência de ficheiros

2. **Selecionar nó de destino:**
   - Na lista de nós, selecionar **n1** (NaveMae)
   - Ou **n2**, **n3**, **n4** conforme necessário

3. **Enviar ficheiro:**
   - Clicar em **Upload** ou **Send File**
   - Selecionar `nms_code.tar.gz` (ou `nms_code.zip`)
   - O ficheiro será enviado para `/tmp/` no nó

4. **Repetir para cada nó:**
   - n1 (NaveMae)
   - n2 (GroundControl)
   - n3 (Rover1)
   - n4 (Rover2)

#### Opção B: Arrastar e Soltar

1. **Abrir File Transfer** (Tools → File Transfer)
2. **Arrastar** `nms_code.tar.gz` do explorador de ficheiros
3. **Soltar** na janela do nó de destino
4. O ficheiro será copiado automaticamente

### Passo 4: Descompactar nos Nós

Para **cada nó** (n1, n2, n3, n4):

1. **Abrir terminal do nó:**
   - Clicar com botão direito no nó
   - **Shell Window** ou **Terminal**

2. **Criar diretório e descompactar:**
   ```bash
   # Criar diretório
   mkdir -p /tmp/nms
   cd /tmp/nms
   
   # Descompactar (se for .tar.gz)
   tar -xzf /tmp/nms_code.tar.gz
   
   # OU se for .zip
   unzip /tmp/nms_code.zip -d /tmp/nms
   
   # Verificar que ficheiros foram copiados
   ls -la
   ls -R
   ```

3. **Verificar estrutura:**
   ```bash
   cd /tmp/nms
   ls -la
   # Deve mostrar:
   # protocol/
   # server/
   # client/
   # otherEntities/
   # start_nms.py
   # start_rover.py
   # etc.
   ```

### Passo 5: Instalar Dependências

Em **cada nó**, instalar dependências Python:

```bash
cd /tmp/nms
pip3 install -r requirements.txt

# OU instalar manualmente:
pip3 install psutil flask requests
```

**Verificar instalação:**
```bash
python3 -c "import psutil; import flask; import requests; print('OK: Dependências instaladas')"
```

---

## Método Alternativo: Diretório Partilhado (Melhor para Desenvolvimento)

Este método monta o diretório do projeto diretamente nos nós, permitindo acesso direto aos ficheiros.

### Configurar Diretório Partilhado

#### Opção 1: Via Interface do CORE

1. **Antes de iniciar a sessão**, configurar cada nó:
   - Clicar com botão direito no nó (ex: n1)
   - **Configure** → **Services** → **File Transfer**
   - Adicionar:
     - **Source**: `/caminho/completo/para/CC/tp2` (no sistema host)
     - **Destination**: `/tmp/nms` (no nó)
     - **Mount point**: `/tmp/nms`

2. **Repetir para todos os nós** (n1, n2, n3, n4)

3. **Iniciar sessão** - os ficheiros estarão automaticamente disponíveis!

#### Opção 2: Editar Ficheiro .imn

1. **Abrir** `topologiatp2.imn` num editor de texto

2. **Adicionar secção de serviços** para cada nó:
   ```xml
   node n1 {
       type router
       model host
       ...
       services {
           FileTransfer {
               /caminho/completo/para/CC/tp2 /tmp/nms
           }
       }
   }
   ```

3. **Salvar** e abrir no CORE

**Vantagens:**
- ✅ Ficheiros sempre atualizados (sincronização automática)
- ✅ Não precisa copiar manualmente
- ✅ Mudanças no código são imediatamente visíveis
- ✅ Ideal para desenvolvimento e testes

---

## Método Avançado: Script Automático

Usar o script `copy_to_core.py` para copiar automaticamente:

### Uso do Script

```bash
# No diretório do projeto
cd CC/tp2
python3 copy_to_core.py
```

### O que o Script Faz:

1. **Cria arquivo compactado** (`nms_code.tar.gz`) com todos os ficheiros
2. **Tenta encontrar sessão CORE** ativa
3. **Copia para cada nó** usando:
   - `vcmd` (se disponível)
   - `scp` (como alternativa)
4. **Descompacta** automaticamente em cada nó
5. **Verifica** que ficheiros foram copiados

### Requisitos:

- CORE deve estar a correr
- Nós devem estar ativos
- Acesso a `/tmp/pycore.*/` (para vcmd) ou SSH configurado (para scp)

### Se o Script Falhar:

O script mostrará instruções manuais para cada nó que falhou.

---

## Verificação Completa

Após copiar ficheiros, **verificar em cada nó**:

### Script de Verificação

```bash
# Em cada nó (n1, n2, n3, n4)
cd /tmp/nms

# Verificar estrutura
echo "=== Estrutura de Diretórios ==="
ls -la
echo ""
echo "=== Conteúdo de protocol/ ==="
ls -la protocol/
echo ""
echo "=== Conteúdo de server/ ==="
ls -la server/
echo ""
echo "=== Conteúdo de client/ ==="
ls -la client/
echo ""
echo "=== Ficheiros Python na raiz ==="
ls -la *.py

# Verificar ficheiros críticos
echo ""
echo "=== Verificação de Ficheiros Críticos ==="
test -f start_nms.py && echo "[OK] start_nms.py" || echo "[ERRO] start_nms.py"
test -f start_rover.py && echo "[OK] start_rover.py" || echo "[ERRO] start_rover.py"
test -f start_ground_control.py && echo "[OK] start_ground_control.py" || echo "[ERRO] start_ground_control.py"
test -f GroundControl.py && echo "[OK] GroundControl.py" || echo "[ERRO] GroundControl.py"
test -d protocol && echo "[OK] protocol/" || echo "[ERRO] protocol/"
test -d server && echo "[OK] server/" || echo "[ERRO] server/"
test -d client && echo "[OK] client/" || echo "[ERRO] client/"
test -d otherEntities && echo "[OK] otherEntities/" || echo "[ERRO] otherEntities/"
test -f requirements.txt && echo "[OK] requirements.txt" || echo "[ERRO] requirements.txt"

# Verificar permissões
echo ""
echo "=== Definindo Permissões ==="
chmod +x start_nms.py start_rover.py start_ground_control.py
echo "[OK] Permissões definidas"
```

### Estrutura Esperada

Após cópia bem-sucedida, cada nó deve ter:

```
/tmp/nms/
├── protocol/
│   ├── __init__.py
│   ├── MissionLink.py
│   ├── TelemetryStream.py
│   └── (outros ficheiros .md)
├── server/
│   ├── __init__.py
│   └── NMS_Server.py
├── client/
│   ├── __init__.py
│   └── NMS_Agent.py
├── otherEntities/
│   ├── __init__.py
│   ├── Device.py
│   ├── Limit.py
│   └── JSONParser.py
├── start_nms.py
├── start_rover.py
├── start_ground_control.py
├── GroundControl.py
├── requirements.txt
└── (outros ficheiros .py se necessário)
```

---

## Troubleshooting

### Problema: "File Transfer não funciona"

**Solução:**
1. Verificar que sessão CORE está ativa
2. Tentar método alternativo (diretório partilhado)
3. Usar método manual (copiar ficheiro por ficheiro)

### Problema: "Ficheiros não aparecem no nó"

**Solução:**
1. Verificar que descompactou corretamente:
   ```bash
   cd /tmp/nms
   tar -xzf /tmp/nms_code.tar.gz
   ```
2. Verificar localização:
   ```bash
   find /tmp -name "start_nms.py"
   ```
3. Verificar permissões:
   ```bash
   ls -la /tmp/nms
   ```

### Problema: "Module not found" ao executar

**Solução:**
1. Verificar que está no diretório correto:
   ```bash
   cd /tmp/nms
   pwd  # Deve mostrar /tmp/nms
   ```
2. Verificar que `__init__.py` existe em cada pasta:
   ```bash
   test -f protocol/__init__.py && echo "OK" || echo "FALTA"
   test -f server/__init__.py && echo "OK" || echo "FALTA"
   test -f client/__init__.py && echo "OK" || echo "FALTA"
   test -f otherEntities/__init__.py && echo "OK" || echo "FALTA"
   ```

### Problema: "Permission denied"

**Solução:**
```bash
chmod +x start_nms.py start_rover.py start_ground_control.py
chmod -R +r /tmp/nms
```

### Problema: "pip3 not found"

**Solução:**
```bash
# Tentar python3 -m pip
python3 -m pip install -r requirements.txt

# OU instalar pip
apt-get update && apt-get install -y python3-pip  # Debian/Ubuntu
yum install -y python3-pip  # CentOS/RHEL
```

---

## Resumo dos Métodos

| Método | Dificuldade | Velocidade | Recomendado Para |
|--------|-------------|------------|------------------|
| **File Transfer (GUI)** | Fácil | Média | Uso geral |
| **Diretório Partilhado** | Fácil | Rápida | Desenvolvimento |
| **Script Automático** | Média | Rápida | Múltiplas cópias |
| **SCP/SSH** | Média | Rápida | Se SSH configurado |
| **Manual (ficheiro por ficheiro)** | Difícil | Lenta | Último recurso |

---

## Próximos Passos

Após copiar ficheiros com sucesso:

1. ✅ **Instalar dependências** em cada nó
2. ✅ **Verificar estrutura** de ficheiros
3. ✅ **Seguir** `Guia_Teste_CORE.md` para executar o sistema

---

**Dica**: Para desenvolvimento ativo, use **Diretório Partilhado** - é o método mais eficiente!

