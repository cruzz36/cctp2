# Resolver NaveMae e Rovers presos
_Exported on 12/10/2025 at 17:24:44 GMT from Cursor (2.1.50)_

---

**User**

VE O TRABALHO TODO EXTENSIVAMENTE; TODOS OS FICHEIROS, tendo em consideracao CC-ENUNCIADO-TP2-25-26_V1.pdf, ANALISANDO O @Guia_CORE_Unificado.md , PORQUE ESTÁ A DAR ISTO (A NaveMae E OS ROVERS ESTÃO PRESOS NESTE ESTADO)

---

**Cursor**

- Tanto os rovers como o GroundControl estão a tentar falar com a Nave-Mãe em `10.0.1.10` (`start_rover.py` e o default do GC) e o MissionLink/Telemetry no servidor também ficam à escuta no IP da rede dos rovers (`10.0.1.x`).  
```21:38:start_ground_control.py
    default_api = "http://10.0.1.10:8082"
    ...
    print(f"API de Observação: {api_url}")
```  
```132:158:server/NMS_Server.py
        interfaces = self.getinterfaces()
        rover_ip = next((i.split(" ")[1] for i in interfaces if i.split(" ")[1].startswith("10.0.1.")), None)
        self.IPADDRESS = rover_ip if rover_ip else interfaces[0].split(" ")[1]
        self.missionLink = MissionLink.MissionLink(self.IPADDRESS, netDir)
```
- A topologia tem sub-redes distintas: Nave-Mãe em `10.0.1.10/24` (rovers) e `10.0.0.11/24` (GC), Rover1 em `10.0.3.10/24`, Rover2 em `10.0.2.10/24`, e o satélite/gateway em `10.0.1.1/10.0.2.1/10.0.3.1`. Nenhum dos nós tem rotas configuradas para fora da sua subnet. Resultado: os rovers não conseguem chegar a `10.0.1.10` e o GC não alcança a API, por isso todos ficam “presos” no registo/timeout.  
```1:84:topologiatp2.imn
interface eth1
 ip address 10.0.1.10/24    # NaveMae (rovers)
interface eth0
 ip address 10.0.0.11/24    # NaveMae (GC)
...
interface eth0
 ip address 10.0.3.10/24    # Rover1
interface eth0
 ip address 10.0.2.10/24    # Rover2
interface eth0
 ip address 10.0.1.1/24     # Satelite -> gateway para rovers
```

Como destravar agora:
- Em Rover1: `ip route add default via 10.0.3.1`
- Em Rover2: `ip route add default via 10.0.2.1`
- Na Nave-Mãe: `ip route add 10.0.2.0/24 via 10.0.1.1` e `ip route add 10.0.3.0/24 via 10.0.1.1` (ou `ip route add default via 10.0.1.1`).
- No GroundControl: ou usa a API em `http://10.0.0.11:8082` (mesma subnet) ou adiciona rota `ip route add 10.0.1.0/24 via 10.0.0.11`.

Depois de pôr as rotas, volta a lançar pela ordem do guia (Nave-Mãe → rovers → GC). Se quiser confirmar, faz `ping` para `10.0.1.10` a partir de cada rover e `curl http://10.0.1.10:8082/status` a partir do GC.

```python
    default_api = "http://10.0.1.10:8082"
    ...
    print(f"API de Observação: {api_url}")
```

```python
        interfaces = self.getinterfaces()
        rover_ip = next((i.split(" ")[1] for i in interfaces if i.split(" ")[1].startswith("10.0.1.")), None)
        self.IPADDRESS = rover_ip if rover_ip else interfaces[0].split(" ")[1]
        self.missionLink = MissionLink.MissionLink(self.IPADDRESS, netDir)
```

```plaintext
interface eth1
 ip address 10.0.1.10/24    # NaveMae (rovers)
interface eth0
 ip address 10.0.0.11/24    # NaveMae (GC)
...
interface eth0
 ip address 10.0.3.10/24    # Rover1
interface eth0
 ip address 10.0.2.10/24    # Rover2
interface eth0
 ip address 10.0.1.1/24     # Satelite -> gateway para rovers
```

---

**User**

fiz ambos ping e curl e nao recebi nada como resposta, porque? e corrige o que tinhas identificado como errado antes, fica a saber que os ips na imagem sao os que deveriam ser usados, aproveita e analisa todas as conecoes e corrigias para ficarem consuante a imagem qd necessario

