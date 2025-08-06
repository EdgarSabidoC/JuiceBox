import logging, time, threading, docker, docker.errors, redis, json
from scripts.utils.logger import Logger
from scripts.redisManager import RedisManager
from JuiceBoxEngine.models.schemas import Response, Status, RedisResponse
from docker.models.containers import Container
from scripts.utils.validator import validate_container
from docker import DockerClient


class Monitor:
    """
    Clase para monitorear eventos en JuiceBoxEngine, incluyendo:

    - Gestión de logs mediante un logger personalizado.
    - Monitorización de contenedores Docker en segundo plano.
    - Publicación de eventos a través de Redis en dos canales:
      uno para administradores y otro para clientes.
    """

    def __init__(
        # Logger:
        self,
        name: str = "JuiceBoxEngine",
        use_journal: bool = True,
        level: int = logging.DEBUG,
        # Monitor:
        monitor_containers: bool = True,
        container_poll_interval: float = 5.0,
        # Lista de contenedores de RootTheBox y JuiceShop:
        rtb_containers: list[str] | None = None,
        js_containers: list[str] | None = None,
        # Redis:
        redis: RedisManager | None = None,
    ):
        """
        Inicializa el monitor del sistema.

        Args:
            name (str): Nombre del logger.
            use_journal (bool): Si usar journald para logging.
            level (int): Nivel de logging.
            monitor_containers (bool): Si inicia la vigilancia de contenedores.
            container_poll_interval (float): Intervalo entre chequeos de contenedores.
            redis_host (str): Dirección de Redis.
            redis_port (int): Puerto de Redis.
            redis_db (int): Base de datos Redis a usar.
            redis_password (str): Contraseña para Redis.
            admin_channel (str): Canal Redis para mensajes administrativos.
            client_channel (str): Canal Redis para mensajes de clientes.
            rtb_containers (list[str]): Nombres de contenedores de RootTheBox.
            js_containers (list[str]): Nombres de contenedores de JuiceShop.
        """
        # Logger base
        self.logger = Logger(
            name=name,
            to_journal=use_journal,
            identifier=name,
            level=level,
        ).get()

        # Cliente Docker para vigilancia
        self.__docker_client: DockerClient = docker.from_env()

        # Control del hilo de monitorización Docker
        self._monitoring = False
        self._monitor_thread = None
        self._interval = container_poll_interval

        # Diccionario: nombre_de_contenedor → último estado
        self.__last_statuses: dict[str, str] = {}

        # Contenedores
        self.__set_containers(rtb_containers, js_containers)

        if monitor_containers:
            self.start_container_monitoring()

        # Cliente Redis
        if redis:
            self.__redis: RedisManager = redis

    # ─── Métodos de Logging ─────────────────────────────────────────────────────

    def info(self, message: str):
        """Registra un mensaje de tipo INFO."""
        self.logger.info(message)

    def warning(self, message: str):
        """Registra un mensaje de tipo WARNING."""
        self.logger.warning(message)

    def error(self, message: str):
        """Registra un mensaje de tipo ERROR."""
        self.logger.error(message)

    def command_received(self, prog: str, command: str, address: str):
        """Registra un comando recibido desde una dirección."""
        self.logger.info(f"[{address}] {prog} -> {command}")

    def client_connected(self, address=None):
        """Registra una nueva conexión de cliente."""
        suffix = f"from [{address}]" if address else "[]"
        text = f"New client connected {suffix}"
        self.logger.info(text)

    def client_error(self, err: Exception):
        """Registra un error ocurrido con un cliente."""
        text = f"Client error: {err}"
        self.logger.warning(text)

    # ─── Métodos de monitorización de Docker ───────────────────────────────────

    def __set_containers(self, rtb: list[str] | None, js: list[str] | None):
        """
        Inicializa las listas de contenedores a monitorear.

        Args:
            rtb (list[str] | None): Contenedores de RootTheBox.
            js (list[str] | None): Contenedores de JuiceShop.
        """
        self.rtb_containers = rtb if rtb else []
        self.js_containers = js if js else []

    def __container_monitor_loop(self):
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

    def __process_all_containers(self):
        """
        Procesa el estado de todos los contenedores conocidos.
        """
        containers = self.rtb_containers + self.js_containers
        for container_name in containers:
            if not validate_container(self.__docker_client, container_name):
                # Si no existe el contenedor, continúa
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

    def __process_single_container(self, container: Container):
        """
        Procesa un único contenedor: detecta cambios de estado y publica eventos.

        Args:
            container: Objeto del contenedor Docker.
        """
        current_status = container.status
        container_name = container.name or ""
        last_status = self.__last_statuses.get(container_name)

        # Si el estado no ha cambiado, no se hace nada
        if last_status == current_status:
            return

        # Publicación en Redis
        self.__redis.publish_to_admin(container)  # Canal administrativo
        if container_name in self.js_containers:
            self.__redis.publish_to_client(container)  # Canal de clientes

        # Se actualiza el último estado registrado
        self.__last_statuses[container_name] = current_status

    def start_container_monitoring(self):
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

    def stop_container_monitoring(self):
        """
        Detiene el monitoreo de contenedores Docker.
        """
        if not self._monitoring:
            return
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=self._interval + 1)
        self.info("Docker container monitoring stopped.")
