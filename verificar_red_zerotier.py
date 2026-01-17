#!/usr/bin/env python3
"""
Verificador de Red ZeroTier para Pruebas Paxos
Grupo 7 - Sistemas Distribuidos UTPL

Ejecutar ANTES de la reunión para verificar que todo está listo.
"""

import socket
import subprocess
import sys
import time
import platform

# Configuración del grupo
NODOS = {
    "francisco": "10.184.53.33",
    "pablo": "10.184.53.27",
    "farith": "10.184.53.242"
}
PUERTO_PAXOS = 5000
ZEROTIER_NETWORK = "a581878f7d3f9596"


def print_header(texto):
    print(f"\n{'='*60}")
    print(f"  {texto}")
    print('='*60)


def print_ok(msg):
    print(f"  ✅ {msg}")


def print_error(msg):
    print(f"  ❌ {msg}")


def print_warn(msg):
    print(f"  ⚠️  {msg}")


def get_zerotier_cmd():
    """Determina el comando correcto para ZeroTier según el sistema."""
    if platform.system() == "Windows":
        # Intentar rutas comunes en Windows
        paths = [
            r"C:\ProgramData\ZeroTier\One\zerotier-cli.bat",
            r"C:\Program Files (x86)\ZeroTier\One\zerotier-cli.bat",
            r"C:\Program Files\ZeroTier\One\zerotier-cli.bat"
        ]
        import os
        import shutil

        if shutil.which("zerotier-cli"):
            return ["zerotier-cli"]

        for p in paths:
            if os.path.exists(p):
                return [p]

        return ["cmd", "/c", "zerotier-cli"]  # Fallback a shell
    else:
        return ["sudo", "zerotier-cli"]


def verificar_zerotier():
    """Verifica que ZeroTier esté instalado y conectado."""
    print_header("1. VERIFICANDO ZEROTIER")

    try:
        cmd = get_zerotier_cmd()
        result = subprocess.run(
            cmd + ["info"],
            capture_output=True, text=True, timeout=10
        )

        if "ONLINE" in result.stdout:
            print_ok(f"ZeroTier está ONLINE")
            return True
        else:
            print_error(f"ZeroTier no está online: {result.stdout}")
            return False
    except FileNotFoundError:
        print_error(
            f"ZeroTier no encontrado. Intenta agregar 'C:\\ProgramData\\ZeroTier\\One' al PATH")
        return False
    except Exception as e:
        print_error(f"Error verificando ZeroTier: {e}")
        return False


def obtener_ip_local():
    """Obtiene la IP local en la red ZeroTier."""
    print_header("2. OBTENIENDO IP LOCAL ZEROTIER")

    try:
        cmd = get_zerotier_cmd()
        result = subprocess.run(
            cmd + ["listnetworks"],
            capture_output=True, text=True, timeout=10
        )
        # Buscar IP en la línea
        for parte in line.split():
            if parte.startswith("10.184."):
                print_ok(f"Tu IP ZeroTier: {parte.split('/')[0]}")
                return parte.split('/')[0]

        print_error(f"No conectado a la red {ZEROTIER_NETWORK}")
        print("  Ejecuta: zerotier-cli join a581878f7d3f9596")
        return None

    except Exception as e:
        print_error(f"Error obteniendo IP: {e}")
        return None


def verificar_conectividad(mi_ip):
    """Hace ping a los otros nodos."""
    print_header("3. VERIFICANDO CONECTIVIDAD CON OTROS NODOS")

    resultados = {}
    for nombre, ip in NODOS.items():
        if ip == mi_ip:
            print(f"  📍 {nombre.capitalize()} ({ip}) - Eres tú")
            resultados[nombre] = True
            continue

        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["ping", "-n", "2", "-w", "2000", ip],
                    capture_output=True, text=True, timeout=10
                )
            else:
                result = subprocess.run(
                    ["ping", "-c", "2", "-W", "2", ip],
                    capture_output=True, text=True, timeout=10
                )

            if result.returncode == 0:
                print_ok(f"{nombre.capitalize()} ({ip}) - Alcanzable")
                resultados[nombre] = True
            else:
                print_error(f"{nombre.capitalize()} ({ip}) - No responde")
                resultados[nombre] = False

        except subprocess.TimeoutExpired:
            print_error(f"{nombre.capitalize()} ({ip}) - Timeout")
            resultados[nombre] = False
        except Exception as e:
            print_error(f"{nombre.capitalize()} ({ip}) - Error: {e}")
            resultados[nombre] = False

    return resultados


