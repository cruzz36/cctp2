import socket
from protocol import NetTask,AlertFlow
import threading
from otherEntities import Limit
import os
import json

def removeNulls(text):
    while True:
        try:
            text = text.remove("")
        except Exception as e:
            break
    return text

class NMS_Server: 
    def __init__(self):
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
        self.net = NetTask.NetTask(self.IPADDRESS,netDir)
        alertDir = f"{dir}alerts/"
        try:
            os.mkdir(alertDir)
        except FileExistsError:
            None
        self.alert = AlertFlow.AlertFlow(self.IPADDRESS,alertDir,Limit.Limit())
        self.agents =  dict() # (agentId,ip)
        self.tasks = dict()


    def alertRecv(self):
        self.alert.server()

    def netRecv(self):
        lista = self.net.recv()
        idAgent = lista[0]
        requestType = lista[1]
        filename = lista[2]
        ip = lista[3]

        if requestType == self.net.registerAgent:
            self.registerAgent(idAgent,ip) # It already sends the confirmation reply
            return

        if requestType  == self.net.sendMetrics:
            iter = filename.split("_")[3].split(".")[0]
            self.net.send(ip,self.net.port,self.net.ackkey,idAgent,iter)
            return

    def sendTask(self,ip,idAgent,task):
        self.net.send(ip,self.net.port,self.net.taskRequest,idAgent,task)
        lista = self.net.recv()
        while (
            lista[0] != idAgent and
            lista[1] != self.net.ackkey and
            lista[3] != ip
        ):
            self.net.send(ip,self.net.port,self.net.taskRequest,idAgent,task)
            lista = self.net.recv()
            while lista[2] != task:
                self.net.send(ip,self.net.port,self.net.taskRequest,idAgent,task)
                lista = self.net.recv()



    def registerAgent(self,idAgent,ip):
        if self.agents.get(idAgent) == None:
            self.agents[idAgent] = ip
            self.net.send(ip,self.net.port,self.net.ackkey,idAgent,"Registered")
            #print(self.agents[idAgent])
            return
        self.net.send(ip,self.net.port,self.net.ackkey,idAgent,"Already registered")
        #print("Already Registered")


    def parseConfig(self,filename):
        file = open(filename)
        config = json.load(file)
        #print(config)
        i = 0
        for a in config:
            taskid = a["task_id"]
            self.tasks[taskid] = json.dumps(a)
            agentsToSend = a["devices"]
            for agent in agentsToSend:
                self.net.send(self.agents.get(agent["device_id"]),self.net.port,self.net.taskRequest,agent["device_id"],agent)
                #print(f"Agent {agent['device_id']} Parsed and sent")
        print("File Parsed")   
        
            
    def getinterfaces(self):
        text = os.popen("ip -o -4 route show | awk '{print $3,$9}'").read()
        text = text.split("\n")
        removeNulls(text)
        return text[1:]