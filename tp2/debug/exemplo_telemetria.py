"""
Exemplo de uso das novas funcionalidades de telemetria.

Este exemplo demonstra como usar os novos métodos para criar e enviar
mensagens de telemetria que cumprem os requisitos do PDF.
"""

from client import NMS_Agent
from otherEntities import Device
import json
import time

# Exemplo 1: Criar e enviar telemetria básica
def exemplo_telemetria_basica():
    """Exemplo de criação e envio de telemetria com campos obrigatórios."""
    print("=" * 70)
    print("EXEMPLO 1: Telemetria Básica")
    print("=" * 70)
    
    # Criar agente
    agent = NMS_Agent.NMS_Agent("127.0.0.1")  # IP da Nave-Mãe
    
    # Atualizar estado do rover
    agent.updatePosition(20.0, 30.0, 0.0)
    agent.updateOperationalStatus("em missão")
    agent.updateBattery(85.0)
    agent.updateVelocity(1.5)
    agent.updateTemperature(22.5)
    
    # Criar e enviar telemetria
    success = agent.createAndSendTelemetry("127.0.0.1")
    
    if success:
        print("✓ Telemetria enviada com sucesso!")
    else:
        print("✗ Erro ao enviar telemetria")


# Exemplo 2: Telemetria com métricas técnicas
def exemplo_telemetria_com_metricas():
    """Exemplo de criação de telemetria incluindo métricas técnicas."""
    print("\n" + "=" * 70)
    print("EXEMPLO 2: Telemetria com Métricas Técnicas")
    print("=" * 70)
    
    # Criar agente
    agent = NMS_Agent.NMS_Agent("127.0.0.1")
    
    # Simular métricas técnicas (normalmente recolhidas por Device.run())
    metrics = {
        "cpu_usage": 45.2,
        "ram_usage": 67.8,
        "bandwidth": "100 Mbps",
        "latency": "5 ms"
    }
    
    # Atualizar estado
    agent.updatePosition(35.0, 45.0, 0.0)
    agent.updateOperationalStatus("a caminho")
    agent.updateBattery(78.0)
    agent.updateVelocity(1.8)
    
    # Criar mensagem de telemetria (sem enviar)
    telemetry = agent.createTelemetryMessage(metrics)
    
    # Mostrar estrutura
    print("Estrutura da mensagem de telemetria:")
    print(json.dumps(telemetry, indent=2))
    
    # Validar
    is_valid, error = NMS_Agent.validateTelemetryMessage(telemetry)
    if is_valid:
        print("\n✓ Mensagem de telemetria válida!")
    else:
        print(f"\n✗ Mensagem inválida: {error}")


# Exemplo 3: Telemetria usando Device
def exemplo_telemetria_com_device():
    """Exemplo de criação de telemetria usando Device para recolher métricas."""
    print("\n" + "=" * 70)
    print("EXEMPLO 3: Telemetria com Device")
    print("=" * 70)
    
    # Criar agente
    agent = NMS_Agent.NMS_Agent("127.0.0.1")
    
    # Criar device (exemplo de configuração)
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
    
    # Criar mensagem de telemetria usando Device
    telemetry = device.createTelemetryMessage(
        client=agent,
        rover_id="r1",
        position={"x": 45.0, "y": 55.0, "z": 0.0},
        operational_status="em missão"
    )
    
    # Mostrar estrutura
    print("Estrutura da mensagem de telemetria:")
    print(json.dumps(telemetry, indent=2))
    
    # Validar
    is_valid, error = NMS_Agent.validateTelemetryMessage(telemetry)
    if is_valid:
        print("\n✓ Mensagem de telemetria válida!")
    else:
        print(f"\n✗ Mensagem inválida: {error}")


# Exemplo 4: Monitorização contínua
def exemplo_monitorizacao_continua():
    """Exemplo de monitorização contínua com envio periódico de telemetria."""
    print("\n" + "=" * 70)
    print("EXEMPLO 4: Monitorização Contínua")
    print("=" * 70)
    
    # Criar agente
    agent = NMS_Agent.NMS_Agent("127.0.0.1")
    
    # Estado inicial
    agent.updatePosition(0.0, 0.0, 0.0)
    agent.updateOperationalStatus("parado")
    agent.updateBattery(100.0)
    
    print("Iniciando monitorização contínua (5 iterações)...")
    
    for i in range(5):
        # Simular movimento
        x = i * 10.0
        y = i * 15.0
        agent.updatePosition(x, y, 0.0)
        
        # Simular mudança de estado
        if i == 0:
            agent.updateOperationalStatus("a caminho")
        elif i >= 3:
            agent.updateOperationalStatus("em missão")
        
        # Simular consumo de bateria
        battery = 100.0 - (i * 2.0)
        agent.updateBattery(battery)
        
        # Simular velocidade
        velocity = 1.0 + (i * 0.2)
        agent.updateVelocity(velocity)
        
        # Criar e enviar telemetria
        print(f"\nIteração {i+1}:")
        print(f"  Posição: ({x}, {y}, 0.0)")
        print(f"  Estado: {agent.operational_status}")
        print(f"  Bateria: {battery}%")
        print(f"  Velocidade: {velocity} m/s")
        
        # Em produção, descomentar para enviar:
        # success = agent.createAndSendTelemetry("127.0.0.1")
        # if success:
        #     print("  ✓ Telemetria enviada")
        # else:
        #     print("  ✗ Erro ao enviar")
        
        time.sleep(0.5)  # Simular intervalo entre envios
    
    print("\n✓ Monitorização contínua concluída!")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("EXEMPLOS DE USO - TELEMETRIA")
    print("=" * 70)
    
    # Executar exemplos
    try:
        exemplo_telemetria_basica()
        exemplo_telemetria_com_metricas()
        exemplo_telemetria_com_device()
        exemplo_monitorizacao_continua()
    except Exception as e:
        print(f"\n✗ Erro ao executar exemplos: {e}")
        import traceback
        traceback.print_exc()

