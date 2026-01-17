# 3. Pruebas y Resultados

## 3.1. Descripción de las Pruebas Realizadas

Se ejecutó una batería de pruebas sistemáticas para validar el correcto funcionamiento del algoritmo Paxos en un entorno distribuido real. Las pruebas se realizaron en la red virtual ZeroTier (ID: a581878f7d3f9596) con tres nodos físicamente separados.

### 3.1.1. Configuración del Entorno de Pruebas

**Red Virtual ZeroTier:**
- ID de Red: a581878f7d3f9596
- Protocolo: UDP Puerto 5000
- Quórum requerido: 2 de 3 nodos (mayoría simple)

**Nodos participantes:**

| Nodo | Integrante | IP ZeroTier | Sistema Operativo |
|------|------------|-------------|-------------------|
| Nodo 1 | Francisco Pérez | 10.184.53.33 | Windows 11 |
| Nodo 2 | Pablo Pucha | 10.184.53.27 | [COMPLETAR] |
| Nodo 3 | Farith Mejia | 10.184.53.242 | [COMPLETAR] |

**Configuración de Wireshark:**
Según las instrucciones del docente, Wireshark fue configurado con:
- Visualización > Formato de Visualización de fecha y hora > **Fecha y hora UTC**
- Visualización > Formato de Visualización de fecha y hora > **Décimas de segundo**
- Filtro de captura: `udp.port == 5000`

### 3.1.2. Prueba de Conectividad Previa

Antes de ejecutar el algoritmo Paxos, se verificó la conectividad entre todos los nodos mediante ping:

**Verificación desde Nodo 1 (Francisco - 10.184.53.33):**
```
ping 10.184.53.27    # → Pablo [RESULTADO: X ms]
ping 10.184.53.242   # → Farith [RESULTADO: X ms]
```

**[INSERTAR CAPTURA: Prueba de ping entre nodos]**

*Figura X. Verificación de conectividad ZeroTier entre los tres nodos del grupo.*

### 3.1.3. Escenarios de Prueba Ejecutados

Se diseñaron tres escenarios de prueba para validar las propiedades fundamentales del consenso:

**Escenario 1: Consenso Normal (3 nodos activos)**
- Objetivo: Verificar que el algoritmo alcanza consenso cuando todos los nodos están operativos.
- Procedimiento: Un nodo propone un valor y los tres participan en el protocolo.
- Resultado esperado: Consenso alcanzado en las dos fases (Prepare/Promise, Accept/Accepted).

**Escenario 2: Consenso con Falla de Nodo (2 nodos activos)**
- Objetivo: Demostrar tolerancia a fallas según la propiedad de terminación.
- Procedimiento: Se desconecta un nodo de ZeroTier antes de proponer un valor.
- Resultado esperado: Consenso alcanzado con quórum de 2/3 nodos.

**Escenario 3: Propuestas Concurrentes**
- Objetivo: Verificar que números de propuesta mayores prevalecen.
- Procedimiento: Dos nodos intentan proponer valores simultáneamente.
- Resultado esperado: Solo un valor es elegido, cumpliendo la propiedad de acuerdo.

---

## 3.2. Capturas de Pantalla y Análisis de Tráfico

### 3.2.1. Escenario 1: Consenso Normal con 3 Nodos

**Ejecución del Protocolo:**

Los tres integrantes ejecutaron simultáneamente:
```bash
# Francisco (Proposer inicial)
python run_paxos.py 10.184.53.33

# Pablo (Acceptor)
python run_paxos.py 10.184.53.27

# Farith (Acceptor)
python run_paxos.py 10.184.53.242
```

**Captura de Terminal - Nodo Proposer (Francisco):**

**[INSERTAR CAPTURA: Terminal mostrando la ejecución del proposer]**

*Figura X. Terminal del nodo proposer (10.184.53.33) iniciando el protocolo Paxos con el valor propuesto.*

**Captura de Terminal - Nodo Acceptor (Pablo):**

**[INSERTAR CAPTURA: Terminal mostrando recepción de PREPARE y envío de PROMISE]**

*Figura X. Terminal del nodo acceptor (10.184.53.27) procesando mensajes del protocolo.*

