#!/usr/bin/env python3
import os, socket, threading, json
from scripts.juiceShopManager import JuiceShopManager
from scripts.rootTheBoxManager import RootTheBoxManager

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

    def __handle_rtb_command(self, command, args) -> str:
        if command == "__START__":
            self.rtb_manager.run_containers()
            return self.format_response("ok", "RootTheBox iniciado")
        elif command == "__RESTART__":
            self.rtb_manager.restart()
            return self.format_response("ok", "RootTheBox reiniciado")
        elif command == "__KILL__":
            self.rtb_manager.kill_all()
            return self.format_response("ok", "RootTheBox detenido")
        elif command == "__STATUS__":
            status = self.rtb_manager.status()
            return self.format_response("ok", "Estado obtenido", status)
        elif command == "__CONFIG__":
            self.rtb_manager.configure(args)
            return self.format_response("ok", "RootTheBox configurado")
        else:
            return self.format_response("error", "Comando RTB no implementado")

    def __handle_js_command(self, command, args) -> str:
        if command == "__START_CONTAINER__":
            self.js_manager.run_container()
            return self.format_response("ok", "Contenedor Juice Shop iniciado")
        elif command == "__RESTART__":
            self.js_manager.restart()
            return self.format_response("ok", "Juice Shop reiniciado")
        elif command == "__KILL_CONTAINER__":
            self.js_manager.kill_container(args)
            return self.format_response("ok", "Contenedor detenido")
        elif command == "__KILL_ALL__":
            self.js_manager.kill_all()
            return self.format_response(
                "ok", "Todos los contenedores Juice Shop detenidos"
            )
        elif command == "__STATUS__":
            status = self.js_manager.status()
            return self.format_response("ok", "Estado obtenido", status)
        elif command == "__CONFIG__":
            self.js_manager.configure(args)
            return self.format_response("ok", "Juice Shop configurado")
        elif command == "__GENERATE_XML__":
            self.js_manager.generate_xml()
            return self.format_response("ok", "XML generado")
        else:
            return self.format_response("error", "Comando JS no implementado")

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
            if prog == "RTB":
                return self.__handle_rtb_command(command, args)

            # Juice Shop
            if prog == "JS":
                return self.__handle_js_command(command, args)

            return self.format_response("error", "Programa no soportado")

        except json.JSONDecodeError:
            return self.format_response("error", "Formato JSON inválido")
        except Exception as e:
            return self.format_response("error", str(e))

    def cleanup(self):
        self.server_socket.close()
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

    def format_response(self, status: str, message: str, data=None) -> str:
        response = {"status": status, "message": message}
        if data:
            response["data"] = data
        return json.dumps(response)
