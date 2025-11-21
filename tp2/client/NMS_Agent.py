import socket
from protocol import MissionLink,TelemetryStream
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
    """
    Remove todas as strings vazias de uma lista.
    
    Args:
        text (list): Lista de strings
        
    Returns:
        list: Lista sem strings vazias
    """
    while True:
        try:
            text = text.remove("")
        except Exception as e:
            break
    return text

class NMS_Agent:
    """
    Classe que representa um agente/rover no sistema.
    Responsável por medir métricas, comunicar com a Nave-Mãe e executar missões.
    """
    def __init__(self,serverAddress,frequency = 1,storeFolder = "."):
        """
        Inicializa o agente NMS.
        
        Args:
            serverAddress (str): Endereço IP da Nave-Mãe (servidor)
            frequency (int, optional): Frequência de operação. Defaults to 1
            storeFolder (str, optional): Pasta para armazenar ficheiros. Defaults to "."
        """
        self.id = socket.gethostname()
        self.ipAddress = self.getinterfaces()[0].split(" ")[1]
        self.serverAddress = serverAddress
        self.missionLink = MissionLink.MissionLink(self.ipAddress,storeFolder)
        self.telemetryStream = TelemetryStream.TelemetryStream(self.ipAddress,storeFolder) #tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        # Variável não utilizada - guarda nomes de interfaces mas nunca é usada
        # DEVERIA ser usada em getConnections() ou para reportar interfaces ativas ao servidor
        # self.connections = self.getinterfacesNames(self.getinterfaces())
        self.tasks = dict()
        self.frequency = frequency

    def sendMetrics(self,ip,filename:str):
        """
        Envia um ficheiro de métricas para a Nave-Mãe através do MissionLink.
        Retransmite até receber confirmação válida.
        
        Args:
            ip (str): Endereço IP da Nave-Mãe
            filename (str): Nome do ficheiro de métricas a enviar (formato: alert_idMission_task-XXX_iter.json)
        """
        lista = filename.split("_")
        iter = lista[3].split(".")[0]
        idMission = lista[2]
        self.missionLink.send(ip,self.missionLink.port,self.missionLink.sendMetrics,idMission,filename)
        reply = self.missionLink.recv()
        while reply[1] != self.missionLink.ackkey and reply[2] != iter:
            self.missionLink.send(ip,self.missionLink.port,self.missionLink.sendMetrics,idMission,filename)
            reply = self.missionLink.recv()
            
    def register(self,ip):
        """
        Regista o agente na Nave-Mãe através do MissionLink.
        Retransmite o pedido até receber confirmação válida.
        
        Args:
            ip (str): Endereço IP da Nave-Mãe
        """
        self.missionLink.send(ip,self.missionLink.port,self.missionLink.registerAgent,self.id,"\0")
        lista = self.missionLink.recv()
        while lista[1] != self.missionLink.ackkey and lista[0] != self.id:
            self.missionLink.send(ip,self.missionLink.port,self.missionLink.registerAgent,self.id,"\0")
            lista = self.missionLink.recv()


    def recvMissionLink(self):
        """
        Recebe uma mensagem através do MissionLink.
        Se for um pedido de tarefa (taskRequest), armazena a tarefa e envia confirmação.
        """
        lista = self.missionLink.recv()
        if lista[1] == self.missionLink.taskRequest:
            taskId = lista[2].split(".")[0]
            if self.tasks.get(taskId) != None:
                self.tasks[taskId] = lista[2]
            self.missionLink.send(lista[3],self.missionLink.port,self.missionLink.ackkey,self.id,taskId)
        

    def sendTelemetry(self,ip,message):
        """
        Envia dados de telemetria para a Nave-Mãe através do TelemetryStream (TCP).
        
        Args:
            ip (str): Endereço IP da Nave-Mãe
            message (str): Caminho do ficheiro de telemetria a enviar
        """
        self.telemetryStream.send(ip,message)
    
    def parseFile(self,file):
        """
        Faz parse de um ficheiro de configuração e cria objetos Device.
        
        Args:
            file (str): Caminho do ficheiro de configuração
        """
        self.devices = Device.Device(file)

    # Método não utilizado - nunca é chamado no código
    # DEVERIA estar a ser usado para reportar interfaces de rede ao servidor durante o registo
    # ONDE: No método register() ou sendMetrics(), para informar a Nave-Mãe sobre as interfaces disponíveis
    # COMO: Chamar self.getConnections() e incluir no registo ou nas métricas enviadas
    # PORQUÊ: Permite à Nave-Mãe saber quais interfaces cada rover tem disponíveis para comunicação
    # NOTA: Tem um bug - lista[size] deveria ser lista[size-1] para evitar IndexError
    # def getConnections(self):
    #     """
    #     Obtém informações sobre as conexões de rede do agente.
    #     
    #     Returns:
    #         str or None: String formatada com informações das interfaces ou None se não houver interfaces
    #     """
    #     message = f""
    #     lista = self.getinterfaces()
    #     size = len(lista)
    #     if size == 0: return None
    #     message += f"{lista[0]}|"
    #     for a in lista:
    #         if lista[size] != a:  # BUG: deveria ser lista[size-1]
    #             message += f"{a}|"
    #             continue
    #         message += f"{a}\0"
    #     return message
    
    def getBandwidth(self,serverip,role,duration,transport,frequency):
        """
        Mede largura de banda, jitter e perda de pacotes usando iperf.
        
        Args:
            serverip (str): Endereço IP do servidor iperf
            role (str): Papel no teste ('c' para cliente, 's' para servidor)
            duration (int): Duração do teste em segundos
            transport (str): Tipo de transporte ('UDP' ou 'TCP')
            frequency (int): Frequência/intervalo do teste
            
        Returns:
            list or None: Lista com [bandwidth, jitter, packet_loss] ou None em caso de erro
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
        Mede a latência (RTT) usando o comando ping.
        
        Args:
            address (str): Endereço IP ou hostname para fazer ping
            packetCount (int, optional): Número de pacotes a enviar. Defaults to 3
            interval (int, optional): Intervalo entre pacotes em segundos. Defaults to 1
            
        Returns:
            str: Latência média em milissegundos (extraída do output do ping)
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
        """
        Obtém o percentual de utilização da CPU.
        
        Returns:
            float: Percentual de CPU utilizado (0-100)
        """
        return psutil.cpu_percent()
    
    def getram(self):
        """
        Obtém o percentual de utilização da RAM.
        
        Returns:
            float: Percentual de RAM utilizada (0-100)
        """
        return psutil.virtual_memory()[2]

    def getinterfacesNames(self,interfaces):
        """
        Extrai os nomes das interfaces de rede de uma lista de interfaces.
        
        Args:
            interfaces (list): Lista de strings com informações de interfaces
            
        Returns:
            set: Conjunto com os nomes únicos das interfaces
        """
        names = set()
        i = 0
        for a in interfaces:
            name = a.split(" ")
            names.add(name[0])
            i+=1
        return names
 
    def getinterfaces(self):
        """
        Obtém a lista de interfaces de rede do sistema usando o comando ip.
        
        Returns:
            list: Lista de strings com informações das interfaces (formato: "interface ip")
        """
        text = os.popen("ip -o -4 route show | awk '{print $3,$9}'").read()
        text = text.split("\n")
        removeNulls(text)
        return text[1:]
    
    def interfaceStatsCheckpoint(self,interface):
        """
        Obtém estatísticas de uma interface de rede num momento específico.
        
        Args:
            interface (str): Nome da interface de rede
            
        Returns:
            snetio: Objeto com estatísticas de rede (bytes enviados/recebidos, pacotes, etc.)
        """
        return psutil.net_io_counters(pernic = True)[interface]

        
    def get_packet_rate(self,net1,net2):
        """
        Calcula a taxa de pacotes (recebidos + enviados) entre dois checkpoints.
        
        Args:
            net1: Estatísticas de rede do primeiro checkpoint
            net2: Estatísticas de rede do segundo checkpoint
            
        Returns:
            float: Taxa de pacotes por segundo (soma de recebidos e enviados)
        """
        rx_rate = (net2.packets_recv - net1.packets_recv)# / self.frequency
        tx_rate = (net2.packets_sent - net1.packets_sent)# / self.frequency
        return (rx_rate + tx_rate) / self.frequency

    
    # Método não implementado/incompleto - executaria tarefas recebidas da Nave-Mãe
    # DEVERIA estar implementado para executar as missões/tarefas recebidas via MissionLink
    # ONDE: Após receber tarefa em recvMissionLink(), chamar este método para executá-la
    # COMO: 
    #   1. Iterar sobre self.tasks (que contém tarefas recebidas)
    #   2. Fazer parse do JSON da tarefa
    #   3. Executar ações conforme tipo de tarefa
    #   4. Reportar resultados de volta à Nave-Mãe
    # PORQUÊ:
    #   1. Permite aos rovers executar missões recebidas
    #   2. Essencial para o funcionamento completo do sistema
    #   3. Permite coordenação entre Nave-Mãe e rovers
    # NOTA: Código incompleto - falta implementação completa
    #       Atualmente as tarefas são apenas armazenadas em self.tasks mas não executadas
    # def runTask(self):
    #     for task in self.tasks:
    #         file = open(task)
    #         config = json  # Incompleto - falta json.load(file)