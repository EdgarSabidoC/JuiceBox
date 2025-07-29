#!/usr/bin/env python3
import os, socket, threading, json
from queue import Queue
from threading import Thread
from scripts.juiceShopManager import JuiceShopManager
from scripts.rootTheBoxManager import RootTheBoxManager
from scripts.utils.config import RTBConfig, JuiceShopConfig
from Monitor.monitor import Monitor

# Comandos válidos por programa
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
    """
    Servidor del motor JuiceBox que expone una interfaz mediante sockets de Unix para
    gestionar contenedores Docker de Juice Shop y Root The Box de manera concurrente pero segura.
    """

    def __init__(
        self,
        js_manager: JuiceShopManager,
        rtb_manager: RootTheBoxManager,
        socket_path: str = "/tmp/juiceboxengine.sock",
    ):
        """
        Inicializa el servidor, elimina cualquier socket viejo y comienza el hilo worker.

        :param js_manager: Instancia de JuiceShopManager
        :param rtb_manager: Instancia de RootTheBoxManager
        :param socket_path: Ruta del socket UNIX
        """
        self.socket_path = socket_path
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        # Monitor
        self.monitor = Monitor(
            name="JuiceBoxEngine", use_syslog=False
        )  # use_syslog = False para imprimir en consola

        # Se crea socket del servidor
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen()

        # Managers
        self.rtb_manager = rtb_manager
        self.js_manager = js_manager

        # Cola para recibir y procesar comandos de los clientes
        self.command_queue = Queue()
        Thread(target=self.worker, daemon=True).start()

    def worker(self):
        """
        Hilo que atiende solicitudes de la cola una a una.
        """
        while True:
            try:
                conn, raw_data = self.command_queue.get()
                self.process_request(conn, raw_data)
            except Exception as e:
                self.monitor.error(f"Worker failed: {e}")
            finally:
                self.command_queue.task_done()

    def handle_client(self, conn) -> None:
        """
        Maneja la conexión de un cliente y pone su mensaje en la cola.

        :param conn: Socket del cliente
        """
        try:
            data = conn.recv(1024).decode().strip()
            self.monitor.info(f"Data received: {data}")
            self.monitor.command_received(conn, data, conn.getpeername())
            self.command_queue.put((conn, data))
        except socket.timeout:
            self.monitor.warning("Timeout: client couldn't send data.")
            conn.close()
        except Exception as e:
            self.monitor.client_error(e)
            conn.close()

    def process_request(self, conn, data):
        """
        Procesa un mensaje recibido, lo despacha y envía la respuesta.

        :param conn: Conexión del cliente
        :param data: Cadena JSON con el comando
        """
        try:
            # Se parsea para obtener prog y command y loguearlos
            payload = json.loads(data)
            prog = payload.get("prog", "UNKNOWN")
            command = payload.get("command", "UNKNOWN")
            self.monitor.command_received(prog, command, conn.getpeername())

            response = self.dispatch_command(data)
            conn.sendall(response.encode())
            self.monitor.info(f"Response sent to command: {command}")
        except (BrokenPipeError, ConnectionResetError) as e:
            self.monitor.warning(f"Client disconnected before get answer: {e}")
        except Exception as e:
            self.monitor.error(f"Error when processing request: {e}")
            error_json = self.format_response("error", str(e))
            try:
                conn.sendall(error_json.encode())
            except Exception:
                pass
        finally:
            conn.close()

    def __rtb_restart(self) -> dict[str, str]:
        """
        Reinicia la instancia del manager de RTB.
        """
        try:
            self.rtb_manager.cleanup()
        except AttributeError:
            pass

        self.rtb_manager = RootTheBoxManager(RTBConfig())
        return self.rtb_manager.run_containers()

    def __js_restart(self) -> dict[str, str]:
        """
        Reinicia la instancia del manager de Juice Shop.
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
        """
        Reemplaza las instancias actuales de los managers por otras.

        :param rtb: Nueva instancia de RootTheBoxManager
        :param js: Nueva instancia de JuiceShopManager
        """
        self.rtb_manager = rtb
        self.js_manager = js

    def start(self):
        """
        Inicia el servidor y acepta conexiones entrantes indefinidamente.
        """
        print(f"🔌 JuiceBoxEngine listening on {self.socket_path}")
        self.monitor.info(f"JuiceBoxEngine listening on {self.socket_path}")
        while True:
            conn, _ = self.server_socket.accept()
            conn.settimeout(10)
            threading.Thread(
                target=self.handle_client, args=(conn,), daemon=True
            ).start()

    def __handle_rtb_command(self, command: str) -> str:
        """
        Ejecuta un comando específico para Root The Box.

        :param command: Comando recibido
        :return: Respuesta JSON serializada
        """
        match command:
            case "__START__":
                return json.dumps(self.rtb_manager.run_containers())
            case "__RESTART__":
                return json.dumps(self.__rtb_restart())
            case "__KILL__":
                return json.dumps(self.rtb_manager.kill_all())
            case "__STATUS__":
                return json.dumps(self.rtb_manager.status())
            case "__CONFIG__":
                return json.dumps(self.rtb_manager.show_config())
            case _:
                return self.format_response("error", "RTB command not found")

    def __handle_js_command(self, command: str, args: dict) -> str:
        """
        Ejecuta un comando específico para Juice Shop.

        :param command: Comando recibido
        :param args: Argumentos adicionales como puerto o nombre
        :return: Respuesta JSON serializada
        """
        match command:
            case "__START_CONTAINER__":
                return json.dumps(self.js_manager.run_container())
            case "__RESTART__":
                return json.dumps(self.__js_restart())
            case "__KILL_CONTAINER__":
                return json.dumps(self.js_manager.kill_container(args["port"]))
            case "__KILL_ALL__":
                return json.dumps(self.js_manager.kill_all())
            case "__STATUS__":
                return json.dumps(self.js_manager.status(args["port"]))
            case "__CONFIG__":
                return json.dumps(self.js_manager.show_config())
            case "__GENERATE_XML__":
                return json.dumps(self.js_manager.generate_rtb_config())
            case _:
                return self.format_response("error", "JS command not found")

    def dispatch_command(self, raw_data: str) -> str:
        """
        Parsea el comando recibido y lo redirige al manager correspondiente.

        :param raw_data: Cadena JSON enviada por el cliente
        :return: Respuesta serializada en formato JSON
        """
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

            if prog == "RTB":
                return self.__handle_rtb_command(command)
            if prog == "JS":
                return self.__handle_js_command(command, args)

            return self.format_response("error", "Programa no soportado")

        except json.JSONDecodeError:
            return self.format_response("error", "Formato JSON inválido")
        except Exception as e:
            return self.format_response("error", str(e))

    def cleanup(self):
        """
        Limpieza general del servidor: cierra el socket y elimina los contenedores.
        """
        self.server_socket.close()
        self.js_manager.cleanup()
        self.rtb_manager.cleanup()
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

    def format_response(self, status: str, message: str, data=None) -> str:
        """
        Estandariza el formato de las respuestas enviadas a los clientes.

        :param status: 'ok' o 'error'
        :param message: Mensaje descriptivo
        :param data: Objeto opcional con datos extra
        :return: Cadena JSON
        """
        response = {"status": status, "message": message}
        if data:
            response["data"] = data
        return json.dumps(response)
