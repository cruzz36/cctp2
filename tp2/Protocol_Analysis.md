# Análise dos Protocolos e Diagrama de Sequência

## 1. Uso de Cada Campo dos Protocolos

### MissionLink (ML) - Protocolo UDP

**Formato da mensagem:** `flag|idMission|seq|ack|size|requestType|message`

#### Campos e seus usos:

1. **`flag`** (1 byte)
   - **Descrição e Necessidade:** O campo `flag` identifica o tipo de controlo da mensagem no protocolo MissionLink. É necessário porque o protocolo UDP não fornece mecanismos de controlo de conexão nativos, então este campo permite implementar handshake, confirmações e fechamento de conexão a nível aplicacional. Sem este campo, não seria possível distinguir entre diferentes tipos de mensagens (dados, controlo, handshake) e implementar fiabilidade sobre UDP.
   - **Localização no código:** `CC/tp2/protocol/MissionLink.py`, linhas 43-47
   - **Valores possíveis:**
     - `"S"` (SYN): Inicia handshake de 3 vias
       - **Uso:** `CC/tp2/protocol/MissionLink.py`, linha 197: `f"{self.synkey}|{idMission}|{seqinicial}|0|_|0|-.-"`
     - `"Z"` (SYN-ACK): Resposta ao SYN no handshake
       - **Uso:** `CC/tp2/protocol/MissionLink.py`, linha 262: `lista[flagPos] = self.synackkey`
     - `"A"` (ACK): Confirmação de receção
       - **Uso:** `CC/tp2/protocol/MissionLink.py`, linha 223: `f"{self.ackkey}|{idMission}|{seqinicial}|{seqinicial}|_|0|-.-"`
     - `"D"` (Data): Dados a transmitir
       - **Uso:** `CC/tp2/protocol/MissionLink.py`, linha 304: `self.formatMessage(requestType,self.datakey,idMission,seq,ack,message)`
     - `"F"` (FIN): Fecha conexão
       - **Uso:** `CC/tp2/protocol/MissionLink.py`, linha 355: `self.formatMessage(None,self.finkey,idMission,seq,ack,"\0")`

2. **`idMission`** (3 bytes)
   - **Descrição e Necessidade:** O campo `idMission` identifica unicamente a missão/tarefa à qual a mensagem está associada. É necessário porque um rover pode estar a executar múltiplas missões simultaneamente, e a Nave-Mãe precisa de distinguir a qual missão cada mensagem pertence. Permite também rastrear e correlacionar todas as mensagens relacionadas com a mesma missão, essencial para gestão de tarefas e métricas.
   - **Localização no código:** `CC/tp2/protocol/MissionLink.py`, linha 8: `idMissionPos = 1`
   - **Uso:**
     - Identifica a missão/tarefa à qual a mensagem pertence
     - **Registo:** `CC/tp2/client/NMS_Agent.py`, linha 88: `self.missionLink.send(...,self.id,"\0")`
     - **Envio de métricas:** `CC/tp2/client/NMS_Agent.py`, linha 74: `self.missionLink.send(...,idMission,filename)`
     - **Envio de tarefas:** `CC/tp2/server/NMS_Server.py`, linha 95: `self.missionLink.send(...,idMission,task)`
     - **Validação:** `CC/tp2/protocol/MissionLink.py`, linha 271: `lista[idMissionPos] == idMission`

3. **`seq`** (4 bytes)
   - **Descrição e Necessidade:** O campo `seq` (número de sequência) é fundamental para implementar fiabilidade sobre UDP. É necessário porque UDP não garante ordem de entrega nem deteta pacotes duplicados. Este campo permite ao recetor identificar pacotes perdidos, duplicados ou fora de ordem, e solicitar retransmissão quando necessário. Sem este campo, não seria possível garantir entrega confiável de dados críticos.
   - **Localização no código:** `CC/tp2/protocol/MissionLink.py`, linha 9: `seqPos = 2`
   - **Uso:**
     - Número de sequência para controlo de fiabilidade
     - **Inicialização:** `CC/tp2/protocol/MissionLink.py`, linha 190: `seqinicial = 100`
     - **Incremento:** `CC/tp2/protocol/MissionLink.py`, linha 315: `seq += 1`
     - **Validação:** `CC/tp2/protocol/MissionLink.py`, linha 313: `lista[ackPos] == str(seq)`

