#!/usr/bin/env python3
import os, socket, threading, json, redis, time
from queue import Queue
from threading import Thread
from scripts.juiceShopManager import JuiceShopManager
from scripts.rootTheBoxManager import RootTheBoxManager
from scripts.utils.config import RTBConfig, JuiceShopConfig
from scripts.monitor import Monitor
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union

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
            name="JuiceBoxEngine", use_journal=True
        )  # use_syslog = False para imprimir en consola

        # Se crea socket del servidor
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen()

        # Managers
        self.rtb_manager = rtb_manager
        self.js_manager = js_manager
        self.__manager_lock = threading.Lock()

        # Redis:
        redis_url = os.getenv("REDIS_URL", "redis://:C5L48@127.0.0.1:6379/0")
        self.redis = redis.Redis.from_url(redis_url)

        # Canales de Redis:
        self.admin_channel = "admin_channel"
        self.client_channel = "client_channel"

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
            error_json = json.dumps(self.format_response("error", str(e)))
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
        with self.__manager_lock:
            self.rtb_manager = rtb
            self.js_manager = js

    def start(self):
        """
        Inicia el servidor y acepta conexiones entrantes indefinidamente.
        """
        print(f"🔌 JuiceBoxEngine started and listening on port: {self.socket_path}")
        self.monitor.info(
            f"JuiceBoxEngine started and listening on port: {self.socket_path}"
        )
        while True:
            conn, _ = self.server_socket.accept()
            conn.settimeout(10)
            threading.Thread(
                target=self.handle_client, args=(conn,), daemon=True
            ).start()

    def __handle_rtb_command(self, command: str) -> dict:
        """
        Ejecuta un comando específico para Root The Box.

        :param command: Comando recibido
        :return: Respuesta JSON serializada
        """
        # Lee el manager dentro del lock para asegurar coherencia.
        with self.__manager_lock:
            __manager = self.rtb_manager
        __resp: dict
        match command:
            case "__START__":
                __resp = __manager.run_containers()
            case "__RESTART__":
                __resp = self.__rtb_restart()
            case "__KILL__":
                __resp = __manager.kill_all()
            case "__STATUS__":
                __resp = __manager.status()
            case "__CONFIG__":
                __resp = __manager.show_config()
            case _:
                __resp = self.format_response("error", "Root The Box command not found")
        # Se publica en Redis
        self.redis.publish(
            self.admin_channel,
            json.dumps(
                {
                    "prog": "RTB",
                    "command": command,
                    "result": __resp,
                    "timestamp": time.time(),
                }
            ),
        )
        # Retorno
        return __resp

    def __handle_js_command(self, command: str, args: dict) -> dict:
        """
        Ejecuta un comando específico para Juice Shop.

        :param command: Comando recibido
        :param args: Argumentos adicionales como puerto o nombre
        :return: Respuesta JSON serializada
        """
        # Lee el manager dentro del lock para asegurar coherencia.
        with self.__manager_lock:
            __manager = self.js_manager
        __resp: dict
        match command:
            case "__START_CONTAINER__":
                __resp = __manager.run_container()
            case "__RESTART__":
                __resp = self.__js_restart()
            case "__KILL_CONTAINER__":
                __resp = __manager.kill_container(args["port"])
            case "__KILL_ALL__":
                __resp = __manager.kill_all()
            case "__STATUS__":
                __resp = __manager.status(args["port"])
            case "__CONFIG__":
                __resp = __manager.show_config()
            case "__GENERATE_XML__":
                __resp = __manager.generate_rtb_config()
            case _:
                __resp = self.format_response(
                    status="error", message="Juice Shop command not found"
                )
        # Se publica en Redis
        self.redis.publish(
            self.admin_channel,
            json.dumps(
                {
                    "prog": "JS",
                    "command": command,
                    "result": __resp,
                    "timestamp": time.time(),
                }
            ),
        )
        self.redis.publish(
            self.client_channel,
            json.dumps(
                {
                    "prog": "JS",
                    "command": command,
                    "result": __resp,
                    "timestamp": time.time(),
                }
            ),
        )
        # Retorno
        return __resp

    def dispatch_command(self, raw_data: str) -> str:
        """
        Parsea el comando recibido y lo redirige al manager correspondiente.

        :param raw_data: Cadena JSON enviada por el cliente
        :return: Respuesta serializada en formato JSON
        """
        __resp: dict = self.format_response("error", "Program not supported by engine")
        try:
            payload = json.loads(raw_data)
            prog = payload.get("prog")
            command = payload.get("command")
            args = payload.get("args", {})

            if prog not in COMMANDS:
                __resp = self.format_response(
                    status="error", message="Program not recognized"
                )
            elif command not in COMMANDS[prog]:
                __resp = self.format_response(
                    status="error", message="Command not recognized by program"
                )
            elif prog == "RTB":
                __resp = self.__handle_rtb_command(command)
            else:
                # prog == "JS"
                __resp = self.__handle_js_command(command, args)
        except json.JSONDecodeError:
            __resp = self.format_response("error", "Invalid JSON format")
        except Exception as e:
            __resp = self.format_response("error", str(e))
        return json.dumps(__resp)

    def cleanup(self):
        """
        Limpieza general del servidor: cierra el socket y elimina los contenedores.
        """
        # Lee el manager dentro del lock para asegurar coherencia.
        with self.__manager_lock:
            __rtb_manager = self.rtb_manager
            __js_manager = self.js_manager
        self.server_socket.close()
        __js_manager.cleanup()
        __rtb_manager.cleanup()
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

    def format_response(self, status: str, message: str, data=None) -> dict:
        """
        Estandariza el formato de las respuestas enviadas a los clientes.

        :param status: 'ok' o 'error'
        :param message: Mensaje descriptivo
        :param data: Objeto opcional con datos extra
        :return: Objeto dict (JSON)
        """
        response: dict = {"status": status, "message": message}
        if data:
            response["data"] = data
        return response
