#!/bin/bash
# Script para aplicar rotas de rede automaticamente baseado no hostname
# Usado nos blocos services do topologiatp2.imn

HOSTNAME=$(hostname)

case $HOSTNAME in
    NaveMae)
        # Aguardar interfaces estarem prontas
        sleep 1
        # Aplicar rotas para redes dos rovers via Satelite
        ip route add 10.0.2.0/24 via 10.0.1.1 2>/dev/null || true
        ip route add 10.0.3.0/24 via 10.0.1.1 2>/dev/null || true
        ;;
    GroundControl)
        # Aguardar interfaces estarem prontas
        sleep 1
        # Aplicar rota para rede da NaveMae
        ip route add 10.0.1.0/24 via 10.0.0.11 2>/dev/null || true
        ;;
    Satelite)
        # Aguardar interfaces estarem prontas
        sleep 1
        # Habilitar IP forwarding
        echo 1 > /proc/sys/net/ipv4/ip_forward 2>/dev/null || true
        sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1 || true
        # Aplicar packet loss de 1% por pacote na interface eth2 (link para Rover1)
        # Usando netem para packet loss por pacote (não por bit como BER)
        tc qdisc del dev eth2 root 2>/dev/null || true  # Remover configuração anterior se existir
        tc qdisc add dev eth2 root netem loss 1% 2>/dev/null || true
        ;;
    Rover1)
        # Aguardar interfaces estarem prontas
        sleep 1
        # Aplicar rota default via Satelite
        ip route add default via 10.0.3.1 2>/dev/null || true
        # Aplicar packet loss de 1% por pacote na interface eth0 (link para Satelite)
        # Usando netem para packet loss por pacote (não por bit como BER)
        tc qdisc del dev eth0 root 2>/dev/null || true  # Remover configuração anterior se existir
        tc qdisc add dev eth0 root netem loss 1% 2>/dev/null || true
        ;;
    Rover2)
        # Aguardar interfaces estarem prontas
        sleep 1
        # Aplicar rota default via Satelite
        ip route add default via 10.0.2.1 2>/dev/null || true
        ;;
esac

exit 0

