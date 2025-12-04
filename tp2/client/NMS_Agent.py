import socket
from protocol import MissionLink,TelemetryStream
from otherEntities import Device
import os
import subprocess
import time
import psutil  # type: ignore  # Instalar com: pip install psutil
import json

def validateMission(mission_data):
    """
    Valida se um dicionário contém todos os campos obrigatórios de uma missão.
    
    Formato obrigatório de missão (conforme PDF):
    {
        "mission_id": string (obrigatório, identificador único),
        "rover_id": string (obrigatório),
        "geographic_area": dict (obrigatório),
        "task": string (obrigatório: capture_images|sample_collection|environmental_analysis|...),
        "duration_minutes": integer (obrigatório, > 0),
        "update_frequency_seconds": integer (obrigatório, > 0)
    }
    
    Campos opcionais:
    - "priority": string (low|medium|high)
    - "instructions": string
    
    Args:
        mission_data (dict or str): Dicionário ou string JSON com dados da missão
        
    Returns:
        tuple: (bool, str) - (True, "") se válido, (False, mensagem_erro) se inválido
    """
    # Se for string, fazer parse
    if isinstance(mission_data, str):
        try:
            mission_data = json.loads(mission_data)
        except json.JSONDecodeError:
            return False, "Formato JSON inválido"
    
    if not isinstance(mission_data, dict):
        return False, "Dados da missão devem ser um dicionário"
    
    # Campos obrigatórios
    required_fields = {
        "mission_id": str,
        "rover_id": str,
        "geographic_area": dict,
        "task": str,
        "duration_minutes": (int, float),
        "update_frequency_seconds": (int, float)
    }
    
    # Verificar presença e tipo dos campos obrigatórios
    for field, expected_type in required_fields.items():
        if field not in mission_data:
            return False, f"Campo obrigatório ausente: {field}"
        
        if not isinstance(mission_data[field], expected_type):
            return False, f"Campo {field} tem tipo incorreto. Esperado: {expected_type}"
    
    # Validações específicas
    if mission_data["duration_minutes"] <= 0:
        return False, "duration_minutes deve ser maior que 0"
    
    if mission_data["update_frequency_seconds"] <= 0:
        return False, "update_frequency_seconds deve ser maior que 0"
    
    # Validar geographic_area
    geo_area = mission_data["geographic_area"]
    if not isinstance(geo_area, dict):
        return False, "geographic_area deve ser um dicionário"
    
    # Verificar se tem coordenadas (formato rectangle com x1, y1, x2, y2)
    if "x1" in geo_area and "y1" in geo_area and "x2" in geo_area and "y2" in geo_area:
        try:
            x1, y1, x2, y2 = float(geo_area["x1"]), float(geo_area["y1"]), float(geo_area["x2"]), float(geo_area["y2"])
            if x1 >= x2 or y1 >= y2:
                return False, "Coordenadas inválidas: x1 < x2 e y1 < y2 são obrigatórios"
        except (ValueError, TypeError):
            return False, "Coordenadas devem ser números válidos"
    else:
        # Outros formatos podem ser adicionados aqui (polygon, circle, etc.)
        return False, "geographic_area deve conter coordenadas (x1, y1, x2, y2) ou outro formato válido"
    
    # Validar task (valores comuns)
    valid_tasks = ["capture_images", "sample_collection", "environmental_analysis"]
    if mission_data["task"] not in valid_tasks:
        # Aceitar outros valores mas avisar
        pass
    
    return True, ""


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
        # Bug fix: Validar formato do nome do ficheiro antes de fazer split
        try:
            lista = filename.split("_")
            if len(lista) >= 4:
                iter = lista[3].split(".")[0]
                # Bug fix: Formato é alert_idMission_task-XXX_iter.json
                #          Split por "_" dá: [0]="alert", [1]=idMission, [2]="task-XXX", [3]="iter.json"
                #          idMission está no índice 1, não 2
                idMission = lista[1]
            else:
                # Formato inválido - usar valores padrão
                print(f"Erro: Formato de nome de ficheiro inválido: {filename}. Esperado: alert_idMission_task-XXX_iter.json")
                iter = "unknown"
                idMission = "000"
        except (IndexError, AttributeError) as e:
            print(f"Erro ao processar nome de ficheiro de métricas: {e}")
            iter = "error"
            idMission = "000"
        self.missionLink.send(ip,self.missionLink.port,self.missionLink.sendMetrics,self.id,idMission,filename)
        reply = self.missionLink.recv()
        # Bug fix: reply[2] é missionType (não flag), reply[3] é message (contém iter)
        # Quando servidor envia ACK, missionType será None ou vazio, message será iter
        # Validação correta: verificar se message (reply[3]) contém o iter esperado
        # E verificar se recebemos resposta do servidor correto (reply[4] == ip)
        # Usar 'or' porque retransmitir se QUALQUER validação falhar (iter incorreto OU IP incorreto)
        # Bug fix: Adicionar limite de retries para evitar loops infinitos
        retries = 0
        max_retries = 10
        while (reply[3] != iter or reply[4] != ip) and retries < max_retries:
            retries += 1
            self.missionLink.send(ip,self.missionLink.port,self.missionLink.sendMetrics,self.id,idMission,filename)
            reply = self.missionLink.recv()
        
        if retries >= max_retries:
            print(f"Aviso: Máximo de tentativas ({max_retries}) atingido ao enviar métricas")
            
    def register(self,ip):
        """
        Regista o agente na Nave-Mãe através do MissionLink.
        Retransmite o pedido até receber confirmação válida.
        
        Args:
            ip (str): Endereço IP da Nave-Mãe
        """
        # No registo, idMission = "000" porque ainda não há missão atribuída
        self.missionLink.send(ip,self.missionLink.port,self.missionLink.registerAgent,self.id,"000","\0")
        lista = self.missionLink.recv()
        # Bug fix: lista[2] é missionType (não flag), lista[0] é idAgent
        # Quando servidor envia confirmação de registo, missionType será None ou vazio
        # Validação correta: verificar se idAgent corresponde e se recebemos resposta do servidor correto
        # Bug fix: Usar 'or' está correto - retransmitir se QUALQUER validação falhar
        #          Mas vamos adicionar um limite de retries para evitar loops infinitos
        retries = 0
        max_retries = 10
        while (lista[0] != self.id or lista[4] != ip) and retries < max_retries:
            retries += 1
            self.missionLink.send(ip,self.missionLink.port,self.missionLink.registerAgent,self.id,"000","\0")
            lista = self.missionLink.recv()
        
        if retries >= max_retries:
            print(f"Aviso: Máximo de tentativas ({max_retries}) atingido ao registar")


    def requestMission(self, ip):
        """
        Solicita uma missão à Nave-Mãe através do MissionLink.
        Implementa o requisito: "O rover deve ser capaz de solicitar uma missão à Nave-Mãe."
        
        Args:
            ip (str): Endereço IP da Nave-Mãe
            
        Returns:
            dict or None: Dicionário com dados da missão recebida, ou None se não houver missão disponível
        """
        # Enviar solicitação de missão
        self.missionLink.send(ip, self.missionLink.port, self.missionLink.requestMission, self.id, "000", "request")
        
        # Aguardar resposta (pode ser missão ou mensagem de "sem missão disponível")
        try:
            response = self.missionLink.recv()
            # response tem: [idAgent, idMission, missionType, message, ip]
            if response[2] == self.missionLink.taskRequest:
                # Bug fix: Missão já está na primeira resposta (response[3])
                #          Não fazer recv() novamente - extrair e validar diretamente
                mission_message = response[3]
                mission_id = response[1]  # idMission do protocolo
                
                # Validar formato da missão
                is_valid, error_msg = validateMission(mission_message)
                
                if not is_valid:
                    print(f"Erro: Missão recebida é inválida: {error_msg}")
                    # Enviar ACK mesmo assim para não bloquear o servidor
                    self.missionLink.send(response[4], self.missionLink.port, None, self.id, mission_id, "invalid")
                    return None
                
                # Parse do JSON da missão
                try:
                    if isinstance(mission_message, str):
                        mission_data = json.loads(mission_message)
                    else:
                        mission_data = mission_message
                except json.JSONDecodeError as e:
                    print(f"Erro: Não foi possível fazer parse do JSON da missão: {e}")
                    self.missionLink.send(response[4], self.missionLink.port, None, self.id, mission_id, "parse_error")
                    return None
                
                # Verificar se o rover_id corresponde
                if mission_data.get("rover_id") != self.id:
                    print(f"Aviso: Missão {mission_id} destinada a outro rover ({mission_data.get('rover_id')})")
                    # Continuar mesmo assim - pode ser útil para debug
                
                # Armazenar missão validada
                self.tasks[mission_id] = mission_data
                
                # Enviar ACK de confirmação
                self.missionLink.send(response[4], self.missionLink.port, None, self.id, mission_id, mission_id)
                
                return mission_data
            elif response[2] == self.missionLink.noneType:
                # Bug fix: Quando servidor envia com missionType=None, é codificado como "N" no protocolo
                #          O recv() extrai isto como a string "N", não Python None
                #          Verificar response[2] == "N" em vez de response[2] is None
                # Sem missão disponível (mensagem será "no_mission")
                if response[3] == "no_mission":
                    print("Nave-Mãe respondeu: sem missão disponível no momento")
                return None
        except Exception as e:
            print(f"Erro ao solicitar missão: {e}")
            return None

    def recvMissionLink(self):
        """
        Recebe uma mensagem através do MissionLink.
        Se for um pedido de tarefa (taskRequest), valida o formato da missão,
        armazena a missão e envia confirmação.
        
        Formato esperado da missão (conforme PDF):
        {
            "mission_id": string (obrigatório),
            "rover_id": string (obrigatório),
            "geographic_area": {"x1": float, "y1": float, "x2": float, "y2": float},
            "task": string (obrigatório),
            "duration_minutes": integer (obrigatório, > 0),
            "update_frequency_seconds": integer (obrigatório, > 0)
        }
        
        NOTA: O idAgent é usado apenas no handshake. Nas mensagens de dados,
              apenas idMission é enviado no protocolo.
        
        Returns:
            dict or None: Dicionário com dados da missão validada, ou None se não for missão válida
        """
        lista = self.missionLink.recv()
        # lista tem: [idAgent, idMission, missionType, message, ip]
        # idAgent é identificado pelo IP/porta do handshake
        
        # missionType = tipo de operação do protocolo (R, T, M, Q, P)
        # Quando missionType="T" (taskRequest), o campo 'message' contém um JSON
        # que inclui o campo "task" com um dos 3 valores: capture_images, sample_collection, environmental_analysis
        if lista[2] == self.missionLink.taskRequest:
            mission_message = lista[3]
            mission_id = lista[1]  # idMission do protocolo
            
            # Validar formato da missão
            is_valid, error_msg = validateMission(mission_message)
            
            if not is_valid:
                print(f"Erro: Missão recebida é inválida: {error_msg}")
                # Enviar ACK mesmo assim para não bloquear o servidor
                # Bug fix: ackkey é uma flag, não um missionType. Usar None como missionType
                self.missionLink.send(lista[4], self.missionLink.port, None, self.id, mission_id, "invalid")
                return None
            
            # Parse do JSON da missão
            try:
                if isinstance(mission_message, str):
                    mission_data = json.loads(mission_message)
                else:
                    mission_data = mission_message
            except json.JSONDecodeError as e:
                print(f"Erro: Não foi possível fazer parse do JSON da missão: {e}")
                # Bug fix: ackkey é uma flag, não um missionType. Usar None como missionType
                self.missionLink.send(lista[4], self.missionLink.port, None, self.id, mission_id, "parse_error")
                return None
            
            # Verificar se o rover_id corresponde
            if mission_data.get("rover_id") != self.id:
                print(f"Aviso: Missão {mission_id} destinada a outro rover ({mission_data.get('rover_id')})")
                # Continuar mesmo assim - pode ser útil para debug
            
            # Armazenar missão validada
            self.tasks[mission_id] = mission_data
            
            # Extrair informações da missão para processamento
            print(f"Missão recebida e validada:")
            print(f"  ID: {mission_data.get('mission_id')}")
            print(f"  Tarefa: {mission_data.get('task')}")
            print(f"  Duração: {mission_data.get('duration_minutes')} minutos")
            print(f"  Frequência de atualização: {mission_data.get('update_frequency_seconds')} segundos")
            print(f"  Área geográfica: ({mission_data['geographic_area'].get('x1')}, {mission_data['geographic_area'].get('y1')}) a ({mission_data['geographic_area'].get('x2')}, {mission_data['geographic_area'].get('y2')})")
            
            # Enviar ACK de confirmação
            # Bug fix: ackkey é uma flag, não um missionType. Usar None como missionType
            self.missionLink.send(lista[4], self.missionLink.port, None, self.id, mission_id, mission_id)
            
            return mission_data
        
        return None

    def reportMissionProgress(self, ip, mission_id, progress_data):
        """
        Reporta o progresso de uma missão à Nave-Mãe.
        Implementa o requisito: "O rover deve reportar o progresso da missão de acordo 
        com parâmetros definidos na própria missão."
        
        Formato de progress_data:
        {
            "mission_id": string (obrigatório),
            "progress_percent": integer (0-100, obrigatório),
            "status": string (obrigatório: "in_progress"|"completed"|"failed"|"paused"),
            "current_position": {"x": float, "y": float} (opcional),
            "events": list (opcional, lista de eventos ocorridos),
            "samples_collected": integer (opcional, para tarefas de coleta),
            "images_captured": integer (opcional, para tarefas de captura),
            "time_elapsed_minutes": float (opcional),
            "estimated_completion_minutes": float (opcional)
        }
        
        Args:
            ip (str): Endereço IP da Nave-Mãe
            mission_id (str): Identificador da missão
            progress_data (dict): Dicionário com dados de progresso
            
        Returns:
            bool: True se progresso foi reportado com sucesso, False caso contrário
        """
        # Validar campos obrigatórios
        if "mission_id" not in progress_data:
            progress_data["mission_id"] = mission_id
        
        if "progress_percent" not in progress_data:
            print("Erro: progress_percent é obrigatório")
            return False
        
        if "status" not in progress_data:
            print("Erro: status é obrigatório")
            return False
        
        # Converter para JSON
        progress_json = json.dumps(progress_data)
        
        # Enviar reporte de progresso
        try:
            self.missionLink.send(ip, self.missionLink.port, self.missionLink.reportProgress, self.id, mission_id, progress_json)
            
            # Aguardar confirmação
            response = self.missionLink.recv()
            # Bug fix: Quando servidor envia com missionType=None, é codificado como "N" no protocolo
            #          O recv() extrai isto como a string "N", não Python None
            #          Verificar response[2] == "N" em vez de response[2] is None
            if response[2] == self.missionLink.noneType and response[3] in ["progress_received", "Registered", "Already registered"]:
                print(f"Progresso da missão {mission_id} reportado com sucesso")
                return True
            else:
                print(f"Falha ao reportar progresso: resposta inesperada (missionType={response[2]}, message={response[3]})")
                return False
        except Exception as e:
            print(f"Erro ao reportar progresso: {e}")
            return False
        

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