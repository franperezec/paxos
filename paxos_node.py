"""
Nodo Paxos - Implementación Completa
Grupo 7 - Sistemas Distribuidos UTPL

Este módulo implementa un nodo Paxos completo que puede actuar
como Proposer, Acceptor y Learner simultáneamente.
"""

import threading
import time
from typing import Optional, Any
from config import (
    MessageType, QUORUM_SIZE, PREPARE_TIMEOUT, ACCEPT_TIMEOUT,
    create_message, generate_proposal_number, get_node_id_from_ip,
    log_message, Colors
)
from network import PaxosNetwork, ResponseCollector


class PaxosNode:
    """
    Implementación de un nodo Paxos con los tres roles:
    - Proposer: Propone valores para consenso
    - Acceptor: Acepta/rechaza propuestas
    - Learner: Aprende el valor acordado
    """

    def __init__(self, local_ip: str):
        """
        Inicializa el nodo Paxos.

        Args:
            local_ip: Dirección IP del nodo en la red ZeroTier
        """
        self.local_ip = local_ip
        self.node_id = get_node_id_from_ip(local_ip)

        # === Estado del Acceptor ===
        self.promised_proposal: int = 0  # Mayor propuesta prometida
        self.accepted_proposal: int = 0  # Propuesta aceptada
        self.accepted_value: Any = None  # Valor aceptado
        self.acceptor_lock = threading.Lock()

        # === Estado del Learner ===
        self.learned_value: Any = None   # Valor aprendido (consenso alcanzado)
        self.learned_proposal: int = 0
        self.learner_lock = threading.Lock()

        # === Estado del Proposer ===
        self.current_proposal: int = 0
        self.proposer_lock = threading.Lock()
        self.response_collector: Optional[ResponseCollector] = None

        # === Red ===
        self.network = PaxosNetwork(local_ip, self._handle_message)

        # === Estadísticas ===
        self.stats = {
            "proposals_initiated": 0,
            "proposals_accepted": 0,
            "proposals_rejected": 0,
            "messages_sent": 0,
            "messages_received": 0
        }

        log_message(
            "SUCCESS", f"Nodo Paxos inicializado: {local_ip} (ID: {self.node_id})")

    def start(self):
        """Inicia el nodo y comienza a escuchar mensajes."""
        self.network.start()
        log_message("SUCCESS", "Nodo Paxos en funcionamiento")

    def stop(self):
        """Detiene el nodo y libera recursos."""
        self.network.stop()
        log_message("INFO", "Nodo Paxos detenido")

    # =========================================================================
    # PROPOSER - Propone valores para consenso
    # =========================================================================

    def propose(self, value: Any) -> bool:
        """
        Inicia el protocolo Paxos para proponer un valor.

        Este es el método principal que un cliente llamaría para
        lograr consenso sobre un valor.

        Args:
            value: Valor a proponer para consenso

        Returns:
            True si el consenso fue alcanzado, False en caso contrario
        """
        with self.proposer_lock:
            self.stats["proposals_initiated"] += 1
            proposal_num = generate_proposal_number(self.node_id)
            self.current_proposal = proposal_num

        log_message("INFO", f"{'='*50}")
        log_message("INFO", f"INICIANDO PROPUESTA #{proposal_num}")
        log_message("INFO", f"Valor propuesto: {value}")
        log_message("INFO", f"{'='*50}")

        # === FASE 1: PREPARE ===
        log_message("INFO", "\n>>> FASE 1: PREPARE")

        phase1_result = self._phase1_prepare(proposal_num)

        if not phase1_result["success"]:
            log_message(
                "ERROR", "Fase 1 falló: no se alcanzó quórum de promesas")
            self.stats["proposals_rejected"] += 1
            return False

        # Determinar qué valor usar
        # Si algún acceptor ya había aceptado un valor, debemos usar ese
        final_value = value
        if phase1_result["highest_accepted_value"] is not None:
            final_value = phase1_result["highest_accepted_value"]
            log_message(
                "WARN", f"Usando valor previamente aceptado: {final_value}")

        # === FASE 2: ACCEPT ===
        log_message("INFO", "\n>>> FASE 2: ACCEPT")

        phase2_result = self._phase2_accept(proposal_num, final_value)

        if not phase2_result["success"]:
            log_message(
                "ERROR", "Fase 2 falló: no se alcanzó quórum de aceptaciones")
            self.stats["proposals_rejected"] += 1
            return False

        # === CONSENSO ALCANZADO ===
        self.stats["proposals_accepted"] += 1

        with self.learner_lock:
            self.learned_value = final_value
            self.learned_proposal = proposal_num

        log_message("SUCCESS", f"\n{'='*50}")
        log_message("SUCCESS", f"¡CONSENSO ALCANZADO!")
        log_message("SUCCESS", f"Valor acordado: {final_value}")
        log_message("SUCCESS", f"Propuesta #: {proposal_num}")
        log_message("SUCCESS", f"{'='*50}\n")

        return True

    def _phase1_prepare(self, proposal_num: int) -> dict:
        """
        Ejecuta la Fase 1 del protocolo Paxos (Prepare/Promise).

        Args:
            proposal_num: Número de propuesta único

        Returns:
            Diccionario con resultado de la fase
        """
        # Crear recolector de respuestas
        self.response_collector = ResponseCollector(
            expected_type=MessageType.PROMISE,
            proposal_num=proposal_num,
            quorum_size=QUORUM_SIZE
        )

        # Enviar PREPARE a todos los acceptors
        prepare_msg = create_message(
            msg_type=MessageType.PREPARE,
            proposal_num=proposal_num,
            sender=self.local_ip
        )

        log_message(
            "SEND", f"Enviando PREPARE({proposal_num}) a todos los acceptors")
        self.network.send_to_all_acceptors(prepare_msg)

        # También procesamos localmente como acceptor
        self._handle_prepare(prepare_msg, self.local_ip)

        # Esperar respuestas
        log_message("INFO", f"Esperando promesas (quórum: {QUORUM_SIZE})...")
        quorum_reached = self.response_collector.wait_for_quorum(
            PREPARE_TIMEOUT)

        if not quorum_reached:
            return {"success": False}

        # Analizar respuestas para encontrar el valor más alto aceptado
        responses = self.response_collector.get_responses()
        highest_accepted_proposal = 0
        highest_accepted_value = None

        for resp in responses:
            acc_prop = resp.get("accepted_proposal", 0) or 0
            if acc_prop > highest_accepted_proposal:
                highest_accepted_proposal = acc_prop
                highest_accepted_value = resp.get("accepted_value")

        log_message(
            "SUCCESS", f"Fase 1 completada: {len(responses)} promesas recibidas")

        return {
            "success": True,
            "promises": responses,
            "highest_accepted_value": highest_accepted_value
        }

    def _phase2_accept(self, proposal_num: int, value: Any) -> dict:
        """
        Ejecuta la Fase 2 del protocolo Paxos (Accept/Accepted).

        Args:
            proposal_num: Número de propuesta
            value: Valor a aceptar

        Returns:
            Diccionario con resultado de la fase
        """
        # Crear recolector para respuestas ACCEPTED
        self.response_collector = ResponseCollector(
            expected_type=MessageType.ACCEPTED,
            proposal_num=proposal_num,
            quorum_size=QUORUM_SIZE
        )

        # Enviar ACCEPT a todos los acceptors
        accept_msg = create_message(
            msg_type=MessageType.ACCEPT,
            proposal_num=proposal_num,
            value=value,
            sender=self.local_ip
        )

        log_message(
            "SEND", f"Enviando ACCEPT({proposal_num}, {value}) a todos los acceptors")
        self.network.send_to_all_acceptors(accept_msg)

        # También procesamos localmente como acceptor
        self._handle_accept(accept_msg, self.local_ip)

        # Esperar respuestas
        log_message(
            "INFO", f"Esperando aceptaciones (quórum: {QUORUM_SIZE})...")
        quorum_reached = self.response_collector.wait_for_quorum(
            ACCEPT_TIMEOUT)

        if not quorum_reached:
            return {"success": False}

        responses = self.response_collector.get_responses()
        log_message(
            "SUCCESS", f"Fase 2 completada: {len(responses)} aceptaciones recibidas")

        return {
            "success": True,
            "accepted": responses
        }

    # =========================================================================
    # ACCEPTOR - Acepta/rechaza propuestas
    # =========================================================================

    def _handle_prepare(self, message: dict, sender: str):
        """
        Maneja un mensaje PREPARE como Acceptor.

        Args:
            message: Mensaje PREPARE recibido
            sender: IP del proposer
        """
        proposal_num = message["proposal_num"]

        with self.acceptor_lock:
            if proposal_num > self.promised_proposal:
                # Prometer no aceptar propuestas menores
                self.promised_proposal = proposal_num

                # Responder con PROMISE, incluyendo cualquier valor ya aceptado
                promise_msg = create_message(
                    msg_type=MessageType.PROMISE,
                    proposal_num=proposal_num,
                    sender=self.local_ip,
                    accepted_proposal=self.accepted_proposal,
                    accepted_value=self.accepted_value
                )

                log_message("INFO", f"Prometiendo propuesta #{proposal_num}")

                # Si es mensaje propio, agregar directamente al collector
                if sender == self.local_ip:
                    if self.response_collector:
                        self.response_collector.add_response(
                            promise_msg, self.local_ip)
                else:
                    self.network.send_to(promise_msg, sender)
            else:
                # Rechazar con NACK
                nack_msg = create_message(
                    msg_type=MessageType.NACK,
                    proposal_num=proposal_num,
                    sender=self.local_ip
                )
                log_message(
                    "WARN", f"Rechazando propuesta #{proposal_num} (ya prometí #{self.promised_proposal})")

                if sender != self.local_ip:
                    self.network.send_to(nack_msg, sender)

    def _handle_accept(self, message: dict, sender: str):
        """
        Maneja un mensaje ACCEPT como Acceptor.

        Args:
            message: Mensaje ACCEPT recibido
            sender: IP del proposer
        """
        proposal_num = message["proposal_num"]
        value = message["value"]

        with self.acceptor_lock:
            if proposal_num >= self.promised_proposal:
                # Aceptar la propuesta
                self.promised_proposal = proposal_num
                self.accepted_proposal = proposal_num
                self.accepted_value = value

                # Responder con ACCEPTED
                accepted_msg = create_message(
                    msg_type=MessageType.ACCEPTED,
                    proposal_num=proposal_num,
                    value=value,
                    sender=self.local_ip
                )

                log_message(
                    "SUCCESS", f"Aceptando propuesta #{proposal_num} con valor: {value}")

                # Si es mensaje propio, agregar al collector
                if sender == self.local_ip:
                    if self.response_collector:
                        self.response_collector.add_response(
                            accepted_msg, self.local_ip)
                else:
                    self.network.send_to(accepted_msg, sender)
            else:
                # Rechazar
                nack_msg = create_message(
                    msg_type=MessageType.NACK,
                    proposal_num=proposal_num,
                    sender=self.local_ip
                )
                log_message("WARN", f"Rechazando ACCEPT #{proposal_num}")

                if sender != self.local_ip:
                    self.network.send_to(nack_msg, sender)

    # =========================================================================
    # MANEJADOR DE MENSAJES
    # =========================================================================

    def _handle_message(self, message: dict, sender: str):
        """
        Callback para procesar mensajes entrantes.

        Args:
            message: Mensaje recibido
            sender: IP del remitente
        """
        self.stats["messages_received"] += 1
        msg_type = message["type"]

        if msg_type == MessageType.PREPARE:
            self._handle_prepare(message, sender)

        elif msg_type == MessageType.ACCEPT:
            self._handle_accept(message, sender)

        elif msg_type in [MessageType.PROMISE, MessageType.ACCEPTED, MessageType.NACK]:
            # Respuestas para el proposer
            if self.response_collector:
                self.response_collector.add_response(message, sender)

        elif msg_type == MessageType.LEARN:
            # Notificación de valor aprendido
            with self.learner_lock:
                self.learned_value = message.get("value")
                self.learned_proposal = message.get("proposal_num")
            log_message("INFO", f"Valor aprendido: {self.learned_value}")

    # =========================================================================
    # MÉTODOS DE CONSULTA
    # =========================================================================

    def get_status(self) -> dict:
        """Retorna el estado actual del nodo."""
        with self.acceptor_lock:
            acceptor_state = {
                "promised_proposal": self.promised_proposal,
                "accepted_proposal": self.accepted_proposal,
                "accepted_value": self.accepted_value
            }

        with self.learner_lock:
            learner_state = {
                "learned_value": self.learned_value,
                "learned_proposal": self.learned_proposal
            }

        return {
            "node_ip": self.local_ip,
            "node_id": self.node_id,
            "acceptor": acceptor_state,
            "learner": learner_state,
            "stats": self.stats.copy()
        }

    def print_status(self):
        """Imprime el estado actual del nodo de forma legible."""
        status = self.get_status()

        print(f"\n{Colors.HEADER}{'='*60}{Colors.RESET}")
        print(f"{Colors.HEADER}ESTADO DEL NODO PAXOS{Colors.RESET}")
        print(f"{Colors.HEADER}{'='*60}{Colors.RESET}")

        print(f"\n{Colors.BOLD}Identificación:{Colors.RESET}")
        print(f"  IP: {status['node_ip']}")
        print(f"  ID: {status['node_id']}")

        print(f"\n{Colors.BOLD}Estado Acceptor:{Colors.RESET}")
        print(
            f"  Propuesta prometida: {status['acceptor']['promised_proposal']}")
        print(
            f"  Propuesta aceptada:  {status['acceptor']['accepted_proposal']}")
        print(f"  Valor aceptado:      {status['acceptor']['accepted_value']}")

        print(f"\n{Colors.BOLD}Estado Learner:{Colors.RESET}")
        if status['learner']['learned_value']:
            print(
                f"  {Colors.GREEN}Valor aprendido: {status['learner']['learned_value']}{Colors.RESET}")
            print(
                f"  Propuesta #:     {status['learner']['learned_proposal']}")
        else:
            print(f"  {Colors.YELLOW}Aún no hay consenso{Colors.RESET}")

        print(f"\n{Colors.BOLD}Estadísticas:{Colors.RESET}")
        for key, value in status['stats'].items():
            print(f"  {key}: {value}")

        print(f"\n{'='*60}\n")


if __name__ == "__main__":
    # Prueba básica del nodo
    import sys

    if len(sys.argv) < 2:
        print("Uso: python paxos_node.py <IP_LOCAL>")
        print("Ejemplo: python paxos_node.py 10.184.53.33")
        sys.exit(1)

    local_ip = sys.argv[1]

    node = PaxosNode(local_ip)
    node.start()
    node.print_status()

    print("Nodo Paxos en ejecución. Presiona Ctrl+C para salir.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo nodo...")
        node.stop()
