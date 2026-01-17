"""
Configuración Central del Sistema Paxos
Grupo 7 - Sistemas Distribuidos UTPL

Este módulo contiene todas las constantes y configuraciones
necesarias para el funcionamiento del algoritmo Paxos.
"""

import json
import time
from datetime import datetime, timezone

# =============================================================================
# CONFIGURACIÓN DE RED ZEROTIER
# =============================================================================

# Puerto UDP para comunicación Paxos
PAXOS_PORT = 5000

# Nodos del cluster Paxos (Red ZeroTier: a581878f7d3f9596)
NODES = {
    "francisco": "10.184.53.33",
    "pablo": "10.184.53.27",
    "farith": "10.184.53.242",
    "fernando": "10.184.53.252"
}

# Lista de todas las IPs de los nodos
ALL_NODE_IPS = list(NODES.values())

# Quórum requerido (mayoría simple: 2 de 3)
QUORUM_SIZE = (len(ALL_NODE_IPS) // 2) + 1  # = 2

# =============================================================================
# CONFIGURACIÓN DE TIMEOUTS
# =============================================================================

# Timeout para esperar respuestas (segundos)
PREPARE_TIMEOUT = 5.0
ACCEPT_TIMEOUT = 5.0

# Intervalo de reintento si no se alcanza quórum
RETRY_INTERVAL = 2.0

# Timeout del socket UDP
SOCKET_TIMEOUT = 1.0

# =============================================================================
# TIPOS DE MENSAJES PAXOS
# =============================================================================


class MessageType:
    """Tipos de mensajes del protocolo Paxos"""
    PREPARE = "PREPARE"      # Fase 1a: Proposer -> Acceptors
    PROMISE = "PROMISE"      # Fase 1b: Acceptor -> Proposer
    ACCEPT = "ACCEPT"        # Fase 2a: Proposer -> Acceptors
    ACCEPTED = "ACCEPTED"    # Fase 2b: Acceptor -> Proposer/Learners
    NACK = "NACK"            # Rechazo de propuesta
    LEARN = "LEARN"          # Notificación a learners

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================


def create_message(msg_type: str, proposal_num: int, value=None,
                   sender: str = "", accepted_proposal: int = None,
                   accepted_value=None) -> dict:
    """
    Crea un mensaje Paxos en formato JSON.

    Args:
        msg_type: Tipo de mensaje (PREPARE, PROMISE, ACCEPT, etc.)
        proposal_num: Número de propuesta único
        value: Valor propuesto (opcional)
        sender: IP del nodo emisor
        accepted_proposal: Número de propuesta previamente aceptada
        accepted_value: Valor previamente aceptado

    Returns:
        Diccionario con la estructura del mensaje
    """
    return {
        "type": msg_type,
        "proposal_num": proposal_num,
        "value": value,
        "sender": sender,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "accepted_proposal": accepted_proposal,
        "accepted_value": accepted_value
    }


def serialize_message(msg: dict) -> bytes:
    """Serializa un mensaje a bytes para envío UDP"""
    return json.dumps(msg).encode('utf-8')


def deserialize_message(data: bytes) -> dict:
    """Deserializa bytes recibidos a un mensaje diccionario"""
    return json.loads(data.decode('utf-8'))


def generate_proposal_number(node_id: int) -> int:
    """
    Genera un número de propuesta único.

    Usa timestamp en milisegundos + node_id para garantizar unicidad.
    El node_id ocupa los últimos 2 dígitos.

    Args:
        node_id: Identificador único del nodo (0-99)

    Returns:
        Número de propuesta único
    """
    timestamp_ms = int(time.time() * 1000)
    return timestamp_ms * 100 + node_id


def get_node_id_from_ip(ip: str) -> int:
    """
    Obtiene un ID numérico único basado en la IP del nodo.

    Args:
        ip: Dirección IP del nodo

    Returns:
        ID numérico (último octeto de la IP)
    """
    return int(ip.split('.')[-1])


def format_timestamp() -> str:
    """Retorna timestamp UTC formateado para logs"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " UTC"

# =============================================================================
# COLORES PARA CONSOLA
# =============================================================================


class Colors:
    """Códigos ANSI para colorear la salida de consola"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'  # Renombrado de ENDC para coincidir con el uso
    BOLD = '\033[1m'


def log_message(level: str, message: str):
    """
    Imprime un mensaje de log con formato y color.

    Args:
        level: Nivel del log (INFO, SEND, RECV, ERROR, SUCCESS)
        message: Mensaje a mostrar
    """
    timestamp = format_timestamp()

    colors = {
        "INFO": Colors.CYAN,
        "SEND": Colors.BLUE,
        "RECV": Colors.YELLOW,
        "ERROR": Colors.RED,
        "SUCCESS": Colors.GREEN,
        "WARN": Colors.YELLOW
    }

    color = colors.get(level, Colors.RESET)
    print(f"{color}[{timestamp}] [{level}] {message}{Colors.RESET}")


if __name__ == "__main__":
    # Prueba de configuración
    print("=" * 60)
    print("CONFIGURACIÓN PAXOS - GRUPO 7")
    print("=" * 60)
    print(f"\nPuerto UDP: {PAXOS_PORT}")
    print(f"Quórum requerido: {QUORUM_SIZE} de {len(ALL_NODE_IPS)} nodos")
    print(f"\nNodos configurados:")
    for name, ip in NODES.items():
        node_id = get_node_id_from_ip(ip)
        print(f"  - {name.capitalize()}: {ip} (Node ID: {node_id})")

    print(f"\nEjemplo de número de propuesta: {generate_proposal_number(33)}")
    print(f"\nMensaje PREPARE de ejemplo:")
    msg = create_message(MessageType.PREPARE, 123456789, sender="10.184.53.33")
    print(json.dumps(msg, indent=2))
