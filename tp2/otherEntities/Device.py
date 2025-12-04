import os
from client import NMS_Agent

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
            text.remove("")
        except:
            break
    return text        


# Classe não implementada - Task seria uma classe separada para representar tarefas
# DEVERIA estar implementada se quisermos separar a lógica de tarefas dos dispositivos
# ONDE: Criar ficheiro Task.py ou adicionar aqui para representar tarefas recebidas da Nave-Mãe
# COMO: class Task: com atributos como task_id, task_type, parameters, etc.
# PORQUÊ:
#   1. Melhor separação de responsabilidades (Device = hardware, Task = missão)
#   2. Permite reutilizar tarefas entre diferentes dispositivos
#   3. Mais fácil de testar e manter
# NOTA: Atualmente as tarefas são armazenadas como strings/dicts em self.tasks
# class Task:
        
class Device:
    """
    Classe que representa um dispositivo/rover e as suas configurações de monitorização.
    """
    def __init__(self,taskid,device):
        """
        Inicializa um dispositivo com as suas configurações.
        
        Args:
            taskid (str): Identificador da tarefa associada
            device (dict): Dicionário com configurações do dispositivo (device_id, device_metrics, 
                          link_metrics, telemetry_stream_conditions)
        """
        self.idTask = taskid
        self.id = device["device_id"]
        self.metrics = device["device_metrics"]
        self.bandwidth = device["link_metrics"]["bandwidth"]
        # Variáveis não utilizadas - acede-se diretamente a self.bandwidth["jitter"] e self.bandwidth["packet_loss"]
        # Não são necessárias porque o código usa self.bandwidth diretamente
        # self.jitter = self.bandwidth["jitter"]
        # self.packetLoss = self.bandwidth["packet_loss"]
        self.latency = self.bandwidth["latency"]
        self.limits = device["telemetry_stream_conditions"]
    
    def run(self,client):
        """
        Executa a recolha de métricas do dispositivo usando o cliente NMS_Agent.
        Mede CPU, RAM, largura de banda, jitter, perda de pacotes, latência e estatísticas de interfaces.
        
        Args:
            client (NMS_Agent): Instância do cliente NMS_Agent para fazer medições
            
        Returns:
            dict: Dicionário com todas as métricas recolhidas:
                - cpu_usage (float): Percentual de CPU
                - ram_usage (float): Percentual de RAM
                - bandwidth (str): Largura de banda medida
                - jitter (str): Jitter medido
                - packet_loss (str): Perda de pacotes medida
                - latency (str): Latência medida
                - interface_name (float): Taxa de pacotes por interface
        """
        start = {}
        end = {}
        final = {}
        
        # Bug fix: Usar parâmetro 'client' diretamente em vez de 'self.client' que nunca foi atribuído
        if self.metrics["cpu_usage"] == True:
            final["cpu_usage"] = client.getcpu()
        
        # Bug fix: interfaceStatsCheckpoint() requer parâmetro 'interface'
        for a in self.metrics["interface_stats"]:
            start[a] = client.interfaceStatsCheckpoint(a)

        # Bug fix: Inicializar lista = None antes do bloco condicional
        #          Se todas as condições de medição de bandwidth estiverem desativadas,
        #          lista nunca será definida, causando NameError na linha 105
        lista = None
        
        if (
            self.bandwidth["enabled"] == True or
            self.bandwidth["jitter"]["enabled"] == True or
            self.bandwidth["packet_loss"]["enabled"]  == True
        ):
            # Bug fix: getBandwidth() requer 5 argumentos: serverip, role, duration, transport, frequency
            #          Extrair todos os parâmetros do dicionário self.bandwidth
            lista = client.getBandwidth(
                self.bandwidth["server_address"],  # serverip
                self.bandwidth["role"],            # role ("c" ou "s")
                self.bandwidth["test_duration"],   # duration (segundos)
                self.bandwidth["transport_type"],  # transport ("TCP" ou "UDP")
                self.bandwidth["frequency"]       # frequency (segundos)
            )
        
        # Bug fix: getBandwidth() pode retornar None em caso de erro (linha 548 de NMS_Agent.py)
        #          Verificar se lista não é None antes de aceder aos índices para evitar TypeError
        if lista is not None:
            if self.bandwidth["enabled"] == True: final["bandwidth"] = lista[0]
            if self.bandwidth["jitter"]["enabled"] == True: final["jitter"] = lista[1]
            if self.bandwidth["packet_loss"]["enabled"]  == True: final["packet_loss"] = lista[2]

        if self.latency["enabled"] == True:
            final["latency"] = client.getLatency(self.latency["destination"],
                                                      self.latency["packet_count"],
                                                      self.latency["frequency"])

        if self.metrics["ram_usage"] == True:
            final["ram_usage"] = client.getram()

        # Bug fix: interfaceStatsCheckpoint() requer parâmetro 'interface'
        for a in self.metrics["interface_stats"]:
            end[a] = client.interfaceStatsCheckpoint(a)
        
        for a in self.metrics["interface_stats"]:
            final[a] = client.get_packet_rate(start[a],end[a])

        return final