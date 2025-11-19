import os
from client import NMS_Agent

def removeNulls(text):
    while True:
        try:
            text.remove("")
        except:
            break
    return text        


#class Task:
        
class Device:
    def __init__(self,taskid,device):
        self.idTask = taskid
        self.id = device["device_id"]
        self.metrics = device["device_metrics"]
        self.bandwidth = device["link_metrics"]["bandwidth"]
        self.jitter = self.bandwidth["jitter"]
        self.packetLoss = self.bandwidth["packet_loss"]
        self.latency = self.bandwidth["latency"]
        self.limits = device["alertflow_conditions"]
    
    def run(self,client):
        start = {}
        end = {}
        final = {}
        
        if self.metrics["cpu_usage"] == True:
            final["cpu_usage"] = self.client.getcpu()
        
        for a in self.metrics["interface_stats"]:
            start[a] = self.client.interfaceStatsCheckpoint()

        
        if (
            self.bandwidth["enabled"] == True or
            self.bandwidth["jitter"]["enabled"] == True or
            self.bandwidth["packet_loss"]["enabled"]  == True
        ):
            lista = self.client.getBandwidth(self.bandwidth["server_address"])
        
        if self.bandwidth["enabled"] == True: final["bandwidth"] = lista[0]
        if self.bandwidth["jitter"]["enabled"] == True: final["jitter"] = lista[1]
        if self.bandwidth["packet_loss"]["enabled"]  == True: final["packet_loss"] = lista[2]

        if self.latency["enabled"] == True:
            final["latency"] = self.client.getLatency(self.latency["destination"],
                                                      self.latency["packet_count"],
                                                      self.latency["frequency"])

        if self.metrics["ram_usage"] == True:
            final["ram_usage"] = self.client.getram()

        for a in self.metrics["interface_stats"]:
            end[a] = self.client.interfaceStatsCheckpoint()
        
        for a in self.metrics["interface_stats"]:
            final[a] = self.client.get_packet_rate(start[a],end[a])

        return final