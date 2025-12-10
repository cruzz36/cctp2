# Guia de Diagnóstico de Problemas de Conexão

Este documento ajuda a diagnosticar e resolver problemas de conexão entre Ground Control, Rovers e a Nave-Mãe.

## Problemas Comuns e Soluções

### 1. Ground Control não consegue conectar à API

**Sintomas:**
```
[ERRO] Não foi possível conectar à API em http://10.0.1.10:8082
```

**Verificações:**

1. **Verificar se a Nave-Mãe está a correr:**
   ```bash
   # No nó Nave-Mãe
   python3 start_nms.py
   ```
   
   Deve ver:
   ```
   [OK] MissionLink (UDP:8080) iniciado
   [OK] TelemetryStream (TCP:8081) iniciado
   [OK] API de Observação (HTTP:8082) iniciada
   ```

2. **Verificar se Flask está instalado:**
   ```bash
   pip3 install flask requests
   # ou
   pip3 install -r requirements.txt
   ```

3. **Testar conectividade de rede:**
   ```bash
   # No nó Ground Control
   ping 10.0.1.10
   curl http://10.0.1.10:8082/health
   ```

4. **Verificar se a porta 8082 está a escutar:**
   ```bash
   # No nó Nave-Mãe
   netstat -tuln | grep 8082
   # ou
   ss -tuln | grep 8082
   ```

5. **Verificar logs da Nave-Mãe:**
   - Deve mostrar: `[OK] API de Observação (HTTP:8082) iniciada`
   - Deve mostrar: `[INFO] API acessível em: http://10.0.1.10:8082`

### 2. Rovers não conseguem conectar à Nave-Mãe

**Sintomas:**
- Rovers não aparecem na lista de rovers ativos
- Mensagens de erro no registo

**Verificações:**

1. **Verificar se a Nave-Mãe está a correr:**
   ```bash
   # No nó Nave-Mãe
   python3 start_nms.py
   ```

2. **Verificar IP da Nave-Mãe:**
   ```bash
   # No nó Nave-Mãe
   ip addr show
   # ou
   hostname -I
   ```
   
   Deve usar o IP correto (10.0.1.10) ao iniciar o rover:
   ```bash
   python3 start_rover.py 10.0.1.10 r1
   ```

3. **Verificar conectividade UDP (porta 8080):**
   ```bash
   # No nó Rover
   nc -u -v 10.0.1.10 8080
   ```

4. **Verificar se a porta UDP 8080 está a escutar:**
   ```bash
   # No nó Nave-Mãe
   netstat -uln | grep 8080
   ```

5. **Verificar logs do Rover:**
   - Deve mostrar: `[OK] Registado como r1`
   - Se falhar, verificar mensagens de erro

### 3. API não inicia

**Sintomas:**
- Nave-Mãe inicia mas não mostra `[OK] API de Observação`
- Mensagem: `[AVISO] API de Observação não disponível`

**Soluções:**

1. **Instalar Flask:**
   ```bash
   pip3 install flask>=2.3.0
   ```

2. **Verificar se há conflito de porta:**
   ```bash
   # Matar processos usando a porta 8082
   fuser -k 8082/tcp
   # ou
   lsof -ti:8082 | xargs kill -9
   ```

3. **Verificar permissões:**
   - Certifique-se de que tem permissão para escutar na porta 8082
   - Em alguns sistemas, portas < 1024 requerem privilégios root

### 4. Problemas de Rede no CORE

**Verificações:**

1. **Verificar topologia:**
   - Certifique-se de que os nós estão na mesma rede
   - Verifique se os IPs estão corretos na topologia

2. **Testar conectividade básica:**
   ```bash
   # De qualquer nó
   ping <IP_DO_OUTRO_NO>
   ```

3. **Verificar rotas:**
   ```bash
   ip route show
   ```

## Comandos Úteis de Diagnóstico

### Verificar processos Python a correr:
```bash
ps aux | grep python
```

### Verificar portas em uso:
```bash
netstat -tuln | grep -E '8080|8081|8082'
```

### Testar API manualmente:
```bash
curl http://10.0.1.10:8082/health
curl http://10.0.1.10:8082/status
curl http://10.0.1.10:8082/rovers
```

### Ver logs em tempo real:
```bash
# No nó Nave-Mãe
python3 start_nms.py 2>&1 | tee nms.log

# No nó Ground Control
python3 start_ground_control.py 2>&1 | tee gc.log

# No nó Rover
python3 start_rover.py 10.0.1.10 r1 2>&1 | tee rover.log
```

## Ordem Recomendada de Inicialização

1. **Iniciar Nave-Mãe primeiro:**
   ```bash
   python3 start_nms.py
   ```
   Aguardar até ver todas as mensagens `[OK]`

2. **Iniciar Rovers:**
   ```bash
   python3 start_rover.py 10.0.1.10 r1
   python3 start_rover.py 10.0.1.10 r2
   ```

3. **Iniciar Ground Control:**
   ```bash
   python3 start_ground_control.py
   ```

## Melhorias Implementadas

As seguintes melhorias foram adicionadas ao código:

1. **Retries automáticos:** Ground Control e Rovers tentam conectar várias vezes antes de falhar
2. **Melhor logging:** Mensagens de erro mais informativas
3. **Health check endpoint:** `/health` para verificar se a API está a funcionar
4. **Verificação de inicialização:** Verifica se a API iniciou corretamente
5. **Delays apropriados:** Pequenos delays para garantir que serviços estão prontos

## Contacto

Se os problemas persistirem, verifique:
- Logs detalhados de cada componente
- Conectividade de rede entre nós
- Versões das dependências (Flask, requests)
- Configuração da topologia CORE

