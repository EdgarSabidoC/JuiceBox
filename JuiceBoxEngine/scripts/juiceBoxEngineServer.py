#!/usr/bin/env python3
import os, socket, threading, json
from scripts.juiceShopManager import JuiceShopManager
from scripts.rootTheBoxManager import RootTheBoxManager
from scripts.utils.config import RTBConfig, JuiceShopConfig

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

    def __rtb_restart(self) -> dict[str, str]:
        """
        Desecha la instancia vieja de RootTheBoxManager y crea una nueva.
        """
        try:
            self.rtb_manager.cleanup()
        except AttributeError:
            pass

        # Crea una nueva instancia usando la misma configuración
        self.rtb_manager = RootTheBoxManager(RTBConfig())
        status = self.rtb_manager.run_containers()

        return status

    def __js_restart(self) -> dict[str, str]:
        """
        Desecha la instancia vieja de JuiceShopManager y crea una nueva.
        """
        try:
            self.js_manager.cleanup()
        except AttributeError:
            pass

        self.js_manager = JuiceShopManager(JuiceShopConfig())
        return {
            "status": "ok",
            "message": "JuiceShop manager reiniciado",
        }

    def set_managers(self, rtb, js):
        self.rtb_manager = rtb
        self.js_manager = js

    def start(self):
        print(f"🔌 JuiceBoxEngine listening on {self.socket_path}")
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

    def __handle_rtb_command(self, command) -> str:
        if command == "__START__":
            status = self.rtb_manager.run_containers()
            return json.dumps(status)
        elif command == "__RESTART__":
            status = self.__rtb_restart()
            return json.dumps(status)
        elif command == "__KILL__":
            status = self.rtb_manager.kill_all()
            return json.dumps(status)
        elif command == "__STATUS__":
            status = self.rtb_manager.status()
            return json.dumps(status)
        elif command == "__CONFIG__":
            status = self.rtb_manager.show_config()
            return json.dumps(status)
        else:
            return self.format_response("error", "RTB command not found")

    def __handle_js_command(self, command, args) -> str:
        if command == "__START_CONTAINER__":
            status = self.js_manager.run_container()
            return json.dumps(status)
        elif command == "__RESTART__":
            status = self.__js_restart()
            return json.dumps(status)
        elif command == "__KILL_CONTAINER__":
            port = args["port"]
            status = self.js_manager.kill_container(port)
            return json.dumps(status)
        elif command == "__KILL_ALL__":
            status = self.js_manager.kill_all()
            return json.dumps(status)
        elif command == "__STATUS__":
            port = args["port"]
            status = self.js_manager.status(port)
            return json.dumps(status)
        elif command == "__CONFIG__":
            status = self.js_manager.show_config()
            return json.dumps(status)
        elif command == "__GENERATE_XML__":
            status = self.js_manager.generate_rtb_config()
            return json.dumps(status)
        else:
            return self.format_response("error", "JS command not found")

    def dispatch_command(self, raw_data: str) -> str:
        try:
            payload = json.loads(raw_data)
            prog = payload.get("prog")
            command = payload.get("command")
            args = payload.get("args", {})

            if prog not in COMMANDS:
                return self.format_response("error", "Programa no reconocido")

            if command not in COMMANDS[prog]:
                return self.format_response(
                    "error", "Comando no válido para el programa"
                )

            # Root The Box
            if prog == "RTB" and command in COMMANDS["RTB"]:
                return self.__handle_rtb_command(command)

            # Juice Shop
            if prog == "JS" and command in COMMANDS["JS"]:
                return self.__handle_js_command(command, args)

            return self.format_response("error", "Programa no soportado")

        except json.JSONDecodeError:
            return self.format_response("error", "Formato JSON inválido")
        except Exception as e:
            return self.format_response("error", str(e))

    def cleanup(self):
        """
        Cierra la conexión al socket y elimina todos los contenedores de RTB y JuiceShop.
        """
        self.server_socket.close()  # Se cierra el socket
        self.js_manager.cleanup()
        self.rtb_manager.cleanup()

        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

    def format_response(self, status: str, message: str, data=None) -> str:
        response = {"status": status, "message": message}
        if data:
            response["data"] = data
        return json.dumps(response)
