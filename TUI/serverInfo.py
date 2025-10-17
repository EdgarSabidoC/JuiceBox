#!/usr/bin/env python3
import platform
import psutil
import os
import socket
from datetime import datetime


class ServerInfo:
    """
    Clase encargada de obtener y formatear información del sistema anfitrión.

    Reúne datos sobre el sistema operativo, arquitectura, versión del kernel,
    memoria RAM, dirección IP local, versión de Python y entorno del terminal.
    Esta información se usa principalmente para mostrar en la interfaz TUI
    de JuiceBox.

    Atributos:
        os_name (str): Nombre del sistema operativo (por ejemplo, 'Linux').
        architecture (str): Arquitectura del sistema ('x86_64', 'arm64', etc.).
        hostname (str): Nombre del host de la máquina.
        uptime (datetime.timedelta): Tiempo de actividad desde el último arranque.
        kernel (str): Versión del kernel del sistema operativo.
        ram (dict): Información sobre la memoria RAM total.
        python_version (str): Versión actual de Python.
        local_ip (str): Dirección IP local del dispositivo.
        terminal (str | None): Nombre del emulador de terminal detectado.
    """

    def __init__(self) -> None:
        """
        Inicializa los atributos de la clase con información del sistema.

        Al crear una instancia, se consultan los datos básicos del sistema operativo,
        hardware y entorno actual, utilizando las librerías estándar `platform`,
        `psutil` y `socket`.
        """
        self.os_name = platform.system()
        self.architecture = platform.machine()
        self.hostname = platform.node()
        self.uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        self.kernel = platform.release()
        self.ram = self.get_ram()
        self.python_version = platform.python_version()
        self.local_ip = socket.gethostbyname(socket.gethostname())
        self.terminal = self.detect_terminal_emulator()

    def get_os_name(self) -> dict:
        """
        Obtiene el nombre del sistema operativo.

        Returns:
            dict: Diccionario con el nombre del sistema bajo la clave 'OS'.
        """
        return {"OS": self.os_name}

    def get_os_architecture(self) -> dict:
        """
        Obtiene la arquitectura del sistema.

        Returns:
            dict: Diccionario con la arquitectura bajo la clave 'Architecture'.
        """
        return {"Architecture": self.architecture}

    def get_hostname(self) -> dict:
        """
        Obtiene el nombre del host del sistema.

        Returns:
            dict: Diccionario con el nombre del host bajo la clave 'Hostname'.
        """
        return {"Hostname": self.hostname}

    def get_uptime(self) -> dict:
        """
        Calcula el tiempo de actividad del sistema desde el último arranque.

        Returns:
            dict: Diccionario con el tiempo de actividad bajo la clave 'Uptime'.
        """
        return {"Uptime": self.uptime}

    def get_kernel(self) -> dict:
        """
        Obtiene la versión del kernel del sistema operativo.

        Returns:
            dict: Diccionario con la versión del kernel bajo la clave 'Kernel'.
        """
        return {"Kernel": self.kernel}

    def get_ram(self, show_current: bool = False) -> dict:
        """
        Obtiene información sobre la memoria RAM del sistema.

        Args:
            show_current (bool, opcional): Si es True, muestra el uso actual de
                la memoria (usada/total y porcentaje). Si es False, solo muestra
                la memoria total. Por defecto es False.

        Returns:
            dict: Diccionario con la información de RAM bajo la clave 'RAM'.
        """
        if show_current:
            # Retorna el estado y uso actual de la RAM:
            return {
                "RAM": f"{round(psutil.virtual_memory().used / 1e9, 2)} GiB / {round(psutil.virtual_memory().total / 1e9, 2)} GiB ({psutil.virtual_memory().percent}%)"
            }
        # Retorna el total de RAM reconocida por el sistema:
        return {"RAM": f"{round(psutil.virtual_memory().total / 1e9, 2)} GiB"}

    def get_python_version(self) -> dict:
        """
        Obtiene la versión actual de Python utilizada por el programa.

        Returns:
            dict: Diccionario con la versión bajo la clave 'Python version'.
        """
        return {"Python version": self.python_version}

    def get_local_ip(self) -> dict:
        """
        Obtiene la dirección IP local del dispositivo.

        Returns:
            dict: Diccionario con la dirección IP bajo la clave 'Local IP'.
        """
        return {"Local IP": self.local_ip}

    def get_terminal(self) -> dict:
        """
        Obtiene el nombre del emulador de terminal actual (si es posible).

        Returns:
            dict: Diccionario con el nombre del terminal bajo la clave 'Terminal'.
        """
        return {"Terminal": self.terminal}

    def get_all_info(self) -> dict:
        """
        Reúne toda la información del sistema en un solo diccionario.

        Combina los resultados de todos los métodos `get_*` para entregar
        una vista completa del estado del sistema.

        Returns:
            dict: Diccionario con todos los datos del sistema.
        """
        return (
            self.get_os_name()
            | self.get_os_architecture()
            | self.get_hostname()
            | self.get_uptime()
            | self.get_kernel()
            | self.get_ram()
            | self.get_python_version()
            | self.get_local_ip()
            | self.get_terminal()
        )

    def get_all_info_as_str(self) -> str:
        """
        Devuelve toda la información del sistema formateada como texto legible.

        Returns:
            str: Cadena con los datos del sistema, uno por línea, en formato clave: valor.
        """
        info = ""
        raw_data = self.get_all_info()
        raw_data_keys = raw_data.keys()
        for key in raw_data_keys:
            info += f"{key}: {raw_data[key]}\n"
        return info

    def detect_terminal_emulator(self) -> str | None:
        """
        Intenta detectar el nombre del emulador de terminal actual.

        El método obtiene el proceso actual (Python), su proceso padre (shell)
        y su abuelo (terminal), utilizando `psutil`. Si logra identificar
        el terminal, devuelve su nombre.

        Returns:
            str | None: Nombre del emulador de terminal detectado, o None si no se pudo determinar.
        """
        # PID de Python
        pid_py = os.getpid()
        # padre == shell, abuelo == terminal
        shell = psutil.Process(pid_py).parent()
        if shell:
            terminal = shell.parent()
            if terminal:
                return terminal.name()