4. **`ack`** (4 bytes)
   - **Descrição e Necessidade:** O campo `ack` (acknowledgment) confirma a receção de um pacote específico identificado pelo seu número de sequência. É necessário para implementar confirmação de entrega e detetar perdas de pacotes. Quando o recetor envia um ACK com o número de sequência recebido, o emissor sabe que o pacote chegou corretamente. Se não receber ACK dentro de um timeout, pode retransmitir. Sem este campo, não haveria forma de confirmar entrega bem-sucedida.
   - **Localização no código:** `CC/tp2/protocol/MissionLink.py`, linha 10: `ackPos = 3`
   - **Uso:**
     - Número de acknowledgment - confirma receção de pacote com seq específico
     - **Handshake:** `CC/tp2/protocol/MissionLink.py`, linha 272: `lista[ackPos] == lista[seqPos]`
     - **Validação de dados:** `CC/tp2/protocol/MissionLink.py`, linha 337: `lista[ackPos] == str(seq)`

5. **`size`** (4 bytes)
   - **Descrição e Necessidade:** O campo `size` indica o tamanho do campo `message` em bytes. É necessário para permitir fragmentação de mensagens grandes que excedem o tamanho máximo do buffer UDP (1024 bytes). O recetor usa este valor para saber quantos bytes ler do campo `message` e quando parar de esperar por mais dados. Também permite validação de integridade - se o tamanho não corresponder ao conteúdo recebido, há um erro. Sem este campo, seria impossível fragmentar e reconstruir mensagens grandes corretamente.
   - **Localização no código:** `CC/tp2/protocol/MissionLink.py`, linha 11: `sizePos = 4`
   - **Uso:**
     - Tamanho da mensagem em bytes
     - **Cálculo:** `CC/tp2/protocol/MissionLink.py`, linha 89: `{len(message)}`
     - Usado para fragmentação quando mensagem excede buffer size

6. **`requestType`** (1 byte)
   - **Descrição e Necessidade:** O campo `requestType` identifica o tipo de operação que a mensagem representa (Registo, Tarefa, Métricas). É necessário para que o recetor saiba como processar a mensagem - se é um registo de rover, envio de tarefa, ou envio de métricas. Cada tipo requer processamento diferente e roteamento para diferentes handlers. Sem este campo, o recetor não saberia que ação tomar com a mensagem recebida.
   - **Localização no código:** `CC/tp2/protocol/MissionLink.py`, linha 12: `reqType = 5`
   - **Valores possíveis:**
     - `"R"` (Register): Registo de rover
       - **Uso:** `CC/tp2/client/NMS_Agent.py`, linha 88: `self.missionLink.registerAgent`
       - **Processamento:** `CC/tp2/server/NMS_Server.py`, linha 76: `if requestType == self.missionLink.registerAgent`
     - `"T"` (Task): Envio de tarefa/missão
       - **Uso:** `CC/tp2/server/NMS_Server.py`, linha 95: `self.missionLink.taskRequest`
       - **Processamento:** `CC/tp2/client/NMS_Agent.py`, linha 101: `if lista[1] == self.missionLink.taskRequest`
     - `"M"` (Metrics): Envio de métricas
       - **Uso:** `CC/tp2/client/NMS_Agent.py`, linha 74: `self.missionLink.sendMetrics`
       - **Processamento:** `CC/tp2/server/NMS_Server.py`, linha 80: `if requestType == self.missionLink.sendMetrics`
     - `"N"` (None): Sem tipo de pedido específico
       - **Uso:** `CC/tp2/protocol/MissionLink.py`, linha 90: quando `requestType == None`

