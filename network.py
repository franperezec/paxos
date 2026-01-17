"""
Capa de Comunicación de Red para Paxos
Grupo 7 - Sistemas Distribuidos UTPL

Este módulo maneja toda la comunicación UDP entre nodos Paxos,
incluyendo envío y recepción de mensajes con threading.
"""

import socket
import threading
from typing import Callable, Optional, Tuple
from config import (
    PAXOS_PORT, ALL_NODE_IPS, SOCKET_TIMEOUT,
    serialize_message, deserialize_message, log_message
)


class PaxosNetwork:
    """
    Maneja la comunicación de red UDP para el protocolo Paxos.
    
    Utiliza dos sockets:
    - Uno para envío de mensajes
    - Uno para recepción con un hilo dedicado
    """
    
    def __init__(self, local_ip: str, message_handler: Callable[[dict, str], None]):
        """
        Inicializa la capa de red.
        
        Args:
            local_ip: IP local del nodo (IP de ZeroTier)
            message_handler: Función callback para procesar mensajes recibidos
        """
        self.local_ip = local_ip
        self.message_handler = message_handler
        self.running = False
        
        # Socket para envío
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Socket para recepción
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recv_socket.settimeout(SOCKET_TIMEOUT)
        
        # Hilo de recepción
        self.receiver_thread: Optional[threading.Thread] = None
        
        log_message("INFO", f"Red inicializada en {local_ip}:{PAXOS_PORT}")
    
    def start(self):
        """Inicia el hilo de recepción de mensajes."""
        try:
            # Intentar bind a la IP específica de ZeroTier
            self.recv_socket.bind((self.local_ip, PAXOS_PORT))
            log_message("INFO", f"Socket de recepción vinculado a {self.local_ip}:{PAXOS_PORT}")
        except OSError as e:
            # Si falla, intentar bind a todas las interfaces
            log_message("WARN", f"No se pudo vincular a {self.local_ip}, usando 0.0.0.0")
            self.recv_socket.bind(('0.0.0.0', PAXOS_PORT))
        
        self.running = True
        self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receiver_thread.start()
        log_message("SUCCESS", "Hilo de recepción iniciado")
    
    def stop(self):
        """Detiene la capa de red y libera recursos."""
        self.running = False
        if self.receiver_thread:
            self.receiver_thread.join(timeout=2.0)
        self.send_socket.close()
        self.recv_socket.close()
        log_message("INFO", "Red detenida")
    
    def _receive_loop(self):
        """Bucle principal de recepción de mensajes (ejecuta en hilo separado)."""
        while self.running:
            try:
                data, addr = self.recv_socket.recvfrom(4096)
                sender_ip = addr[0]
                
                # Ignorar mensajes propios
                if sender_ip == self.local_ip:
                    continue
                
                # Deserializar y procesar mensaje
                message = deserialize_message(data)
                log_message("RECV", f"De {sender_ip}: {message['type']} (prop#{message['proposal_num']})")
                
                # Llamar al handler del nodo Paxos
                self.message_handler(message, sender_ip)
                
            except socket.timeout:
                # Timeout normal, continuar esperando
                continue
            except Exception as e:
                if self.running:
                    log_message("ERROR", f"Error recibiendo mensaje: {e}")
    
    def send_to(self, message: dict, target_ip: str):
        """
        Envía un mensaje a un nodo específico.
        
        Args:
            message: Diccionario con el mensaje Paxos
            target_ip: IP destino
        """
        try:
            data = serialize_message(message)
            self.send_socket.sendto(data, (target_ip, PAXOS_PORT))
            log_message("SEND", f"A {target_ip}: {message['type']} (prop#{message['proposal_num']})")
        except Exception as e:
            log_message("ERROR", f"Error enviando a {target_ip}: {e}")
    
    def broadcast(self, message: dict, exclude_self: bool = True):
        """
        Envía un mensaje a todos los nodos del cluster.
        
        Args:
            message: Diccionario con el mensaje Paxos
            exclude_self: Si True, no envía al propio nodo
        """
        for ip in ALL_NODE_IPS:
            if exclude_self and ip == self.local_ip:
                continue
            self.send_to(message, ip)
    
    def send_to_all_acceptors(self, message: dict):
        """
        Envía un mensaje a todos los acceptors (todos los nodos excepto yo).
        En nuestra implementación, todos los nodos son acceptors.
        """
        self.broadcast(message, exclude_self=True)


class ResponseCollector:
    """
    Recolecta respuestas de múltiples nodos con timeout.
    
    Utilizado por el Proposer para esperar respuestas PROMISE y ACCEPTED.
    """
    
    def __init__(self, expected_type: str, proposal_num: int, quorum_size: int):
        """
        Inicializa el recolector.
        
        Args:
            expected_type: Tipo de mensaje esperado (PROMISE, ACCEPTED)
            proposal_num: Número de propuesta asociado
            quorum_size: Cantidad de respuestas necesarias para quórum
        """
        self.expected_type = expected_type
        self.proposal_num = proposal_num
        self.quorum_size = quorum_size
        
        self.responses: list[dict] = []
        self.nacks: list[dict] = []
        self.lock = threading.Lock()
        self.quorum_event = threading.Event()
    
    def add_response(self, message: dict, sender: str):
        """
        Añade una respuesta recibida.
        
        Args:
            message: Mensaje recibido
            sender: IP del nodo que envió la respuesta
        """
        with self.lock:
            # Verificar que sea para nuestra propuesta
            if message.get('proposal_num') != self.proposal_num:
                return
            
            if message['type'] == self.expected_type:
                # Evitar duplicados del mismo sender
                if not any(r.get('sender') == sender for r in self.responses):
                    message['sender'] = sender
                    self.responses.append(message)
                    log_message("INFO", f"Respuesta {len(self.responses)}/{self.quorum_size} de {sender}")
                    
                    # Verificar si alcanzamos quórum
                    if len(self.responses) >= self.quorum_size:
                        self.quorum_event.set()
            
            elif message['type'] == 'NACK':
                self.nacks.append(message)
    
    def wait_for_quorum(self, timeout: float) -> bool:
        """
        Espera hasta alcanzar quórum o timeout.
        
        Args:
            timeout: Tiempo máximo de espera en segundos
        
        Returns:
            True si se alcanzó quórum, False si timeout
        """
        return self.quorum_event.wait(timeout)
    
    def get_responses(self) -> list[dict]:
        """Retorna las respuestas recolectadas."""
        with self.lock:
            return list(self.responses)
    
    def has_quorum(self) -> bool:
        """Verifica si se alcanzó el quórum."""
        with self.lock:
            return len(self.responses) >= self.quorum_size


if __name__ == "__main__":
    # Prueba básica de la capa de red
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python network.py <IP_LOCAL>")
        print("Ejemplo: python network.py 10.184.53.33")
        sys.exit(1)
    
    local_ip = sys.argv[1]
    
    def test_handler(msg: dict, sender: str):
        print(f"\n>>> Mensaje recibido de {sender}:")
        print(f"    Tipo: {msg['type']}")
        print(f"    Propuesta: {msg['proposal_num']}")
        print(f"    Valor: {msg.get('value')}")
    
    print("=" * 60)
    print("PRUEBA DE CAPA DE RED PAXOS")
    print("=" * 60)
    
    network = PaxosNetwork(local_ip, test_handler)
    network.start()
    
    print("\nEsperando mensajes... (Ctrl+C para salir)")
    print("Puedes enviar un mensaje de prueba desde otro nodo.\n")
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nDeteniendo...")
        network.stop()