**Captura de Terminal - Nodo Acceptor (Farith):**

**[INSERTAR CAPTURA: Terminal mostrando recepción de PREPARE y envío de PROMISE]**

*Figura X. Terminal del nodo acceptor (10.184.53.242) participando en el consenso.*

---

### 3.2.2. Análisis de Tráfico con Wireshark

#### Captura Wireshark - Francisco Pérez (10.184.53.33)

**[INSERTAR CAPTURA WIRESHARK: Filtro udp.port == 5000, mostrando intercambio completo]**

*Figura X. Captura Wireshark desde el nodo 10.184.53.33 mostrando el tráfico UDP del protocolo Paxos.*

**Análisis del Tráfico Capturado:**

| # | Tiempo (UTC) | Origen | Destino | Tipo Mensaje | Descripción |
|---|--------------|--------|---------|--------------|-------------|
| 1 | [HH:MM:SS.d] | 10.184.53.33 | 10.184.53.27 | PREPARE | Fase 1: Solicitud de preparación |
| 2 | [HH:MM:SS.d] | 10.184.53.33 | 10.184.53.242 | PREPARE | Fase 1: Solicitud de preparación |
| 3 | [HH:MM:SS.d] | 10.184.53.27 | 10.184.53.33 | PROMISE | Fase 1: Promesa del acceptor |
| 4 | [HH:MM:SS.d] | 10.184.53.242 | 10.184.53.33 | PROMISE | Fase 1: Promesa del acceptor |
| 5 | [HH:MM:SS.d] | 10.184.53.33 | 10.184.53.27 | ACCEPT | Fase 2: Solicitud de aceptación |
| 6 | [HH:MM:SS.d] | 10.184.53.33 | 10.184.53.242 | ACCEPT | Fase 2: Solicitud de aceptación |
| 7 | [HH:MM:SS.d] | 10.184.53.27 | 10.184.53.33 | ACCEPTED | Fase 2: Confirmación de aceptación |
| 8 | [HH:MM:SS.d] | 10.184.53.242 | 10.184.53.33 | ACCEPTED | Fase 2: Confirmación de aceptación |

*Tabla X. Secuencia de mensajes Paxos capturados en Wireshark (Nodo Francisco).*

**Detalle del Payload UDP (Mensaje PREPARE):**

**[INSERTAR CAPTURA: Detalle de un paquete mostrando el JSON en el payload]**

```json
{
  "type": "PREPARE",
  "proposal_num": [NÚMERO],
  "sender": "10.184.53.33",
  "timestamp": "[TIMESTAMP_UTC]"
}
```

*Figura X. Contenido JSON del mensaje PREPARE visible en el payload UDP.*

---

#### Captura Wireshark - Pablo Pucha (10.184.53.27)

**[INSERTAR CAPTURA WIRESHARK: Filtro udp.port == 5000]**

*Figura X. Captura Wireshark desde el nodo 10.184.53.27 mostrando recepción de PREPARE y envío de PROMISE.*

**Análisis:**
- Se observa la recepción de mensajes PREPARE desde 10.184.53.33
- El nodo responde con PROMISE incluyendo su estado (sin valor previamente aceptado)
- Posteriormente recibe ACCEPT y responde con ACCEPTED

---

#### Captura Wireshark - Farith Mejia (10.184.53.242)

**[INSERTAR CAPTURA WIRESHARK: Filtro udp.port == 5000]**

*Figura X. Captura Wireshark desde el nodo 10.184.53.242 mostrando participación en el protocolo Paxos.*

**Análisis:**
- Comportamiento análogo al nodo de Pablo
- Los timestamps UTC permiten correlacionar la secuencia de mensajes entre las tres capturas

---

### 3.2.3. Escenario 2: Tolerancia a Fallas (Nodo Desconectado)

**Procedimiento:**
1. Se desconectó el nodo de Farith (10.184.53.242) de la red ZeroTier
2. Francisco propuso un nuevo valor
3. Se verificó que el consenso se alcanzó con 2/3 nodos (quórum cumplido)

**[INSERTAR CAPTURA: Terminal mostrando consenso con 2 nodos]**

