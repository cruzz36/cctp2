# Ground Control - Documentação

## Visão Geral

O **Ground Control** é um nó cliente que consome a API de Observação da Nave-Mãe, permitindo ao utilizador acompanhar a operação da missão em tempo real através de uma interface em linha de comandos.

## Requisitos do PDF Implementados

✅ **Rovers em operação e respetivo estado** - Visualização completa de todos os rovers registados  
✅ **Missões atribuídas e seu progresso** - Lista e detalhes de missões com progresso em tempo real  
✅ **Valores de telemetria mais recentes** - Últimos dados de telemetria de todos os rovers ou de um rover específico  

## Instalação

### Dependências

O Ground Control requer apenas a biblioteca `requests`:

```bash
pip install requests
```

Ou instalar todas as dependências do projeto:

```bash
pip install -r requirements.txt
```

## Execução

### Modo Interativo (Recomendado)

Execute o Ground Control sem argumentos para iniciar a interface interativa:

```bash
python GroundControl.py
```

A interface apresenta um menu com as seguintes opções:

1. **Dashboard completo** - Visão geral de todo o sistema
2. **Listar rovers** - Lista de todos os rovers registados
3. **Detalhes de um rover** - Informação detalhada de um rover específico
4. **Listar missões** - Lista de missões (com filtro opcional por status)
5. **Detalhes de uma missão** - Informação detalhada de uma missão específica
6. **Telemetria (todos os rovers)** - Últimos dados de telemetria de todos os rovers
7. **Telemetria de um rover específico** - Últimos dados de telemetria de um rover
8. **Estado geral do sistema** - Estatísticas gerais
9. **Atualização automática** - Dashboard com atualização periódica automática
0. **Sair** - Encerrar o Ground Control

### Modo Dashboard Único

Para mostrar o dashboard uma vez e sair (útil para scripts):

```bash
python GroundControl.py --dashboard
```

### Especificar URL da API

Por padrão, o Ground Control conecta-se a `http://localhost:8082`. Para especificar uma URL diferente:

```bash
python GroundControl.py --api http://10.0.4.10:8082
```

### Exemplos de Uso

#### 1. Interface Interativa (Padrão)

```bash
python GroundControl.py
```

Depois escolha uma opção do menu.

#### 2. Dashboard com Atualização Automática

```bash
python GroundControl.py
# Escolha opção 9
# Defina o intervalo de atualização (ex: 5 segundos)
# Pressione Ctrl+C para parar
```

#### 3. Consultar Rover Específico

```bash
python GroundControl.py
# Escolha opção 3
# Digite o ID do rover (ex: r1)
```

#### 4. Consultar Missões Ativas

```bash
python GroundControl.py
# Escolha opção 4
# Digite "active" para filtrar apenas missões ativas
```

#### 5. Ver Última Telemetria de um Rover

```bash
python GroundControl.py
# Escolha opção 7
# Digite o ID do rover (ex: r1)
# Digite o número de registos (ex: 5)
```

## Funcionalidades

### 1. Dashboard Completo

O dashboard apresenta uma visão consolidada do sistema:

- **Estado geral**: Total de rovers, missões ativas/pendentes/concluídas
- **Rovers**: Lista de todos os rovers com estado e missão atual
- **Missões ativas**: Lista de missões em execução
- **Última telemetria**: Últimos 5 registos de telemetria

### 2. Visualização de Rovers

Mostra para cada rover:
- ID do rover
- Endereço IP
- Estado (sempre "active" para rovers registados)
- Última atividade (timestamp da última telemetria)
- Missão atual (ID da missão ou "Nenhuma")

### 3. Detalhes de Rover

Informação completa de um rover específico:
- Informação básica (IP, estado, última atividade)
- Progresso da missão atual (percentual, estado, posição)
- Última telemetria recebida (posição, bateria, velocidade, etc.)

### 4. Visualização de Missões

Lista todas as missões com:
- ID da missão
- Rover atribuído
- Tipo de tarefa
- Estado (active, completed, pending)
- Duração e frequência de atualização
- Área geográfica
- Prioridade

Suporta filtro por status:
- `active` - Apenas missões ativas
- `completed` - Apenas missões concluídas
- `pending` - Apenas missões pendentes
- (vazio) - Todas as missões

### 5. Detalhes de Missão

Informação completa de uma missão específica:
- Informação básica (rover, tarefa, estado, duração, etc.)
- Área geográfica
- Instruções (se disponíveis)
- Progresso detalhado por rover:
  - Percentual de conclusão
  - Estado do progresso
  - Posição atual
  - Tempo decorrido e estimado para conclusão