7. **`message`** (variável)
   - **Descrição e Necessidade:** O campo `message` contém o payload real da mensagem - os dados efetivos a transmitir. É necessário porque é onde se transporta a informação útil: nomes de ficheiros, dados JSON de tarefas, métricas, ou confirmações. O tamanho variável permite flexibilidade para diferentes tipos de conteúdo, desde mensagens curtas até ficheiros grandes fragmentados. Sem este campo, não haveria forma de transportar os dados reais da comunicação.
   - **Localização no código:** `CC/tp2/protocol/MissionLink.py`, linha 13: `messagePos = 6`
   - **Uso:**
     - Conteúdo da mensagem (texto, nome de ficheiro, dados JSON, etc.)
     - **Registo:** `CC/tp2/client/NMS_Agent.py`, linha 88: `"\0"` (mensagem vazia)
     - **Métricas:** `CC/tp2/client/NMS_Agent.py`, linha 74: `filename` (ex: "alert_idMission_task-202_1.json")
     - **Tarefas:** `CC/tp2/server/NMS_Server.py`, linha 95: `task` (JSON com configuração da tarefa)

---

### TelemetryStream (TS) - Protocolo TCP

**Formato implementado:** `[tamanho_nome:4 bytes][nome_ficheiro:N bytes][conteúdo:variável]`

#### Campos e seus usos:

1. **`tamanho_nome`** (4 bytes)
   - **Descrição e Necessidade:** O campo `tamanho_nome` indica quantos bytes tem o nome do ficheiro que segue. É necessário porque o nome do ficheiro tem tamanho variável, e o recetor precisa saber quantos bytes ler antes de receber o nome completo. Usa formato fixo de 4 dígitos ASCII (ex: "0025" para 25 bytes) para facilitar parsing. Sem este campo, o recetor não saberia onde termina o nome do ficheiro e começam os dados.
   - **Localização no código:** `CC/tp2/protocol/TelemetryStream.py`, linha 11: `lenMessageSize = 4`
   - **Uso:**
     - Tamanho do nome do ficheiro em bytes (formato ASCII com 4 dígitos, zeros à esquerda)
     - **Envio:** `CC/tp2/protocol/TelemetryStream.py`, linha 134: `length = self.formatInteger(len(message))`
     - **Receção:** `CC/tp2/protocol/TelemetryStream.py`, linha 103: `message = clientSock.recv(lenMessageSize)`
     - **Formatação:** `CC/tp2/protocol/TelemetryStream.py`, linhas 72-86: `formatInteger()` garante 4 dígitos

2. **`nome_ficheiro`** (N bytes, variável)
   - **Descrição e Necessidade:** O campo `nome_ficheiro` contém o nome do ficheiro de telemetria a transmitir. É necessário para que o recetor saiba como nomear o ficheiro recebido e possa organizar os dados de telemetria por ficheiro. O tamanho variável permite nomes de ficheiros de qualquer comprimento, desde que o tamanho seja indicado no campo anterior. Sem este campo, o recetor não saberia como guardar ou identificar os dados recebidos.
   - **Localização no código:** `CC/tp2/protocol/TelemetryStream.py`, linha 106
   - **Uso:**
     - Nome do ficheiro de telemetria a enviar/receber
     - **Envio:** `CC/tp2/protocol/TelemetryStream.py`, linha 138: `self.socket.sendall(message.encode())`
     - **Receção:** `CC/tp2/protocol/TelemetryStream.py`, linha 106: `filename = clientSock.recv(fileNameLen)`
     - **Exemplo:** `CC/tp2/client/NMS_Agent.py`, linha 116: `"alert_n1_task-202_1.json"`

3. **`conteúdo`** (variável)
   - **Descrição e Necessidade:** O campo `conteúdo` contém os dados reais do ficheiro de telemetria (geralmente JSON com métricas). É necessário porque é onde se transporta a informação útil de monitorização - métricas de CPU, RAM, rede, etc. O tamanho variável permite enviar ficheiros de qualquer tamanho, fragmentados em chunks de 1024 bytes. Como o protocolo usa TCP, a fiabilidade é garantida pela camada de transporte, mas este campo é essencial para transportar os dados efetivos. Sem este campo, não haveria dados de telemetria para monitorizar.
   - **Localização no código:** `CC/tp2/protocol/TelemetryStream.py`, linhas 110-114
   - **Uso:**
     - Conteúdo do ficheiro de telemetria (dados JSON com métricas)
     - **Envio:** `CC/tp2/protocol/TelemetryStream.py`, linha 141-144: enviado em chunks de `self.limit.buffersize` (1024 bytes)
     - **Receção:** `CC/tp2/protocol/TelemetryStream.py`, linha 110-114: recebido em chunks até `b""`

