#!/usr/bin/env python3
"""
run_paxos.py - Script principal para ejecutar y probar el algoritmo Paxos
Grupo 7 - Sistemas Distribuidos UTPL

Uso:
    python run_paxos.py <ip_zerotier>
    
Ejemplos:
    python run_paxos.py 10.184.53.33   # Francisco
    python run_paxos.py 10.184.53.27   # Pablo
    python run_paxos.py 10.184.53.242  # Farith
"""

import sys
import time
from datetime import datetime, timezone

from config import NODES, Colors, log_message
from paxos_node import PaxosNode


def print_banner():
    """Imprime banner de inicio."""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}   ALGORITMO DE PAXOS - Grupo 7 - Sistemas Distribuidos{Colors.RESET}")
    print(f"{Colors.CYAN}   Universidad Técnica Particular de Loja{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")


def print_nodes_info():
    """Imprime información de los nodos configurados."""
    print(f"{Colors.YELLOW}Nodos configurados en la red ZeroTier:{Colors.RESET}")
    print(f"  • Francisco: 10.184.53.33")
    print(f"  • Pablo:     10.184.53.27")
    print(f"  • Farith:    10.184.53.242")
    print(f"  • Fernando:  10.184.53.252")
    print()


def print_menu():
    """Imprime el menú de opciones."""
    print(f"\n{Colors.GREEN}--- MENÚ DE OPCIONES ---{Colors.RESET}")
    print("  1. Proponer un valor (iniciar consenso)")
    print("  2. Ver estado del nodo")
    print("  3. Ver valor consensuado actual")
    print("  4. Prueba rápida con valor por defecto")
    print("  5. Salir")
    print()


