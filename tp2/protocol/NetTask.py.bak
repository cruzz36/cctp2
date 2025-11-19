import socket
import os

class NetTask:
    def __init__(self,serverAddress,port,timeout = 1.5,connectionMax = 1024,storeFolder = "."):
        self.serverAddress = serverAddress
        self.port = port
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.settimeout(timeout)
        self.seqNum = 0
        self.connectionMax = connectionMax
        self.storeFolder = storeFolder

    #sendPacket
    def splitMessage(self,message):
        if len(message) > self.connectionMax - 7: return [message[i:i+self.connectionMax] for i in range(0,len(message),self.connectionMax)]
        else: return message

    def joinMessage(self,bytes):
        return "".join(bytes)





    def sendFile(self,fileName):
        #Enviar nome do ficheiro
        self.sock.sendto(fileName.encode(),(self.serverAddress,self.port))
        while self.recvACK() != 0:
            self.sock.sendto(fileName.encode(),(self.serverAddress,self.port))
        
        
        maxReadableSize = self.connectionMax - 7
        fileSize = os.stat(fileName).st_size
        counter = 0

        # O tamanho dos chunks a ler do ficheiro devem ser o mesmo que o tamanho da 
        # conexão menos o overhead de bytes para o número de sequência
        file = open(fileName,"rb")
        chunk = file.read(maxReadableSize)
        counter += len(chunk) - 7

        while chunk:
            # End Case
            #if chunk.endswith(b""):
            if len(chunk) < maxReadableSize or counter == fileSize:
                chunkToSend = f"{self.seqNum}|".encode()
                chunkToSend += chunk + b"EOF"
                self.sock.sendto(chunkToSend,(self.serverAddress,self.port))
                while self.recvFIN() != 0:
                    self.sock.sendto(chunkToSend(self.serverAddress,self.port))
                self.seqNum = 0
                break
            # Common case
            chunkToSend = f"{self.seqNum}|".encode()
            chunkToSend += chunk
            self.sock.sendto(chunkToSend,(self.serverAddress,self.port))
            # TODO - TROCAR RECVACK PARA N PRECISAR DE PASSAR ARGUMENTO
            ack = self.recvACK(self.seqNum) 
            while ack == None:
                self.sock.sendto(chunkToSend,(self.serverAddress,self.port))
                ack = self.recvACK(self.seqNum)
            self.seqNum += 1
            chunk = file.read(maxReadableSize)
            print(chunk)
            counter += len(chunk) - 5
        file.close()
        print("FILE SENT")

            
                



    def sendPacket(self,message,kind = None):
        # Dividir a mensagem em chunks com valor a preencher o máximo possível da conexão
        chunks = self.splitMessage(message)

        # Se a variável chunks for uma string, envia-se a string completa
        if isinstance(chunks,str):
            if kind != None:
                chunks = f"{kind}|{self.seqNum}|{chunks}EOF".encode()
            else:
                chunks = f"{self.seqNum}|{chunks}EOF".encode()

            self.sock.sendto(chunks,(self.serverAddress,self.port))
            fin = self.recvFIN()
            while fin != 0:
                self.sock.sendto(chunks,(self.serverAddress,self.port))
                fin = self.recvFIN()
            return "MESSAGE ARRIVED AT THE SERVER"
        

        # Ciclo trata do envio da mensagem
        for i in range(len(chunks)):
            # Formato da mensagem "2|mmmmmm"
            print(chunks[i])
            if i == 0 and kind != None:
                sendingChunk = f"{kind}|{self.seqNum}|{chunks[i]}".encode()
            else: 
                sendingChunk = f"{self.seqNum}|{chunks[i]}".encode()

            # Caso seja o ultimo chunk de mensagem
            if(i == len(chunks) - 1): 
                # Concatenar bytes de EOF
                sendingChunk += b"EOF"
                # Envio do chunk
                self.sock.sendto(sendingChunk,(self.serverAddress,self.port))
                print(f"Sent : {sendingChunk}")
                # Receção do FIN
                #ack = self.recvFIN()
                #while ack != 0: ack = self.recvFIN(self.seqNum)
                self.seqNum = 0
                break

            # Envio do chunk
            self.sock.sendto(sendingChunk,(self.serverAddress,self.port))
            print(f"Sent : {sendingChunk}")
            # Receção do acknoledgment
            ack = self.recvACK(self.seqNum)
            # Caso o ack não seja recebido ou seja um número incorreto 
            while ack == None: 
                self.sock.sendto(sendingChunk,(self.serverAddress,self.port))
                ack = self.recvACK(self.seqNum)

            # Quando receber o acknowledgement, incrementar o numero de sequencia
            self.seqNum += 1
        
        print("MESSAGE SENT")

    def receiveFile(self,fileName = None,returnAddress = None):
        if fileName == None:
            # Receber o nome do ficheiro e enviar ACK
            fileName,returnAddress = self.sock.recvfrom(self.connectionMax)
            print("FILE FOUND")
            fileName = fileName.decode("utf-8")
            
            fileName = self.storeFolder + fileName
        print(fileName)
        self.sendACK(returnAddress[0],returnAddress[1])

        file = open(self.storeFolder + fileName,"wb")
        buffer,returnAddress = self.sock.recvfrom(self.connectionMax)
        while buffer.endswith(b"EOF") == False:
            chunk = buffer.decode()
            text = chunk.split("|",1)
            receivedSeqNum = int(text[0])
            print(f"SEQ RECEIVED : {receivedSeqNum}")
            if self.seqNum == receivedSeqNum:
                file.write(text[1].encode())
                print(text[1])
                self.sendACK(returnAddress[0],returnAddress[1])
                self.seqNum += 1
            try:
                buffer,returnAddress = self.sock.recvfrom(self.connectionMax)
            except socket.timeout:
                print("CHUNK LOST")
        chunk = buffer.decode("utf-8")
        text = chunk.split("|",1)
        text[1] = text[1].replace("EOF","")
        print(text[1])
        file.write(text[1].encode())
        self.sendFIN(returnAddress[0],returnAddress[1])
        file.close()
        print("FILE RECEIVED")




            
    # Only use receivePacket as it 
    def receivePacket(self):
        # newMessage : Lista para armazenar os chunks
        kind = None
        newMessage = []
        
        # 
        data, returnAddress = self.sock.recvfrom(1024)

        # A primeira mensagem deve ser do formato
        # "R|0|message"
        #  0 1    2
        message = data.decode()
        type = message.split("|",2)
        print(type)
        kind = type[0]
        if type[2].endswith(".json"):
            return kind,self.receiveFile(type[2],returnAddress)
        
        

        data, returnAddress = self.sock.recvfrom(1024)
        while data.endswith(b"EOF") == False:
            message = data.decode("utf-8")

            seqReceived = message.split("|", 1)
            seq = int(seqReceived[0])
            
            if seq == self.seqNum: 
                newMessage.append(seqReceived[1])
                self.sendACK(returnAddress[0],returnAddress[1])
                self.seqNum += 1
            
            try:
                data,returnAddress = self.sock.recvfrom(1024)
            except socket.timeout:
                print("Chunk Lost")

        message = data.decode("utf-8")
        seqReceived = message.split("|",2)
        print(f"RECEIVED : {seqReceived}")

        # Esta condição indica que a mensagem foi enviada de uma vez só
        if len(seqReceived) == 3:
            newMessage.append(seqReceived[1])
            self.sendFIN(returnAddress[0],returnAddress[1])
            return kind,newMessage[0]
        newMessage.append(seqReceived[1].replace("EOF",""))
        self.sendFIN(returnAddress[0],returnAddress[1])
        return kind,self.joinMessage(newMessage)



    def recvACK(self,expected = None):
        try:
            data , _ = self.sock.recvfrom(1024)
            ack = int(data.decode("utf-8"))
            print(f"Received ACK {ack}")
            print(f"Expected : {expected}")
            if expected == None: return 0
            if ack == expected: return ack + 1
            elif ack < expected: return -1
            else: return None

        except socket.timeout:
            print("Timeout, no ACK received")
            return None
    
    def sendACK(self,address,port):
        self.sock.sendto(str(self.seqNum).encode(),(address,port))

    def sendFIN(self,client,port):
        self.sock.sendto(b"EOF",(client,port))

    def recvFIN(self):
        try:
            data,_ = self.sock.recvfrom(1024)
            if data.endswith(b"EOF"):
                return 0
            else: return 1
        except socket.timeout:
            print("TIMEOUT, NO FIN RECEIVED")
            return 2

    #def recvPacket(self,message):

    #start