---

## 2. Diagrama de Sequência - Comunicação Rover ↔ Nave-Mãe

### Cenário 1: Registo do Rover

```
Rover                    MissionLink (UDP)              Nave-Mãe
  |                           |                              |
  |--1. SYN------------------>|                              |
  |   flag=S                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=100                 |                              |
  |   ack=0                   |                              |
  |   size=_                  |                              |
  |   reqType=0               |                              |
  |   message=-.-             |                              |
  |                           |--2. SYN--------------------->|
  |                           |                              |
  |<--3. SYN-ACK--------------|                              |
  |   flag=Z                  |<--2. SYN-ACK-----------------|
  |   idMission=rover_id        |   flag=Z                     |
  |   seq=100                 |   idMission=rover_id           |
  |   ack=100                 |   seq=100                    |
  |                           |   ack=100                    |
  |                           |                              |
  |--4. ACK------------------>|                              |
  |   flag=A                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=100                 |                              |
  |   ack=100                 |                              |
  |                           |--4. ACK--------------------->|
  |                           |                              |
  |--5. DATA----------------->|                              |
  |   flag=D                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=101                 |                              |
  |   ack=101                 |                              |
  |   size=1                  |                              |
  |   reqType=R               |                              |
  |   message=\0              |                              |
  |                           |--5. DATA-------------------->|
  |                           |                              |
  |<--6. ACK------------------|                              |
  |   flag=A                  |<--6. ACK---------------------|
  |   idMission=rover_id        |   flag=A                     |
  |   seq=101                 |   idMission=rover_id           |
  |   ack=101                 |   seq=101                    |
  |                           |   ack=101                    |
  |                           |                              |
  |<--7. DATA-----------------|                              |
  |   flag=D                  |<--7. DATA--------------------|
  |   idMission=rover_id        |   flag=D                     |
  |   seq=102                 |   idMission=rover_id           |
  |   ack=102                 |   seq=102                    |
  |   size=9                  |   ack=102                    |
  |   reqType=A               |   size=9                     |
  |   message=Registered      |   reqType=A                  |
  |                           |   message=Registered         |
  |                           |                              |
  |--8. ACK------------------>|                              |
  |   flag=A                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=102                 |                              |
  |   ack=102                 |                              |
  |                           |--8. ACK--------------------->|
  |                           |                              |
  |--9. FIN------------------>|                              |
  |   flag=F                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=103                 |                              |
  |   ack=103                 |                              |
  |   size=1                  |                              |
  |   reqType=N               |                              |
  |   message=\0              |                              |
  |                           |--9. FIN--------------------->|
  |                           |                              |
  |<--10. FIN-ACK-------------|                              |
  |   flag=F                  |<--10. FIN-ACK----------------|
  |   idMission=rover_id        |   flag=F                     |
  |   seq=103                 |   idMission=rover_id           |
  |   ack=103                 |   seq=103                    |
  |                           |   ack=103                    |
  |                           |                              |
  |--11. ACK----------------->|                              |
  |   flag=A                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=104                 |                              |
  |   ack=104                 |                              |
  |                           |--11. ACK-------------------->|
```

**Código correspondente:**
- **Rover:** `CC/tp2/client/NMS_Agent.py`, método `register()`, linhas 80-92
- **Nave-Mãe:** `CC/tp2/server/NMS_Server.py`, método `recvMissionLink()`, linhas 65-78
- **Handshake:** `CC/tp2/protocol/MissionLink.py`, métodos `startConnection()` (linhas 173-235) e `acceptConnection()` (linhas 238-277)
- **Envio de dados:** `CC/tp2/protocol/MissionLink.py`, método `send()`, linhas 280-430

