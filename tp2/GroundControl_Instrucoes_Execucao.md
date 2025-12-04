# Ground Control - Instruções de Execução

## Pré-requisitos

1. **Nave-Mãe a correr**: O servidor NMS deve estar ativo
2. **API de Observação ativa**: A API deve estar a correr na porta 8082 (padrão)
3. **Dependências instaladas**: `requests` (ou todas as dependências via `requirements.txt`)

## Instalação Rápida

```bash
# Instalar dependências
pip install requests

# Ou instalar todas as dependências do projeto
pip install -r requirements.txt
```

## Execução Básica

### 1. Interface Interativa (Recomendado)

```bash
python GroundControl.py
```

**Saída esperada:**
```
Conectando à API em http://localhost:8082...
[OK] Conexão estabelecida com sucesso!

================================================================================
GROUND CONTROL - INTERFACE INTERATIVA
================================================================================

Comandos disponíveis:
  1 - Dashboard completo
  2 - Listar rovers
  3 - Detalhes de um rover
  4 - Listar missões
  5 - Detalhes de uma missão
  6 - Telemetria (todos os rovers)
  7 - Telemetria de um rover específico
  8 - Estado geral do sistema
  9 - Atualização automática (dashboard)
  0 - Sair
================================================================================

Escolha uma opção:
```

### 2. Dashboard Único

```bash
python GroundControl.py --dashboard
```

**Saída esperada:**
```
Conectando à API em http://localhost:8082...
[OK] Conexão estabelecida com sucesso!

================================================================================
GROUND CONTROL - DASHBOARD
Atualizado: 2024-01-01 12:00:00
================================================================================

============================================================
ESTADO GERAL DO SISTEMA
============================================================
Total de Rovers:        3
Rovers Ativos:          3
Total de Missões:       5
Missões Ativas:          2
Missões Pendentes:       1
Missões Concluídas:     2
Timestamp:               2024-01-01 12:00:00
============================================================

[... resto do dashboard ...]
```

### 3. Especificar URL da API

Se a Nave-Mãe estiver noutro nó:

```bash
python GroundControl.py --api http://10.0.4.10:8082
```

## Exemplos de Utilização

### Exemplo 1: Ver Estado Geral do Sistema

**Comando:**
```bash
python GroundControl.py
# Escolha opção 8
```

**Saída:**
```
============================================================
ESTADO GERAL DO SISTEMA
============================================================
Total de Rovers:        3
Rovers Ativos:          3
Total de Missões:       5
Missões Ativas:          2
Missões Pendentes:       1
Missões Concluídas:     2
Timestamp:               2024-01-01 12:00:00
============================================================
```

### Exemplo 2: Listar Todos os Rovers

**Comando:**
```bash
python GroundControl.py
# Escolha opção 2
```

**Saída:**
```
================================================================================
ROVERS EM OPERAÇÃO
================================================================================

Rover ID: r1
  IP:              10.0.4.11
  Estado:          active
  Última Atividade: 2024-01-01 12:00:00
  Missão Atual:    M-001

Rover ID: r2
  IP:              10.0.4.12
  Estado:          active
  Última Atividade: 2024-01-01 11:59:30
  Missão Atual:    Nenhuma

Rover ID: r3
  IP:              10.0.4.13
  Estado:          active
  Última Atividade: 2024-01-01 11:58:15
  Missão Atual:    M-002

================================================================================
```

### Exemplo 3: Detalhes de um Rover Específico

**Comando:**
```bash
python GroundControl.py
# Escolha opção 3
# Digite: r1
```

