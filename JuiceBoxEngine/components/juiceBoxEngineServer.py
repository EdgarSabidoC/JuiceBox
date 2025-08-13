#!/usr/bin/env python3
import os, socket, threading, json, atexit
from queue import Queue
from threading import Thread
from .juiceShopManager import JuiceShopManager
from .rootTheBoxManager import RootTheBoxManager
from .redisManager import RedisManager
from ..utils import RTBConfig, JuiceShopConfig
from .monitor import Monitor
from Models import (
    BaseManager,
    Response,
    Status,
    RedisPayload,
    ManagerResult,
)
from docker import DockerClient
from dotenv import dotenv_values

# Comandos válidos por programa
COMMANDS = {
    "RTB": [
        "__START__",
        "__STOP__",
        "__RESTART__",
        "__CONFIG__",
        "__STATUS__",
        "__SET_CONFIG__",
    ],
    "JS": [
        "__RESTART__",
        "__CONFIG__",
        "__STATUS__",
        "__START_CONTAINER__",
        "__STOP_CONTAINER__",
        "__CONTAINER_STATUS__",
        "__STATUS__",
        "__STOP__",
        "__SET_CONFIG__",
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
        monitor: Monitor,
        js_manager: JuiceShopManager,
        rtb_manager: RootTheBoxManager,
        docker_client: DockerClient,
        redis_manager: RedisManager,
    ):
        """
        Inicializa el servidor, elimina cualquier socket viejo y comienza el hilo worker.

        :param: monitor (Monitor): Monitor
        :param: js_manager (str): Instancia de JuiceShopManager
        :param: rtb_manager (str): Instancia de RootTheBoxManager
        :param: docker_client (DockerClient): Cliente de Docker
        :param: redis_manager (RedisManager): Manager de Redis
        """
        # Obtiene la ruta del socket
        self.socket_path: str = (
            dotenv_values().get("JUICEBOX_SOCKET") or "/run/juicebox/juicebox.sock"
        )
        # Obtiene la carpeta que contiene el socket
        socket_dir = os.path.dirname(self.socket_path)

        # Crea la carpeta si no existe
        os.makedirs(socket_dir, exist_ok=True)

        # 3. Si hay un socket antiguo, elimínalo
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        # Cliente Docker
        if docker_client:
            self.docker_client: DockerClient | None = docker_client

        # Monitor
        self.monitor = monitor

        # Se crea socket del servidor
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen()

        # Managers
        self.rtb_manager = rtb_manager
        self.js_manager = js_manager
        self.redis_manager = redis_manager
        self.__manager_lock = threading.Lock()

        # Cola para recibir y procesar comandos de los clientes
        self.command_queue = Queue()
        Thread(target=self.__worker, daemon=True).start()

        atexit.register(self.cleanup)

    def __worker(self):
        """
        Hilo que atiende solicitudes de la cola una a una.
        """
        while True:
            try:
                conn, raw_data = self.command_queue.get()
                self.__process_request(conn, raw_data)
            except Exception as e:
                self.monitor.error(f"Worker failed: {e}")
            finally:
                self.command_queue.task_done()

    def __handle_client(self, conn) -> None:
        """
        Maneja la conexión de un cliente y pone su mensaje en la cola.

        Args:
            conn: Socket del cliente
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

    def __process_request(self, conn, data):
        """
        Procesa un mensaje recibido, lo despacha y envía la respuesta.

        Args:
            conn: Conexión del cliente.
            data: Cadena JSON con el comando.
        """
        try:
            # Se parsea para obtener prog y command y loggearlos
            payload = json.loads(data)
            prog = payload.get("prog", "UNKNOWN")
            command = payload.get("command", "UNKNOWN")
            self.monitor.command_received(prog, command, conn.getpeername())

            response = self.dispatch_command(data)
            if response.status != Status.OK:
                self.monitor.error(
                    f"Error processing command {command} for program {prog}: {response.message}"
                )
            else:
                self.monitor.info(
                    f"Command {command} for program {prog} processed successfully."
                )
            response = response.to_json()
            conn.sendall(response.encode())
            self.monitor.info(
                f"Response sent to command: {command}. Response data: {response}"
            )
        except (BrokenPipeError, ConnectionResetError) as e:
            self.monitor.warning(f"Client disconnected before get answer: {e}")
        except Exception as e:
            self.monitor.error(f"Error when processing request: {e}")
            error_json = Response.error(str(e)).to_json()
            try:
                conn.sendall(error_json.encode())
            except Exception:
                pass
        finally:
            conn.close()

    def __rtb_restart(self) -> ManagerResult:
        """
        Reinicia la instancia del manager de Root The Box.

        Returns:
          ManagerResult: Resultado de la operación.
        """
        try:
            self.rtb_manager.cleanup()
        except AttributeError as e:
            return ManagerResult.failure(
                message="Error at restarting Root The Box Manager", error=str(e)
            )

        self.rtb_manager = RootTheBoxManager(RTBConfig())
        return self.rtb_manager.start()

    def __js_restart(self) -> ManagerResult:
        """
        Reinicia la instancia del manager de la Juice Shop.

        Returns:
          ManagerResult: Resultado de la operación.
        """
        try:
            self.js_manager.cleanup()
        except AttributeError as e:
            return ManagerResult.failure(
                message="Error at restarting Juice Shop Manager", error=str(e)
            )

        self.js_manager = JuiceShopManager(JuiceShopConfig())
        return ManagerResult.ok(message="Juice Shop Manager restarted")

    def set_managers(self, rtb: RootTheBoxManager, js: JuiceShopManager):
        """
        Reemplaza las instancias actuales de los managers por otras.

        Args:
            rtb (RootTheBoxManager): Nueva instancia de RootTheBoxManager.
            js (JuiceShopManager): Nueva instancia de JuiceShopManager.
        """
        with self.__manager_lock:
            self.rtb_manager = rtb
            self.js_manager = js

    def start(self) -> None:
        """
        Arranca el motor y acepta conexiones entrantes indefinidamente.
        """
        print(f"🔌 JuiceBoxEngine started and listening on port: {self.socket_path}")
        self.monitor.info(
            f"JuiceBoxEngine started and listening on port: {self.socket_path}"
        )
        self.redis_manager.start()  # Arranca el servicio de redis
        self.monitor.start_container_monitoring()  # Arranca la monitorización de contenedores
        while True:
            conn, _ = self.server_socket.accept()
            conn.settimeout(10)
            threading.Thread(
                target=self.__handle_client, args=(conn,), daemon=True
            ).start()

    def stop(self) -> ManagerResult:
        """
        Detiene el motor y cierra el socket.

        Returns:
          ManagerResult: Resultado de la operación.
        """
        try:
            self.server_socket.close()
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
            return ManagerResult.ok(message="Engine stopped and socket removed")
        except Exception as e:
            return ManagerResult.failure(message="Error stopping server", error=str(e))

    def __handle_rtb_command(self, command: str) -> Response:
        """
        Ejecuta un comando específico para Root The Box.

        Args:
        command (str): Comando recibido

        Returns:
            Response: Respuesta serializada en formato JSON
        """
        # Lee el manager dentro del lock para asegurar coherencia.
        with self.__manager_lock:
            __manager = self.rtb_manager
        __res: ManagerResult
        __message: str
        match command:
            case "__START__":
                __res = __manager.start()
                __message = __res.message
                if __res.success:
                    self.monitor.info(__message)
                    return Response.ok(__message)
                if __res.error:
                    __message += f": {__res.error}"
                self.monitor.error(__message)
                return Response.error(
                    message="Error when trying to start Root The Box containers."
                )
            case "__RESTART__":
                __res = self.__rtb_restart()
                __message = __res.message
                if __res.success:
                    self.monitor.info(__message)
                    return Response.ok(__message)

                if __res.error:
                    __message += f": {__res.error}"
                self.monitor.error(__message)
                return Response.error(
                    message="Error when trying to restart Root The Box containers."
                )
            case "__STOP__":
                __res = __manager.stop()
                __message = __res.message
                if __res.success:
                    return Response.ok(message=__message)
                if __res.error:
                    __message += f": {__res.error}"
                self.monitor.error(message=__message)
                return Response.error(
                    message="Error when trying to stop Root The Box containers."
                )
            case "__STATUS__":
                __res = __manager.status()
                if self.rtb_manager and __res.success and __res.data:
                    return Response.ok(
                        message="Root The Box Manager is active.", data=__res.data
                    )
                return Response.error(
                    message="Error when trying to retrieve Root The Box Manager Status.",
                    data={},
                )
                # self.redis_manager.publish_to_admin(
                #     RedisPayload.from_dict(__resp.data["containers"][0]["data"]),
                # )
                # self.redis_manager.publish_to_admin(
                #     RedisPayload.from_dict(__resp.data["containers"][1]["data"]),
                # )
            case "__CONFIG__":
                __res = __manager.show_config()
                if __res.success and __res.data:
                    return Response.ok(message=__res.message, data=__res.data)
                return Response.error(
                    message="Error when trying to retrieve Root The Box Manager config."
                )
            case _:
                __message = "Root The Box command error"
                self.monitor.error(message=__message + f": {command}")
                return Response.error(message=__message)

    def __handle_js_command(self, command: str, args: dict[str, str | int]) -> Response:
        """
        Ejecuta un comando específico para Juice Shop.

        Args:
          command (str): Comando recibido
          args (dict[str, str | int]): Argumentos adicionales como puerto o nombre

        Returns:
            Response: Respuesta serializada en formato JSON
        """
        # Lee el manager dentro del lock para asegurar coherencia.
        with self.__manager_lock:
            __manager = self.js_manager
        __resp: Response = Response.error(message="Juice Shop command error")
        __res: ManagerResult
        match command:
            case "__START_CONTAINER__":
                __res = __manager.start()
                if __res.success:
                    __resp = Response.ok(message=__res.message)
                else:
                    __resp = Response.error(
                        message="Error when trying to start Juice Shop container."
                    )
            case "__RESTART__":
                __res = self.__js_restart()
                if __res.success:
                    __resp = Response.ok(message=__res.message)
                else:
                    __resp = Response.error(
                        message="Error when trying to restart Juice Shop containers."
                    )
            case "__STOP_CONTAINER__":
                __res = __manager.stop_container(args["port"])
                if __res.success:
                    __resp = Response.ok(message=__res.message)
                else:
                    __resp = Response.error(
                        message="Error when trying to stop Juice Shop container."
                    )
            case "__STOP__":
                __res = __manager.stop()
                if __res.success:
                    __resp = Response.ok(message=__res.message)
                else:
                    __resp = Response.error(
                        message="Error when trying to stop Juice Shop containers."
                    )
            case "__CONTAINER_STATUS__":
                argument: str | int = ""
                if args["port"]:
                    argument = args["port"]
                elif args["container"]:
                    argument = args["container"]
                __res = __manager.status(argument)
                if __res.success and __res.data:
                    __resp = Response.ok(message=__res.message, data=__res.data)
                else:
                    __resp = Response.error(
                        message="Error when trying to retrieve Juice Shop container status.",
                        data={},
                    )
            case "__CONFIG__":
                __res = __manager.show_config()
                if __res.success and __res.data:
                    __resp = Response.ok(message=__res.message, data=__res.data)
                else:
                    __resp = Response.error(
                        message="Error when trying to retrieve Juice Shop Manager config."
                    )
            case "__GENERATE_XML__":
                __res = __manager.generate_rtb_config()
                if __res.success and __res.data:
                    __resp = Response.ok(message=__res.message, data=__res.data)
                else:
                    __resp = Response.error(
                        message="Error when trying to generate Root The Box XML file."
                    )
            case "__STATUS__":
                if self.js_manager:
                    __resp = Response.ok(message="Juice Shop Manager is active.")
                else:
                    __resp = Response.error(
                        message="Error when trying to retrieve Juice Shop Manager Status."
                    )
        # Retorno
        return __resp

    def dispatch_command(self, raw_data: str) -> Response:
        """
        Parsea el comando recibido y lo redirige al manager correspondiente.

        Args:
            raw_data (str): Cadena JSON enviada por el cliente

        Returns:
            Response: Respuesta serializada en formato JSON
        """
        __resp: Response = Response.error(message="Program not supported by engine")
        try:
            payload = json.loads(raw_data)
            prog = payload.get("prog")
            command = payload.get("command")
            args = payload.get("args", {})

            if prog not in COMMANDS:
                __resp = Response.error(message="Program not recognized")
            elif command not in COMMANDS[prog]:
                __resp = Response.error(message="Command not recognized by program")
            elif prog == "RTB":
                __resp = self.__handle_rtb_command(command)
            else:
                # prog == "JS"
                __resp = self.__handle_js_command(command, args)
            # Se despachan las respuestas:
        except json.JSONDecodeError:
            __resp = Response.error(message="Invalid JSON format")
        except Exception as e:
            __resp = Response.error(message=str(e))
        return __resp

    def cleanup(self) -> ManagerResult:
        """
        Limpieza general del servidor: cierra el socket, detiene contenedores y conexiones.
        Es idempotente y tolerante a errores.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        with self.__manager_lock:
            __rtb_manager = self.rtb_manager
            __js_manager = self.js_manager
            __redis_manager = self.redis_manager
            __monitor = self.monitor
            __docker_client = self.docker_client

        # Acumulamos mensajes y errores
        messages = []
        errors = []

        for name, component, action in [
            ("JuiceShopManager", __js_manager, lambda: component.cleanup()),
            ("RootTheBoxManager", __rtb_manager, lambda: component.cleanup()),
            ("RedisManager", __redis_manager, lambda: component.cleanup()),
            ("Monitor", __monitor, lambda: component.stop_container_monitoring()),
            ("DockerClient", __docker_client, lambda: component.close()),
        ]:
            if component is not None:
                _resp: Response
                try:
                    _resp = action()
                    if isinstance(_resp, Response) and _resp.status == Status.OK:
                        msg: str = f"{name} cleaned up successfully: {_resp.message}\n"
                        messages.append(
                            f"{name} cleaned up successfully: {_resp.message}\n"
                        )
                        if __monitor:
                            __monitor.info(msg)
                    elif component is __docker_client:
                        msg: str = (
                            f"{name} cleaned up successfully: Docker connection is closed\n"
                        )
                        messages.append(
                            f"{name} cleaned up successfully: Docker connection is closed\n"
                        )
                        if __monitor:
                            __monitor.info(msg)
                    else:
                        error_msg = f"{name} cleanup failed: {_resp.message}\n"
                        errors.append(error_msg)
                        if __monitor:
                            __monitor.error(error_msg)
                except Exception as e:
                    error_msg = f"{name} cleanup failed."
                    errors.append(error_msg)
                    if __monitor:
                        __monitor.error(error_msg)

        # Detiene el motor
        try:
            stop_response: ManagerResult = self.stop()
            if stop_response.success:
                messages.append(f"Server stopped: {stop_response.message}")
            else:
                msg = f"Server stopped, but socket cleanup failed: {stop_response.message}"
                errors.append(msg)
                if __monitor:
                    __monitor.error(msg)
        except Exception as e:
            msg = f"Error stopping server: {e}"
            errors.append(msg)
            if __monitor:
                __monitor.error(msg)

        # Resultado final
        if errors:
            return ManagerResult.failure(
                message="Cleanup completed with errors", error=str(errors)
            )
        else:
            if __monitor:
                __monitor.info("Server cleaned up successfully.")
            return ManagerResult.ok("Cleanup successful", data={"messages": messages})
