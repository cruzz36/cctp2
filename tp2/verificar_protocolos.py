"""
Script para verificar se o envio e receção dos protocolos estão corretos
de acordo com o enunciado do TP2.

Este script adiciona prints que mostram:
1. Formato exato das mensagens sendo enviadas (string e bytes)
2. Formato exato das mensagens sendo recebidas (bytes e string decodificada)
3. Verificação se está de acordo com o enunciado
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ler os ficheiros originais e adicionar prints de verificação
def add_verification_prints():
    """Adiciona prints de verificação nos protocolos"""
    
    # MissionLink - formatMessage
    missionlink_path = "protocol/MissionLink.py"
    with open(missionlink_path, "r", encoding="utf-8") as f:
        ml_content = f.read()
    
    # Verificar se já tem prints de verificação
    if "[VERIFICAÇÃO MissionLink]" in ml_content:
        print("⚠ MissionLink já tem prints de verificação")
        return
    
    # Adicionar prints no formatMessage (envio)
    old_format = '''if missionType != None: 
            return f"{flag}|{idMission}|{seqNum}|{ackNum}|{len(message)}|{missionType}|{message}".encode()'''
    
    new_format = '''if missionType != None: 
            msg_string = f"{flag}|{idMission}|{seqNum}|{ackNum}|{len(message)}|{missionType}|{message}"
            msg_bytes = msg_string.encode()
            print(f"[VERIFICAÇÃO MissionLink ENVIO]")
            print(f"  Formato esperado: flag|idMission|seq|ack|size|missionType|message")
            print(f"  String: {msg_string}")
            print(f"  Bytes (hex): {msg_bytes.hex()}")
            print(f"  ✓ Enviado em binário (bytes)")
            return msg_bytes'''
    
    ml_content = ml_content.replace(old_format, new_format)
    
    # Adicionar prints no else também
    old_format_else = '''return f"{flag}|{idMission}|{seqNum}|{ackNum}|{len(message)}|N|{message}".encode()'''
    
    new_format_else = '''msg_string = f"{flag}|{idMission}|{seqNum}|{ackNum}|{len(message)}|N|{message}"
            msg_bytes = msg_string.encode()
            print(f"[VERIFICAÇÃO MissionLink ENVIO]")
            print(f"  Formato esperado: flag|idMission|seq|ack|size|missionType|message")
            print(f"  String: {msg_string}")
            print(f"  Bytes (hex): {msg_bytes.hex()}")
            print(f"  ✓ Enviado em binário (bytes)")
            return msg_bytes'''
    
    ml_content = ml_content.replace(old_format_else, new_format_else)
    
    # Adicionar prints na receção (primeira mensagem)
    old_recv = '''firstMessage,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
                lista = firstMessage.decode().split("|")'''
    
    new_recv = '''firstMessage,(ip,port) = self.sock.recvfrom(self.limit.buffersize)
                print(f"[VERIFICAÇÃO MissionLink RECEÇÃO]")
                print(f"  Bytes recebidos (hex): {firstMessage.hex()}")
                print(f"  ✓ Recebido em binário (bytes)")
                lista = firstMessage.decode().split("|")
                print(f"  String após decode: {'|'.join(lista)}")
                print(f"  Formato verificado: flag|idMission|seq|ack|size|missionType|message")
                print(f"  ✓ Decodificado corretamente para string")'''
    
    ml_content = ml_content.replace(old_recv, new_recv, 1)
    
    # Adicionar prints na receção de chunks
    old_recv_chunk = '''chunks, (ip,port) = self.sock.recvfrom(self.limit.buffersize)
                    lista = chunks.decode().split("|")'''
    
    new_recv_chunk = '''chunks, (ip,port) = self.sock.recvfrom(self.limit.buffersize)
                    print(f"[VERIFICAÇÃO MissionLink RECEÇÃO]")
                    print(f"  Bytes recebidos (hex): {chunks.hex()[:100]}...")
                    print(f"  ✓ Recebido em binário (bytes)")
                    lista = chunks.decode().split("|")
                    print(f"  String após decode: {'|'.join(lista[:7])}...")
                    print(f"  ✓ Decodificado corretamente para string")'''
    
    ml_content = ml_content.replace(old_recv_chunk, new_recv_chunk, 1)
    
    # Guardar backup
    backup_path = missionlink_path + ".backup_verificacao"
    with open(backup_path, "w", encoding="utf-8") as f:
        with open(missionlink_path, "r", encoding="utf-8") as orig:
            f.write(orig.read())
    print(f"✓ Backup criado: {backup_path}")
    
    # Escrever ficheiro modificado
    with open(missionlink_path, "w", encoding="utf-8") as f:
        f.write(ml_content)
    
    print(f"✓ Prints de verificação adicionados a {missionlink_path}")
    
    # TelemetryStream - send
    telemetry_path = "protocol/TelemetryStream.py"
    with open(telemetry_path, "r", encoding="utf-8") as f:
        ts_content = f.read()
    
    # Verificar se já tem prints de verificação
    if "[VERIFICAÇÃO TelemetryStream]" in ts_content:
        print("⚠ TelemetryStream já tem prints de verificação")
        return
    
    # Adicionar prints no send
    old_send_length = '''length = self.formatInteger(len(filename))
            client_socket.sendall(length.encode())'''
    
    new_send_length = '''length = self.formatInteger(len(filename))
            length_bytes = length.encode()
            print(f"[VERIFICAÇÃO TelemetryStream ENVIO]")
            print(f"  Formato esperado: [tamanho_nome(4 bytes)][nome_ficheiro][conteúdo_ficheiro]")
            print(f"  Tamanho do nome (string): {length}")
            print(f"  Tamanho do nome (bytes hex): {length_bytes.hex()}")
            print(f"  ✓ Enviado em binário (bytes)")
            client_socket.sendall(length_bytes)'''
    
    ts_content = ts_content.replace(old_send_length, new_send_length)
    
    old_send_filename = '''client_socket.sendall(filename.encode())'''
    
    new_send_filename = '''filename_bytes = filename.encode()
            print(f"  Nome do ficheiro (string): {filename}")
            print(f"  Nome do ficheiro (bytes hex): {filename_bytes.hex()}")
            print(f"  ✓ Enviado em binário (bytes)")
            client_socket.sendall(filename_bytes)'''
    
    ts_content = ts_content.replace(old_send_filename, new_send_filename)
    
    old_send_content = '''while buffer != "":
                    client_socket.sendall(buffer.encode())
                    buffer = file.read(self.limit.buffersize)'''
    
    new_send_content = '''chunk_num = 0
                while buffer != "":
                    buffer_bytes = buffer.encode()
                    print(f"  Chunk {chunk_num} conteúdo (primeiros 50 chars): {buffer[:50]}...")
                    print(f"  Chunk {chunk_num} (bytes hex): {buffer_bytes.hex()[:100]}...")
                    print(f"  ✓ Enviado em binário (bytes)")
                    client_socket.sendall(buffer_bytes)
                    buffer = file.read(self.limit.buffersize)
                    chunk_num += 1'''
    
    ts_content = ts_content.replace(old_send_content, new_send_content)
    
    # Adicionar prints no recv
    old_recv_length = '''message = clientSock.recv(lenMessageSize)
            if len(message) != lenMessageSize:'''
    
    new_recv_length = '''message = clientSock.recv(lenMessageSize)
            print(f"[VERIFICAÇÃO TelemetryStream RECEÇÃO]")
            print(f"  Formato esperado: [tamanho_nome(4 bytes)][nome_ficheiro][conteúdo_ficheiro]")
            print(f"  Tamanho do nome recebido (bytes hex): {message.hex()}")
            print(f"  ✓ Recebido em binário (bytes)")
            if len(message) != lenMessageSize:'''
    
    ts_content = ts_content.replace(old_recv_length, new_recv_length)
    
    old_recv_filename = '''filename = clientSock.recv(fileNameLen)
            if len(filename) != fileNameLen:'''
    
    new_recv_filename = '''filename = clientSock.recv(fileNameLen)
            print(f"  Nome do ficheiro recebido (bytes hex): {filename.hex()}")
            print(f"  ✓ Recebido em binário (bytes)")
            if len(filename) != fileNameLen:'''
    
    ts_content = ts_content.replace(old_recv_filename, new_recv_filename)
    
    old_recv_content = '''message = clientSock.recv(self.limit.buffersize)
                while message != b"":
                    file.write(message.decode())
                    message = clientSock.recv(self.limit.buffersize)'''
    
    new_recv_content = '''message = clientSock.recv(self.limit.buffersize)
                chunk_num = 0
                while message != b"":
                    print(f"  Chunk {chunk_num} recebido (bytes hex): {message.hex()[:100]}...")
                    print(f"  ✓ Recebido em binário (bytes)")
                    decoded = message.decode()
                    print(f"  Chunk {chunk_num} decodificado (primeiros 50 chars): {decoded[:50]}...")
                    print(f"  ✓ Decodificado corretamente para string")
                    file.write(decoded)
                    message = clientSock.recv(self.limit.buffersize)
                    chunk_num += 1'''
    
    ts_content = ts_content.replace(old_recv_content, new_recv_content)
    
    # Guardar backup
    backup_path = telemetry_path + ".backup_verificacao"
    with open(backup_path, "w", encoding="utf-8") as f:
        with open(telemetry_path, "r", encoding="utf-8") as orig:
            f.write(orig.read())
    print(f"✓ Backup criado: {backup_path}")
    
    # Escrever ficheiro modificado
    with open(telemetry_path, "w", encoding="utf-8") as f:
        f.write(ts_content)
    
    print(f"✓ Prints de verificação adicionados a {telemetry_path}")
    print("\n✓ Concluído! Execute o seu código normalmente para ver as verificações.")
    print("  Os prints mostrarão se o envio/receção está correto de acordo com o enunciado.")


def remove_verification_prints():
    """Remove prints de verificação e restaura backups"""
    files = ["protocol/MissionLink.py", "protocol/TelemetryStream.py"]
    
    for file_path in files:
        backup_path = file_path + ".backup_verificacao"
        if os.path.exists(backup_path):
            with open(backup_path, "r", encoding="utf-8") as f:
                content = f.read()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ {file_path} restaurado do backup")
        else:
            print(f"⚠ Backup não encontrado para {file_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Verificar formato de envio/receção dos protocolos")
    parser.add_argument("--remove", action="store_true", help="Remover prints de verificação e restaurar backups")
    
    args = parser.parse_args()
    
    if args.remove:
        remove_verification_prints()
    else:
        add_verification_prints()

