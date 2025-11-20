import socket
from otherEntities import Limit


# Variáveis não utilizadas - formato documentado não implementado
# idAgentPos = 0
# taskidPos = 1
# flagPos = 2
# messagePos = 3

lenMessageSize = 4

class TelemetryStream:
    """
    Protocolo TelemetryStream (TS) - Protocolo aplicacional sobre TCP para transmissão
    contínua de dados de monitorização dos rovers para a Nave-Mãe.
    Message format : idAgent|task_id|flag|message
    """
    def __init__(self,ip,storefolder = ".",limit = 1024):
        """
        Inicializa o protocolo TelemetryStream.
        
        Args:
            ip (str): Endereço IP do servidor
            storefolder (str, optional): Pasta onde armazenar ficheiros recebidos. Defaults to "."
            limit (int, optional): Tamanho do buffer em bytes. Defaults to 1024
        """
        self.ip = ip
        self.port = 8081
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind((self.ip,self.port))
        except OSError:
            None
        if storefolder.endswith("/"): self.storefolder = storefolder
        else: self.storefolder = f"{storefolder}/"
        self.limit = Limit.Limit(limit)
        # Flags não utilizadas - formato documentado não implementado
        # self.flagend = "F"
        # self.flagdata = "D"

    def server(self):
        """
        Inicia o servidor TelemetryStream em modo loop infinito.
        Aceita conexões TCP, recebe dados de telemetria e fecha a conexão.
        """
        self.socket.listen()
        while True:
            clientSocket,(ip,_) = self.socket.accept()
            print(self.recv(clientSocket,ip,self.port))
            clientSocket.close()
        
    # Método não utilizado - calcula tamanho do cabeçalho para formato documentado não implementado
    # DEVERIA estar a ser usado se o formato idAgent|task_id|flag|message fosse implementado
    # ONDE: No método send() e recv() para calcular espaço disponível para dados
    # COMO: Chamar self.getHeaderSize(idAgent, taskid) antes de enviar/receber para saber tamanho do cabeçalho
    # PORQUÊ:
    #   1. Permite calcular corretamente o tamanho máximo de dados por pacote
    #   2. Necessário se implementar o formato documentado no PDF
    #   3. Melhor gestão de buffers e fragmentação
    # NOTA: O formato atual não usa este cabeçalho - envia tamanho do nome (4 bytes) + nome + conteúdo
    # def getHeaderSize(self,idAgent,taskid):
    #     """- \'|' - 1  bytes
    #        - idAgent - 4  bytes
    #        - task_id - 4 + 3 bytes
    #        - flag - 1 bytes
    #     """
    #     #return 3 + 4 + 7 + 1
    #     return len(f"{idAgent}|{taskid}|D|")


    def formatInteger(self,num):
        """
        Formata um número inteiro como string com 4 dígitos, preenchendo com zeros à esquerda.
        
        Args:
            num (int): Número a formatar
            
        Returns:
            str: String com 4 dígitos
        """
        line = str(num)
        displacement = 4 - len(line)
        for i in range(displacement):
            line = "0" + line
        return line

    def recv(self,clientSock:socket.socket,ip,port):
        """
        Recebe dados de telemetria de um cliente através de uma conexão TCP.
        Primeiro recebe o tamanho do nome do ficheiro (4 bytes), depois o nome do ficheiro,
        e finalmente o conteúdo do ficheiro.
        
        Args:
            clientSock (socket.socket): Socket TCP do cliente conectado
            ip (str): Endereço IP do cliente
            port (int): Porta do cliente
            
        Returns:
            bytes: Nome do ficheiro recebido
        """ 

        message = clientSock.recv(lenMessageSize)
        fileNameLen = int(message.decode())

        filename = clientSock.recv(fileNameLen)

        file = open(f"{self.storefolder}{filename.decode()}","w")

        message = clientSock.recv(self.limit.buffersize)

        while message != b"":
            file.write(message.decode())
            message = clientSock.recv(self.limit.buffersize)
        file.close()
        return filename
                


    def send(self,ip,message:str):
        """
        Envia um ficheiro de telemetria para o servidor através de TCP.
        Primeiro envia o tamanho do nome do ficheiro, depois o nome, e finalmente o conteúdo.
        
        Args:
            ip (str): Endereço IP do servidor destinatário
            message (str): Caminho do ficheiro a enviar
            
        Returns:
            bool: True se o ficheiro foi enviado com sucesso
        """
        self.socket.connect((ip,self.port))
        #self.reconnect(ip)
        length = self.formatInteger(len(message))
        print(length)
        self.socket.sendall(length.encode())

        self.socket.sendall(message.encode())
        file = open(message,"r")

        buffer = file.read(self.limit.buffersize)
        while buffer != "":
            self.socket.sendall(buffer.encode())
            buffer = file.read(self.limit.buffersize)
        
        file.close()
        self.endConnection()
        print("Sent")
        return True
        


    # Método alternativo de servidor não utilizado - implementação diferente de server()
    # DEVERIA estar a ser usado se quisermos manter múltiplas conexões abertas simultaneamente
    # ONDE: Substituir o método server() atual que fecha conexões imediatamente
    # COMO: Usar este método em vez de server() no NMS_Server.recvTelemetry()
    # PORQUÊ:
    #   1. Permite manter conexões TCP abertas para múltiplos rovers simultaneamente
    #   2. Melhor para transmissão contínua de telemetria sem reestabelecer conexão
    #   3. Mais eficiente para comunicação frequente
    # NOTA: A implementação atual (server()) fecha a conexão após cada receção, 
    #       este método manteria conexões abertas mas requer gestão de threads
    # def listen(self):
    #     self.socket.bind((self.ip,self.port))
    #     self.socket.listen()
    #     print(f"Server listening on {self.ip}:{self.port}...")
    #     
    #     while True:
    #         clientSocket, address = self.socket.accept()
    #         print(f"Connection established with {address}")
    #         
    #         try:
    #             while True:
    #                 data = clientSocket.recv(1024)
    #                 
    #                 if not data:
    #                     print(f"Connection closed by {address}")
    #                     break  # Exit loop if the client disconnects
    #
    #                 try:
    #                     decoded_data = data.decode()
    #                     print(f"Received data: {decoded_data}")
    #                     # Process the decoded_data here, e.g., store or handle the message
    #                 except UnicodeDecodeError:
    #                     print("Received invalid data, skipping...")
    #                     continue  # Skip to the next iteration if decoding fails
    #
    #         except Exception as e:
    #             print(f"Error with client {address}: {e}")
    #         finally:
    #             clientSocket.close()
    #             print(f"Connection with {address} closed.")

    # Método não utilizado - implementação alternativa para envio de alertas
    # DEVERIA estar a ser usado para enviar alertas em formato texto simples em vez de ficheiros
    # ONDE: No NMS_Agent quando condições de telemetria são excedidas, em vez de criar ficheiro JSON
    # COMO: Chamar self.telemetryStream.sendAlert(idAgent, metrics_dict, serverIP) 
    #       em vez de criar ficheiro e chamar send()
    # PORQUÊ:
    #   1. Mais rápido para alertas simples (não precisa criar ficheiro)
    #   2. Formato mais compacto para alertas urgentes
    #   3. Menos overhead de I/O
    # NOTA: Tem problemas:
    #   - Usa sendto() (UDP) mas TelemetryStream é TCP - deveria usar sendall()
    #   - Referencia self.serverPort que não existe - deveria ser self.port
    #   - Formato diferente do atual (JSON em ficheiros)
    # def sendAlert(self, id, metrics,ip):
    #     # Parse metrics into a string
    #     parsedMetrics = ";".join([f"{metric}={value}" for metric, value in metrics])
    #     message = f"{id}|{parsedMetrics}"
    #
    #     try:
    #         # Attempt to send the message
    #         self.socket.sendto(message.encode(),(ip,self.serverPort))  # ERRO: sendto é UDP, deveria ser sendall para TCP
    #         print(f"Sent alert: {message}")
    #     except (BrokenPipeError, ConnectionResetError):
    #         # Connection issues, handle reconnection
    #         print("Connection lost, attempting to reconnect...")
    #         self.reconnect()  # ERRO: reconnect() não existe ou não está implementado corretamente
    #         try:
    #             self.socket.send(message.encode())
    #             print(f"Sent alert after reconnect: {message}")
    #         except Exception as error:
    #             print(f"Failed to send alert after reconnect: {error}")
    #     except Exception as error:
    #         # General exception handling
    #         print(f"Failed to send alert: {error}")

    # Método não utilizado - nunca é chamado no código
    # def reconnect(self,ip):
    #     """
    #     Reconecta o socket TCP ao servidor após uma desconexão.
    #     
    #     Args:
    #         ip (str): Endereço IP do servidor
    #         
    #     Note:
    #         Este método parece ter uma referência a self.serverPort que pode não existir.
    #     """
    #     # Close existing socket and create a new one
    #     if self.socket is not None:
    #         self.socket.close()
    #     self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     try:
    #         self.socket.connect((ip, self.serverPort))
    #         print("Reconnected successfully.")
    #     except Exception as error:
    #         print(f"Failed to reconnect: {error}")
    #         self.socket = None  # Ensure socket is None if reconnection fails

    def endConnection(self):
        """
        Fecha a conexão TCP atual.
        """
        if self.socket is not None:
            self.socket.close()
            print("Connection closed.")