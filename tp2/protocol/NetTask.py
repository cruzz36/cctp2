import socket
from otherEntities import Limit


# [flag,idAgent,seq,ack,size,requestType,message]
#   0       1    2   3   4      5           6
flagPos = 0
idAgentPos = 1
seqPos = 2
ackPos = 3
sizePos = 4
reqType = 5
messagePos = 6


class NetTask:
    def __init__(self,serverAddress,storeFolder = "."):
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
        self.eofkey = '\0'

    
    def server(self):
        self.sock.bind((self.serverAddress,self.port))


    def getHeaderSize(self):
        # flag + | + idAgent + | + seq + | + ack + | + size + | + reqType + |
        return 1 + 1 + 3 + 1 + 4 + 1 + 4 + 1 + 4 + 1 + 1 + 1
    
    def formatMessage(self,requestType,flag,idAgent,seqNum,ackNum,message):
        if requestType != None: 
            return f"{flag}|{idAgent}|{seqNum}|{ackNum}|{len(message)}|{requestType}|{message}".encode()
        return f"{flag}|{idAgent}|{seqNum}|{ackNum}|{len(message)}|N|{message}".encode()
        

    #sendPacket
    def splitMessage(self,message):
        if len(message) > self.limit.buffersize - self.getHeaderSize(): return [message[i:i+self.limit.buffersize - self.getHeaderSize()] for i in range(0,len(message),self.limit.buffersize - self.getHeaderSize())]
        else: return message

    def joinMessage(self,bytes):
        return "".join(bytes)
    
    
    def receiveSYNACK(self, idAgent, destAddress, destPort, expectedSeq, retryLimit=5):
        retries = 0
        while retries < retryLimit:
            try:
                # Wait for SYN-ACK
                message, (ip, porta) = self.sock.recvfrom(self.limit.buffersize)
                message = message.decode()
                parts = message.split("|")
                if len(parts) != 7:
                    print("Mensagem com tamanho diferente")
                    raise ValueError("Malformed message")
                
                flag, receivedIdAgent, seq, ack, *_ = parts
                
                if (self.verifySYNACK(flag, destAddress, destPort, ip, porta) and
                    self.verifyIdAgent(idAgent, receivedIdAgent) and
                    self.verifyACKnum(expectedSeq,ack)):
                    return True  # Valid SYN-ACK received
                
            except (TimeoutError, ValueError):
                retries += 1
                print(message)
                print(f"Timeout or invalid message. Retrying... ({retries}/{retryLimit})")
        
        raise TimeoutError("Failed to receive valid SYN-ACK after multiple attempts.")

    def startConnection(self, idAgent, destAddress, destPort, retryLimit=5):
        seqinicial = 100 #random.randint(0, 10000)
        retries = 0
        
        while retries < retryLimit:
            try:
                # Send SYN
                self.sock.sendto(
                    f"{self.synkey}|{idAgent}|{seqinicial}|0|_|0|-.-".encode(),
                    (destAddress, destPort)
                )
                #print("SYN ENVIADO")
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
                    #print("RECEBEU O SYNACK CORRETO")

                except TimeoutError:
                    print("Nao deu")

                # Send ACK
                #print(f"Sending ACK: seq={seqinicial}")
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


    # The must be run usually by a server
    # It receives a connection request and respond, forming an handshake
    # It returns the ip address, port, agentID, sequential number and the acknowledge number
    # The sequential number and the acknowledge number must be the same
    def acceptConnection(self):
        # RECEBER O SYN
        message,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
        #print(f"Message : {message}\nFrom : {ip}:{port}")
        lista = message.decode().split("|")
        while lista[flagPos] != self.synkey:
            message,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
            print(f"Message : {message}\nFrom : {ip}:{port}")
            lista = message.decode().split("|")
        idAgent = lista[idAgentPos]
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
                lista[idAgentPos] == idAgent and 
                lista[ackPos] == lista[seqPos]):
                    print("CONECTION ESTABLISHED\n---------------")
                    return (ip,port),idAgent,int(lista[seqPos]),int(lista[ackPos])
            except TimeoutError:
                self.sock.sendto("|".join(prevLista).encode(),(ip,port))

        
        
    ## Method is used to send either strings or files
    # Shall return True when the message is sent
    def send(self,ip,port,requestType,idAgent,message):
        # The connection starts with an handshake to assure it has a somewhat reliable 
        # transfers between the client and the server 
        _,idAgent,seq,ack = self.startConnection(idAgent,ip,port)

        #print(f"SEQ - {seq}\nACK - {ack}")

        if message.endswith(".json"):
            # First cycle is to send the filename
            while True:
                self.sock.sendto(self.formatMessage(requestType,self.datakey,idAgent,seq,ack,message),(ip,port))
                try:
                    text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                    lista = text.decode().split("|")
                    if(
                        responseIp == ip and
                        responsePort == port and
                        lista[flagPos] == self.ackkey and
                        lista[idAgentPos] == idAgent and
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
                self.sock.sendto(self.formatMessage(requestType,self.datakey,idAgent,seq,ack,buffer),(ip,port))
                try:
                    text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                    lista = text.decode().split("|")
                    if(
                        responseIp == ip and
                        responsePort == port and
                        lista[idAgentPos] == idAgent and
                        lista[flagPos] == self.ackkey and
                        lista[ackPos] == str(seq)
                    ):
                        seq += 1
                        ack = seq
                        buffer = file.read(self.limit.buffersize - self.getHeaderSize())
                except TimeoutError:
                    self.sock.sendto(self.formatMessage(requestType,self.datakey,idAgent,seq,ack,buffer),(ip,port))
            #seq+=1
            #ack = seq
            self.sock.sendto(self.formatMessage(None,self.finkey,idAgent,seq,ack,"\0"),(ip,port))
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
                        self.sock.sendto(self.formatMessage(None,self.ackkey,idAgent,seq,ack,"\0"),(ip,port))
                        return True
                except TimeoutError:
                    self.sock.sendto(self.formatMessage(None,self.finkey,idAgent,seq,ack,"\0"),(ip,port))
                    

        else:
            chunks = self.splitMessage(message)

            # If chunks is a string, only a packet with data is sent
            # The next one is a connection closing one
            if isinstance(chunks,str):
                self.sock.sendto(self.formatMessage(requestType,self.datakey,idAgent,seq,ack,chunks),(ip,port))
                while True: 
                    try:
                        text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                        lista = text.decode().split("|")
                        #print(lista)
                        if (responseIp == ip and
                            responsePort == port and
                            lista[idAgentPos] == idAgent and
                            lista[ackPos] == str(seq) and 
                            lista[flagPos] == self.ackkey
                            ):
                            seq += 1
                            ack = seq
                            self.sock.sendto(self.formatMessage(None,self.finkey,idAgent,seq,ack,"\0"),(ip,port))
                            return True
                            """
                            while True:
                                try:
                                    text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                                    lista = text.decode().split("|")
                                    if(
                                        responseIp == ip and
                                        responsePort == port and
                                        lista[idAgentPos] == idAgent and
                                        lista[ackPos] == seq and
                                        lista[flagPos] == self.finkey
                                    ):
                                        seq += 1
                                        ack = seq
                                        self.sock.sendto(self.formatMessage(None,self.ackkey,idAgent,seq,ack,"\0"))
                                        return "Message Sent"
                                except TimeoutError:
                                    self.sock.sendto(self.formatMessage(None,self.finkey,idAgent,seq,ack,"\0"),(ip,port))
                            """
                                    
                        continue
                    except TimeoutError:
                        print("Deu timeout")
                        self.sock.sendto(self.formatMessage(requestType,self.datakey,idAgent,seq,ack,chunks),(ip,port))
                        continue
            # In case the message is big enough, 
            # we must send each element of the list
            i = 0
            while i != len(chunks):
                self.sock.sendto(self.formatMessage(requestType,self.datakey,idAgent,seq,ack,chunks[i]),(ip,port))
                try:
                    response,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                    lista = response.decode().split("|")
                    print(f"EXPECTING - {seq}\nRECEIVED - {lista[ackPos]}")
                    if(
                        len(lista) == 7 and
                        responseIp == ip and
                        responsePort == port and
                        lista[idAgentPos] == idAgent and
                        lista[ackPos] == str(seq) and 
                        lista[flagPos] == self.ackkey
                    ):
                        seq += 1
                        ack = seq
                        i += 1
                        continue
                except TimeoutError:
                    print(f"\n\nResent the seq - {seq}")
                    self.sock.sendto(self.formatMessage(requestType,self.datakey,idAgent,seq,ack,chunks[i]),(ip,port))
                    continue
            self.sock.sendto(self.formatMessage(None,self.finkey,idAgent,seq,ack,"\0"),(ip,port))
            while True:
                try:
                    text,(responseIp,responsePort) = self.sock.recvfrom(self.limit.buffersize)
                    lista = text.decode().split("|")
                    if(
                        responseIp == ip and
                        responsePort == port and
                        lista[idAgentPos] == idAgent and
                        lista[ackPos] == str(seq) and
                        lista[flagPos] == self.finkey
                    ):
                        return True                  
                except TimeoutError:
                    self.sock.sendto(self.formatMessage(None,self.finkey,idAgent,seq,ack,"\0"),(ip,port))
                    
                



    # Method to receive messages/files
    # Will either return the message or the name of the transfered file
    # along with the agent ID 
    def recv(self):
        """
        Returns a list with 4 items by order
            - 0 - agentId
            - 1 - request type
            - 2 - file name  or the message in string
            - 3 - ip address
        """
        message = ""
        # Establish connection
        (ipDest,portDest),idAgent,seq,ack = self.acceptConnection()

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
                    lista[idAgentPos] == idAgent and
                    lista[seqPos] == str(seq + 1)
                ):
                    requestType = lista[reqType]
                    seq += 1
                    ack = seq
                    if lista[messagePos].endswith(".json"):
                        print("File")
                        fileName = lista[messagePos]
                    else:
                        print("Message")
                        firstMessage = lista[messagePos]
                    self.sock.sendto(self.formatMessage(None,self.ackkey,idAgent,seq,ack,"\0"),(ip,port))
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
                    # the agent id is the same of the connection determined id
                    # the seq is greater 1 unit the whats stored on receiver side
                    # the IP address and Port must be the same
                    if(
                        len(lista) == 7 and
                        lista[idAgentPos] == idAgent and 
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
                            #print(lista)
                            #print("Received the end connection packet")
                            self.sock.sendto(self.formatMessage(None,self.finkey,idAgent,seq,ack,"\0"),(ip,port))
                            # Eventually is necessary to add a response with ACK
                            #_ ,_ = self.sock.recvfrom(self.limit.buffersize)
                            return [idAgent,requestType,message,ip]
                        
                        # The response to a normal message
                        #prevMessage = "|".join(lista)
                        self.sock.sendto(self.formatMessage(lista[reqType],self.ackkey,idAgent,seq,ack,"\0"),(ip,port))
                    



                # In case of a timeout, it means the
                # either the message did not reach the destination
                # or the message do not correspond to the expected sequence
                # So, to make sure, we sent the previous message that was supposed to be sent
                except TimeoutError:
                    if prevMessage != None:
                        self.sock.sendto(self.formatMessage(None,self.ackkey,idAgent,seq,ack,"\0"),(ip,port))
                    continue


        ## With retransmission
        # there is the probability of writing 2 times the same text
        # Therefore, has the chunks arrive, we store the message before writing
        # so only when the next chunk arrives, the next chunk is store and the other is written
        else:
            file = open(self.storeFolder + fileName,"w")
            previous = None
            while True:
                try:
                    text,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
                    lista = text.decode().split("|")
                    if(
                        len(lista) == 7 and
                        lista[idAgentPos] == idAgent and
                        ip == ipDest and
                        port == portDest and
                        lista[seqPos] == str(seq + 1) 
                    ):
                        seq += 1
                        ack = seq
                        # The packet is a Fin packet
                        if previous != None:
                            file.write(previous)
                        if lista[flagPos] == self.finkey: # Verify this, can be correct
                                #print(f"SEQ SENT - {seq}\nACK SENT - {ack}")
                                #print(f"SEQ FROM LAST MESSAGE - {lista[seqPos]}\nACK FROM LAST MESSAGE - {lista[ackPos]}")
                                file.close()
                                self.sock.sendto(self.formatMessage(None,self.finkey,idAgent,seq,ack,"\0"),(ip,port))
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
                                            lista[idAgentPos] == idAgent and
                                            lista[seqPos] == str(seq) and
                                            lista[flagPos] == self.finkey
                                        ):
                                            print("Supposedly ended")
                                            return [idAgent,requestType,fileName,ip]
                                    except TimeoutError:
                                        self.sock.sendto(self.formatMessage(None,self.finkey,idAgent,seq,ack,"\0"),(ip,port))
                                        continue
                        
                        #if previous != None: 
                        #    file.write(previous)

                        previous = lista[messagePos]
                        
                        self.sock.sendto(self.formatMessage(None,self.ackkey,idAgent,seq,ack,"\0"),(ip,port))

                        
                except TimeoutError:
                    self.sock.sendto(self.formatMessage(None,self.ackkey,idAgent,seq,ack,"\0"),(ip,port))
                    continue


    def startServer(self):
        self.sock.bind((self.serverAddress,self.port))
        while True:
            print(self.receivePacket())
            self.seqNum = 0
