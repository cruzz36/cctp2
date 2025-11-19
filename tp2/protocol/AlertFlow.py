import socket
from otherEntities import Limit


idAgentPos = 0
taskidPos = 1
flagPos = 2
messagePos = 3

lenMessageSize = 4

class AlertFlow:
    """
    Message format : idAgent|task_id|flag|message
    """
    def __init__(self,ip,storefolder = ".",limit = 1024):
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
        self.flagend = "F"
        self.flagdata = "D"

    def server(self):
        self.socket.listen()
        while True:
            clientSocket,(ip,_) = self.socket.accept()
            print(self.recv(clientSocket,ip,self.port))
            clientSocket.close()
        
    #def getHeaderSize(self,idAgent,taskid):
    #    """- \'|' - 1  bytes
    #       - idAgent - 4  bytes
    #       - task_id - 4 + 3 bytes
    #       - flag - 1 bytes
    #    """
    #    #return 3 + 4 + 7 + 1
    #    return len(f"{idAgent}|{taskid}|D|")


    def formatInteger(self,num):
        line = str(num)
        displacement = 4 - len(line)
        for i in range(displacement):
            line = "0" + line
        return line

    def recv(self,clientSock:socket.socket,ip,port):
        """
        Method to receive an alert from a given client\\
        Returns:
            - filename  
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
        


    #def listen(self):
    #    self.socket.bind((self.ip,self.port))
    #    self.socket.listen()
    #    print(f"Server listening on {self.ip}:{self.port}...")
    #    
    #    while True:
    #        clientSocket, address = self.socket.accept()
    #        print(f"Connection established with {address}")
    #        
    #        try:
    #            while True:
    #                data = clientSocket.recv(1024)
    #                
    #                if not data:
    #                    print(f"Connection closed by {address}")
    #                    break  # Exit loop if the client disconnects
    #
    #                try:
    #                    decoded_data = data.decode()
    #                    print(f"Received data: {decoded_data}")
    #                    # Process the decoded_data here, e.g., store or handle the message
    #                except UnicodeDecodeError:
    #                    print("Received invalid data, skipping...")
    #                    continue  # Skip to the next iteration if decoding fails
    #
    #        except Exception as e:
    #            print(f"Error with client {address}: {e}")
    #        finally:
    #            clientSocket.close()
    #            print(f"Connection with {address} closed.")

    #def sendAlert(self, id, metrics,ip):
    #    # Parse metrics into a string
    #    parsedMetrics = ";".join([f"{metric}={value}" for metric, value in metrics])
    #    message = f"{id}|{parsedMetrics}"
    #
    #    try:
    #        # Attempt to send the message
    #        self.socket.sendto(message.encode(),(ip,self.serverPort))
    #        print(f"Sent alert: {message}")
    #    except (BrokenPipeError, ConnectionResetError):
    #        # Connection issues, handle reconnection
    #        print("Connection lost, attempting to reconnect...")
    #        self.reconnect()
    #        try:
    #            self.socket.send(message.encode())
    #            print(f"Sent alert after reconnect: {message}")
    #        except Exception as error:
    #            print(f"Failed to send alert after reconnect: {error}")
    #    except Exception as error:
    #        # General exception handling
    #        print(f"Failed to send alert: {error}")

    def reconnect(self,ip):
        # Close existing socket and create a new one
        if self.socket is not None:
            self.socket.close()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((ip, self.serverPort))
            print("Reconnected successfully.")
        except Exception as error:
            print(f"Failed to reconnect: {error}")
            self.socket = None  # Ensure socket is None if reconnection fails

    def endConnection(self):
        if self.socket is not None:
            self.socket.close()
            print("Connection closed.")