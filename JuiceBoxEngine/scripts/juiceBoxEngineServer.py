#!/usr/bin/env python3
import os, socket, threading, json
from juiceShopManager import JuiceShopManager
from rootTheBoxManager import RootTheBoxManager

COMMANDS = {
    "RTB": ["__START__", "__KILL__", "__RESTART__", "__CONFIG__", "__STATUS__"],
    "JS": [
        "__RESTART__",
        "__CONFIG__",
        "__STATUS__",
        "__START_CONTAINER__",
        "__KILL_CONTAINER__",
        "__KILL_ALL__",
        "__GENERATE_XML__",
    ],
}


class JuiceBoxEngineServer:
    def __init__(
        self,
        js_manager: JuiceShopManager,
        rtb_manager: RootTheBoxManager,
        socket_path: str = "/tmp/juiceboxengine.sock",
    ):
        # Verifica si el socket ya existe y lo elimina
        self.socket_path = socket_path
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        # Configura el socket
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen()

        # Managers
        self.rtb_manager = rtb_manager
        self.js_manager = js_manager

    def set_managers(self, rtb, js):
        self.rtb_manager = rtb
        self.js_manager = js

    def start(self):
        print(f"🔌 JuiceBoxEngine escuchando en {self.socket_path}")
        while True:
            conn, _ = self.server_socket.accept()
            threading.Thread(
                target=self.handle_client, args=(conn,), daemon=True
            ).start()

    def handle_client(self, conn):
        with conn:
            try:
                data = conn.recv(1024).decode().strip()
                response = self.dispatch_command(data)
                conn.sendall(response.encode())
            except Exception as e:
                conn.sendall(f"Error: {e}".encode())

    def dispatch_command(self, cmd: str) -> str:
        if cmd == "run_rtb":
            self.rtb_manager.run_containers()
            return "RootTheBox iniciado"
        elif cmd == "kill_rtb":
            self.rtb_manager.kill_all()
            return "RootTheBox detenido"
        elif cmd == "run_container_js":
            self.js_manager.run_container()
            return "Juice Shop iniciado"
        elif cmd == "kill_all_js":
            self.js_manager.kill_all()
            return "Juice Shop detenido"
        else:
            return "Comando no reconocido"

    def cleanup(self):
        self.server_socket.close()
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

    def format_response(self, status: str, message: str, data=None) -> str:
        response = {"status": status, "message": message}
        if data:
            response["data"] = data
        return json.dumps(response)
