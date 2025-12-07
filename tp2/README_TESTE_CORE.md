# Guia de Teste Automatizado no CORE

Este guia explica como testar o sistema dentro do CORE usando scripts automatizados.

## Scripts de Teste Disponíveis

### 1. `test_core_automated.py`
Script Python que testa todas as funcionalidades básicas em cada nó.

**Uso:**
```bash
# Em qualquer nó do CORE
cd /tmp/nms
python3 test_core_automated.py [node_type]
```

**Tipos de nó:**
- `nms` - Para nó Nave-Mãe (n1)
- `rover` - Para nó Rover (n3, n4)
- `ground_control` - Para nó Ground Control (n2)
- `auto` - Detecta automaticamente (padrão)

**O que testa:**
- ✓ Imports de todos os módulos
- ✓ Criação de instâncias (NMS_Server, NMS_Agent)
- ✓ Estrutura de ficheiros
- ✓ Informações de rede
- ✓ Funcionalidades básicas

### 2. `test_core_integration.sh`
Script bash para teste rápido de integração.

**Uso:**
```bash
cd /tmp/nms
chmod +x test_core_integration.sh
./test_core_integration.sh
```

## Passo a Passo para Testar no CORE

### Passo 1: Preparar Ambiente

1. **Abrir CORE e carregar topologia:**
   - File → Open → `topologiatp2.imn`
   - Start the session (▶️)

2. **Copiar ficheiros para todos os nós:**
   - Usar File Transfer do CORE ou diretório partilhado
   - Descompactar em `/tmp/nms` em cada nó

3. **Instalar dependências em cada nó:**
   ```bash
   cd /tmp/nms
   pip3 install -r requirements.txt
   ```

### Passo 2: Executar Testes em Cada Nó

#### No nó n1 (NaveMae):
```bash
cd /tmp/nms
python3 test_core_automated.py nms
```

**Saída esperada:**
```
============================================================
TESTE AUTOMATIZADO PARA CORE
============================================================

Nó: NaveMae (10.0.1.10)
Tipo detectado: nms
...

✓ TODOS OS TESTES PASSARAM!
```

#### No nó n3 (Rover1):
```bash
cd /tmp/nms
python3 test_core_automated.py rover
```

#### No nó n4 (Rover2):
```bash
cd /tmp/nms
python3 test_core_automated.py rover
```

#### No nó n2 (GroundControl):
```bash
cd /tmp/nms
python3 test_core_automated.py ground_control
```

### Passo 3: Teste de Integração Completo

Após todos os testes individuais passarem:

1. **Iniciar Nave-Mãe (n1):**
   ```bash
   cd /tmp/nms
   python3 start_nms.py
   ```
   Aguardar mensagem: "Nave-Mãe pronta e a escutar!"

2. **Iniciar Rover1 (n3):**
   ```bash
   cd /tmp/nms
   python3 start_rover.py 10.0.1.10 r1
   ```
   Verificar: "Registado como r1" e "Telemetria contínua ativa"

3. **Iniciar Rover2 (n4):**
   ```bash
   cd /tmp/nms
   python3 start_rover.py 10.0.1.10 r2
   ```
   Verificar: "Registado como r2" e "Telemetria contínua ativa"

4. **Verificar no servidor (n1):**
   - Deve mostrar mensagens de conexão dos rovers
   - Deve mostrar receção de telemetria

5. **Testar Ground Control (n2):**
   ```bash
   cd /tmp/nms
   python3 start_ground_control.py
   ```
   - Escolher opção 1 (Dashboard completo)
   - Verificar que mostra rovers e telemetria

## Interpretação dos Resultados

### ✓ Teste Passou
- O componente está funcionando corretamente
- Pode prosseguir para o próximo teste

### ✗ Teste Falhou
- Verificar mensagem de erro específica
- Verificar se dependências estão instaladas
- Verificar estrutura de ficheiros

### ⚠ Aviso
- Funcionalidade opcional não disponível
- Não impede execução, mas algumas features podem não funcionar
- Exemplo: API de Observação requer Flask

## Troubleshooting

### Erro: "Module not found"
**Solução:**
```bash
# Verificar que está no diretório correto
cd /tmp/nms
pwd

# Verificar estrutura
ls -la protocol/ server/ client/

# Verificar imports
python3 -c "from server import NMS_Server; print('OK')"
```

### Erro: "Permission denied"
**Solução:**
```bash
chmod +x test_core_automated.py
chmod +x start_nms.py start_rover.py start_ground_control.py
```

### Erro: "Address already in use"
**Solução:**
```bash
# Verificar processos em execução
ps aux | grep python

# Matar processos antigos se necessário
pkill -f start_nms.py
pkill -f start_rover.py
```

### Erro: "Connection refused"
**Solução:**
- Verificar que servidor está a correr antes de iniciar clientes
- Verificar conectividade de rede: `ping 10.0.1.10` (do rover para nave-mãe)
- Verificar firewall/regras de rede no CORE

## Checklist de Teste

- [ ] Todos os nós têm ficheiros copiados em `/tmp/nms`
- [ ] Dependências instaladas em todos os nós
- [ ] `test_core_automated.py` passa em todos os nós
- [ ] Nave-Mãe inicia sem erros
- [ ] Rovers registam-se com sucesso
- [ ] Telemetria é enviada periodicamente
- [ ] Ground Control consegue conectar à API
- [ ] Dashboard mostra informações corretas

## Próximos Passos Após Testes

Se todos os testes passarem:

1. ✅ Sistema está pronto para uso
2. ✅ Pode executar missões reais
3. ✅ Pode usar Ground Control para monitorização
4. ✅ Pode enviar missões para rovers

Se algum teste falhar:

1. ❌ Corrigir erros antes de prosseguir
2. ❌ Verificar logs detalhados
3. ❌ Consultar troubleshooting acima
4. ❌ Verificar documentação adicional

---

**Nota:** Estes testes verificam funcionalidade básica. Para testes completos de integração, execute o sistema completo conforme descrito no Passo 3.