---

### Cenário 2: Envio de Tarefa da Nave-Mãe para o Rover

```
Nave-Mãe                 MissionLink (UDP)              Rover
  |                           |                              |
  |--1. SYN------------------>|                              |
  |   flag=S                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=100                 |                              |
  |   ack=0                   |                              |
  |                           |--1. SYN--------------------->|
  |                           |                              |
  |<--2. SYN-ACK--------------|                              |
  |   flag=Z                  |<--2. SYN-ACK-----------------|
  |   idMission=rover_id        |   flag=Z                     |
  |   seq=100                 |   idMission=rover_id           |
  |   ack=100                 |   seq=100                    |
  |                           |   ack=100                    |
  |                           |                              |
  |--3. ACK------------------>|                              |
  |   flag=A                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=100                 |                              |
  |   ack=100                 |                              |
  |                           |--3. ACK--------------------->|
  |                           |                              |
  |--4. DATA----------------->|                              |
  |   flag=D                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=101                 |                              |
  |   ack=101                 |                              |
  |   size=XXX                |                              |
  |   reqType=T               |                              |
  |   message={task JSON}     |                              |
  |                           |--4. DATA-------------------->|
  |                           |                              |
  |<--5. ACK------------------|                              |
  |   flag=A                  |<--5. ACK---------------------|
  |   idMission=rover_id        |   flag=A                     |
  |   seq=101                 |   idMission=rover_id           |
  |   ack=101                 |   seq=101                    |
  |                           |   ack=101                    |
  |                           |                              |
  |--6. FIN------------------>|                              |
  |   flag=F                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=102                 |                              |
  |   ack=102                 |                              |
  |                           |--6. FIN--------------------->|
  |                           |                              |
  |<--7. FIN-ACK--------------|                              |
  |   flag=F                  |<--7. FIN-ACK-----------------|
  |   idMission=rover_id        |   flag=F                     |
  |   seq=102                 |   idMission=rover_id           |
  |   ack=102                 |   seq=102                    |
  |                           |   ack=102                    |
  |                           |                              |
  |--8. ACK------------------>|                              |
  |   flag=A                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=103                 |                              |
  |   ack=103                 |                              |
  |                           |--8. ACK--------------------->|
```

**Código correspondente:**
- **Nave-Mãe:** `CC/tp2/server/NMS_Server.py`, método `sendTask()`, linhas 85-106
- **Rover:** `CC/tp2/client/NMS_Agent.py`, método `recvMissionLink()`, linhas 95-106
- **Envio:** `CC/tp2/protocol/MissionLink.py`, método `send()`, linhas 280-430

---

### Cenário 3: Envio de Métricas do Rover para a Nave-Mãe

