from protocol import NetTask
from client import NMS_Agent
from protocol import AlertFlow
import threading
import os

def run(num): 
    client = NetTask.NetTask("127.0.0.1",8081 + num)
    client.server()

    #(ip,port),idAgent,seq,ack = client.startConnection("n" + str(num),"127.0.0.1",8080)

    message = f"template{num}.json"

    #client.send(ip,port,idAgent,"template.json")
    client.send("127.0.0.1",8080,client.registerAgent,"n1",message)


#for i in range (1,11):
#    t1 = threading.Thread(target=run(i))
#    t1.start()



import psutil
import time

def get_packet_rate(interface, interval=1):
    net1 = psutil.net_io_counters(pernic=True)[interface]
    time.sleep(interval)
    print(1)
    print(1)
    print(1)
    print(1)
    print(1)
    net2 = psutil.net_io_counters(pernic=True)[interface]
    
    rx_rate = (net2.packets_recv - net1.packets_recv) / interval
    tx_rate = (net2.packets_sent - net1.packets_sent) / interval
    return rx_rate, tx_rate

import time
import subprocess

def get_packet_count(interface):
    # Run the ip command and parse RX and TX packet counts
    result = subprocess.run(["ip", "-s", "link", "show", interface], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    rx_line = lines[[i for i, line in enumerate(lines) if "RX:" in line][0] + 1].strip()
    tx_line = lines[[i for i, line in enumerate(lines) if "TX:" in line][0] + 1].strip()
    rx_packets = int(rx_line.split()[1])
    tx_packets = int(tx_line.split()[1])
    return rx_packets, tx_packets

def calculate_packet_rate(interface, interval=1):
    rx1, tx1 = get_packet_count(interface)
    time.sleep(interval)
    rx2, tx2 = get_packet_count(interface)
    rx_rate = (rx2 - rx1) / interval
    tx_rate = (tx2 - tx1) / interval
    return rx_rate, tx_rate

# Example usage
client = NMS_Agent.NMS_Agent("10.0.4.10")  # Replace with your interface

#print(client.getBandwidth("10.0.3.1"))
#print(client.getcpu(client.frequency))
#print(client.getram())
#print(client.getLatency("10.0.1.2"))

client.alertServer("10.0.4.10","alert_n1_task-202_1.json")
#client.alertFlow.endConnection()
