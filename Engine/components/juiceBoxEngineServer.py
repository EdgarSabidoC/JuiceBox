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
    Response,
    Status,
    RedisPayload,
    ManagerResult,
)
from docker import DockerClient
from dotenv import dotenv_values
from collections.abc import Callable
from typing import Any


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
        "__START__",
        "__STOP_CONTAINER__",
        "__CONTAINER_STATUS__",
        "__STATUS__",
        "__STOP__",
        "__SET_CONFIG__",
        "__GENERATE_XML__",
        "__PORTS_RANGE__",
    ],
}


class JuiceBoxEngineServer:
    """
    Servidor del motor JuiceBox que expone una interfaz mediante sockets de Unix para
    gestionar contenedores Docker de OWASP Juice Shop y Root The Box de manera concurrente.
    """

    def __init__(
        self,
        monitor: Monitor,
        js_manager: JuiceShopManager,
        rtb_manager: RootTheBoxManager,
        docker_client: DockerClient,
        redis_manager: RedisManager,
    ) -> None:
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
        self.rtb_manager: RootTheBoxManager = rtb_manager
        self.js_manager: JuiceShopManager = js_manager
        self.redis_manager: RedisManager = redis_manager
        self.__manager_lock = threading.Lock()

        # Cola para recibir y procesar comandos de los clientes
        self.command_queue = Queue()
        Thread(target=self.__worker, daemon=True).start()

        atexit.register(self.cleanup)

    def __worker(self) -> None:
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
            if not data:
                self.monitor.warning("Empty message received from client, ignoring.")
                conn.close()
                return

            self.monitor.info(f"Data received: {data}")
            self.monitor.command_received(conn, data, conn.getpeername())
            self.command_queue.put((conn, data))
        except socket.timeout:
            self.monitor.warning("Timeout: client couldn't send data.")
            conn.close()
        except Exception as e:
            self.monitor.client_error(e)
            conn.close()

    def __process_request(self, conn, data) -> None:
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

    def __rtb_start(self, manager: RootTheBoxManager) -> Response:
        """_summary_
        Inicia los contenedores gestionados por Root The Box.

        Args:
            manager (RootTheBoxManager): Instancia del manejador de Root The Box

        Returns:
            Response: Respuesta de la operación
        """
        self.__init_manager(manager)  # Se asegura de que la config esté cargada
        __res: ManagerResult = manager.start()
        __message: str = __res.message
        if __res.success:
            self.monitor.info(
                message=f"Root The Box Manager containers have been started -> {__res.data}"
            )
            return Response.ok(__message)
        if __res.error:
            __message += f": {__res.error}"
        self.monitor.error(
            message=f"Root The Box Manager containers couldn't be started -> {__message}"
        )
        return Response.error(
            message="Error when trying to start Root The Box Manager containers."
        )

    def __rtb_restart(self) -> Response:
        """_summary_
        Reinicia la instancia del manager de Root The Box.

        Args:
            manager (RootTheBoxManager): Instancia del manejador de Root The Box

        Returns:
            Response: Respuesta de la operación
        """
        try:
            self.rtb_manager.cleanup()
            # Crea una nueva instancia y carga la configuración
            new_manager: RootTheBoxManager = RootTheBoxManager(
                RTBConfig(), docker_client=self.docker_client
            )
            self.__init_manager(new_manager)  # Se asegura de que la config esté cargada
        except AttributeError as e:
            self.monitor.error(f"Root The Box Manager couldn't be restarted -> {e}")
            return Response.error(message=f"Error restarting Root The Box Manager: {e}")

        return Response.ok("Root The Box Manager restarted")

    def __rtb_stop(self, manager: RootTheBoxManager) -> Response:
        """
        Detiene los contenedores gestionados por Root The Box.

        Args:
            manager (RootTheBoxManager): Instancia del manejador de Root The Box

        Returns:
            Response: Respuesta de la operación
        """
        __res: ManagerResult = manager.stop()
        __message: str = __res.message
        if __res.success:
            self.monitor.info(
                message=f"Root The Box Manager containers have been stopped -> {__res.data}"
            )
            return Response.ok(message=__message)
        if __res.error:
            __message += f": {__res.error}"
        self.monitor.error(
            message=f"Root The Box Manager containers couldn't be stopped -> {__message}"
        )
        return Response.error(
            message="Error when trying to stop Root The Box containers."
        )

    def __rtb_status(self, manager: RootTheBoxManager) -> Response:
        """
        Obtiene el estado actual de los contenedores gestionados por Root The Box.

        Args:
            manager (RootTheBoxManager): Manejador de Root The Box

        Returns:
            Response: Respuesta de la operación
        """
        __res: ManagerResult = manager.status()
        __response: Response = Response.error(
            message=f"Error when trying to retrieve Root The Box Manager Status -> {__res.error}",
            data={},
        )
        if __res.success and __res.data:
            # Se publica en redis
            self.redis_manager.publish_to_admin(
                RedisPayload.from_dict(__res.data["containers"][0]["data"]),
            )
            self.redis_manager.publish_to_admin(
                RedisPayload.from_dict(__res.data["containers"][1]["data"]),
            )
            # Respuesta de éxito:
            if self.rtb_manager and __res.success:
                __response = Response.ok(
                    message="Root The Box Manager is active.", data=__res.data
                )
                self.monitor.info(
                    message=f"Root The Box Manager Status retrieved -> {__res.data}"
                )
            else:
                self.monitor.error(
                    message=f"Root The Box Manager Status couldn't be retrieved -> {__res.error}"
                )
        return __response

    def __rtb_set_config(self, manager: RootTheBoxManager, config: Any) -> Response:
        """
        Cambia la configuración del manager de Root The Box y reinicia el servicio.

        Args:
            manager (RootTheBoxManager): Instancia del manejador de Root The Box
            config (Any):  Nueva configuración en formato dict

        Returns:
            Response: Respuesta de la operación
        """
        __resp: ManagerResult = manager.set_config(config)

        if __resp.success:
            # Se actualizan los contenedores del monitor:
            self.monitor.set_containers(
                rtb=self.rtb_manager.get_containers(),
                js=self.js_manager.get_containers(),
            )
            self.monitor.info(
                message=f"Root The Box Manager running config has been changed -> {__resp.data}"
            )
            __res: Response = self.__js_restart()
            if __res.status == Status.OK:
                self.monitor.info(
                    message=f"Root The Box Manager config has been changed and manager service has been restarted -> {__res.data}"
                )
                return Response.ok(message=__res.message, data=__res.data or {})
            self.monitor.error(
                message=f"Root The Box Manager config has been changed, but manager service couldn't been restarted -> {__res.error}"
            )
            return Response.error(message=__res.message, data={})
        self.monitor.error(
            message=f"Root The Box Manager config couldn't be changed -> {__resp.error}"
        )
        return Response.error(message=__resp.error or __resp.message, data={})

    def __rtb_config(self, manager: RootTheBoxManager) -> Response:
        """
        Obtiene la configuración actual del manager de Root The Box.

        Args:
            manager (RootTheBoxManager): Instancia del manejador de Root The Box

        Returns:
            Response: Respuesta de la operación
        """
        __res: ManagerResult = manager.show_config()
        if __res.success and __res.data:
            self.monitor.info(
                message=f"Root The Box Manager Config retrieved -> {__res.data}"
            )
            return Response.ok(message=__res.message, data=__res.data)
        self.monitor.error(
            message=f"Root The Box Manager Config couldn't be retrieved -> {__res.error}"
        )
        return Response.error(
            message="Error when trying to retrieve Root The Box Manager Config."
        )

    def __js_start_container(self, manager: JuiceShopManager) -> Response:
        """
        Inicia un nuevo contenedor de Juice Shop.

        Args:
            manager (JuiceShopManager): Instancia del manejador de Juice Shop

        Returns:
            Response: Respuesta de la operación
        """
        __res: ManagerResult = manager.start()
        if __res.success:
            self.monitor.info(message=f"Juice Shop container started -> {__res.data}")
            return Response.ok(message=__res.message)
        self.monitor.error(
            message=f"Juice Shop container couldn't be started -> {__res.data}"
        )
        return Response.error(
            message="Error when trying to start Juice Shop container."
        )

    def __js_restart(self) -> Response:
        """
        Reinicia la instancia del manager de la Juice Shop.

        Returns:
            Response: Respuesta de la operación
        """
        try:
            result: ManagerResult = self.js_manager.cleanup()
            if result.success:
                self.monitor.info(f"Juice Shop Manager cleaned up -> {result.data}")
            else:
                self.monitor.error(
                    f"Juice Shop Manager cleanup failed -> {result.error}"
                )
                return Response.error(message=f"Cleanup failed: {result.error}")
        except AttributeError as e:
            self.monitor.error(f"Juice Shop Manager couldn't be restarted -> {e}")
            return Response.error(message=f"Error restarting Juice Shop Manager: {e}")

        # Crea una nueva instancia y carga la configuración
        new_manager = JuiceShopManager(
            JuiceShopConfig(), docker_client=self.docker_client
        )
        self.__init_manager(new_manager)  # Se asegura de que la config esté cargada
        return Response.ok("Juice Shop Manager restarted")

    def __js_set_config(self, manager: JuiceShopManager, config: Any) -> Response:
        """
        Cambia la configuración del manager de Juice Shop y reinicia el servicio.

        Args:
            manager (JuiceShopManager): Instancia del manejador de Juice Shop
            config (Any):  Nueva configuración en formato dict
        Returns:
            Response: Respuesta de la operación
        """
        __resp: ManagerResult = manager.set_config(config)
        if __resp.success:
            # Se actualizan los contenedores del monitor:
            self.monitor.set_containers(
                rtb=self.rtb_manager.get_containers(),
                js=self.js_manager.get_containers(),
            )
            self.monitor.info(
                message=f"Juice Shop Manager running config has been changed -> {__resp.data}"
            )
            __res: Response = self.__js_restart()
            if __res.status == Status.OK:
                self.monitor.info(
                    message=f"Juice Shop Manager config has been changed and manager service has been restarted -> {__res.data}"
                )
                return Response.ok(message=__res.message, data=__res.data or {})
            self.monitor.error(
                message=f"Juice Shop Manager config has been changed, but manager service couldn't been restarted -> {__res.error}"
            )
            return Response.error(message=__res.message, data={})
        self.monitor.error(
            message=f"Juice Shop Manager config couldn't be changed -> {__resp.error}"
        )
        return Response.error(message=__resp.error or __resp.message, data={})

    def __js_stop_container(self, manager: JuiceShopManager, args: Any) -> Response:
        """
        Detiene un contenedor específico de Juice Shop.

        Args:
            manager (JuiceShopManager): Instancia del manejador de Juice Shop
            args (Any): Argumentos adicionales (puerto: int | nombre: str)

        Returns:
            Response: Respuesta de la operación
        """
        container: str | int = args.get("port") or args.get("container")
        if not container:
            return Response.error("Missing 'port' or 'container' in args")

        __res: ManagerResult = manager.stop_container(container)
        if __res.success:
            self.monitor.info(
                message=f"Juice Shop container has been stopped -> {__res.data}"
            )
            return Response.ok(message=__res.message, data=__res.data or {})
        else:
            self.monitor.error(
                message=f"Juice Shop container couldn't be stopped -> {__res.error}"
            )
            return Response.error(
                message="Error when trying to stop Juice Shop container."
            )

    def __js_stop(self, manager: JuiceShopManager) -> Response:
        """
        Detiene todos los contenedores gestionados por Juice Shop.

        Args:
            manager (JuiceShopManager): Instancia del manejador de Juice Shop
        Returns:
            Response: Respuesta de la operación
        """
        __res: ManagerResult = manager.stop()
        if __res.success:
            self.monitor.info(
                message=f"Juice Shop Manager has been stopped -> {__res.data}"
            )
            return Response.ok(message=__res.message)
        else:
            self.monitor.error(
                message=f"Juice Shop Manager couldn't be stopped -> {__res.error}"
            )
            return Response.error(
                message="Error when trying to stop Juice Shop containers."
            )

    def __js_container_status(self, manager: JuiceShopManager, args: Any) -> Response:
        """
        Obtiene el estado de un contenedor específico de Juice Shop.

        Args:
            manager (JuiceShopManager): Instancia del manejador de Juice Shop
            args (Any): Argumentos adicionales (puerto: int | nombre: str)
        Returns:
            Response: Respuesta de la operación
        """
        container: str | int = args.get("port") or args.get("container")
        if not container:
            return Response.error("Missing 'port' or 'container' in args")

        __res: ManagerResult = manager.container_status(container)
        if __res.success and __res.data:
            self.redis_manager.publish_to_admin(
                payload=RedisPayload.from_dict(__res.data)
            )
            self.redis_manager.publish_to_client(
                payload=RedisPayload.from_dict(__res.data)
            )
            self.monitor.info(
                message=f"Juice Shop container status retrieved -> {__res.data}"
            )
            return Response.ok(message=__res.message, data=__res.data)
        else:
            self.monitor.error(
                message=f"Juice Shop container status couldn't be retrieved -> {__res.error}"
            )
            return Response.error(
                message="Error when trying to retrieve Juice Shop container status.",
                data={},
            )

    def __js_config(self, manager: JuiceShopManager) -> Response:
        """
        Obtiene la configuración actual del manager de Juice Shop.

        Args:
            manager (JuiceShopManager): Instancia del manejador de Juice Shop

        Returns:
            Response: Respuesta de la operación
        """
        __res: ManagerResult = manager.show_config()
        if __res.success and __res.data:
            self.monitor.info(
                message=f"Juice Shop Manager config retrieved -> {__res.data}"
            )
            return Response.ok(message=__res.message, data=__res.data)
        else:
            self.monitor.error(
                message=f"Juice Shop Manager config couldn't be retrieved -> {__res.error}"
            )
            return Response.error(
                message="Error when trying to retrieve Juice Shop Manager config."
            )

    def __js_get_ports_range(self, manager: JuiceShopManager) -> Response:
        """
        Obtiene el rango de puertos actual del manager de Juice Shop.

        Args:
            manager (JuiceShopManager): Instancia del manejador de Juice Shop

        Returns:
            Response: Respuesta de la operación
        """
        __res: list[int] = manager.ports_range
        if __res:
            self.monitor.info(
                message=f"Juice Shop Manager ports range retrieved -> {__res}"
            )
            return Response.ok(
                message="Juice Shop Manager ports range retrieved",
                data={"ports_range": __res},
            )
        else:
            self.monitor.error(
                message="Juice Shop Manager ports range couldn't be retrieved"
            )
            return Response.error(
                message="Error when trying to retrieve Juice Shop Manager ports range."
            )

    def __js_generate_xml(self, manager: JuiceShopManager) -> Response:
        """
        Genera el archivo XML de configuración para Root The Box basado en la configuración actual de Juice Shop.

        Args:
            manager (JuiceShopManager): Instancia del manejador de Juice Shop

        Returns:
            Response: Respuesta de la operación
        """
        __res: ManagerResult = manager.generate_rtb_config()
        if __res.success:
            self.monitor.info(
                message=f"Juice Shop Manager generated XML file for RTB -> {__res.data}"
            )
            return Response.ok(message=__res.message)
        else:
            self.monitor.error(
                message=f"Juice Shop Manager couldn't generate XML file for RTB -> {__res.error}"
            )
            return Response.error(
                message="Error when trying to generate Root The Box XML file."
            )

    def __js_status(self, manager: JuiceShopManager) -> Response:
        """
        Obtiene el estado actual de los contenedores gestionados por la OWASP Juice Shop.

        Args:
            manager (JuiceShopManager): Instancia del manejador de OWASP Juice Shop

        Returns:
            Response: Respuesta de la operación
        """
        __res: ManagerResult = manager.status()
        __response: Response = Response.error(
            message=f"Error when trying to retrieve Juice Shop Manager Status -> {__res.error}",
            data={},
        )

        if __res.success and __res.data:
            # Se publica en Redis el estado de cada contenedor
            for container_entry in __res.data.get("containers", []):
                # container_entry viene de r.to_dict(), así que es un dict con "data"
                container_data = container_entry.get("data", {})
                if container_data:
                    self.redis_manager.publish_to_admin(
                        RedisPayload.from_dict(container_data)
                    )
                    self.redis_manager.publish_to_client(
                        RedisPayload.from_dict(container_data)
                    )

            # Respuesta de éxito
            __response = Response.ok(
                message="Juice Shop Manager is active.", data=__res.data
            )
            self.monitor.info(
                message=f"Juice Shop Manager Status retrieved -> {__res.data}"
            )
        else:
            self.monitor.error(
                message=f"Juice Shop Manager Status couldn't be retrieved -> {__res.error}"
            )

        return __response

    def __init_manager(self, manager: RootTheBoxManager | JuiceShopManager) -> None:
        """
        Inicializa un manager cargando su configuración y registrando los logs.

        Args:
            manager (RootTheBoxManager | JuiceShopManager):  Instancia del manager correspondiente.
        """
        name: str = "JuiceShop"
        with self.__manager_lock:
            if isinstance(manager, RootTheBoxManager):
                self.rtb_manager = manager
                name = "RTB"
            else:
                self.js_manager = manager

            # Carga la configuración si no está cargada
            if manager.config.loaded:
                self.monitor.info(f"✅ {name} config already loaded")
                return

            result = manager.config.load_config()
            if not result.success:
                self.monitor.error(f"❌ {name} config error: {result.message}")
            else:
                self.monitor.info(f"✅ {name} config loaded successfully")

    def start(self) -> None:
        """
        Arranca el motor y acepta conexiones entrantes indefinidamente.
        """
        print(f"🔌 JuiceBoxEngine started and listening on port: {self.socket_path}")
        self.monitor.info(
            f"JuiceBoxEngine started and listening on port: {self.socket_path}"
        )
        self.redis_manager.start()  # Arranca el servicio de redis
        self.__init_manager(self.js_manager)  # Carga la config de JuiceShop
        # Se cargan los contenedores al monitor:
        self.monitor.set_containers(
            rtb=self.rtb_manager.get_containers(), js=self.js_manager.get_containers()
        )
        # Publica el arranque del motor
        self.redis_manager.publish_to_admin(
            RedisPayload.from_dict(
                {
                    "container": "juicebox-engine",
                    "status": "running",
                }
            )
        )
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

    def __handle_rtb_command(
        self, command: str, args: dict[str, str | int]
    ) -> Response:
        """
        Ejecuta un comando específico para Root The Box.

        Args:
        command (str): Comando recibido

        Returns:
            Response: Respuesta serializada en formato JSON
        """
        # Lee el manager dentro del lock para asegurar coherencia.
        with self.__manager_lock:
            __manager: RootTheBoxManager = self.rtb_manager
        match command:
            case "__START__":
                return self.__rtb_start(__manager)
            case "__RESTART__":
                return self.__rtb_restart()
            case "__STOP__":
                return self.__rtb_stop(__manager)
            case "__STATUS__":
                return self.__rtb_status(__manager)
            case "__CONFIG__":
                return self.__rtb_config(__manager)
            case "__SET_CONFIG__":
                return self.__rtb_set_config(__manager, args)
            case _:
                __message: str = "Root The Box Manager command error"
                self.monitor.error(message=__message + f" -> {command}")
                return Response.error(message=__message)

    def __handle_js_command(
        self, command: str, args: dict[str, str | int | list[int]]
    ) -> Response:
        """
        Ejecuta un comando específico para Juice Shop.

        Args:
          command (str): Comando recibido
          args (dict[str, str | int | list[int]]): Argumentos adicionales como puerto o nombre

        Returns:
            Response: Respuesta serializada en formato JSON
        """
        # Lee el manager dentro del lock para asegurar coherencia.
        with self.__manager_lock:
            __manager = self.js_manager
        __resp: Response = Response.error(message="Juice Shop command error")
        __res: ManagerResult
        match command:
            case "__START__":
                return self.__js_start_container(__manager)
            case "__RESTART__":
                return self.__js_restart()
            case "__STOP_CONTAINER__":
                return self.__js_stop_container(__manager, args)
            case "__STOP__":
                return self.__js_stop(__manager)
            case "__CONTAINER_STATUS__":
                return self.__js_container_status(__manager, args)
            case "__CONFIG__":
                return self.__js_config(__manager)
            case "__GENERATE_XML__":
                return self.__js_generate_xml(__manager)
            case "__STATUS__":
                return self.__js_status(__manager)
            case "__SET_CONFIG__":
                return self.__js_set_config(__manager, args)
            case "__PORTS_RANGE__":
                return self.__js_get_ports_range(__manager)
            case _:
                __message: str = "Juice Shop Manager command error"
                self.monitor.error(message=__message + f" -> {command}")
                return Response.error(message=__message)
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
        if not raw_data:
            return Response.error(message="Empty request received")
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
                __resp = self.__handle_rtb_command(command=command, args=args)
            else:
                # prog == "JS"
                __resp = self.__handle_js_command(command=command, args=args)
            # Se despachan las respuestas:
        except json.JSONDecodeError:
            __resp = Response.error(message="Invalid JSON format")
        except Exception as e:
            __resp = Response.error(message=str(e))
        return __resp

    def __run_component_action(
        self,
        name: str,
        component: object,
        method_name: str,
        monitor: Monitor,
    ) -> tuple[list[str], list[str]]:

        # Listas de mensajes y errores:
        messages: list[str] = []
        errors: list[str] = []
        __STATIC_OK = {
            "Monitor": "Docker containers monitorization stopped!",
            "DockerClient": "Docker connection is closed",
        }

        try:
            action: Callable[[], object] = getattr(component, method_name)
        except Exception as e:
            err = f"{name} cleanup failed: missing action '{method_name}' ({e})"
            errors.append(err)
            monitor.error(err)
            return messages, errors

        try:
            result = action()
            # Caso 1: retorna ManagerResult
            if isinstance(result, ManagerResult):
                if result.success:
                    msg = f"{name} cleaned up successfully: {result.message}"
                    messages.append(msg)
                    monitor.info(msg)
                else:
                    err = f"{name} cleanup failed: {result.message} -> {result.error}"
                    errors.append(err)
                    monitor.error(err)
            # Caso 2: retorna mensaje estático (monitor/docker)
            else:
                text = __STATIC_OK.get(name, "Completed")
                msg = f"{name} cleaned up successfully: {text}"
                messages.append(msg)
                monitor.info(msg)
        except Exception as e:
            err = f"{name} cleanup failed -> {e}"
            errors.append(err)
            monitor.error(err)

        return messages, errors

    def __cleanup_components(
        self,
        js: JuiceShopManager,
        rtb: RootTheBoxManager,
        redis: RedisManager,
        monitor: Monitor,
        docker_client: DockerClient | None,
    ) -> tuple[list[str], list[str]]:
        messages: list[str] = []
        errors: list[str] = []

        specs: list[tuple[str, object | None, str]] = [
            ("JuiceShopManager", js, "cleanup"),
            ("RootTheBoxManager", rtb, "cleanup"),
            ("RedisManager", redis, "cleanup"),
            ("Monitor", monitor, "stop_container_monitoring"),
            ("DockerClient", docker_client, "close"),
        ]

        for name, component, method in specs:
            if component is None:
                continue
            msg, err = self.__run_component_action(name, component, method, monitor)
            messages.extend(msg)
            errors.extend(err)

        return messages, errors

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
        messages, errors = self.__cleanup_components(
            __js_manager, __rtb_manager, __redis_manager, __monitor, __docker_client
        )
        # Detiene el motor
        __redis_manager.publish_to_admin(
            RedisPayload.from_dict(
                {
                    "container": "juicebox-engine",
                    "status": "stopped",
                }
            )
        )
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
