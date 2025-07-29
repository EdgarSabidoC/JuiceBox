#!/usr/bin/env python3
import os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))  # …/project_root/JuiceBoxEngine
sys.path.insert(0, os.path.dirname(ROOT))  # …/project_root
from scripts.juiceBoxEngineServer import JuiceBoxEngineServer
from scripts.juiceShopManager import JuiceShopManager
from scripts.rootTheBoxManager import RootTheBoxManager
from scripts.utils.config import JuiceShopConfig, RTBConfig
from types import FrameType
import sys, signal, atexit


if __name__ == "__main__":
    # Se instancian los managers
    rtb = RootTheBoxManager(RTBConfig())  # Root the Box
    js = JuiceShopManager(JuiceShopConfig())  # Juice Shop

    # Se instancia el motor
    jb_server = JuiceBoxEngineServer(js, rtb)  # Juice Box Engine

    # Función para manejar el cierre del programa
    def handle_exit(signum: int, frame: FrameType | None):
        print(f"\n📶 Received signal: {signum}. Closing socket...")
        jb_server.cleanup()  # Se limpia el socket
        sys.exit(0)

    # Se capturan las señales de interrupción
    signal.signal(signal.SIGINT, handle_exit)  # Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit)  # kill
    signal.signal(signal.SIGHUP, handle_exit)  # cierre de terminal (hangup)

    # En Windows existe SIGBREAK para Ctrl+Break
    sigbreak = getattr(signal, "SIGBREAK", None)
    if sigbreak is not None:
        try:
            signal.signal(sigbreak, handle_exit)
        except OSError:
            pass

    # atexit para cualquier otra salida limpia
    atexit.register(lambda: jb_server.cleanup())

    # Arranca el motor
    jb_server.start()