**Saída:**
```
================================================================================
DETALHES DO ROVER: r1
================================================================================

Informação Básica:
  IP:              10.0.4.11
  Estado:          active
  Última Atividade: 2024-01-01 12:00:00
  Missão Atual:    M-001

Progresso da Missão:
  Progresso:      45%
  Estado:         in_progress
  Posição Atual:  (25.50, 35.20, 0.00)

Última Telemetria:
  Timestamp:           2024-01-01 12:00:00
  Posição:             (10.50, 20.30, 0.00)
  Estado Operacional:  em missão
  Bateria:             75.0%
  Velocidade:          1.50 m/s
  Direção:             45.0°
  Temperatura:         25.0°C
  Saúde do Sistema:    operacional
  CPU:                 45.2%
  RAM:                 60.5%
  Latência:            5 ms
  Largura de Banda:    100 Mbps

================================================================================
```

### Exemplo 4: Listar Missões Ativas

**Comando:**
```bash
python GroundControl.py
# Escolha opção 4
# Digite: active
```

**Saída:**
```
================================================================================
MISSÕES (ACTIVE)
================================================================================

Missão ID: M-001
  Rover:              r1
  Tarefa:             capture_images
  Estado:             active
  Duração:            30 minutos
  Frequência Update:  120 segundos
  Prioridade:         high
  Área Geográfica:    (10.00, 20.00) a (50.00, 60.00)

Missão ID: M-002
  Rover:              r3
  Tarefa:             sample_collection
  Estado:             active
  Duração:            45 minutos
  Frequência Update:  60 segundos
  Prioridade:         medium
  Área Geográfica:    (15.00, 25.00) a (55.00, 65.00)

================================================================================
```

### Exemplo 5: Detalhes de uma Missão

**Comando:**
```bash
python GroundControl.py
# Escolha opção 5
# Digite: M-001
```

**Saída:**
```
================================================================================
DETALHES DA MISSÃO: M-001
================================================================================

Informação Básica:
  Rover:              r1
  Tarefa:             capture_images
  Estado:             active
  Duração:            30 minutos
  Frequência Update:  120 segundos
  Prioridade:         high
  Área Geográfica:    (10.00, 20.00) a (50.00, 60.00)
  Instruções:          Capturar imagens de alta resolução

Progresso:
  Rover r1:
    Progresso:      45%
    Estado:         in_progress
    Posição Atual:  (25.50, 35.20, 0.00)
    Tempo Decorrido: 13.5 minutos
    Tempo Restante:  16.5 minutos

================================================================================
```

### Exemplo 6: Ver Última Telemetria

**Comando:**
```bash
python GroundControl.py
# Escolha opção 6
# Digite: 5 (número de registos)
```

**Saída:**
```
================================================================================
TELEMETRIA
================================================================================

--- Registo 1 ---
Timestamp:           2024-01-01 12:00:00
Posição:             (10.50, 20.30, 0.00)
Estado Operacional:  em missão
Bateria:             75.0%
Velocidade:          1.50 m/s
Direção:             45.0°
Temperatura:         25.0°C
Saúde do Sistema:    operacional
CPU:                 45.2%
RAM:                 60.5%
Latência:            5 ms
Largura de Banda:    100 Mbps

--- Registo 2 ---
Timestamp:           2024-01-01 11:59:30
Posição:             (15.20, 25.80, 0.00)
Estado Operacional:  a caminho
Bateria:             80.0%
Velocidade:          2.00 m/s
Direção:             90.0°
Temperatura:         22.0°C
Saúde do Sistema:    operacional

[... mais registos ...]

================================================================================
```

### Exemplo 7: Telemetria de um Rover Específico

**Comando:**
```bash
python GroundControl.py
# Escolha opção 7
# Digite: r1
# Digite: 3 (número de registos)
```

**Saída:**
```
================================================================================
TELEMETRIA - r1
================================================================================

--- Registo 1 ---
Timestamp:           2024-01-01 12:00:00
Posição:             (10.50, 20.30, 0.00)
Estado Operacional:  em missão
Bateria:             75.0%
Velocidade:          1.50 m/s
Direção:             45.0°
Temperatura:         25.0°C
Saúde do Sistema:    operacional
CPU:                 45.2%
RAM:                 60.5%

--- Registo 2 ---
[...]

================================================================================
```

### Exemplo 8: Atualização Automática (Dashboard)

