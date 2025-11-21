import socket
from protocol import MissionLink,TelemetryStream
import threading
from otherEntities import Limit
import os
import json

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

class NMS_Server: 
    """
    Classe que representa a Nave-Mãe (servidor) no sistema.
    Responsável por coordenar rovers, receber telemetria e enviar missões.
    """
    def __init__(self):
        """
        Inicializa o servidor NMS.
        Cria diretórios necessários e inicializa os protocolos MissionLink e TelemetryStream.
        """
        self.id = socket.gethostname()
        self.IPADDRESS = self.getinterfaces()[0].split(" ")[1]
        dir = f"../{self.id}/"
        try:
            os.mkdir(dir)
        except FileExistsError:
            None
        netDir = f"{dir}net/"
        try:
            os.mkdir(netDir)
        except FileExistsError:
            None
        self.missionLink = MissionLink.MissionLink(self.IPADDRESS,netDir)
        alertDir = f"{dir}alerts/"
        try:
            os.mkdir(alertDir)
        except FileExistsError:
            None
        self.telemetryStream = TelemetryStream.TelemetryStream(self.IPADDRESS,alertDir,Limit.Limit())
        self.agents =  dict() # (agentId,ip)
        self.tasks = dict()


    def recvTelemetry(self):
        """
        Inicia o servidor TelemetryStream para receber dados de telemetria dos rovers.
        Executa em loop infinito.
        """
        self.telemetryStream.server()

    def recvMissionLink(self):
        """
        Recebe e processa mensagens através do MissionLink.
        Processa registos de agentes e envio de métricas.
        
        NOTA: O idAgent é extraído do handshake e identificado pelo IP/porta.
              O protocolo de dados não inclui idAgent, apenas idMission.
        """
        lista = self.missionLink.recv()
        # lista tem: [idAgent, idMission, requestType, message, ip]
        # idAgent é identificado pelo IP/porta do handshake
        idAgent = lista[0]
        idMission = lista[1]
        requestType = lista[2]
        filename = lista[3]
        ip = lista[4]

        if requestType == self.missionLink.registerAgent:
            self.registerAgent(idAgent,ip) # It already sends the confirmation reply
            return

        if requestType  == self.missionLink.sendMetrics:
            iter = filename.split("_")[3].split(".")[0]
            self.missionLink.send(ip,self.missionLink.port,self.missionLink.ackkey,idAgent,idMission,iter)
            return

    def sendTask(self,ip,idAgent,idMission,task):
        """
        Envia uma tarefa/missão para um rover através do MissionLink.
        Retransmite até receber confirmação válida.
        
        Args:
            ip (str): Endereço IP do rover
            idAgent (str): Identificador do rover
            idMission (str): Identificador da missão
            task: Objeto ou string com a definição da tarefa
        """
        self.missionLink.send(ip,self.missionLink.port,self.missionLink.taskRequest,idAgent,idMission,task)
        lista = self.missionLink.recv()
        # lista agora tem: [idAgent, idMission, requestType, message, ip]
        while (
            lista[0] != idAgent and
            lista[2] != self.missionLink.ackkey and
            lista[4] != ip
        ):
            self.missionLink.send(ip,self.missionLink.port,self.missionLink.taskRequest,idAgent,idMission,task)
            lista = self.missionLink.recv()
            while lista[3] != task:
                self.missionLink.send(ip,self.missionLink.port,self.missionLink.taskRequest,idAgent,idMission,task)
                lista = self.missionLink.recv()



    def registerAgent(self,idAgent,ip):
        """
        Regista um agente/rover no sistema.
        Envia confirmação de registo através do MissionLink.
        
        Args:
            idAgent (str): Identificador único do agente
            ip (str): Endereço IP do agente
        """
        if self.agents.get(idAgent) == None:
            self.agents[idAgent] = ip
            # No registo, idMission = "000" porque ainda não há missão atribuída
            self.missionLink.send(ip,self.missionLink.port,self.missionLink.ackkey,idAgent,"000","Registered")
            #print(self.agents[idAgent])
            return
        self.missionLink.send(ip,self.missionLink.port,self.missionLink.ackkey,idAgent,"000","Already registered")
        #print("Already Registered")


    def parseConfig(self,filename):
        """
        Faz parse de um ficheiro de configuração JSON e envia tarefas para os rovers.
        
        Args:
            filename (str): Caminho do ficheiro de configuração JSON
        """
        file = open(filename)
        config = json.load(file)
        #print(config)
        i = 0
        for a in config:
            taskid = a["task_id"]
            self.tasks[taskid] = json.dumps(a)
            agentsToSend = a["devices"]
            for agent in agentsToSend:
                # Envia tarefa com idAgent=agent["device_id"] e idMission=taskid
                self.missionLink.send(self.agents.get(agent["device_id"]),self.missionLink.port,self.missionLink.taskRequest,agent["device_id"],taskid,agent)
                #print(f"Agent {agent['device_id']} Parsed and sent")
        print("File Parsed")   
        
            
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