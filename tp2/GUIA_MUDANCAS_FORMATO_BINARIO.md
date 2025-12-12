# Guia Completo: Mudanças para Formato Binário Fixo SEM Separadores

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Formato Atual vs Novo](#formato-atual-vs-novo)
3. [Mudanças em MissionLink.py](#mudanças-em-missionlinkpy)
4. [Impacto em Outros Ficheiros](#impacto-em-outros-ficheiros)
5. [Validações e Limites](#validações-e-limites)
6. [Wraparound de SEQ/ACK](#wraparound-de-seqack)
7. [Mapeamento de idMission](#mapeamento-de-idmission)
8. [Checklist de Implementação](#checklist-de-implementação)

---

## Visão Geral

### Objetivo
Alterar o protocolo MissionLink de formato **texto com separadores** para formato **binário fixo sem separadores**.

### Benefícios
- ✅ **Economia**: 23 bytes → 7 bytes de cabeçalho (economia de 16 bytes por pacote)
- ✅ **Performance**: Parsing binário é mais rápido que split de string
- ✅ **Eficiência**: Menos overhead de rede

### Compatibilidade
⚠️ **Quebra total**: Não é compatível com versão anterior. Todos os nós devem ser atualizados simultaneamente.

---

## Formato Atual vs Novo

### Formato Atual (Texto com Separadores)
```
flag|idMission|seq|ack|size|missionType|message
D|M01|101|101|256|T|{...}
```
- **Tamanho cabeçalho**: 23 bytes
- **Separadores**: 6 bytes de "|" desperdiçados
- **Parsing**: `message.decode().split("|")`

### Novo Formato (Binário SEM Separadores)
```
[flag:1][idMission:1][seq:1][ack:1][size:2][missionType:1][message]
```
- **Tamanho cabeçalho**: 7 bytes (fixo)
- **Sem separadores**: Campos concatenados diretamente
- **Parsing**: Acesso direto por offset de bytes

### Estrutura Binária
```
Offset:  0    1    2    3    4-5      6       7+
         ┌────┴────┴────┴────┴────────┴───────┴─────────────┐
Bytes:   │flag│idM │seq │ack │  size  │type  │  message    │
         └────┴────┴────┴────┴────────┴───────┴─────────────┘
         1byte 1byte 1byte 1byte  2bytes  1byte   variável
```

---

## Mudanças em MissionLink.py

### 1. Adicionar Import struct (Linha ~4)

**Adicionar após imports existentes:**
```python
import socket
from otherEntities import Limit
import time
import threading
import struct  # ← ADICIONAR ESTA LINHA
```

### 2. Mudar Constantes de Posição (Linhas 11-17)

**Mudar de:**
```python
flagPos = 0
idMissionPos = 1
seqPos = 2
ackPos = 3
sizePos = 4
missionTypePos = 5
messagePos = 6
```

**Para:**
```python
# Offsets em bytes (não mais índices de lista)
FLAG_OFFSET = 0          # 1 byte
IDMISSION_OFFSET = 1     # 1 byte
SEQ_OFFSET = 2           # 1 byte
ACK_OFFSET = 3           # 1 byte
SIZE_OFFSET = 4          # 2 bytes (big-endian)
MISSIONTYPE_OFFSET = 6   # 1 byte
MESSAGE_OFFSET = 7       # Variável (após cabeçalho fixo)
HEADER_SIZE = 7          # Tamanho fixo do cabeçalho

# Mantidos para compatibilidade com código existente (serão removidos gradualmente)
flagPos = 0
idMissionPos = 1
seqPos = 2
ackPos = 3
sizePos = 4
missionTypePos = 5
messagePos = 6
```

### 3. Mudar getHeaderSize() (Linha 273-306)

**Mudar de:**
```python
def getHeaderSize(self):
    # flag + | + idMission + | + seq + | + ack + | + size + | + missionType + |
    return 1 + 1 + 3 + 1 + 4 + 1 + 4 + 1 + 4 + 1 + 1 + 1
```

**Para:**
```python
def getHeaderSize(self):
    """
    Retorna o tamanho do cabeçalho binário fixo.
    Formato: [flag:1][idMission:1][seq:1][ack:1][size:2][missionType:1]
    Total: 7 bytes (sem separadores)
    """
    return HEADER_SIZE  # 7 bytes
```

### 4. Reescrever formatMessage() (Linha 308-375)

**Mudar de:**
```python
def formatMessage(self, missionType, flag, idMission, seqNum, ackNum, message):
    if missionType != None: 
        return f"{flag}|{idMission}|{seqNum}|{ackNum}|{len(message)}|{missionType}|{message}".encode()
    return f"{flag}|{idMission}|{seqNum}|{ackNum}|{len(message)}|N|{message}".encode()
```

**Para:**
```python
def formatMessage(self, missionType, flag, idMission, seqNum, ackNum, message):
    """
    Formata mensagem em formato binário fixo SEM separadores.
    Formato: [flag:1][idMission:1][seq:1][ack:1][size:2][missionType:1][message]
    
    Args:
        missionType (str or None): Tipo de operação (R, T, M, Q, P) ou None
        flag (str): Flag de controlo (S, Z, A, F, D)
        idMission (str): ID da missão (será convertido para 1 byte)
        seqNum (int): Número de sequência (0-255)
        ackNum (int): Número de acknowledgment (0-255)
        message (str or bytes): Conteúdo da mensagem
        
    Returns:
        bytes: Mensagem formatada em binário
    """
    # Validar limites
    if seqNum < 0 or seqNum > 255:
        raise ValueError(f"seq fora do limite: {seqNum} (deve ser 0-255)")
    if ackNum < 0 or ackNum > 255:
        raise ValueError(f"ack fora do limite: {ackNum} (deve ser 0-255)")
    
    message_bytes = message.encode() if isinstance(message, str) else message
    message_size = len(message_bytes)
    
    if message_size > 65535:
        raise ValueError(f"Tamanho da mensagem excede 65535: {message_size}")
    
    # Converter valores para bytes
    flag_byte = ord(flag) if isinstance(flag, str) else flag
    
    # Mapear idMission para 1 byte (ver seção Mapeamento de idMission)
    idmission_byte = self._idmission_to_byte(idMission)
    
    seq_byte = seqNum & 0xFF  # Garantir 1 byte
    ack_byte = ackNum & 0xFF  # Garantir 1 byte
    size_bytes = struct.pack('>H', message_size)  # 2 bytes big-endian
    missiontype_byte = ord(missionType) if missionType else ord('N')
    
    # Construir cabeçalho binário SEM separadores (7 bytes fixos)
    header = bytes([
        flag_byte,           # offset 0
        idmission_byte,      # offset 1
        seq_byte,            # offset 2
        ack_byte,            # offset 3
        size_bytes[0],       # offset 4 (byte alto)
        size_bytes[1],       # offset 5 (byte baixo)
        missiontype_byte     # offset 6
    ])
    
    # Concatenar mensagem diretamente (sem separador!)
    return header + message_bytes
```

### 5. Adicionar Função parseMessage() (Após formatMessage)

**Adicionar nova função:**
```python
def parseMessage(self, data):
    """
    Parse mensagem binária fixa SEM separadores.
    
    Args:
        data: bytes - dados recebidos
        
    Returns:
        tuple: (flag, idMission, seq, ack, size, missionType, message_content)
        
    Raises:
        ValueError: Se mensagem estiver malformada ou incompleta
    """
    if len(data) < HEADER_SIZE:
        raise ValueError(f"Mensagem muito curta: {len(data)} bytes (mínimo {HEADER_SIZE})")
    
    # Acesso direto por offset (sem split!)
    flag = chr(data[FLAG_OFFSET])
    idmission_byte = data[IDMISSION_OFFSET]
    idMission = self._byte_to_idmission(idmission_byte)  # Converter byte para string
    seq = data[SEQ_OFFSET]
    ack = data[ACK_OFFSET]
    size = struct.unpack('>H', data[SIZE_OFFSET:SIZE_OFFSET+2])[0]  # 2 bytes big-endian
    missionType = chr(data[MISSIONTYPE_OFFSET])
    
    # Validar tamanho total
    expected_size = HEADER_SIZE + size
    if len(data) < expected_size:
        raise ValueError(f"Mensagem incompleta: esperado {expected_size} bytes, recebido {len(data)}")
    
    # Extrair mensagem
    message_content = data[MESSAGE_OFFSET:MESSAGE_OFFSET+size]
    
    # Tentar decodificar como string, se falhar retornar bytes
    try:
        message_str = message_content.decode()
    except UnicodeDecodeError:
        message_str = message_content  # Manter como bytes se não for texto
    
    return (flag, idMission, seq, ack, size, missionType, message_str)
```

### 6. Adicionar Funções Auxiliares de Mapeamento (Após parseMessage)

**Adicionar:**
```python
def _idmission_to_byte(self, idMission):
    """
    Converte idMission (string) para 1 byte.
    
    Mapeamento:
    - 'M01', 'M02', etc. → 'M' (ord('M') = 77)
    - 'r1', 'r2' → 'r' (ord('r') = 114)
    - '000' → '0' (ord('0') = 48)
    - Outros: primeiro caractere
    """
    if isinstance(idMission, int):
        return idMission & 0xFF
    
    if isinstance(idMission, str):
        # Se começa com 'M', usar 'M'
        if idMission.startswith('M'):
            return ord('M')
        # Se começa com 'r', usar 'r'
        if idMission.startswith('r'):
            return ord('r')
        # Se é '000', usar '0'
        if idMission == '000':
            return ord('0')
        # Caso padrão: primeiro caractere
        return ord(idMission[0])
    
    return ord(str(idMission)[0])

def _byte_to_idmission(self, byte_value):
    """
    Converte byte para idMission (string).
    Mapeamento inverso de _idmission_to_byte.
    """
    char = chr(byte_value)
    # Mapeamento reverso aproximado
    if char == 'M':
        return 'M01'  # Valor padrão, pode precisar contexto
    elif char == 'r':
        return 'r1'   # Valor padrão, pode precisar contexto
    elif char == '0':
        return '000'
    else:
        return char
```

### 7. Substituir TODAS as ocorrências de `.split("|")`

**Padrão a procurar:**
```python
lista = message.decode().split("|")
if len(lista) < 7:
    # Erro
flag = lista[flagPos]
idMission = lista[idMissionPos]
seq = int(lista[seqPos])
ack = int(lista[ackPos])
size = int(lista[sizePos])
missionType = lista[missionTypePos]
message_content = lista[messagePos]
```

**Substituir por:**
```python
flag, idMission, seq, ack, size, missionType, message_content = self.parseMessage(message)
```

**Locais principais a mudar (aproximadamente 70-80 ocorrências):**

1. **`acceptConnection()`** (~linha 585-645)
   - Substituir `lista = message.decode().split("|")`
   - Atualizar todas as referências `lista[flagPos]` → `flag`, etc.

2. **`startConnection()`** (~linha 469-540)
   - Mesma mudança

3. **`send()`** - múltiplas ocorrências:
   - Linha ~708: Validação de ACK do nome do ficheiro
   - Linha ~766: Validação de ACK de chunks de ficheiro
   - Linha ~798: Validação de FIN-ACK de ficheiro
   - Linha ~866: Validação de ACK de mensagem curta
   - Linha ~1044: Validação de ACK de chunks de mensagem longa
   - Todas as validações precisam usar `parseMessage()`

4. **`recv()`** - múltiplas ocorrências:
   - Linha ~1327: Parsing de chunks recebidos
   - Linha ~1448: Validação de chunks duplicados/futuros
   - Linha ~1555: Parsing de chunks de ficheiro
   - Todas as validações precisam usar `parseMessage()`

### 8. Adicionar Validações de Limites (No __init__ ou como métodos auxiliares)

**Adicionar métodos:**
```python
def _validate_seq_ack(self, seq, ack):
    """Valida que seq e ack estão dentro dos limites (0-255)"""
    if seq < 0 or seq > 255:
        raise ValueError(f"seq fora do limite: {seq} (deve ser 0-255)")
    if ack < 0 or ack > 255:
        raise ValueError(f"ack fora do limite: {ack} (deve ser 0-255)")
    return True

def _validate_message_size(self, size):
    """Valida que o tamanho da mensagem está dentro dos limites (0-65535)"""
    if size < 0 or size > 65535:
        raise ValueError(f"Tamanho da mensagem fora do limite: {size} (deve ser 0-65535)")
    return True
```

### 9. Adicionar Lógica de Wraparound (Após validações)

**Adicionar métodos:**
```python
def _seq_wraparound(self, seq):
    """Gerencia wraparound de seq (0-255)"""
    return seq % 256

def _seq_compare(self, seq1, seq2):
    """
    Compara dois seq considerando wraparound.
    Retorna diferença: positivo se seq1 > seq2, negativo se seq1 < seq2
    """
    diff = (seq1 - seq2) % 256
    if diff > 127:
        diff = diff - 256  # Considerar wraparound
    return diff

def _is_seq_greater(self, seq1, seq2):
    """Verifica se seq1 > seq2 considerando wraparound"""
    diff = self._seq_compare(seq1, seq2)
    return diff > 0

def _is_seq_equal(self, seq1, seq2):
    """Verifica se seq1 == seq2"""
    return seq1 == seq2
```

### 10. Atualizar Handshake (startConnection e acceptConnection)

**Em `startConnection()` (~linha 437-540):**

**Mudar de:**
```python
seqinicial = 100
self.sock.sendto(
    f"{self.synkey}|{idAgent}|{seqinicial}|0|_|0|-.-".encode(),
    (destAddress, destPort)
)
```

**Para:**
```python
seqinicial = 100  # OK, está dentro do limite de 255
# Usar formatMessage para construir SYN
syn_message = self.formatMessage(
    None,           # missionType
    self.synkey,   # flag
    idAgent,       # idMission (será convertido para 1 byte)
    seqinicial,    # seq
    0,             # ack
    "-.-"          # message
)
self.sock.sendto(syn_message, (destAddress, destPort))
```

**Em `acceptConnection()` (~linha 585-645):**

**Mudar de:**
```python
lista = message.decode().split("|")
if lista[flagPos] == self.synkey:
    # ...
    lista[flagPos] = self.synackkey
    self.sock.sendto("|".join(lista).encode(), (ip, port))
```

**Para:**
```python
flag, idMission, seq, ack, size, missionType, msg = self.parseMessage(message)
if flag == self.synkey:
    # ...
    # Enviar SYN-ACK usando formatMessage
    synack_message = self.formatMessage(
        None,
        self.synackkey,
        idMission,
        seq,
        seq,  # ACK reconhece o seq recebido
        "-.-"
    )
    self.sock.sendto(synack_message, (ip, port))
```

---

## Validações e Limites

### Limites do Novo Formato

| Campo | Tamanho | Limite | Observações |
|-------|---------|--------|-------------|
| flag | 1 byte | 0-255 | Caracteres ASCII (S, Z, A, F, D) |
| idMission | 1 byte | 0-255 | Mapeado para 1 caractere |
| seq | 1 byte | 0-255 | Wraparound necessário |
| ack | 1 byte | 0-255 | Wraparound necessário |
| size | 2 bytes | 0-65535 | Suficiente para buffersize de 1024 |
| missionType | 1 byte | 0-255 | Caracteres ASCII (R, T, M, Q, P, N) |

### Validações Necessárias

1. **seq/ack**: Validar antes de enviar (0-255)
2. **size**: Validar antes de enviar (0-65535)
3. **idMission**: Mapear para 1 byte antes de enviar
4. **Wraparound**: Implementar lógica de wraparound para seq/ack

---

## Wraparound de SEQ/ACK

### Problema
Com 1 byte, seq/ack vão de 0-255, depois voltam a 0. Precisamos de lógica especial para comparar.

### Solução
```python
# Exemplo: seq atual = 250, próximo = 5 (wraparound)
# Diferença real: 5 - 250 = -245
# Com wraparound: (5 - 250) % 256 = 11 (incorreto!)
# Correto: considerar que diferença máxima é 127

def _seq_compare(self, seq1, seq2):
    """Compara dois seq considerando wraparound"""
    diff = (seq1 - seq2) % 256
    if diff > 127:
        diff = diff - 256  # Considerar wraparound negativo
    return diff

# Uso:
if self._seq_compare(received_seq, expected_seq) == 1:
    # Recebido seq esperado
elif self._seq_compare(received_seq, expected_seq) < 0:
    # Chunk duplicado (seq menor)
else:
    # Chunk futuro (seq maior)
```

---

## Mapeamento de idMission

### Problema
idMission atual usa 3 caracteres ('M01', 'r1', '000'), mas novo formato só permite 1 byte.

### Soluções Possíveis

**Opção 1: Usar primeiro caractere (RECOMENDADO)**
```python
'M01' → 'M' (ord('M') = 77)
'M02' → 'M' (ord('M') = 77)
'r1' → 'r' (ord('r') = 114)
'r2' → 'r' (ord('r') = 114)
'000' → '0' (ord('0') = 48)
```

**Opção 2: Usar índice numérico**
```python
'M01' → 1
'M02' → 2
'r1' → 10
'r2' → 11
'000' → 0
```

**Implementação recomendada (Opção 1):**
```python
def _idmission_to_byte(self, idMission):
    if isinstance(idMission, str):
        if idMission.startswith('M'):
            return ord('M')
        elif idMission.startswith('r'):
            return ord('r')
        elif idMission == '000':
            return ord('0')
        else:
            return ord(idMission[0])
    return ord(str(idMission)[0])
```

---

## Impacto em Outros Ficheiros

### NMS_Server.py
- **Impacto**: Mínimo
- **Mudanças**: Nenhuma necessária (usa MissionLink internamente)
- **Nota**: Se houver validações diretas de formato, atualizar

### NMS_Agent.py
- **Impacto**: Mínimo
- **Mudanças**: Nenhuma necessária (usa MissionLink internamente)
- **Nota**: Se houver validações diretas de formato, atualizar

### Testes (se existirem)
- **Impacto**: Alto
- **Mudanças**: Atualizar todos os testes que verificam formato de mensagem
- **Exemplo**: Se teste verifica `"D|M01|101|101|256|T|"`, precisa verificar formato binário

---

## Checklist de Implementação

### Fase 1: Preparação
- [ ] Fazer backup do código atual
- [ ] Criar branch para mudanças
- [ ] Adicionar import `struct`

### Fase 2: Constantes e Estruturas
- [ ] Mudar constantes de posição (linhas 11-17)
- [ ] Adicionar offsets de bytes
- [ ] Adicionar HEADER_SIZE = 7

### Fase 3: Funções Core
- [ ] Reescrever `getHeaderSize()` → retornar 7
- [ ] Reescrever `formatMessage()` → formato binário
- [ ] Adicionar `parseMessage()` → parsing binário
- [ ] Adicionar `_idmission_to_byte()` e `_byte_to_idmission()`

### Fase 4: Validações e Wraparound
- [ ] Adicionar `_validate_seq_ack()`
- [ ] Adicionar `_validate_message_size()`
- [ ] Adicionar `_seq_wraparound()`
- [ ] Adicionar `_seq_compare()`
- [ ] Adicionar `_is_seq_greater()` e `_is_seq_equal()`

### Fase 5: Substituir Parsing
- [ ] `acceptConnection()` - substituir `.split("|")`
- [ ] `startConnection()` - substituir `.split("|")`
- [ ] `send()` - todas as ocorrências (~10-15 locais)
- [ ] `recv()` - todas as ocorrências (~20-30 locais)
- [ ] Handshake - usar `formatMessage()` em vez de f-strings

### Fase 6: Validações de Limites
- [ ] Adicionar validação de seq/ack antes de enviar
- [ ] Adicionar validação de size antes de enviar
- [ ] Adicionar validação de wraparound em comparações

### Fase 7: Testes
- [ ] Testar handshake (SYN, SYN-ACK, ACK)
- [ ] Testar envio de mensagens curtas
- [ ] Testar envio de mensagens longas (fragmentação)
- [ ] Testar envio de ficheiros
- [ ] Testar packet loss e retransmissão
- [ ] Testar duplicatas
- [ ] Testar jitter (pacotes fora de ordem)
- [ ] Testar wraparound de seq/ack

### Fase 8: Limpeza
- [ ] Remover constantes antigas (flagPos, etc.) se não usadas
- [ ] Atualizar comentários e documentação
- [ ] Verificar logs e mensagens de debug

---

## Exemplo Completo de Mudança

### Antes (Formato Texto)
```python
# Enviar mensagem
message = self.formatMessage('T', 'D', 'M01', 101, 101, '{"mission_id":"M-001"}')
# Resultado: b'D|M01|101|101|23|T|{"mission_id":"M-001"}'

# Receber mensagem
lista = data.decode().split("|")
if len(lista) < 7:
    continue
flag = lista[0]
idMission = lista[1]
seq = int(lista[2])
ack = int(lista[3])
```

### Depois (Formato Binário)
```python
# Enviar mensagem
message = self.formatMessage('T', 'D', 'M01', 101, 101, '{"mission_id":"M-001"}')
# Resultado: bytes([68, 77, 101, 101, 0, 23, 84]) + b'{"mission_id":"M-001"}'
#            [flag][idM][seq][ack][size ][type][message]

# Receber mensagem
flag, idMission, seq, ack, size, missionType, message_content = self.parseMessage(data)
# Acesso direto por offset, sem split!
```

---

## Notas Importantes

1. **Wraparound**: Implementar lógica de wraparound é crítico para seq/ack > 255
2. **idMission**: Mapeamento pode perder informação (M01 e M02 ambos → 'M')
3. **Compatibilidade**: Quebra total - todos os nós devem atualizar simultaneamente
4. **Testes**: Testar extensivamente antes de deploy em produção
5. **Rollback**: Manter código antigo comentado durante transição

---

## Estimativa de Esforço

- **Linhas modificadas**: ~200-300 linhas
- **Novas funções**: 5-7 funções auxiliares
- **Locais de mudança**: ~70-80 ocorrências de parsing
- **Tempo estimado**: 6-10 horas de desenvolvimento + testes

---

**Fim do Guia**