def verificar_puerto_disponible():
    """Verifica que el puerto UDP 5000 esté disponible."""
    print_header("4. VERIFICANDO PUERTO UDP 5000")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', PUERTO_PAXOS))
        sock.close()
        print_ok(f"Puerto {PUERTO_PAXOS} disponible para usar")
        return True
    except OSError as e:
        print_error(f"Puerto {PUERTO_PAXOS} no disponible: {e}")
        print("  Posible solución: cerrar otras instancias de Paxos")
        return False


def verificar_archivos():
    """Verifica que los archivos necesarios existan."""
    print_header("5. VERIFICANDO ARCHIVOS DEL PROYECTO")

    archivos = ["config.py", "network.py", "paxos_node.py", "run_paxos.py"]
    todos_ok = True

    for archivo in archivos:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                f.read(1)
            print_ok(f"{archivo}")
        except FileNotFoundError:
            print_error(f"{archivo} - NO ENCONTRADO")
            todos_ok = False

    return todos_ok


def verificar_imports():
    """Verifica que los módulos se puedan importar."""
    print_header("6. VERIFICANDO MÓDULOS PYTHON")

    try:
        import config
        print_ok("config.py importado correctamente")
    except Exception as e:
        print_error(f"Error importando config: {e}")
        return False

    try:
        import network
        print_ok("network.py importado correctamente")
    except Exception as e:
        print_error(f"Error importando network: {e}")
        return False

    try:
        import paxos_node
        print_ok("paxos_node.py importado correctamente")
    except Exception as e:
        print_error(f"Error importando paxos_node: {e}")
        return False

    return True


def mostrar_resumen(resultados):
    """Muestra resumen final."""
    print_header("RESUMEN")

    total_checks = len(resultados)
    passed = sum(1 for v in resultados.values() if v)

    for check, status in resultados.items():
        emoji = "✅" if status else "❌"
        print(f"  {emoji} {check}")

    print(f"\n  Resultado: {passed}/{total_checks} verificaciones pasaron")

    if passed == total_checks:
        print("\n  🎉 ¡TODO LISTO PARA LAS PRUEBAS!")
        print("\n  Próximo paso:")
        print("  1. Coordinar con compañeros por WhatsApp/Discord")
        print("  2. Abrir Wireshark (filtro: udp.port == 5000)")
        print("  3. Ejecutar: python run_paxos.py [TU_IP]")
    else:
        print("\n  ⚠️  Hay problemas que resolver antes de las pruebas")
        print("  Revisa los errores marcados con ❌")


def main():
    print("\n" + "🔍 VERIFICADOR DE RED ZEROTIER - PAXOS GRUPO 7 🔍".center(60))
    print("="*60)

    resultados = {}

    # 1. ZeroTier
    resultados["ZeroTier Online"] = verificar_zerotier()

    # 2. IP Local
    mi_ip = obtener_ip_local()
    resultados["IP ZeroTier Asignada"] = mi_ip is not None

    # 3. Conectividad (solo si tenemos IP)
    if mi_ip:
        conectividad = verificar_conectividad(mi_ip)
        nodos_alcanzables = sum(1 for v in conectividad.values() if v)
        resultados["Conectividad (mín. 2 nodos)"] = nodos_alcanzables >= 2
    else:
        resultados["Conectividad (mín. 2 nodos)"] = False

    # 4. Puerto
    resultados["Puerto UDP 5000"] = verificar_puerto_disponible()

    # 5. Archivos
    resultados["Archivos Proyecto"] = verificar_archivos()

    # 6. Imports
    resultados["Módulos Python"] = verificar_imports()

    # Resumen
    mostrar_resumen(resultados)


if __name__ == "__main__":
    main()
