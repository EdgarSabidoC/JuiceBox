import logging, time, threading, docker, docker.errors
from ..utils import Logger
from .redisManager import RedisManager
from Models import ManagerResult, ManagerResult, RedisPayload
from docker.models.containers import Container
from ..utils import validate_container
from docker import DockerClient


class Monitor:
    """
    Clase para monitorear eventos en JuiceBoxEngine.

    ## Características
    - Gestión de logs mediante un logger personalizado.
    - Monitorización de contenedores Docker en segundo plano.
    - Publicación de eventos a través de Redis en dos canales:
      uno para administradores y otro para clientes.

    ## Operaciones
    - Iniciar y detener la monitorización de contenedores Docker.
    - Registrar eventos de conexión y comandos de clientes.
    - Detectar y notificar cambios en el estado de contenedores Docker.
    """

    def __init__(
        # Logger:
        self,
        name: str = "JuiceBoxEngine",
        use_journal: bool = True,
        level: int = logging.DEBUG,
        # Docker:
        docker_client: DockerClient | None = None,
        # Monitor:
        container_poll_interval: float = 5.0,
        # Lista de contenedores de RootTheBox y JuiceShop:
        rtb_containers: list[str] | None = None,
        js_containers: list[str] | None = None,
        # Redis:
        redis_manager: RedisManager | None = None,
    ):
        """
        Inicializa el monitor del sistema.

        Args:
            name (str): Nombre del logger.
            use_journal (bool): Si usar journald para logging.
            level (int): Nivel de logging.
            container_poll_interval (float): Intervalo entre chequeos de contenedores.
            redis_host (str): Dirección de Redis.
            redis_port (int): Puerto de Redis.
            redis_db (int): Base de datos Redis a usar.
            redis_password (str): Contraseña para Redis.
            admin_channel (str): Canal Redis para mensajes administrativos.
            client_channel (str): Canal Redis para mensajes de clientes.
            rtb_containers (list[str]): Nombres de contenedores de RootTheBox.
            js_containers (list[str]): Nombres de contenedores de JuiceShop.
            docker_client (DockerClient | None): Cliente Docker opcional.
            redis_manager (RedisManager | None): Gestor Redis opcional.
        Raises:
            TypeError: Si redis_manager no es una instancia de RedisManager.
        """
        # Logger base
        self.logger = Logger(
            name=name,
            to_journal=use_journal,
            identifier=name,
            level=level,
        ).get()

        # Cliente Docker
        if docker_client:
            self.__docker_client: DockerClient = docker_client
        else:
            self.__docker_client: DockerClient = docker.from_env()

        # Control del hilo de monitorización Docker
        self._monitoring = False
        self._monitor_thread = None
        self._interval = container_poll_interval

        # Diccionario: nombre_de_contenedor → último estado
        self.__last_statuses: dict[str, str] = {}

        # Contenedores
        self.set_containers(rtb_containers, js_containers)

        # Cliente Redis
        if redis_manager:
            self.__redis: RedisManager = redis_manager
        else:
            self.__redis: RedisManager = RedisManager()

    # ─── Métodos de Logging ─────────────────────────────────────────────────────

    def info(self, message: str) -> None:
        """
        Registra un mensaje de tipo INFO.

        Args:
            message (str): Mensaje a registrar.
        """
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """
        Registra un mensaje de tipo WARNING.

        Args:
            message (str): Mensaje a registrar.
        """
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """
        Registra un mensaje de tipo ERROR.

        Args:
            message (str): Mensaje a registrar.
        """
        self.logger.error(message)

    def command_received(self, prog: str, command: str, address: str) -> None:
        """
        Registra un comando recibido desde una dirección.

        Args:
            prog (str): Programa que envió el comando.
            command (str): Comando recibido.
            address (str): Dirección del cliente que envió el comando.
        """
        self.logger.info(f"[{address}] {prog} -> {command}")

    def client_connected(self, address: str | None = None) -> None:
        """
        Registra una nueva conexión de cliente.

        Args:
            address (str | None): Dirección del cliente que se conectó.
        """
        suffix = f"from [{address}]" if address else "[]"
        text = f"New client connected {suffix}"
        self.logger.info(text)

    def client_error(self, err: Exception) -> None:
        """
        Registra un error ocurrido con un cliente.

        Args:
            err (Exception): Error del cliente.

        """
        text = f"Client error: {err}"
        self.logger.warning(text)

    # ─── Métodos de monitorización de Docker ───────────────────────────────────

    def set_containers(self, rtb: list[str] | None, js: list[str] | None) -> None:
        """
        Inicializa las listas de contenedores a monitorear.

        Args:
            rtb (list[str] | None): Contenedores de RootTheBox.
            js (list[str] | None): Contenedores de JuiceShop.
        """
        self.rtb_containers = rtb if rtb else []
        self.js_containers = js if js else []

    def __container_monitor_loop(self) -> None:
        """
        Bucle de vigilancia de contenedores. Ejecutado en segundo plano.
        """
        while self._monitoring:
            containers = self.rtb_containers + self.js_containers

            if not containers:
                return  # No hay contenedores a monitorear

            try:
                self.__process_all_containers()
            except Exception as e:
                self.error(f"Monitor containers error: {e}")

            time.sleep(self._interval)

    def __process_all_containers(self) -> None:
        """
        Procesa el estado de todos los contenedores conocidos.
        """
        containers = self.rtb_containers + self.js_containers
        for container_name in containers:
            if not validate_container(self.__docker_client, container_name):
                if self.__last_statuses.get(container_name) != "not_found":
                    self.change_status(
                        container_name=container_name, current_status="not_found"
                    )
                    self.warning(f"Container '{container_name}' does not exist.")
                continue
            container = self.__get_container(container_name)  # Se obtiene el contenedor
            if not container:
                continue
            self.__process_single_container(container)

    def __get_container(self, container_name: str) -> Container | None:
        """
        Obtiene un objeto `Container` de Docker por nombre.

        Args:
            container_name (str): Nombre del contenedor.

        Returns:
            docker.models.containers.Container | None
        """
        try:
            return self.__docker_client.containers.get(container_name)
        except docker.errors.NotFound:
            return None

    def __process_single_container(self, container: Container) -> None:
        """
        Procesa un único contenedor: detecta cambios de estado y publica eventos.

        Args:
            container: Objeto del contenedor Docker.
        """
        current_status = container.status
        container_name = container.name or ""
        self.change_status(container_name, current_status)

    def change_status(self, container_name: str, current_status: str) -> None:
        """
        Cambia el estado/status de un único contenedor.

        Args:
            container_name: Nombre del contenedor Docker.
            current_status: Nuevo estado del contenedor.
        """
        last_status = self.__last_statuses.get(container_name)
        # Si el estado no ha cambiado, no se hace nada
        if last_status == current_status:
            return

        # Se actualiza el último estado registrado
        self.__last_statuses[container_name] = current_status

        self.info(
            f"--> Container '{container_name}' status changed: {current_status} <--"
        )

        container: dict[str, str] = {
            "container": container_name,
            "status": current_status,
        }

        # Publicación en Redis
        self.__redis.publish_to_admin(
            RedisPayload.from_dict(container)
        )  # Canal administrativo
        if container_name in self.js_containers:
            self.__redis.publish_to_client(
                RedisPayload.from_dict(container)
            )  # Canal de clientes

    def start_container_monitoring(self) -> None:
        """
        Inicia el hilo de monitoreo de contenedores Docker.
        """
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self.__container_monitor_loop, daemon=True
        )
        self._monitor_thread.start()
        self.info("Docker container monitoring started...")

    def stop_container_monitoring(self) -> ManagerResult:
        """
        Detiene el monitoreo de contenedores Docker.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        try:
            if not self._monitoring:
                return ManagerResult.ok(message="Monitor is not running")
            self._monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=self._interval + 1)
            self.info("Docker container monitoring stopped.")
            return ManagerResult.ok(message="Docker container monitoring stopped")
        except Exception as e:
            return ManagerResult.failure(
                message="Error stopping Docker container monitoring",
                error=str(e),
            )