```
Rover                    MissionLink (UDP)              Nave-Mãe
  |                           |                              |
  |--1. SYN------------------>|                              |
  |   flag=S                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=100                 |                              |
  |   ack=0                   |                              |
  |                           |--1. SYN--------------------->|
  |                           |                              |
  |<--2. SYN-ACK--------------|                              |
  |   flag=Z                  |<--2. SYN-ACK-----------------|
  |   idMission=rover_id        |   flag=Z                     |
  |   seq=100                 |   idMission=rover_id           |
  |   ack=100                 |   seq=100                    |
  |                           |   ack=100                    |
  |                           |                              |
  |--3. ACK------------------>|                              |
  |   flag=A                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=100                 |                              |
  |   ack=100                 |                              |
  |                           |--3. ACK--------------------->|
  |                           |                              |
  |--4. DATA (filename)------>|                              |
  |   flag=D                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=101                 |                              |
  |   ack=101                 |                              |
  |   size=XXX                |                              |
  |   reqType=M               |                              |
  |   message=alert_...json   |                              |
  |                           |--4. DATA (filename)--------->|
  |                           |                              |
  |<--5. ACK------------------|                              |
  |   flag=A                  |<--5. ACK---------------------|
  |   idMission=rover_id        |   flag=A                     |
  |   seq=101                 |   idMission=rover_id           |
  |   ack=101                 |   seq=101                    |
  |                           |   ack=101                    |
  |                           |                              |
  |--6. DATA (chunk 1)------->|                              |
  |   flag=D                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=102                 |                              |
  |   ack=102                 |                              |
  |   size=1000               |                              |
  |   reqType=M               |                              |
  |   message={JSON chunk 1}  |                              |
  |                           |--6. DATA (chunk 1)---------->|
  |                           |                              |
  |<--7. ACK------------------|                              |
  |   flag=A                  |<--7. ACK---------------------|
  |   idMission=rover_id        |   flag=A                     |
  |   seq=102                 |   idMission=rover_id           |
  |   ack=102                 |   seq=102                    |
  |                           |   ack=102                    |
  |                           |                              |
  |--8. DATA (chunk 2)------->|                              |
  |   flag=D                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=103                 |                              |
  |   ack=103                 |                              |
  |   size=500                |                              |
  |   reqType=M               |                              |
  |   message={JSON chunk 2}  |                              |
  |                           |--8. DATA (chunk 2)---------->|
  |                           |                              |
  |<--9. ACK------------------|                              |
  |   flag=A                  |<--9. ACK---------------------|
  |   idMission=rover_id        |   flag=A                     |
  |   seq=103                 |   idMission=rover_id           |
  |   ack=103                 |   seq=103                    |
  |                           |   ack=103                    |
  |                           |                              |
  |--10. FIN----------------->|                              |
  |   flag=F                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=104                 |                              |
  |   ack=104                 |                              |
  |                           |--10. FIN-------------------->|
  |                           |                              |
  |<--11. FIN-ACK-------------|                              |
  |   flag=F                  |<--11. FIN-ACK----------------|
  |   idMission=rover_id        |   flag=F                     |
  |   seq=104                 |   idMission=rover_id           |
  |   ack=104                 |   seq=104                    |
  |                           |   ack=104                    |
  |                           |                              |
  |--12. ACK----------------->|                              |
  |   flag=A                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=105                 |                              |
  |   ack=105                 |                              |
  |                           |--12. ACK-------------------->|
  |                           |                              |
  |<--13. DATA----------------|                              |
  |   flag=D                  |<--13. DATA-------------------|
  |   idMission=rover_id        |   flag=D                     |
  |   seq=106                 |   idMission=rover_id           |
  |   ack=106                 |   seq=106                    |
  |   size=1                  |   ack=106                    |
  |   reqType=A               |   size=1                     |
  |   message=1               |   reqType=A                  |
  |                           |   message=1 (iteração)       |
  |                           |                              |
  |--14. ACK----------------->|                              |
  |   flag=A                  |                              |
  |   idMission=rover_id        |                              |
  |   seq=106                 |                              |
  |   ack=106                 |                              |
  |                           |--14. ACK-------------------->|
```

**Código correspondente:**
- **Rover:** `CC/tp2/client/NMS_Agent.py`, método `sendMetrics()`, linhas 62-78
- **Nave-Mãe:** `CC/tp2/server/NMS_Server.py`, método `recvMissionLink()`, linhas 80-83
- **Envio de ficheiro:** `CC/tp2/protocol/MissionLink.py`, método `send()`, linhas 301-379 (caso `.json`)

---

### Cenário 4: Envio de Telemetria via TelemetryStream (TCP)

```
Rover                    TelemetryStream (TCP)          Nave-Mãe
  |                           |                              |
  |--1. CONNECT-------------->|                              |
  |   (TCP 3-way handshake)   |                              |
  |                           |-1. CONNECT------------------>|
  |                           |                              |
  |--2. DATA (4 bytes)------->|                              |
  |   tamanho_nome=0025       |                              |
  |                           |--2. DATA (4 bytes)---------->|
  |                           |                              |
  |--3. DATA (25 bytes)------>|                              |
  |nome=alert_n1_task-202_1.json|                            |
  |                           |--3. DATA (25 bytes)--------->|
  |                           |                              |
  |--4. DATA (chunk 1)------->|                              |
  |   buffer=1024 bytes       |                              |
  |   {JSON telemetry data}   |                              |
  |                           |--4. DATA (chunk 1)---------->|
  |                           |                              |
  |--5. DATA (chunk 2)------->|                              |
  |   buffer=500 bytes        |                              |
  |   {JSON telemetry data}   |                              |
  |                           |--5. DATA (chunk 2)---------->|
  |                           |                              |
  |--6. CLOSE---------------->|                              |
  |   (TCP connection close)  |                              |
  |                           |--6. CLOSE------------------->|
```