**Comando:**
```bash
python GroundControl.py
# Escolha opção 9
# Digite: 5 (intervalo em segundos)
```

**Saída:**
```
Atualização automática ativada. Pressione Ctrl+C para parar.
Intervalo em segundos (default 5): 5

================================================================================
GROUND CONTROL - DASHBOARD
Atualizado: 2024-01-01 12:00:00
================================================================================

[... dashboard completo ...]

Próxima atualização em 5 segundos... (Ctrl+C para parar)
```

O dashboard será atualizado automaticamente a cada 5 segundos até pressionar Ctrl+C.

## Exemplo de Sessão Completa

Aqui está um exemplo de uma sessão completa de utilização:

```
$ python GroundControl.py

Conectando à API em http://localhost:8082...
[OK] Conexão estabelecida com sucesso!

================================================================================
GROUND CONTROL - INTERFACE INTERATIVA
================================================================================

Comandos disponíveis:
  1 - Dashboard completo
  2 - Listar rovers
  3 - Detalhes de um rover
  4 - Listar missões
  5 - Detalhes de uma missão
  6 - Telemetria (todos os rovers)
  7 - Telemetria de um rover específico
  8 - Estado geral do sistema
  9 - Atualização automática (dashboard)
  0 - Sair
================================================================================

Escolha uma opção: 1

================================================================================
GROUND CONTROL - DASHBOARD
Atualizado: 2024-01-01 12:00:00
================================================================================

============================================================
ESTADO GERAL DO SISTEMA
============================================================
Total de Rovers:        3
Rovers Ativos:          3
Total de Missões:       5
Missões Ativas:          2
Missões Pendentes:       1
Missões Concluídas:     2
Timestamp:               2024-01-01 12:00:00
============================================================

================================================================================
ROVERS EM OPERAÇÃO
================================================================================

Rover ID: r1
  IP:              10.0.4.11
  Estado:          active
  Última Atividade: 2024-01-01 12:00:00
  Missão Atual:    M-001

[... mais rovers ...]

Escolha uma opção: 3
ID do rover: r1

================================================================================
DETALHES DO ROVER: r1
================================================================================

[... detalhes completos ...]

Escolha uma opção: 0

A encerrar Ground Control...
```

## Execução em Scripts

Para usar o Ground Control em scripts Python:

```python
from GroundControl import GroundControl

# Criar instância
gc = GroundControl(api_url="http://localhost:8082")

# Verificar conexão
if gc._make_request('/status') is None:
    print("Erro: API não disponível")
    exit(1)

# Mostrar dashboard
gc.show_dashboard()

# Obter dados programaticamente
rovers_data = gc._make_request('/rovers')
if rovers_data:
    for rover in rovers_data.get('rovers', []):
        print(f"Rover {rover['rover_id']}: {rover['status']}")
```

## Troubleshooting

### Erro: "Não foi possível conectar à API"

**Causa**: API não está a correr ou URL incorreta.

**Solução**:
1. Verifique se a Nave-Mãe está a correr
2. Verifique se `server.startObservationAPI()` foi chamado
3. Verifique a porta (padrão: 8082)
4. Use `--api` para especificar URL correta

### Erro: "requests não encontrada"

**Solução**:
```bash
pip install requests
```

### Timeout

**Solução**: Verifique conectividade de rede e firewall.

## Integração na Topologia

Para adicionar o Ground Control à topologia:

1. **Criar nó Ground Control** na topologia (ex: `ground_control`)
2. **Ligar à Nave-Mãe** (conectividade de rede)
3. **Executar o Ground Control** no nó:
   ```bash
   python GroundControl.py --api http://<IP_NAVE_MAE>:8082
   ```

O Ground Control não requer configuração especial de rede, apenas conectividade HTTP com a Nave-Mãe.

## Conclusão

O Ground Control fornece uma interface completa e funcional para monitorização do sistema NMS. Siga estas instruções para executar e utilizar todas as funcionalidades disponíveis.

Para mais informações, consulte `GroundControl_README.md`.