def get_utc_timestamp():
    """Retorna timestamp UTC formateado."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " UTC"


def run_interactive(node: PaxosNode):
    """Ejecuta el modo interactivo del nodo Paxos."""

    print(f"\n{Colors.GREEN}✓ Nodo Paxos iniciado correctamente{Colors.RESET}")
    print(f"  IP Local: {node.local_ip}")
    print(f"  Node ID:  {node.node_id}")
    print(f"  Puerto:   5000 (UDP)")
    print(f"\n{Colors.YELLOW}⚡ IMPORTANTE: Asegúrate de que Wireshark esté capturando{Colors.RESET}")
    print(f"   Filtro recomendado: udp.port == 5000")
    print()

    while True:
        try:
            print_menu()
            choice = input(
                f"{Colors.CYAN}Selecciona una opción (1-5): {Colors.RESET}").strip()

            if choice == "1":
                # Proponer un valor personalizado
                print(f"\n{Colors.YELLOW}--- PROPONER VALOR ---{Colors.RESET}")
                value = input("Ingresa el valor a proponer: ").strip()

                if not value:
                    print(
                        f"{Colors.RED}Error: El valor no puede estar vacío{Colors.RESET}")
                    continue

                print(
                    f"\n{Colors.CYAN}[{get_utc_timestamp()}] Iniciando propuesta...{Colors.RESET}")
                print(f"  Valor: '{value}'")
                print(f"  Quórum requerido: 2/3 nodos")
                print()

                # Ejecutar propuesta
                start_time = time.time()
                success = node.propose(value)
                elapsed = time.time() - start_time

                print(
                    f"\n{Colors.CYAN}[{get_utc_timestamp()}] Resultado:{Colors.RESET}")
                if success:
                    print(f"  {Colors.GREEN}✓ CONSENSO ALCANZADO{Colors.RESET}")
                    print(f"  Valor acordado: '{node.learned_value}'")
                    print(f"  Propuesta #: {node.learned_proposal}")
                else:
                    print(
                        f"  {Colors.RED}✗ NO SE ALCANZÓ CONSENSO{Colors.RESET}")
                    print(f"  Posibles causas:")
                    print(f"    - No hay suficientes nodos activos (necesita 2/3)")
                    print(f"    - Timeout en la comunicación")
                    print(f"    - Conflicto con otra propuesta")

                print(f"  Tiempo transcurrido: {elapsed:.2f}s")

            elif choice == "2":
                # Ver estado completo del nodo
                print(f"\n{Colors.YELLOW}--- ESTADO DEL NODO ---{Colors.RESET}")
                print(f"Timestamp: {get_utc_timestamp()}")
                node.print_status()

            elif choice == "3":
                # Ver valor consensuado
                print(f"\n{Colors.YELLOW}--- VALOR CONSENSUADO ---{Colors.RESET}")
                print(f"Timestamp: {get_utc_timestamp()}")

                if node.learned_value is not None:
                    print(
                        f"  {Colors.GREEN}Valor: '{node.learned_value}'{Colors.RESET}")
                    print(f"  Propuesta #: {node.learned_proposal}")
                else:
                    print(
                        f"  {Colors.YELLOW}Ningún valor consensuado aún{Colors.RESET}")

            elif choice == "4":
                # Prueba rápida con valor por defecto
                test_value = f"test_grupo7_{int(time.time())}"

                print(f"\n{Colors.YELLOW}--- PRUEBA RÁPIDA ---{Colors.RESET}")
                print(
                    f"{Colors.CYAN}[{get_utc_timestamp()}] Iniciando propuesta de prueba...{Colors.RESET}")
                print(f"  Valor: '{test_value}'")
                print()

                start_time = time.time()
                success = node.propose(test_value)
                elapsed = time.time() - start_time

                print(
                    f"\n{Colors.CYAN}[{get_utc_timestamp()}] Resultado:{Colors.RESET}")
                if success:
                    print(f"  {Colors.GREEN}✓ CONSENSO ALCANZADO{Colors.RESET}")
                    print(f"  Valor acordado: '{node.learned_value}'")
                else:
                    print(
                        f"  {Colors.RED}✗ NO SE ALCANZÓ CONSENSO{Colors.RESET}")
                print(f"  Tiempo: {elapsed:.2f}s")

            elif choice == "5":
                print(f"\n{Colors.YELLOW}Cerrando nodo Paxos...{Colors.RESET}")
                break

            else:
                print(f"{Colors.RED}Opción inválida. Selecciona 1-5.{Colors.RESET}")

        except KeyboardInterrupt:
            print(
                f"\n\n{Colors.YELLOW}Interrupción recibida (Ctrl+C){Colors.RESET}")
            break
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")


def main():
    """Función principal."""
    print_banner()

    # Verificar argumentos
    if len(sys.argv) != 2:
        print(f"{Colors.RED}Error: Debes especificar tu IP de ZeroTier{Colors.RESET}")
        print(f"\nUso: python run_paxos.py <ip_zerotier>")
        print_nodes_info()
        print("Ejemplo:")
        print("  python run_paxos.py 10.184.53.33")
        sys.exit(1)

    local_ip = sys.argv[1]

    # Validar IP
    valid_ips = list(NODES.values())
    if local_ip not in valid_ips:
        print(
            f"{Colors.RED}Error: IP '{local_ip}' no está en la configuración{Colors.RESET}")
        print_nodes_info()
        sys.exit(1)

    # Identificar nodo
    node_name = next((name for name, ip in NODES.items()
                     if ip == local_ip), "unknown")
    print(
        f"Iniciando como: {Colors.GREEN}{node_name.capitalize()}{Colors.RESET} ({local_ip})")
    print()

    # Crear e iniciar nodo Paxos
    try:
        print(f"{Colors.CYAN}Inicializando nodo Paxos...{Colors.RESET}")
        node = PaxosNode(local_ip)
        node.start()

        # Dar tiempo para que el socket se estabilice
        time.sleep(0.5)

        # Ejecutar modo interactivo
        run_interactive(node)

    except Exception as e:
        print(f"{Colors.RED}Error fatal: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Asegurar cierre limpio
        if 'node' in locals():
            print(f"{Colors.CYAN}Deteniendo nodo...{Colors.RESET}")
            node.stop()
            print(f"{Colors.GREEN}✓ Nodo detenido correctamente{Colors.RESET}")


if __name__ == "__main__":
    main()