**Código correspondente:**
- **Rover:** `CC/tp2/client/NMS_Agent.py`, método `sendTelemetry()`, linha 116
- **Envio:** `CC/tp2/protocol/TelemetryStream.py`, método `send()`, linhas 120-149
- **Nave-Mãe:** `CC/tp2/server/NMS_Server.py`, método `recvTelemetry()`, linha 63
- **Receção:** `CC/tp2/protocol/TelemetryStream.py`, método `recv()`, linhas 88-116

---

## 3. Resumo dos Campos por Operação

### Registo (Register - R)
- **flag:** D (Data) → A (ACK)
- **idMission:** ID do rover
- **seq/ack:** Controlo de sequência
- **size:** 1 (mensagem vazia `\0`)
- **requestType:** R (Register)
- **message:** `\0` (vazio)

### Envio de Tarefa (Task - T)
- **flag:** D (Data) → A (ACK)
- **idMission:** ID do rover destinatário
- **seq/ack:** Controlo de sequência
- **size:** Tamanho do JSON da tarefa
- **requestType:** T (Task)
- **message:** JSON com configuração da tarefa

### Envio de Métricas (Metrics - M)
- **flag:** D (Data) → A (ACK) (múltiplos chunks)
- **idMission:** ID do rover
- **seq/ack:** Controlo de sequência (incrementa por chunk)
- **size:** Tamanho de cada chunk (máx 1000 bytes por chunk)
- **requestType:** M (Metrics)
- **message:** Nome do ficheiro (primeiro pacote), depois chunks do ficheiro JSON

### Telemetria (TelemetryStream)
- **tamanho_nome:** 4 bytes (formato "0025" para 25 bytes)
- **nome_ficheiro:** N bytes (nome do ficheiro de telemetria)
- **conteúdo:** Variável (chunks de 1024 bytes até EOF)

---

## 4. Referências de Código

### MissionLink
- **Formato:** `CC/tp2/protocol/MissionLink.py`, linhas 5-13, 72-90
- **Handshake:** `CC/tp2/protocol/MissionLink.py`, linhas 173-277
- **Envio:** `CC/tp2/protocol/MissionLink.py`, linhas 280-430
- **Flags:** `CC/tp2/protocol/MissionLink.py`, linhas 40-47

### TelemetryStream
- **Formato:** `CC/tp2/protocol/TelemetryStream.py`, linhas 11, 88-116, 120-149
- **Envio:** `CC/tp2/protocol/TelemetryStream.py`, método `send()`, linhas 120-149
- **Receção:** `CC/tp2/protocol/TelemetryStream.py`, método `recv()`, linhas 88-116

### Uso no Rover
- **Registo:** `CC/tp2/client/NMS_Agent.py`, método `register()`, linhas 80-92
- **Envio métricas:** `CC/tp2/client/NMS_Agent.py`, método `sendMetrics()`, linhas 62-78
- **Receção tarefas:** `CC/tp2/client/NMS_Agent.py`, método `recvMissionLink()`, linhas 95-106
- **Envio telemetria:** `CC/tp2/client/NMS_Agent.py`, método `sendTelemetry()`, linha 116

### Uso na Nave-Mãe
- **Receção registos:** `CC/tp2/server/NMS_Server.py`, método `recvMissionLink()`, linhas 65-78
- **Envio tarefas:** `CC/tp2/server/NMS_Server.py`, método `sendTask()`, linhas 85-106
- **Receção métricas:** `CC/tp2/server/NMS_Server.py`, método `recvMissionLink()`, linhas 80-83
- **Receção telemetria:** `CC/tp2/server/NMS_Server.py`, método `recvTelemetry()`, linha 63

