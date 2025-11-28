import socket
from otherEntities import Limit


# [flag,idMission,seq,ack,size,requestType,message]
#   0       1      2   3   4      5           6
# NOTA: No handshake, idMission contém temporariamente o ID do rover
#       Após handshake, idMission contém o ID da missão
flagPos = 0
idMissionPos = 1
seqPos = 2
ackPos = 3
sizePos = 4
reqType = 5
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
        self.registerAgent = "R"
        self.taskRequest = "T"
        self.sendMetrics = "M"
        self.datakey = "D"
        self.synkey = "S"
        self.ackkey = "A"
        self.finkey = "F"
        self.synackkey = "Z"
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
            int: Tamanho do cabeçalho em bytes (flag + separadores + idMission + seq + ack + size + reqType)
        """
        # flag + | + idMission + | + seq + | + ack + | + size + | + reqType + |
        return 1 + 1 + 3 + 1 + 4 + 1 + 4 + 1 + 4 + 1 + 1 + 1
    
    def formatMessage(self,requestType,flag,idMission,seqNum,ackNum,message):
        """
        Formata uma mensagem segundo o protocolo MissionLink.
        Formato: flag|idMission|seq|ack|size|requestType|message
        
        NOTA: No handshake, idMission contém temporariamente o ID do rover.
              Nas mensagens de dados, idMission contém o ID da missão.
        
        Args:
            requestType (str or None): Tipo de pedido (R=Register, T=Task, M=Metrics) ou None
            flag (str): Flag de controlo (S=SYN, A=ACK, F=FIN, Z=SYN-ACK, D=Data)
            idMission (str): Identificador da missão (3 caracteres) ou ID do rover no handshake
            seqNum (int): Número de sequência
            ackNum (int): Número de acknowledgment
            message (str): Conteúdo da mensagem
            
        Returns:
            bytes: Mensagem formatada e codificada em bytes
        """
        if requestType != None: 
            return f"{flag}|{idMission}|{seqNum}|{ackNum}|{len(message)}|{requestType}|{message}".encode()
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

    # Método não utilizado - as mensagens são tratadas como strings diretamente
    # Não é necessário porque o código usa split/join diretamente nas strings
    # def joinMessage(self,bytes):
    #     """
    #     Junta uma lista de bytes numa string.
    #     
    #     Args:
    #         bytes (list): Lista de strings/bytes a juntar
    #         
    #     Returns:
    #         str: String resultante da junção
    #     """
    #     return "".join(bytes)
    
    
    # Método não utilizado - o handshake é feito diretamente em startConnection()
    # DEVERIA estar a ser usado em startConnection() para melhorar modularidade e validação
    # ONDE: No método startConnection(), linha ~188, em vez de fazer a validação inline
    # COMO: Substituir o código inline por: if self.receiveSYNACK(idMission, destAddress, destPort, seqinicial):
    # PORQUÊ: 
    #   1. Melhor separação de responsabilidades
    #   2. Validação mais robusta usando métodos verifySYNACK, verifyIdAgent, verifyACKnum
    #   3. Código mais limpo e reutilizável
    # NOTA: Este método chama verifySYNACK, verifyIdAgent, verifyACKnum que NÃO EXISTEM
    #       Estes métodos DEVERIAM ser implementados para validação adequada do handshake
    # def receiveSYNACK(self, idMission, destAddress, destPort, expectedSeq, retryLimit=5):
    #     """
    #     Recebe e valida um pacote SYN-ACK durante o handshake.
    #     
    #     Args:
    #         idMission (str): Identificador do agente esperado
    #         destAddress (str): Endereço IP de destino esperado
    #         destPort (int): Porta de destino esperada
    #         expectedSeq (int): Número de sequência esperado
    #         retryLimit (int, optional): Número máximo de tentativas. Defaults to 5
    #         
    #     Returns:
    #         bool: True se recebeu SYN-ACK válido
    #         
    #     Raises:
    #         TimeoutError: Se não receber SYN-ACK válido após múltiplas tentativas
    #     """
    #     retries = 0
    #     while retries < retryLimit:
    #         try:
    #             # Wait for SYN-ACK
    #             message, (ip, porta) = self.sock.recvfrom(self.limit.buffersize)
    #             message = message.decode()
    #             parts = message.split("|")
    #             if len(parts) != 7:
    #                 print("Mensagem com tamanho diferente")
    #                 raise ValueError("Malformed message")
    #             
    #             flag, receivedIdAgent, seq, ack, *_ = parts
    #             
    #             if (self.verifySYNACK(flag, destAddress, destPort, ip, porta) and
    #                 self.verifyIdAgent(idMission, receivedIdAgent) and
    #                 self.verifyACKnum(expectedSeq,ack)):
    #                 return True  # Valid SYN-ACK received
    #             
    #         except (TimeoutError, ValueError):
    #             retries += 1
    #             print(message)
    #             print(f"Timeout or invalid message. Retrying... ({retries}/{retryLimit})")
    #     
    #     raise TimeoutError("Failed to receive valid SYN-ACK after multiple attempts.")

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
                        lista = message.split("|")
                    # Print de debug comentado - confirma receção de SYN-ACK
                    # print("RECEBEU O SYNACK CORRETO")

                except TimeoutError:
                    print("Nao deu para fazer Handshake na connection")  # Mensagem de erro - deveria ser mais descritiva

                # Send ACK
                # Print de debug comentado - mostra sequência do ACK enviado
                # print(f"Sending ACK: seq={seqinicial}")
                self.sock.sendto(
                    f"{self.ackkey}|{idAgent}|{seqinicial}|{seqinicial}|_|0|-.-".encode(),
                    (destAddress, destPort)
                )
                print("CONNECTION ESTABLISHED\n--------------")
                return  (destAddress,destPort),idAgent,seqinicial + 1,seqinicial + 1 # Handshake successful

            
        
            except TimeoutError:
                retries += 1
                print(f"Retrying SYN: ({retries}/{retryLimit})")
        
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
            print(f"Message : {message}\nFrom : {ip}:{port}")  # Print ativo - mostra mensagens inválidas
            lista = message.decode().split("|")
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
                if (lista[flagPos] == self.ackkey and 
                lista[idMissionPos] == idAgent and 
                lista[ackPos] == lista[seqPos]):
                    print("CONECTION ESTABLISHED\n---------------")
                    return (ip,port),idAgent,int(lista[seqPos]),int(lista[ackPos])
            except TimeoutError:
                self.sock.sendto("|".join(prevLista).encode(),(ip,port))

        
        
    def send(self,ip,port,requestType,idAgent,idMission,message):
        """
        Envia uma mensagem ou ficheiro através do protocolo MissionLink.
        Estabelece conexão, envia dados com confirmação e fecha conexão.
        
        Args:
            ip (str): Endereço IP do destinatário
            port (int): Porta do destinatário
            requestType (str): Tipo de pedido (R=Register, T=Task, M=Metrics)
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
                self.sock.sendto(self.formatMessage(requestType,self.datakey,idMission,seq,ack,message),(ip,port))
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
                        print("File name sent")
                        break
                except TimeoutError:
                    continue

            file = open(message,"r")
            buffer = file.read(self.limit.buffersize-self.getHeaderSize())
            i = 1
            while buffer:
                print(f"Iteration {i}")
                i+=1
                self.sock.sendto(self.formatMessage(requestType,self.datakey,idMission,seq,ack,buffer),(ip,port))
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
                except TimeoutError:
                    self.sock.sendto(self.formatMessage(requestType,self.datakey,idMission,seq,ack,buffer),(ip,port))
            # ANTES: Enviava FIN com o mesmo seq do último chunk (seq já incrementado no loop)
            # MUDANÇA: Incrementar seq antes de enviar FIN para garantir número de sequência diferente
            # PORQUÊ: 
            #   1. Garante que o FIN tem um número de sequência diferente do último dado
            #   2. Mais correto do ponto de vista do protocolo
            #   3. Evita ambiguidade entre último chunk e FIN
            # COMO: Incrementar seq e ack antes de enviar FIN
            seq += 1
            ack = seq
            # Código antigo (comentado):
            # # Código comentado - incremento de seq/ack não necessário
            # # DEVERIA estar a ser usado se quisermos incrementar seq antes de enviar FIN
            # # ONDE: Antes de enviar o pacote FIN para fechar conexão
            # # COMO: Descomentar estas linhas antes de self.sock.sendto(...self.finkey...)
            # # PORQUÊ: 
            # #   1. Garante que o FIN tem um número de sequência diferente do último dado
            # #   2. Mais correto do ponto de vista do protocolo
            # # NOTA: Atualmente não é necessário porque seq já foi incrementado no loop anterior
            # #       e o FIN usa o mesmo seq, o que funciona mas não é ideal
            # # seq+=1
            # # ack = seq
            self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
            while True:
                try:
                    text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                    lista = text.decode().split("|")
                    print(f"{len(text)} - 7")
                    print(f"{responseIp} - {ip}")
                    print(f"{responsePort} - {port}")
                    print(f"{lista[ackPos]} - {str(seq)}")
                    print(f"{lista[flagPos]} - {self.finkey}")
                    if(
                        len(lista) == 7 and
                        responseIp == ip and
                        responsePort == port and
                        lista[ackPos] == str(seq) and
                        lista[flagPos] == self.finkey
                    ):
                        seq += 1
                        ack = seq
                        print("Got the correct packet")
                        self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                        return True
                except TimeoutError:
                    self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                    

        else:
            chunks = self.splitMessage(message)

            # If chunks is a string, only a packet with data is sent
            # The next one is a connection closing one
            if isinstance(chunks,str):
                self.sock.sendto(self.formatMessage(requestType,self.datakey,idMission,seq,ack,chunks),(ip,port))
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
                            # ANTES: return True imediatamente após enviar FIN
                            # MUDANÇA: Implementar fechamento bidirecional completo (4-way handshake)
                            # PORQUÊ: 
                            #   1. Implementa fechamento de conexão completo (4-way handshake)
                            #   2. Garante que ambos os lados confirmam o fechamento
                            #   3. Mais robusto para garantir que a conexão está realmente fechada
                            # COMO: Após enviar FIN, aguardar ACK do FIN enviado OU FIN do outro lado
                            #       Se receber FIN do outro lado, responder com ACK e terminar
                            while True:
                                try:
                                    text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                                    lista = text.decode().split("|")
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
                                except TimeoutError:
                                    # Reenvia FIN se timeout (pode ser que o outro lado ainda não recebeu)
                                    self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                    continue
                            # Código antigo (comentado):
                            # return True
                            # # Código comentado - implementação alternativa de fechamento de conexão
                            # # DEVERIA estar a ser usado para garantir fechamento bidirecional da conexão
                            # # ONDE: Após enviar FIN e receber ACK, esperar pelo FIN do outro lado e responder com ACK
                            # # COMO: Descomentar este bloco em vez de apenas return True após enviar FIN
                            # # PORQUÊ:
                            # #   1. Implementa fechamento de conexão TCP completo (4-way handshake)
                            # #   2. Garante que ambos os lados confirmam o fechamento
                            # #   3. Mais robusto para garantir que a conexão está realmente fechada
                            # # NOTA: Tem um bug - lista[ackPos] == seq deveria ser lista[ackPos] == str(seq)
                            # #       e falta (ip,port) no último sendto
                            # # """
                            # # while True:
                            # #     try:
                            # #         text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                            # #         lista = text.decode().split("|")
                            # #         if(
                            # #             responseIp == ip and
                            # #             responsePort == port and
                            # #             lista[idMissionPos] == idMission and
                            # #             lista[ackPos] == str(seq) and  # BUG corrigido: era seq, deveria ser str(seq)
                            # #             lista[flagPos] == self.finkey
                            # #         ):
                            # #             seq += 1
                            # #             ack = seq
                            # #             self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,"\0"),(ip,port))  # BUG corrigido: faltava (ip,port)
                            # #             return "Message Sent"
                            # #     except TimeoutError:
                            # #         self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,"\0"),(ip,port))
                            # # """
                                    
                        continue
                    except TimeoutError:
                        print("Deu timeout")
                        self.sock.sendto(self.formatMessage(requestType,self.datakey,idMission,seq,ack,chunks),(ip,port))
                        continue
            # In case the message is big enough, 
            # we must send each element of the list
            i = 0
            while i != len(chunks):
                self.sock.sendto(self.formatMessage(requestType,self.datakey,idMission,seq,ack,chunks[i]),(ip,port))
                try:
                    response,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                    lista = response.decode().split("|")
                    print(f"EXPECTING - {seq}\nRECEIVED - {lista[ackPos]}")
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
                except TimeoutError:
                    print(f"\n\nResent the seq - {seq}")
                    self.sock.sendto(self.formatMessage(requestType,self.datakey,idMission,seq,ack,chunks[i]),(ip,port))
                    continue
            self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
            while True:
                try:
                    text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                    lista = text.decode().split("|")
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
            - 2 - request type
            - 3 - file name or the message in string
            - 4 - ip address
        """
        message = ""
        # Establish connection
        (ipDest,portDest),idAgent,seq,ack = self.acceptConnection()
        idMission = None  # Será extraído da primeira mensagem

        print(f"SEQ - {seq}\nACK - {ack}")        

        fileName = None
        requestType = ""

        # We get the first message with data to know if it is a message or a file 
        firstMessage = None
        while firstMessage == None:
            try:
                firstMessage,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
                lista = firstMessage.decode().split("|")
                if (
                    ip == ipDest and 
                    port == portDest and
                    lista[seqPos] == str(seq + 1)
                ):
                    idMission = lista[idMissionPos]  # Extrai idMission da primeira mensagem
                    requestType = lista[reqType]
                    seq += 1
                    ack = seq
                    if lista[messagePos].endswith(".json"):
                        print("File")
                        fileName = lista[messagePos]
                    else:
                        print("Message")
                        firstMessage = lista[messagePos]
                    self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                    break
            except TimeoutError:
                #print("Timed out on the first message")
                firstMessage = None
                continue

        prevMessage = firstMessage

        if fileName == None:
            # Catch packets until the fin packet arrives
            while True:
                # Try to receive a packet until timeout
                try:
                    chunks, (ip,port) = self.sock.recvfrom(self.limit.buffersize)
                    lista = chunks.decode().split("|")
                    print(f"EXPECTING - {ack + 1}\nRECEIVED - {lista[seqPos]}")
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
                            # ANTES: Retornava imediatamente após enviar FIN sem esperar confirmação
                            # MUDANÇA: Esperar pelo ACK do FIN enviado antes de retornar
                            # PORQUÊ: Garante que o outro lado recebeu e confirmou o FIN, fechamento mais robusto
                            # COMO: Aguardar receção de ACK com flag apropriada antes de return
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
                                        return [idAgent,idMission,requestType,message,ip]
                                except TimeoutError:
                                    # Reenvia FIN se não receber ACK
                                    self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                    continue
                            # Código antigo (comentado):
                            # _ ,_ = self.sock.recvfrom(self.limit.buffersize)
                            # return [idAgent,idMission,requestType,message,ip]
                        
                        # Código comentado - alternativa de formatação de mensagem
                        # Não é necessário porque prevMessage já contém a mensagem correta
                        # prevMessage = "|".join(lista)
                        # ANTES: self.sock.sendto(self.formatMessage(lista[reqType],self.ackkey,idMission,seq,ack,"\0"),(ip,port))
                        # MUDANÇA: Usar self.eofkey em vez de "\0" hardcoded
                        # PORQUÊ: Melhora manutenibilidade - se precisarmos mudar o EOF, mudamos apenas em um lugar
                        # COMO: Substituir "\0" por self.eofkey
                        self.sock.sendto(self.formatMessage(lista[reqType],self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                    



                # In case of a timeout, it means the
                # either the message did not reach the destination
                # or the message do not correspond to the expected sequence
                # So, to make sure, we sent the previous message that was supposed to be sent
                except TimeoutError:
                    if prevMessage != None:
                        self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                    continue


        ## Comentário explicativo sobre estratégia de escrita de ficheiros
        # Com retransmissão, há probabilidade de escrever o mesmo texto 2 vezes
        # Portanto, quando os chunks chegam, guardamos a mensagem antes de escrever
        # assim só quando o próximo chunk chega, guardamos o próximo e escrevemos o anterior
        # Esta estratégia previne duplicação de dados em caso de retransmissão
        else:
            file = open(self.storeFolder + fileName,"w")
            previous = None
            while True:
                try:
                    text,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
                    lista = text.decode().split("|")
                    if(
                        len(lista) == 7 and
                        lista[idMissionPos] == idMission and
                        ip == ipDest and
                        port == portDest and
                        lista[seqPos] == str(seq + 1) 
                    ):
                        seq += 1
                        ack = seq
                        # ANTES: Escrevia previous apenas quando recebia FIN
                        # MUDANÇA: Escrever chunk anterior antes de processar o atual (estratégia anti-duplicação)
                        # PORQUÊ: 
                        #   1. Implementa a estratégia descrita: escrever chunk anterior quando próximo chega
                        #   2. Previne duplicação em caso de retransmissão
                        #   3. Garante que todos os chunks são escritos, mesmo o último
                        # COMO: Escrever previous antes de atualizar para lista[messagePos]
                        if previous != None:
                            file.write(previous)
                        # Código antigo (comentado):
                        # # The packet is a Fin packet
                        # if previous != None:
                        #     file.write(previous)
                        if lista[flagPos] == self.finkey: # Verify this, can be correct
                                #print(f"SEQ SENT - {seq}\nACK SENT - {ack}")
                                #print(f"SEQ FROM LAST MESSAGE - {lista[seqPos]}\nACK FROM LAST MESSAGE - {lista[ackPos]}")
                                file.close()
                                self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                while True:
                                    try:
                                        text,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
                                        print(f"{len(lista)} - 7")
                                        print(f"{ipDest} - {ip}")
                                        print(f"{portDest} - {port}")
                                        print(f"{lista[seqPos]} - {str(seq)}")
                                        print(f"{lista[flagPos]} - {self.finkey}")
                                        if(
                                            len(lista) == 7 and
                                            ip == ipDest and
                                            port == portDest and 
                                            lista[idMissionPos] == idMission and
                                            lista[seqPos] == str(seq) and
                                            lista[flagPos] == self.finkey
                                        ):
                                            print("Supposedly ended")
                                            return [idAgent,idMission,requestType,fileName,ip]
                                    except TimeoutError:
                                        self.sock.sendto(self.formatMessage(None,self.finkey,idMission,seq,ack,self.eofkey),(ip,port))
                                        continue
                        
                        # ANTES: previous era atualizado sem escrever o chunk anterior primeiro
                        #        (exceto quando recebia FIN)
                        # MUDANÇA: Escrever previous antes de atualizar (já implementado acima)
                        # PORQUÊ: Previne duplicação e garante que todos os chunks são escritos
                        # COMO: A escrita já foi movida para antes desta linha (ver código acima)
                        # Código antigo (comentado):
                        # # Código comentado - escrita de chunk anterior
                        # # DEVERIA estar a ser usado para escrever o chunk anterior antes do atual
                        # # ONDE: Antes de processar o chunk atual, escrever o anterior
                        # # COMO: Descomentar estas linhas antes de previous = lista[messagePos]
                        # # PORQUÊ: 
                        # #   1. Implementa a estratégia descrita acima (escrever chunk anterior quando próximo chega)
                        # #   2. Previne duplicação em caso de retransmissão
                        # # NOTA: Atualmente o código escreve previous apenas quando recebe FIN,
                        # #       o que pode perder o último chunk se não houver FIN
                        # if previous != None: 
                        #     file.write(previous)
                        previous = lista[messagePos]
                        
                        self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))

                        
                except TimeoutError:
                    self.sock.sendto(self.formatMessage(None,self.ackkey,idMission,seq,ack,self.eofkey),(ip,port))
                    continue


    # Método não utilizado - o servidor usa recv() diretamente em vez deste método
    # DEVERIA estar a ser usado no NMS_Server para receber mensagens continuamente
    # ONDE: No NMS_Server.py, método recvMissionLink(), em vez de chamar self.missionLink.recv() diretamente
    # COMO: Criar um thread ou loop que chama self.missionLink.startServer() para processar múltiplas conexões
    # PORQUÊ:
    #   1. Permite processar múltiplas conexões em paralelo
    #   2. Melhor organização do código do servidor
    #   3. Facilita escalabilidade para múltiplos rovers simultâneos
    # NOTA: Este método chama receivePacket() que NÃO EXISTE
    #       receivePacket() DEVERIA ser implementado ou substituído por recv()
    # def startServer(self):
    #     """
    #     Inicia o servidor MissionLink em modo loop infinito.
    #     Liga o socket e fica à espera de receber pacotes continuamente.
    #     """
    #     self.sock.bind((self.serverAddress,self.port))
    #     while True:
    #         print(self.receivePacket())  # ERRO: receivePacket() não existe, deveria ser recv()
    #         self.seqNum = 0  # ERRO: self.seqNum não está definido