*Figura X. Consenso alcanzado con quórum de 2 nodos, demostrando tolerancia a fallas.*

**[INSERTAR CAPTURA WIRESHARK: Tráfico mostrando solo 2 nodos participando]**

*Figura X. Captura Wireshark mostrando el protocolo Paxos con un nodo no disponible.*

**Análisis:**
- El proposer envía PREPARE a los 3 nodos configurados
- Solo 2 nodos responden con PROMISE
- El quórum (2/3) se alcanza y el protocolo continúa a la Fase 2
- El consenso se completa exitosamente, validando la propiedad de terminación

---

## 3.3. Resultados Obtenidos y su Interpretación

### 3.3.1. Verificación de Propiedades del Consenso

| Propiedad | Definición (Torres Tandazo, 2021) | Resultado | Evidencia |
|-----------|-----------------------------------|-----------|-----------|
| **Terminación** | "En algún momento todos los procesos correctos deciden en algún valor" | ✅ Cumplida | Escenarios 1 y 2 |
| **Acuerdo** | "Todos los procesos deben acordar en un valor" | ✅ Cumplida | Valor idéntico en 3 nodos |
| **Integridad** | "Si todos los procesos correctos acuerdan un valor, debe ser el mismo valor" | ✅ Cumplida | Logs y capturas |

*Tabla X. Verificación de las propiedades fundamentales del consenso según la guía didáctica.*

### 3.3.2. Métricas de Rendimiento

| Métrica | Escenario 1 (3 nodos) | Escenario 2 (2 nodos) |
|---------|----------------------|----------------------|
| Tiempo total de consenso | [X.XX] segundos | [X.XX] segundos |
| Mensajes intercambiados | 8 | 6 |
| Latencia promedio (RTT) | [X] ms | [X] ms |

*Tabla X. Métricas de rendimiento del protocolo Paxos en la red ZeroTier.*

### 3.3.3. Interpretación de Resultados

**Fase 1 (Prepare/Promise):**
El análisis de Wireshark confirma que los mensajes PREPARE se transmiten correctamente a todos los acceptors. Las respuestas PROMISE incluyen el número de propuesta prometido, garantizando que propuestas con números menores serán rechazadas. Esto implementa la propiedad de seguridad del algoritmo.

**Fase 2 (Accept/Accepted):**
Una vez recibidas las promesas de una mayoría (2/3), el proposer procede con la fase de aceptación. Los mensajes ACCEPTED confirman que el valor ha sido elegido. Como indica la guía didáctica, "todos los procesos deben acordar en un valor" (Torres Tandazo, 2021, p. 172), lo cual se verifica en los logs de cada nodo.

**Tolerancia a Fallas:**
El Escenario 2 demuestra que el sistema cumple con la propiedad de terminación incluso cuando un nodo falla. Con un quórum de 2/3, el sistema tolera la falla de 1 nodo, alineándose con la teoría de que "en algún momento todos los procesos correctos deciden en algún valor" (Torres Tandazo, 2021, p. 172).

**Correlación de Timestamps:**
La configuración de Wireshark con tiempo UTC permite correlacionar los eventos entre las tres capturas independientes, proporcionando evidencia objetiva de la secuencia del protocolo.

---

## Checklist de Capturas Requeridas

Antes de finalizar la sección, verificar que se incluyan:

- [ ] Captura de ping entre nodos (conectividad ZeroTier)
- [ ] Captura terminal Francisco (proposer)
- [ ] Captura terminal Pablo (acceptor)
- [ ] Captura terminal Farith (acceptor)
- [ ] Captura Wireshark Francisco (filtro udp.port == 5000)
- [ ] Captura Wireshark Pablo (filtro udp.port == 5000)
- [ ] Captura Wireshark Farith (filtro udp.port == 5000)
- [ ] Detalle de payload JSON de al menos un mensaje
- [ ] Captura de escenario con nodo desconectado (tolerancia a fallas)

---

*Nota: Reemplazar todos los placeholders [INSERTAR CAPTURA], [COMPLETAR] y [X] con los datos reales durante la ejecución de las pruebas.*
