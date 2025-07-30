#!/usr/bin/env python3
import platform
import psutil
import os
import socket
from datetime import datetime


class ServerInfo:
    def __init__(self) -> None:
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
        return {"OS": self.os_name}

    def get_os_architecture(self) -> dict:
        return {"Architecture": self.architecture}

    def get_hostname(self) -> dict:
        return {"Hostname": self.hostname}

    def get_uptime(self) -> dict:
        return {"Uptime": self.uptime}

    def get_kernel(self) -> dict:
        return {"Kernel": self.kernel}

    def get_ram(self, show_current: bool = False) -> dict:
        if show_current:
            # Retorna el estado y uso actual de la RAM:
            return {
                "RAM": f"{round(psutil.virtual_memory().used / 1e9, 2)} GiB / {round(psutil.virtual_memory().total / 1e9, 2)} GiB ({psutil.virtual_memory().percent}%)"
            }
        # Retorna el total de RAM reconocida por el sistema:
        return {"RAM": f"{round(psutil.virtual_memory().total / 1e9, 2)} GiB"}

    def get_python_version(self) -> dict:
        return {"Python version": self.python_version}

    def get_local_ip(self) -> dict:
        return {"Local IP": self.local_ip}

    def get_terminal(self) -> dict:
        return {"Terminal": self.terminal}

    def get_all_info(self) -> dict:
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
        info = ""
        raw_data = self.get_all_info()
        raw_data_keys = raw_data.keys()
        for key in raw_data_keys:
            info += f"{key}: {raw_data[key]}\n"
        return info

    def detect_terminal_emulator(self) -> str | None:
        # PID de Python
        pid_py = os.getpid()
        # padre == shell, abuelo == terminal
        shell = psutil.Process(pid_py).parent()
        if shell:
            terminal = shell.parent()
            if terminal:
                return terminal.name()