### 6. Telemetria

Apresenta dados de telemetria mais recentes, incluindo:

**Campos obrigatórios (conforme PDF):**
- Identificação do rover
- Posição (coordenadas x, y, z)
- Estado operacional

**Campos opcionais:**
- Bateria (%)
- Velocidade (m/s)
- Direção (graus)
- Temperatura (°C)
- Saúde do sistema
- Métricas técnicas (CPU, RAM, latência, largura de banda)

Pode ser filtrado por rover específico e limitado no número de registos.

### 7. Estado Geral do Sistema

Estatísticas consolidadas:
- Total de rovers e rovers ativos
- Total de missões
- Missões ativas, pendentes e concluídas
- Timestamp da consulta

### 8. Atualização Automática

Modo de monitorização contínua:
- Atualiza o dashboard automaticamente a intervalos configuráveis
- Útil para acompanhamento em tempo real
- Pressione Ctrl+C para parar

## Formato de Apresentação

Toda a informação é apresentada de forma legível e organizada:

- **Separadores visuais**: Linhas de "=" para delimitar secções
- **Indentação**: Hierarquia clara de informação
- **Formatação de números**: Decimais formatados (ex: 75.0%, 1.50 m/s)
- **Timestamps**: Convertidos para formato legível (YYYY-MM-DD HH:MM:SS)
- **Posições**: Formatadas como (x.xx, y.yy, z.zz)
- **Valores ausentes**: Mostrados como "N/A" quando não disponíveis

## Tratamento de Erros

O Ground Control trata os seguintes erros:

- **Conexão recusada**: Verifica se a API está a correr
- **Timeout**: Verifica conectividade de rede
- **Erros HTTP**: Mostra código de status e mensagem
- **Recursos não encontrados**: Mensagem clara quando rover/missão não existe
- **Erros inesperados**: Captura e exibe mensagem de erro

## Integração com a Topologia

O Ground Control deve ser adicionado à topologia como um nó separado, ligado à Nave-Mãe:

```
[Ground Control] ----(HTTP)----> [Nave-Mãe (API:8082)]
```

O Ground Control atua apenas como **cliente** da API, não requerendo portas específicas ou configuração de rede especial além de conectividade HTTP com a Nave-Mãe.

## Limitações e Melhorias Futuras

### Limitações Atuais:

1. **Interface texto apenas**: Não possui interface gráfica
2. **Sem representação gráfica de mobilidade**: Não mostra mapa/grelha de posições
3. **Sem histórico persistente**: Não armazena dados localmente
4. **Sem alertas**: Não notifica sobre eventos importantes

### Melhorias Possíveis:

1. **Interface gráfica**: Usar bibliotecas como `tkinter` ou `PyQt` para GUI
2. **Representação gráfica de mobilidade**: 
   - Mapa 2D mostrando posições dos rovers
   - Histórico de trajetórias
   - Grelha de coordenadas
3. **Histórico local**: Armazenar dados de telemetria localmente para análise
4. **Alertas e notificações**: Notificar sobre eventos importantes (bateria baixa, erros, etc.)
5. **Exportação de dados**: Exportar dados para CSV/JSON
6. **Gráficos**: Visualização de métricas ao longo do tempo
7. **Filtros avançados**: Mais opções de filtragem e pesquisa

## Exemplos de Saída

### Dashboard

```
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

...
```

### Telemetria

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
Latência:            5 ms
Largura de Banda:    100 Mbps
...
```

## Troubleshooting

### Erro: "Não foi possível conectar à API"

**Causa**: A API de Observação não está a correr ou a URL está incorreta.

**Solução**:
1. Verifique se a Nave-Mãe está a correr
2. Verifique se a API de Observação foi iniciada (`server.startObservationAPI()`)
3. Verifique a URL da API (padrão: `http://localhost:8082`)
4. Se a Nave-Mãe estiver noutro nó, use `--api` para especificar a URL correta

### Erro: "requests não encontrada"

**Causa**: Biblioteca `requests` não está instalada.

**Solução**:
```bash
pip install requests
```

### Timeout ao conectar

**Causa**: Problemas de conectividade de rede ou API muito lenta.

**Solução**:
1. Verifique conectividade de rede
2. Verifique se não há firewall bloqueando
3. Aumente o timeout no código se necessário

## Conclusão

O Ground Control fornece uma interface completa e funcional para monitorização do sistema NMS, implementando todos os requisitos do PDF. A interface em linha de comandos é simples, eficiente e adequada para acompanhamento em tempo real das operações da missão.

---

**Versão**: 1.0  
**Data**: 2024  
**Autor**: Sistema de Documentação Automática

