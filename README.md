# Simulación Paxos Distribuido
Implementación del algoritmo de consenso Paxos sobre red ZeroTier.

## Requisitos Previos
- Python 3.8+
- ZeroTier instalado y conectado a la red
- Firewall configurado para permitir UDP puerto 5000

## Configuración

### 1. Verificar ZeroTier
```bash
zerotier-cli info
# Debe mostrar: 200 info [ID] [VERSION] ONLINE

zerotier-cli listnetworks
# Verificar que estés conectado a la red correcta
```

### 2. Configurar redes en config.py
Editar `config.py` y verificar que las IPs de los nodos sean correctas:
```python
NODES = {
    "node1": "10.184.53.33",
    "node2": "10.184.53.27",
    "node3": "10.184.53.242"
}
```

Asegúrate de que las direcciones IP correspondan a las asignadas por ZeroTier a cada nodo.

## Ejecución

### Ejecutar un nodo
```bash
python paxos_node.py
```

O utilizando el script de ejecución:
```bash
python run_paxos.py <IP_DEL_NODO>
```

Ejemplo:
```bash
python run_paxos.py 10.184.53.33
```

### Proponer un valor
Una vez que los nodos estén ejecutándose, puedes proponer valores escribiendo en la terminal:
```
propose mi_valor
```
## Estructura del Proyecto
- `config.py` - Configuración de nodos y parámetros de red
- `network.py` - Capa de comunicación UDP
- `paxos_node.py` - Implementación del algoritmo Paxos
- `run_paxos.py` - Script para ejecutar nodos
- `verificar_red_zerotier.py` - Verificación de conectividad

## Grupo 7
Francisco, Pablo, Farith, Fernando
