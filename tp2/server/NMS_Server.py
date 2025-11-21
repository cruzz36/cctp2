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
        """
        lista = self.missionLink.recv()
        idMission = lista[0]
        requestType = lista[1]
        filename = lista[2]
        ip = lista[3]

        if requestType == self.missionLink.registerAgent:
            self.registerAgent(idMission,ip) # It already sends the confirmation reply
            return

        if requestType  == self.missionLink.sendMetrics:
            iter = filename.split("_")[3].split(".")[0]
            self.missionLink.send(ip,self.missionLink.port,self.missionLink.ackkey,idMission,iter)
            return

    def sendTask(self,ip,idMission,task):
        """
        Envia uma tarefa/missão para um rover através do MissionLink.
        Retransmite até receber confirmação válida.
        
        Args:
            ip (str): Endereço IP do rover
            idMission (str): Identificador do rover
            task: Objeto ou string com a definição da tarefa
        """
        self.missionLink.send(ip,self.missionLink.port,self.missionLink.taskRequest,idMission,task)
        lista = self.missionLink.recv()
        while (
            lista[0] != idMission and
            lista[1] != self.missionLink.ackkey and
            lista[3] != ip
        ):
            self.missionLink.send(ip,self.missionLink.port,self.missionLink.taskRequest,idMission,task)
            lista = self.missionLink.recv()
            while lista[2] != task:
                self.missionLink.send(ip,self.missionLink.port,self.missionLink.taskRequest,idMission,task)
                lista = self.missionLink.recv()



    def registerAgent(self,idMission,ip):
        """
        Regista um agente/rover no sistema.
        Envia confirmação de registo através do MissionLink.
        
        Args:
            idMission (str): Identificador único do agente
            ip (str): Endereço IP do agente
        """
        if self.agents.get(idMission) == None:
            self.agents[idMission] = ip
            self.missionLink.send(ip,self.missionLink.port,self.missionLink.ackkey,idMission,"Registered")
            #print(self.agents[idMission])
            return
        self.missionLink.send(ip,self.missionLink.port,self.missionLink.ackkey,idMission,"Already registered")
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
                self.missionLink.send(self.agents.get(agent["device_id"]),self.missionLink.port,self.missionLink.taskRequest,agent["device_id"],agent)
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