---

**Cursor**

Estás sem resposta no `ping`/`curl` porque a malha não tem rotas entre sub-redes:  
- Rover1 (10.0.3.10/24) e Rover2 (10.0.2.10/24) não têm gateway para chegar à NaveMãe (10.0.1.10).  
- GroundControl (10.0.0.10/24) está numa subnet diferente da NaveMãe; sem gateway comum, o TCP para a API nunca sai.

Usa exatamente os IPs do diagrama e acrescenta as rotas mínimas:

1) Rovers → Satélite (gateway)
- Rover1: `ip route add default via 10.0.3.1`
- Rover2: `ip route add default via 10.0.2.1`

2) NaveMãe → redes dos rovers
- `ip route add 10.0.2.0/24 via 10.0.1.1`
- `ip route add 10.0.3.0/24 via 10.0.1.1`

3) GroundControl ↔ NaveMãe
- Para manter os IPs do diagrama, atribui um IP secundário na interface da NaveMãe que liga ao GC:  
  `ip addr add 10.0.0.11/24 dev eth0`
- No GC, cria rota para a rede da NaveMãe:  
  `ip route add 10.0.1.0/24 via 10.0.0.11`
- Depois acede à API usando `http://10.0.1.10:8082` (continua a ser o IP do diagrama).

Verificação rápida:
- Nos rovers: `ping 10.0.1.10`
- Na NaveMãe: `ping 10.0.2.10` e `ping 10.0.3.10`
- No GC: `curl http://10.0.1.10:8082/status`

Em seguida relança na ordem recomendada (NaveMãe → rovers → GC).

---

**User**

isso e para adicionar no codigo ou no ficheiro imn?

---

**Cursor**

Não é no código nem no .imn obrigatório. São comandos de rede nos nós do CORE (runtime). Podes aplicar de duas formas:

- Rápido (sem mexer no .imn): em cada nó, abre shell e corre:
  - Rover1: `ip route add default via 10.0.3.1`
  - Rover2: `ip route add default via 10.0.2.1`
  - NaveMae: `ip route add 10.0.2.0/24 via 10.0.1.1` e `ip route add 10.0.3.0/24 via 10.0.1.1`
  - GroundControl: `ip route add 10.0.1.0/24 via 10.0.0.11`
  - (Se precisares, dá à NaveMae o IP 10.0.0.11 na interface para o GC: `ip addr add 10.0.0.11/24 dev eth0`)

- Permanente no .imn (opcional): podes pôr estas rotas em “Services → Custom commands” de cada nó ou em “node commands” do imn para serem aplicadas no arranque.

Escolhe o método rápido para testar já; só mexe no .imn se quiseres que fique automático ao abrir a topologia.

---

**User**

estes comandos sao algo que por default ja devia acontecer no imn? se nao, pq que n tinha sido adicionado este passo ao @Guia_CORE_Unificado.md ?

---

**Cursor**

Não, o .imn só traz endereços das interfaces; o CORE não cria rotas automáticas entre sub-redes. Por isso é normal precisares de acrescentar rotas/gateways à mão (ou via “custom commands” no .imn) para ligar 10.0.1.x ↔ 10.0.2.x/10.0.3.x e o GC em 10.0.0.x.  
O passo ficou em falta no guia — foi uma omissão. Podes:  
- Adicionar no guia uma secção rápida de “Rotas pós-arranque” com esses comandos; ou  
- Colocar os mesmos comandos em “Services → Custom commands” de cada nó no .imn para ficarem permanentes.

---

**User**

adicionar estes comando e algo permitido para este trabalho de acordo com CC-Enunciado-TP2-25-26_v1.pdf?

---

**Cursor**

Sim. O enunciado pede que os nós comuniquem entre si (MissionLink/Telemetry/API), não proíbe configurar rotas estáticas ou gateways. Acrescentar as rotas é infraestrutura de rede para cumprir os requisitos de comunicação; não altera o protocolo nem o código. Portanto, podes (e deves) adicionar essas rotas para que o cenário funcione de acordo com o enunciado.

---

**User**

adiciona estas rotas ao imn entao e adiciona o porque de existirem no local onde se devia chamar esses comandos no @Guia_CORE_Unificado.md 

---

**Cursor**

