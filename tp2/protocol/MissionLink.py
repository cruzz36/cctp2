import socket
from otherEntities import Limit


# [flag,idMission,seq,ack,size,missionType,message]
#   0       1      2   3   4        5           6
# NOTA: No handshake, idMission contém temporariamente o ID do rover
#       Após handshake, idMission contém o ID da missão
flagPos = 0
idMissionPos = 1
seqPos = 2
ackPos = 3
sizePos = 4
missionTypePos = 5
messagePos = 6


class MissionLink:
    """
    Protocolo MissionLink (ML) - Protocolo aplicacional sobre UDP para comunicação crítica
    entre a Nave-Mãe e os rovers. Implementa mecanismos de fiabilidade a nível aplicacional
    incluindo handshake, números de sequência, acknowledgments e retransmissão.
    """
    def __init__(self,serverAddress,storeFolder = "."):
        """
        Inicializa o protocolo MissionLink.
        
        Args:
            serverAddress (str): Endereço IP do servidor
            storeFolder (str, optional): Pasta onde armazenar ficheiros recebidos. Defaults to "."
        """
        self.serverAddress = serverAddress
        self.port = 8080
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.server()
        self.limit = Limit.Limit()
        self.sock.settimeout(self.limit.timeout)
        if storeFolder.endswith("/"):
            self.storeFolder = storeFolder
        else:
            self.storeFolder = storeFolder + "/"
        # ============================================================
        # TIPOS DE OPERAÇÃO DO PROTOCOLO (missionType)
        # ============================================================
        # NOTA IMPORTANTE: Estes valores (R, T, M, Q, P) são diferentes dos tipos de tarefa
        #                  que aparecem dentro do JSON da missão (capture_images, sample_collection, environmental_analysis).
        #
        # missionType indica o TIPO DE OPERAÇÃO do protocolo:
        #   - Como processar a mensagem recebida
        #   - Que handler chamar no servidor/cliente
        #   - Qual o propósito da comunicação
        #
        # task (dentro do JSON) indica o TIPO DE TAREFA da missão:
        #   - O que o rover deve executar fisicamente
        #   - Apenas aparece quando missionType="T" (Task)
        #   - Valores possíveis: "capture_images", "sample_collection", "environmental_analysis"
        # ============================================================
        self.registerAgent = "R"      # Register: Rover regista-se na Nave-Mãe
        self.taskRequest = "T"        # Task: Nave-Mãe envia missão ao rover (JSON contém campo "task")
        self.sendMetrics = "M"       # Metrics: Rover envia métricas à Nave-Mãe
        self.requestMission = "Q"    # Request/Query: Rover solicita uma missão à Nave-Mãe
        self.reportProgress = "P"      # Progress: Rover reporta progresso de uma missão em execução
        
        # ============================================================
        # FLAGS DE CONTROLO DO PROTOCOLO
        # ============================================================
        # Flags para controlo de conexão e fiabilidade sobre UDP
        self.datakey = "D"           # Data: Mensagem de dados normal
        self.synkey = "S"            # SYN: Inicia handshake (3-way)
        self.ackkey = "A"            # ACK: Confirmação de receção
        self.finkey = "F"            # FIN: Fecha conexão
        self.synackkey = "Z"         # SYN-ACK: Resposta ao SYN no handshake
        # Constante para fim de mensagem - melhora manutenibilidade
        self.eofkey = '\0'

    
    def server(self):
        """
        Liga o socket UDP ao endereço e porta especificados.
        Prepara o socket para receber mensagens.
        """
        self.sock.bind((self.serverAddress,self.port))


    def getHeaderSize(self):
        """
        Calcula o tamanho do cabeçalho da mensagem do protocolo.
        
        Returns:
            int: Tamanho do cabeçalho em bytes (flag + separadores + idMission + seq + ack + size + missionType)
        """
        # flag + | + idMission + | + seq + | + ack + | + size + | + missionType + |
        return 1 + 1 + 3 + 1 + 4 + 1 + 4 + 1 + 4 + 1 + 1 + 1
    
    def formatMessage(self,missionType,flag,idMission,seqNum,ackNum,message):
        """
        Formata uma mensagem segundo o protocolo MissionLink.
        Formato: flag|idMission|seq|ack|size|missionType|message
        
        NOTA: No handshake, idMission contém temporariamente o ID do rover.
              Nas mensagens de dados, idMission contém o ID da missão.
        
        ============================================================
        DIFERENÇA ENTRE missionType E task:
        ============================================================
        - missionType (campo do protocolo): Tipo de OPERAÇÃO (R, T, M, Q, P)
          * R = Register: Rover regista-se
          * T = Task: Nave-Mãe envia missão
          * M = Metrics: Rover envia métricas
          * Q = Request: Rover solicita missão
          * P = Progress: Rover reporta progresso
        
        - task (campo dentro do JSON): Tipo de TAREFA física (quando missionType="T")
          * "capture_images": Capturar imagens
          * "sample_collection": Recolher amostras
          * "environmental_analysis": Análise ambiental
        ============================================================
        
        Formato de mensagem de missão (quando missionType="T"):
        O campo 'message' deve conter um JSON com os seguintes campos obrigatórios:
        {
            "mission_id": string (obrigatório, identificador único da missão),
            "rover_id": string (obrigatório, ID do rover destinatário),
            "geographic_area": {
                "x1": float, "y1": float, "x2": float, "y2": float
            } (obrigatório, área geográfica a explorar),
            "task": string (obrigatório, tipo de tarefa: capture_images|sample_collection|environmental_analysis),
            "duration_minutes": integer (obrigatório, > 0, tempo máximo para execução),
            "update_frequency_seconds": integer (obrigatório, > 0, frequência de reporte de progresso)
        }
        
        Campos opcionais:
        - "priority": string (low|medium|high)
        - "instructions": string (instruções adicionais)
        
        Exemplo de mensagem de missão:
        {
            "mission_id": "M-001",
            "rover_id": "r1",
            "geographic_area": {"x1": 10.0, "y1": 20.0, "x2": 50.0, "y2": 60.0},
            "task": "capture_images",  ← Tipo de tarefa (um dos 3 possíveis)
            "duration_minutes": 30,
            "update_frequency_seconds": 120
        }
        
        Args:
            missionType (str or None): Tipo de operação do protocolo (R=Register, T=Task, M=Metrics, Q=Request, P=Progress) ou None
            flag (str): Flag de controlo (S=SYN, A=ACK, F=FIN, Z=SYN-ACK, D=Data)
            idMission (str): Identificador da missão (3 caracteres) ou ID do rover no handshake
            seqNum (int): Número de sequência
            ackNum (int): Número de acknowledgment
            message (str): Conteúdo da mensagem (JSON string quando missionType="T", onde o JSON contém o campo "task")
            
        Returns:
            bytes: Mensagem formatada e codificada em bytes
        """
        if missionType != None: 
            return f"{flag}|{idMission}|{seqNum}|{ackNum}|{len(message)}|{missionType}|{message}".encode()
        return f"{flag}|{idMission}|{seqNum}|{ackNum}|{len(message)}|N|{message}".encode()
        

    def splitMessage(self,message):
        """
        Divide uma mensagem em chunks se exceder o tamanho máximo do buffer.
        
        Args:
            message (str): Mensagem a dividir
            
        Returns:
            str or list: Mensagem original se couber num pacote, ou lista de chunks
        """
        if len(message) > self.limit.buffersize - self.getHeaderSize(): return [message[i:i+self.limit.buffersize - self.getHeaderSize()] for i in range(0,len(message),self.limit.buffersize - self.getHeaderSize())]
        else: return message


    def startConnection(self, idAgent, destAddress, destPort, retryLimit=5):
        """
        Inicia uma conexão com handshake de 3 vias (SYN, SYN-ACK, ACK).
        Implementa mecanismo de fiabilidade sobre UDP.
        
        NOTA: No handshake, o campo idMission é usado temporariamente para enviar o ID do rover.
              A Nave-Mãe guarda o mapeamento (IP, porta) -> ID do rover.
        
        Args:
            idAgent (str): Identificador do agente/rover (3 caracteres)
            destAddress (str): Endereço IP do destino
            destPort (int): Porta do destino
            retryLimit (int, optional): Número máximo de tentativas. Defaults to 5
            
        Returns:
            tuple: ((destAddress, destPort), idAgent, seq, ack) - Informação da conexão estabelecida
            
        Raises:
            TimeoutError: Se não conseguir estabelecer conexão após múltiplas tentativas
        """
        seqinicial = 100 #random.randint(0, 10000)
        retries = 0
        
        while retries < retryLimit:
            try:
                # Send SYN - no handshake, idMission contém o ID do rover
                self.sock.sendto(
                    f"{self.synkey}|{idAgent}|{seqinicial}|0|_|0|-.-".encode(),
                    (destAddress, destPort)
                )
                # Print de debug comentado - útil para troubleshooting do handshake
                # print("SYN ENVIADO")
                # Wait for SYN-ACK
                try:
                    message, _ = self.sock.recvfrom(self.limit.buffersize)
                    lista = message.decode().split("|")
                    while lista[flagPos] != self.synackkey:
                        self.sock.sendto(
                            f"{self.synkey}|{idAgent}|{seqinicial}|0|_|0|-.-".encode(),
                            (destAddress, destPort)
                        )
                        message,_ = self.sock.recvfrom(self.limit.buffersize)
                        lista = message.decode().split("|")
                        # Validar formato da mensagem
                        if len(lista) < 7:
                            # Mensagem malformada - reenviar SYN e continuar
                            self.sock.sendto(
                                f"{self.synkey}|{idAgent}|{seqinicial}|0|_|0|-.-".encode(),
                                (destAddress, destPort)
                            )
                            continue
                    # Print de debug comentado - confirma receção de SYN-ACK
                    # print("RECEBEU O SYNACK CORRETO")

                except socket.timeout:
                    # Timeout ao aguardar SYN-ACK - continuar para retry
                    continue
                except Exception as e:
                    print(f"Erro ao aguardar SYN-ACK: {e}")
                    continue

                # Send ACK
                # Print de debug comentado - mostra sequência do ACK enviado
                # print(f"Sending ACK: seq={seqinicial}")
                self.sock.sendto(
                    f"{self.ackkey}|{idAgent}|{seqinicial}|{seqinicial}|_|0|-.-".encode(),
                    (destAddress, destPort)
                )
                print("CONNECTION ESTABLISHED\n--------------")
                return  (destAddress,destPort),idAgent,seqinicial + 1,seqinicial + 1 # Handshake successful

            
        
            except socket.timeout:
                retries += 1
                print(f"Retrying SYN: ({retries}/{retryLimit})")
            except Exception as e:
                retries += 1
                print(f"Erro no handshake: {e}. Retrying... ({retries}/{retryLimit})")
        
        raise TimeoutError("Failed to establish connection after multiple attempts.")


    def acceptConnection(self):
        """
        Aceita uma conexão recebendo um pedido SYN e respondendo com handshake de 3 vias.
        Deve ser executado pelo servidor (Nave-Mãe).
        
        NOTA: No handshake, o campo idMission contém temporariamente o ID do rover.
              O servidor deve guardar o mapeamento (IP, porta) -> ID do rover.
        
        Returns:
            tuple: ((ip, port), idAgent, seq, ack) - Informação da conexão estabelecida
                - ip (str): Endereço IP do cliente
                - port (int): Porta do cliente
                - idAgent (str): Identificador do agente/rover (extraído de idMission no handshake)
                - seq (int): Número de sequência inicial
                - ack (int): Número de acknowledgment inicial (igual a seq)
        """
        # RECEBER O SYN
        message,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
        # Print de debug comentado - mostra primeira mensagem recebida
        # print(f"Message : {message}\nFrom : {ip}:{port}")
        lista = message.decode().split("|")
        while lista[flagPos] != self.synkey:
            message,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
            # Mensagem inválida recebida - ignorar e continuar
            # print(f"Message : {message}\nFrom : {ip}:{port}")  # Debug: descomentar para troubleshooting
            lista = message.decode().split("|")
            # Validar formato da mensagem
            if len(lista) < 7:
                # Mensagem malformada - continuar loop
                continue
        # No handshake, idMission contém o ID do rover
        idAgent = lista[idMissionPos]
        # ENVIAR SYNACK 
        lista[flagPos] = self.synackkey
        prevLista = lista.copy()
        self.sock.sendto("|".join(lista).encode(),(ip,port))
        # RECEBER ACK
        while True:
            try:
                message,_ = self.sock.recvfrom(self.limit.buffersize)
                lista = message.decode().split("|")
                # Validar formato da mensagem
                if len(lista) < 7:
                    # Mensagem malformada - reenviar SYN-ACK e continuar
                    self.sock.sendto("|".join(prevLista).encode(),(ip,port))
                    continue
                if (lista[flagPos] == self.ackkey and 
                lista[idMissionPos] == idAgent and 
                lista[ackPos] == lista[seqPos]):
                    print("CONECTION ESTABLISHED\n---------------")
                    return (ip,port),idAgent,int(lista[seqPos]),int(lista[ackPos])
            except socket.timeout:
                # Reenviar SYN-ACK se timeout ao aguardar ACK
                self.sock.sendto("|".join(prevLista).encode(),(ip,port))
            except Exception as e:
                print(f"Erro ao aguardar ACK no acceptConnection: {e}")
                # Reenviar SYN-ACK
                self.sock.sendto("|".join(prevLista).encode(),(ip,port))

        
        
    def send(self,ip,port,missionType,idAgent,idMission,message):
        """
        Envia uma mensagem ou ficheiro através do protocolo MissionLink.
        Estabelece conexão, envia dados com confirmação e fecha conexão.
        
        Args:
            ip (str): Endereço IP do destinatário
            port (int): Porta do destinatário
            missionType (str): Tipo de missão/operação (R=Register, T=Task, M=Metrics, Q=Request, P=Progress)
            idAgent (str): Identificador do agente/rover (usado apenas no handshake)
            idMission (str): Identificador da missão (3 caracteres, "000" se não aplicável)
            message (str): Mensagem ou caminho do ficheiro a enviar
            
        Returns:
            bool: True se a mensagem foi enviada com sucesso
        """
        # The connection starts with an handshake to assure it has a somewhat reliable 
        # transfers between the client and the server 
        _,idAgent,seq,ack = self.startConnection(idAgent,ip,port)

        #print(f"SEQ - {seq}\nACK - {ack}")

        if message.endswith(".json"):
            # First cycle is to send the filename
            while True:
                self.sock.sendto(self.formatMessage(missionType,self.datakey,idMission,seq,ack,message),(ip,port))
                try:
                    text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                    lista = text.decode().split("|")
                    # Validar formato da mensagem
                    if len(lista) < 7:
                        # Mensagem malformada - retransmitir nome do ficheiro
                        continue
                    if(
                        responseIp == ip and
                        responsePort == port and
                        lista[flagPos] == self.ackkey and
                        lista[ackPos] == str(seq)
                    ):
                        seq += 1
                        ack = seq
                        print("File name sent")
                        break
                except socket.timeout:
                    # Timeout ao aguardar ACK - retransmitir nome do ficheiro
                    continue
                except Exception as e:
                    print(f"Erro ao aguardar ACK do nome do ficheiro: {e}")
                    continue

            with open(message,"r") as file:
                buffer = file.read(self.limit.buffersize-self.getHeaderSize())
                i = 1
                while buffer:
                    # Debug: mostrar iteração (pode ser removido em produção)
                    # print(f"Iteration {i}")
                    i+=1
                    self.sock.sendto(self.formatMessage(missionType,self.datakey,idMission,seq,ack,buffer),(ip,port))
                    try:
                        text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                        lista = text.decode().split("|")
                        if(
                            responseIp == ip and
                            responsePort == port and
                            lista[flagPos] == self.ackkey and
                            lista[ackPos] == str(seq)
                        ):
                            seq += 1
                            ack = seq
                            buffer = file.read(self.limit.buffersize - self.getHeaderSize())
                    except socket.timeout:
                        # Retransmitir chunk em caso de timeout
                        self.sock.sendto(self.formatMessage(missionType,self.datakey,idMission,seq,ack,buffer),(ip,port))
                        continue
            # Incrementar seq antes de enviar FIN para garantir número de sequência diferente
            # Evita ambiguidade entre último chunk e FIN
            seq += 1
            ack = seq
            self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
            while True:
                try:
                    text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                    lista = text.decode().split("|")
                    # Validação do pacote FIN recebido
                    if(
                        len(lista) == 7 and
                        responseIp == ip and
                        responsePort == port and
                        lista[ackPos] == str(seq) and
                        lista[flagPos] == self.finkey
                    ):
                        seq += 1
                        ack = seq
                        # Confirmação FIN recebida corretamente
                        self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                        return True
                except socket.timeout:
                    self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                    

        else:
            chunks = self.splitMessage(message)

            # If chunks is a string, only a packet with data is sent
            # The next one is a connection closing one
            if isinstance(chunks,str):
                self.sock.sendto(self.formatMessage(missionType,self.datakey,idMission,seq,ack,chunks),(ip,port))
                while True: 
                    try:
                        text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                        lista = text.decode().split("|")
                        #print(lista)
                        if (responseIp == ip and
                            responsePort == port and
                            lista[ackPos] == str(seq) and 
                            lista[flagPos] == self.ackkey
                            ):
                            seq += 1
                            ack = seq
                            self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                            # Fechamento bidirecional completo (4-way handshake)
                            # Aguarda ACK do FIN enviado OU FIN do outro lado
                            while True:
                                try:
                                    text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                                    lista = text.decode().split("|")
                                    # Validar formato da mensagem
                                    if len(lista) < 7:
                                        # Mensagem malformada - reenviar FIN
                                        self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                        continue
                                    if (
                                        responseIp == ip and
                                        responsePort == port and
                                        len(lista) == 7 and
                                        lista[idMissionPos] == idMission
                                    ):
                                        if lista[flagPos] == self.finkey:
                                            # Recebeu FIN do outro lado - responder com ACK e terminar
                                            seq += 1
                                            ack = seq
                                            self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                                            return True
                                        elif lista[flagPos] == self.ackkey and lista[ackPos] == str(seq):
                                            # Recebeu ACK do FIN enviado - agora esperar FIN do outro lado
                                            # Continuar loop para aguardar FIN
                                            continue
                                except socket.timeout:
                                    # Reenvia FIN se timeout (pode ser que o outro lado ainda não recebeu)
                                    self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                    continue
                                except Exception as e:
                                    print(f"Erro ao aguardar resposta FIN: {e}")
                                    # Reenviar FIN
                                    self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                    continue
                        continue
                    except socket.timeout:
                        # Timeout ao aguardar ACK - retransmitir mensagem
                        self.sock.sendto(self.formatMessage(missionType,self.datakey,idMission,seq,ack,chunks),(ip,port))
                        continue
                    except Exception as e:
                        print(f"Erro ao aguardar ACK: {e}")
                        # Retransmitir mensagem
                        self.sock.sendto(self.formatMessage(missionType,self.datakey,idMission,seq,ack,chunks),(ip,port))
                        continue
            # In case the message is big enough, 
            # we must send each element of the list
            i = 0
            while i != len(chunks):
                self.sock.sendto(self.formatMessage(missionType,self.datakey,idMission,seq,ack,chunks[i]),(ip,port))
                try:
                    response,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                    lista = response.decode().split("|")
                    # Debug: mostrar sequência esperada vs recebida (pode ser removido em produção)
                    # print(f"EXPECTING - {seq}\nRECEIVED - {lista[ackPos]}")
                    if(
                        len(lista) == 7 and
                        responseIp == ip and
                        responsePort == port and
                        lista[ackPos] == str(seq) and 
                        lista[flagPos] == self.ackkey
                    ):
                        seq += 1
                        ack = seq
                        i += 1
                        continue
                except socket.timeout:
                    # Timeout ao aguardar ACK - retransmitir chunk
                    # Debug: mostrar retransmissão (pode ser removido em produção)
                    # print(f"\n\nResent the seq - {seq}")
                    self.sock.sendto(self.formatMessage(missionType,self.datakey,idMission,seq,ack,chunks[i]),(ip,port))
                    continue
                except Exception as e:
                    print(f"Erro ao receber ACK do chunk: {e}")
                    # Retransmitir chunk
                    self.sock.sendto(self.formatMessage(missionType,self.datakey,idMission,seq,ack,chunks[i]),(ip,port))
                    continue
            self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
            while True:
                try:
                    text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                    lista = text.decode().split("|")
                    # Validar formato da mensagem
                    if len(lista) < 7:
                        # Mensagem malformada - reenviar FIN
                        self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                        continue
                    if(
                        responseIp == ip and
                        responsePort == port and
                        lista[ackPos] == str(seq) and
                        lista[flagPos] == self.finkey
                    ):
                        return True                  
                except TimeoutError:
                    self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                    
                



    # Method to receive messages/files
    # Will either return the message or the name of the transfered file
    # along with the agent ID 
    def recv(self):
        """
        Returns a list with 5 items by order
            - 0 - idAgent (ID do rover)
            - 1 - idMission (ID da missão)
            - 2 - missionType (tipo de missão/operação)
            - 3 - file name or the message in string
            - 4 - ip address
        """
        message = ""
        # Establish connection
        (ipDest,portDest),idAgent,seq,ack = self.acceptConnection()
        idMission = None  # Será extraído da primeira mensagem

        # Debug: mostrar sequência inicial (pode ser removido em produção)
        # print(f"SEQ - {seq}\nACK - {ack}")        

        fileName = None
        missionType = ""

        # We get the first message with data to know if it is a message or a file 
        firstMessage = None
        while firstMessage == None:
            try:
                firstMessage,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
                lista = firstMessage.decode().split("|")
                # Validar formato da mensagem
                if len(lista) < 7:
                    # Mensagem malformada - ignorar e continuar
                    firstMessage = None
                    continue
                if (
                    ip == ipDest and 
                    port == portDest and
                    lista[seqPos] == str(seq + 1)
                ):
                    idMission = lista[idMissionPos]  # Extrai idMission da primeira mensagem
                    missionType = lista[missionTypePos]
                    seq += 1
                    ack = seq
                    if lista[messagePos].endswith(".json"):
                        # É um ficheiro
                        fileName = lista[messagePos]
                    else:
                        # É uma mensagem
                        firstMessage = lista[messagePos]
                    self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                    break
            except socket.timeout:
                #print("Timed out on the first message")
                firstMessage = None
                continue
            except Exception as e:
                print(f"Erro ao receber primeira mensagem: {e}")
                firstMessage = None
                continue

        # firstMessage pode ser string (mensagem) ou None (ficheiro)
        # Se for string, usar como prevMessage; se for None, prevMessage será None
        # NOTA: Se fileName foi definido, firstMessage será None (é ficheiro, não mensagem)
        prevMessage = firstMessage if (isinstance(firstMessage, str) and fileName is None) else None

        if fileName == None:
            # Catch packets until the fin packet arrives
            while True:
                # Try to receive a packet until timeout
                try:
                    chunks, (ip,port) = self.sock.recvfrom(self.limit.buffersize)
                    lista = chunks.decode().split("|")
                    # Debug: mostrar sequência esperada vs recebida (pode ser removido em produção)
                    # print(f"EXPECTING - {ack + 1}\nRECEIVED - {lista[seqPos]}")
                    # When receiving a packet, the packet is accepted if:
                    # the length of the list is 7
                    # the mission id matches the connection's mission
                    # the seq is greater 1 unit the whats stored on receiver side
                    # the IP address and Port must be the same (identifica o rover)
                    if(
                        len(lista) == 7 and
                        lista[idMissionPos] == idMission and
                        lista[seqPos] == str(seq + 1) and
                        ipDest == ip and
                        port == portDest
                    ):
                        message += prevMessage
                        prevMessage = lista[messagePos]

                        # Increase the seq num to the new value (+1)
                        seq += 1
                        # The acknowledge number becomnes the same as the new sequence number
                        ack = seq
                        # The new acknowledge number is put in the list of fields
                        lista[ackPos] = str(ack)

                        #Check if the client send a connection closing message
                        if lista[flagPos] == self.finkey:
                            # Prints de debug comentados - útil para troubleshooting
                            # DEVERIAM estar ativos durante desenvolvimento/debug
                            # print(lista)
                            # print("Received the end connection packet")
                            self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                            # Aguardar ACK do FIN enviado para garantir fechamento robusto
                            while True:
                                try:
                                    ack_response, (ack_ip, ack_port) = self.sock.recvfrom(self.limit.buffersize)
                                    ack_lista = ack_response.decode().split("|")
                                    if (
                                        ack_ip == ipDest and
                                        ack_port == portDest and
                                        len(ack_lista) == 7 and
                                        ack_lista[flagPos] == self.ackkey and
                                        ack_lista[idMissionPos] == idMission and
                                        ack_lista[ackPos] == str(seq)
                                    ):
                                        # Recebeu ACK do FIN - conexão fechada corretamente
                                        return [idAgent,idMission,missionType,message,ip]
                                except socket.timeout:
                                    # Reenvia FIN se não receber ACK
                                    self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                    continue
                                except Exception as e:
                                    print(f"Erro ao aguardar ACK do FIN: {e}")
                                    # Reenviar FIN
                                    self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                    continue
                        # Enviar ACK do chunk recebido
                        self.sock.sendto(self.formatMessage(lista[missionTypePos],self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                    



                # In case of a timeout, it means the
                # either the message did not reach the destination
                # or the message do not correspond to the expected sequence
                # So, to make sure, we sent the previous message that was supposed to be sent
                except socket.timeout:
                    # Reenviar último ACK para solicitar retransmissão
                    self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                    continue
                except Exception as e:
                    print(f"Erro ao receber chunk: {e}")
                    # Reenviar último ACK
                    self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                    continue


        ## Comentário explicativo sobre estratégia de escrita de ficheiros
        # Com retransmissão, há probabilidade de escrever o mesmo texto 2 vezes
        # Portanto, quando os chunks chegam, guardamos a mensagem antes de escrever
        # assim só quando o próximo chunk chega, guardamos o próximo e escrevemos o anterior
        # Esta estratégia previne duplicação de dados em caso de retransmissão
        else:
            # Usar with para garantir fechamento do ficheiro mesmo em caso de erro
            with open(self.storeFolder + fileName,"w") as file:
                previous = None
                while True:
                    try:
                        text,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
                        lista = text.decode().split("|")
                        # Validar formato da mensagem
                        if len(lista) < 7:
                            # Mensagem malformada - reenviar ACK e continuar
                            self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                            continue
                        if(
                            len(lista) == 7 and
                            lista[idMissionPos] == idMission and
                            ip == ipDest and
                            port == portDest and
                            lista[seqPos] == str(seq + 1) 
                        ):
                            seq += 1
                            ack = seq
                            # Estratégia anti-duplicação: escrever chunk anterior quando próximo chega
                            # Previne duplicação em caso de retransmissão
                            if previous != None:
                                file.write(previous)
                            
                            if lista[flagPos] == self.finkey:
                                # Escrever último chunk se houver (já escrito acima se previous != None)
                                # Ficheiro será fechado automaticamente pelo with
                                self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                while True:
                                    try:
                                        text,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
                                        lista = text.decode().split("|")
                                        # Validação do pacote FIN recebido
                                        if(
                                            len(lista) == 7 and
                                            ip == ipDest and
                                            port == portDest and 
                                            lista[idMissionPos] == idMission and
                                            lista[seqPos] == str(seq) and
                                            lista[flagPos] == self.finkey
                                        ):
                                            # Ficheiro recebido e conexão fechada
                                            # print("Supposedly ended")  # Debug: descomentar para troubleshooting
                                            return [idAgent,idMission,missionType,fileName,ip]
                                    except socket.timeout:
                                        # Reenviar FIN se timeout
                                        self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                        continue
                                    except Exception as e:
                                        print(f"Erro ao aguardar confirmação FIN: {e}")
                                        # Reenviar FIN
                                        self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                        continue
                            else:
                                # Atualizar previous para o próximo chunk (estratégia anti-duplicação)
                                previous = lista[messagePos]
                                # Enviar ACK do chunk recebido
                                self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))

                    except socket.timeout:
                        # Reenviar último ACK para solicitar retransmissão
                        self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                        continue
                    except Exception as e:
                        print(f"Erro ao receber chunk de ficheiro: {e}")
                        # Reenviar último ACK
                        self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                        continue


