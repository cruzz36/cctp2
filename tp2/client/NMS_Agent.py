import socket
from protocol import NetTask,AlertFlow
from otherEntities import Device
import os
import subprocess
import time
import psutil


"""
    Esta classe deve poder medir :
        bandwith
        jitter (iperf)
        packet loss (iperf)
        latency (ping)

    iperf Tutorial:
        iperf -u -f B -o filename.* ... - protocolo udp, formato em Bytes,output para ficheiro 
"""
def removeNulls(text):
    while True:
        try:
            text = text.remove("")
        except Exception as e:
            break
    return text

class NMS_Agent:
    def __init__(self,serverAddress,frequency = 1,storeFolder = "."):
        self.id = socket.gethostname()
        self.ipAddress = self.getinterfaces()[0].split(" ")[1]
        self.serverAddress = serverAddress
        self.netTask = NetTask.NetTask(self.ipAddress,storeFolder)
        self.alertFlow = AlertFlow.AlertFlow(self.ipAddress,storeFolder) #tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connections = self.getinterfacesNames(self.getinterfaces())
        self.tasks = dict()
        self.frequency = frequency

    def sendMetrics(self,ip,filename:str):
        lista = filename.split("_")
        iter = lista[3].split(".")[0]
        idAgent = lista[2]
        self.netTask.send(ip,self.netTask.port,self.netTask.sendMetrics,idAgent,filename)
        reply = self.netTask.recv()
        while reply[1] != self.netTask.ackkey and reply[2] != iter:
            self.netTask.send(ip,self.netTask.port,self.netTask.sendMetrics,idAgent,filename)
            reply = self.netTask.recv()
            
    def register(self,ip):
        self.netTask.send(ip,self.netTask.port,self.netTask.registerAgent,self.id,"\0")
        lista = self.netTask.recv()
        while lista[1] != self.netTask.ackkey and lista[0] != self.id:
            self.netTask.send(ip,self.netTask.port,self.netTask.registerAgent,self.id,"\0")
            lista = self.netTask.recv()


    def recvNetTask(self):
        lista = self.netTask.recv()
        if lista[1] == self.netTask.taskRequest:
            taskId = lista[2].split(".")[0]
            if self.tasks.get(taskId) != None:
                self.tasks[taskId] = lista[2]
            self.netTask.send(lista[3],self.netTask.port,self.netTask.ackkey,self.id,taskId)
        

    def alertServer(self,ip,message):
        self.alertFlow.send(ip,message)
    
    def parseFile(self,file):
        self.devices = Device.Device(file)

    def getConnections(self):
        message = f""
        lista = self.getinterfaces()
        size = len(lista)
        if size == 0: return None
        message += f"{lista[0]}|"
        for a in lista:
            if lista[size] != a:
                message += f"{a}|"
                continue
            message += f"{a}\0"
        return message
    
    def getBandwidth(self,serverip,role,duration,transport,frequency):
        """
        :return [bandwidth,jitter,packet_loss]
        """

        try:
            if transport == "UDP" :
                output = os.popen(f"iperf -{role} {serverip} -u -t {frequency} -i {frequency}").read()
            else: output = os.popen(f"iperf -{role} -t {duration} -i {frequency}")


            # Separar output em linhas
            items = output.split("\n")

            # Remover os casos em que existem dois espaços consecutivos
            items.remove("")

            try:
                print("Retornou in order")
                # Apenas obter a ultima linha
                final = items[-1]


                # Da ultima linha reter os elementos posteriores à posição 9
                final = final.split(" ")[11:]

                # Remover possiveis caracteres nulos
                while True:
                    try:
                        final.remove("")
                    except:
                        break


                # Remover o numero de pacotes enviados
                final.pop(len(final) - 2)
                final.pop(len(final) - 2)

                final[0] = " ".join(final[0:2])
                final.pop(1)

                final[1] = " ".join(final[1:3])
                final.pop(len(final)-2)

                # Inverter a lista para obter a disposicao desejada 
                return final
            except:
                print("Return out of order")
                final = items[-2]

                final = final.split(" ")[11:]

                while True:
                    try:
                        final.remove("")
                    except:
                        break 

                final.pop(len(final) - 2)
                final.pop(len(final) - 2)

                final[0] = " ".join(final[0:2])
                final.pop(1)

                final[1] = " ".join(final[1:3])
                final.pop(len(final)-2)

                return final
        except:
            return None


    def getLatency(self,address,packetCount = 3,interval = 1):
        """
        Returns the average rtt given by the ping command
        """

        output = os.popen(f"ping {address} -c {packetCount} -i {interval} -W {self.frequency}").read()

        # Separar output em linhas
        items = output.split("\n")

        # Remover os casos em que existem dois espaços consecutivos
        while True:
            try:
                items.remove("")
            except:
                break

        # Apenas obter as 2 primeiras linhas
        items.reverse()
        items = items[0:2]

        final = items[0]
        final = final.split(" ")
        final = final[3:]
        aux = final[0].split("/")[1]

        return aux
        
    def getcpu(self):
        return psutil.cpu_percent()
    
    def getram(self):
        return psutil.virtual_memory()[2]

    def getinterfacesNames(self,interfaces):
        names = set()
        i = 0
        for a in interfaces:
            name = a.split(" ")
            names.add(name[0])
            i+=1
        return names
 
    def getinterfaces(self):
        text = os.popen("ip -o -4 route show | awk '{print $3,$9}'").read()
        text = text.split("\n")
        removeNulls(text)
        return text[1:]
    
    def interfaceStatsCheckpoint(self,interface):
        return psutil.net_io_counters(pernic = True)[interface]

        
    def get_packet_rate(self,net1,net2):
        rx_rate = (net2.packets_recv - net1.packets_recv)# / self.frequency
        tx_rate = (net2.packets_sent - net1.packets_sent)# / self.frequency
        return (rx_rate + tx_rate) / self.frequency

    
    #def runTask(self):
    #    for task in self.tasks:
    #        file = open(task)
    #        config = json