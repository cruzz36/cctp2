"""
Exemplo de uso da monitorização contínua de telemetria.

Este exemplo demonstra como usar o novo método startContinuousTelemetry()
para implementar monitorização contínua conforme requisitos do PDF.
"""

from client import NMS_Agent
from otherEntities import Device
import json
import time

def exemplo_monitorizacao_continua():
    """Exemplo completo de monitorização contínua."""
    print("=" * 70)
    print("EXEMPLO: Monitorização Contínua de Telemetria")
    print("=" * 70)
    
    # Criar agente
    agent = NMS_Agent.NMS_Agent("127.0.0.1")
    
    # Configurar estado inicial do rover
    agent.updatePosition(0.0, 0.0, 0.0)
    agent.updateOperationalStatus("parado")
    agent.updateBattery(100.0)
    agent.updateVelocity(0.0)
    agent.updateDirection(0.0)  # Norte
    agent.updateTemperature(20.0)
    
    # Criar dispositivo para recolher métricas (opcional)
    device_config = {
        "device_id": "r1",
        "device_metrics": {
            "cpu_usage": True,
            "ram_usage": True,
            "interface_stats": ["eth0"]
        },
        "link_metrics": {
            "bandwidth": {
                "enabled": False,  # Desativar para exemplo rápido
                "role": "c",
                "server_address": "127.0.0.1",
                "test_duration": 10,
                "transport_type": "TCP",
                "frequency": 30,
                "jitter": {"enabled": False},
                "packet_loss": {"enabled": False},
                "latency": {
                    "enabled": False,
                    "destination": "127.0.0.1",
                    "packet_count": 10,
                    "frequency": 20
                }
            }
        },
        "telemetry_stream_conditions": {}
    }
    
    device = Device.Device("task-001", device_config)
    agent.setDevices([device])
    
    # Iniciar monitorização contínua (envia a cada 10 segundos)
    print("\nIniciando monitorização contínua...")
    print("  - Intervalo: 10 segundos")
    print("  - Servidor: 127.0.0.1")
    print("  - Pressione Ctrl+C para parar\n")
    
    success = agent.startContinuousTelemetry("127.0.0.1", interval_seconds=10)
    
    if not success:
        print("Erro: Não foi possível iniciar monitorização contínua")
        return
    
    # Simular mudanças no estado do rover
    try:
        for i in range(5):
            time.sleep(12)  # Aguardar um pouco mais que o intervalo
            
            # Simular movimento
            x = i * 10.0
            y = i * 15.0
            agent.updatePosition(x, y, 0.0)
            
            # Simular mudança de estado
            if i == 0:
                agent.updateOperationalStatus("a caminho")
                agent.updateVelocity(1.0)
                agent.updateDirection(45.0)  # Nordeste
            elif i >= 2:
                agent.updateOperationalStatus("em missão")
                agent.updateVelocity(1.5)
                agent.updateDirection(90.0)  # Este
            
            # Simular consumo de bateria
            battery = 100.0 - (i * 2.0)
            agent.updateBattery(battery)
            
            # Simular aumento de temperatura
            temp = 20.0 + (i * 0.5)
            agent.updateTemperature(temp)
            
            print(f"\n[{i+1}] Estado atualizado:")
            print(f"  Posição: ({x}, {y}, 0.0)")
            print(f"  Estado: {agent.operational_status}")
            print(f"  Bateria: {battery}%")
            print(f"  Velocidade: {agent.velocity} m/s")
            print(f"  Direção: {agent.direction}°")
            print(f"  Temperatura: {temp}°C")
            print(f"  Monitorização ativa: {agent.isTelemetryRunning()}")
    
    except KeyboardInterrupt:
        print("\n\nParando monitorização contínua...")
        agent.stopContinuousTelemetry()
        print("Monitorização parada com sucesso!")
    
    # Verificar se ainda está em execução
    if agent.isTelemetryRunning():
        print("Parando monitorização...")
        agent.stopContinuousTelemetry()


def exemplo_telemetria_manual():
    """Exemplo de envio manual de telemetria (sem loop automático)."""
    print("\n" + "=" * 70)
    print("EXEMPLO: Telemetria Manual (sem loop automático)")
    print("=" * 70)
    
    agent = NMS_Agent.NMS_Agent("127.0.0.1")
    
    # Atualizar estado
    agent.updatePosition(50.0, 60.0, 0.0)
    agent.updateOperationalStatus("em missão")
    agent.updateBattery(75.0)
    agent.updateVelocity(1.5)
    agent.updateDirection(180.0)  # Sul
    
    # Enviar telemetria manualmente
    print("\nEnviando telemetria manual...")
    success = agent.createAndSendTelemetry("127.0.0.1")
    
    if success:
        print("✓ Telemetria enviada com sucesso!")
        
        # Mostrar estrutura da mensagem
        telemetry = agent.createTelemetryMessage()
        print("\nEstrutura da mensagem:")
        print(json.dumps(telemetry, indent=2))
    else:
        print("✗ Erro ao enviar telemetria")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("EXEMPLOS DE MONITORIZAÇÃO CONTÍNUA")
    print("=" * 70)
    
    try:
        # Exemplo 1: Monitorização contínua automática
        exemplo_monitorizacao_continua()
        
        # Exemplo 2: Telemetria manual
        exemplo_telemetria_manual()
        
    except Exception as e:
        print(f"\n✗ Erro ao executar exemplos: {e}")
        import traceback
        traceback.print_exc()