```plaintext
*** Begin Patch
*** Update File: CC/tp2/topologiatp2.imn
@@
 node n1 {
     type router
     model host
     network-config {
 	hostname NaveMae
 	!
 	interface eth1
 	 ip address 10.0.1.10/24
 	!
 	interface eth0
 	 ip address 10.0.0.11/24
 	!
     }
+    # Rotas para redes dos rovers via Satelite (10.0.1.1)
+    # Mantemos ligação ao GC em 10.0.0.0/24 através do IP secundário 10.0.0.11
+    custom-config {
+        interface eth1
+        addroute 10.0.2.0/24 10.0.1.1
+        addroute 10.0.3.0/24 10.0.1.1
+    }
     canvas c1
     iconcoords {528.0 152.0}
     labelcoords {528.0 184.0}
     interface-peer {eth0 n2}
     interface-peer {eth1 n5}
 }
@@
 node n2 {
     type router
     model host
     network-config {
 	hostname GroundControl
 	!
 	interface eth0
 	 ip address 10.0.0.10/24
 	!
     }
+    # Rota para chegar à NaveMae (10.0.1.0/24) via IP 10.0.0.11 da NaveMae
+    custom-config {
+        addroute 10.0.1.0/24 10.0.0.11
+    }
     canvas c1
     iconcoords {218.0 152.0}
     labelcoords {218.0 184.0}
     interface-peer {eth0 n1}
 }
@@
 node n3 {
     type router
     model host
     network-config {
 	hostname Rover1
 	!
 	interface eth0
 	 ip address 10.0.3.10/24
 	!
     }
+    # Rota default via Satelite (10.0.3.1) para alcançar NaveMae
+    custom-config {
+        addroute default 10.0.3.1
+    }
     canvas c1
     iconcoords {726.0 511.0}
     labelcoords {726.0 543.0}
     interface-peer {eth0 n5}
 }
@@
 node n4 {
     type router
     model host
     network-config {
 	hostname Rover2
 	!
 	interface eth0
 	 ip address 10.0.2.10/24
 	!
     }
+    # Rota default via Satelite (10.0.2.1) para alcançar NaveMae
+    custom-config {
+        addroute default 10.0.2.1
+    }
     canvas c1
     iconcoords {336.0 511.0}
     labelcoords {336.0 543.0}
     interface-peer {eth0 n5}
 }
@@
 node n5 {
     type router
     model router
*** End Patch
```

```plaintext
*** Begin Patch
*** Update File: CC/tp2/topologiatp2.imn
@@
 node n1 {
     type router
     model host
     network-config {
 	hostname NaveMae
 	!
 	interface eth1
 	 ip address 10.0.1.10/24
 	!
 	interface eth0
 	 ip address 10.0.0.11/24
 	!
     }
+    custom-config {
+        # Rotas para redes dos rovers via Satelite (10.0.1.1)
+        addroute 10.0.2.0/24 10.0.1.1
+        addroute 10.0.3.0/24 10.0.1.1
+    }
     canvas c1
     iconcoords {528.0 152.0}
     labelcoords {528.0 184.0}
     interface-peer {eth0 n2}
     interface-peer {eth1 n5}
 }
@@
 node n2 {
     type router
     model host
     network-config {
 	hostname GroundControl
 	!
 	interface eth0
 	 ip address 10.0.0.10/24
 	!
     }
+    custom-config {
+        # Rota para chegar à NaveMae (10.0.1.0/24) via 10.0.0.11
+        addroute 10.0.1.0/24 10.0.0.11
+    }
     canvas c1
     iconcoords {218.0 152.0}
     labelcoords {218.0 184.0}
     interface-peer {eth0 n1}
 }
@@
 node n3 {
     type router
     model host
     network-config {
 	hostname Rover1
 	!
 	interface eth0
 	 ip address 10.0.3.10/24
 	!
     }
+    custom-config {
+        # Gateway default para chegar à NaveMae
+        addroute default 10.0.3.1
+    }
     canvas c1
     iconcoords {726.0 511.0}
     labelcoords {726.0 543.0}
     interface-peer {eth0 n5}
 }
@@
 node n4 {
     type router
     model host
     network-config {
 	hostname Rover2
 	!
 	interface eth0
 	 ip address 10.0.2.10/24
 	!
     }
+    custom-config {
+        # Gateway default para chegar à NaveMae
+        addroute default 10.0.2.1
+    }
     canvas c1
     iconcoords {336.0 511.0}
     labelcoords {336.0 543.0}
     interface-peer {eth0 n5}
 }
*** End Patch
```

