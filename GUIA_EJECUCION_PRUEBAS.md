# 🚀 Guía de Ejecución - Pruebas Paxos Distribuido
## Grupo 7: Francisco, Pablo, Farith

---

## ⚡ ANTES DE LA REUNIÓN (Cada integrante)

### 1. Verificar ZeroTier
```bash
# Windows (PowerShell como admin)
zerotier-cli info
# Debe mostrar: 200 info [ID] [VERSION] ONLINE
```

### 2. Verificar IP asignada
```bash
zerotier-cli listnetworks
# Buscar red: a581878f7d3f9596
```

### 3. Verificar Python
```bash
python --version
# Requiere Python 3.8+
```

### 4. Descargar código
Todos deben tener los archivos en una carpeta:
- `config.py`
- `network.py`
- `paxos_node.py`
- `run_paxos.py`

---

## 📡 DURANTE LA REUNIÓN

### Paso 1: Verificar Conectividad (5 min)

**Francisco ejecuta:**
```bash
ping 10.184.53.27     # Pablo
ping 10.184.53.242    # Farith
```

**Pablo ejecuta:**
```bash
ping 10.184.53.33     # Francisco
ping 10.184.53.242    # Farith
```

**Farith ejecuta:**
```bash
ping 10.184.53.33     # Francisco
ping 10.184.53.27     # Pablo
```

✅ Si todos responden → Continuar
❌ Si alguno falla → Verificar ZeroTier está conectado

---

### Paso 2: Abrir Wireshark (Todos)

1. Abrir Wireshark
2. **Configurar tiempo UTC:**
   - Ver → Formato de visualización de fecha y hora
   - Seleccionar: "Fecha y hora de UTC"
   - Seleccionar: "décimas de segundo"
3. Seleccionar interfaz ZeroTier (buscar "ZeroTier" o la que tenga IP 10.184.x.x)
4. Iniciar captura
5. Aplicar filtro: `udp.port == 5000`

---

### Paso 3: Ejecutar Nodos (Simultáneo)

Cada uno abre terminal en la carpeta del código y ejecuta:

**Francisco:**
```bash
cd [ruta a la carpeta paxos]
python run_paxos.py 10.184.53.33
```

**Pablo:**
```bash
cd [ruta a la carpeta paxos]
python run_paxos.py 10.184.53.27
```

**Farith:**
```bash
cd [ruta a la carpeta paxos]
python run_paxos.py 10.184.53.242
```

---

### Paso 4: Escenario 1 - Consenso Normal

1. **Francisco** escribe en su terminal:
   ```
   propose test_value_grupo7
   ```

2. **Todos** deben ver en sus terminales:
   - El proceso de PREPARE → PROMISE → ACCEPT → ACCEPTED
   - Mensaje final: "✓ CONSENSUS REACHED"

3. **Tomar capturas de pantalla:**
   - Terminal de cada uno mostrando el consenso
   - Wireshark de cada uno mostrando los paquetes UDP

---

### Paso 5: Escenario 2 - Tolerancia a Fallas

1. **Farith** cierra su terminal (Ctrl+C) o se desconecta de ZeroTier

2. **Francisco** propone nuevo valor:
   ```
   propose valor_con_falla
   ```

3. **Verificar:** El consenso debe alcanzarse con solo 2 nodos

4. **Tomar capturas de pantalla:**
   - Terminal mostrando consenso con 2/3 nodos
   - Wireshark mostrando que solo 2 nodos participan

---

### Paso 6: Guardar Evidencias

1. **Detener captura Wireshark**
2. **Guardar archivo .pcapng:**
   - Francisco: `wireshark_francisco_paxos.pcapng`
   - Pablo: `wireshark_pablo_paxos.pcapng`
   - Farith: `wireshark_farith_paxos.pcapng`
3. **Exportar capturas de pantalla importantes**

---

## 📸 CAPTURAS NECESARIAS (Checklist)

### Terminal
- [ ] Ping exitoso entre nodos
- [ ] Terminal Francisco - Proposer ejecutando consenso
- [ ] Terminal Pablo - Acceptor respondiendo
- [ ] Terminal Farith - Acceptor respondiendo
- [ ] Consenso exitoso con 3 nodos
- [ ] Consenso exitoso con 2 nodos (falla simulada)

### Wireshark
- [ ] Vista general con filtro `udp.port == 5000`
- [ ] Detalle de paquete mostrando JSON (payload)
- [ ] Secuencia PREPARE → PROMISE → ACCEPT → ACCEPTED
- [ ] Timestamps UTC visibles

---

## 🔧 TROUBLESHOOTING

### "No se reciben respuestas"
- Verificar firewall permite UDP puerto 5000
- Windows: `netsh advfirewall firewall add rule name="Paxos UDP" dir=in action=allow protocol=UDP localport=5000`

### "Error de conexión"
- Verificar ZeroTier conectado: `zerotier-cli info`
- Verificar IP correcta: `zerotier-cli listnetworks`

### "Import error"
- Verificar todos los archivos .py en la misma carpeta
- Ejecutar: `python -c "import config, network, paxos_node; print('OK')"`

---

## 📞 IPs de Referencia Rápida

| Integrante | IP ZeroTier |
|------------|-------------|
| Francisco | 10.184.53.33 |
| Pablo | 10.184.53.27 |
| Farith | 10.184.53.242 |

---

*Tiempo estimado total: 30-45 minutos*
