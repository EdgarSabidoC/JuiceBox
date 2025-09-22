import logging, time, asyncio, threading, docker, docker.errors
from ..utils import Logger
from .redisManager import RedisManager
from Models import ManagerResult, ManagerResult, RedisPayload
from docker.models.containers import Container
from ..utils import validate_container
from docker import DockerClient
from ..api import JuiceBoxAPI
from datetime import datetime, timezone, timedelta


class Monitor:
    """
    Clase para monitorear eventos en Engine.

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
        name: str = "Engine",
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

        # Lista para guardar tareas activas de expiración
        self.__expiration_tasks: list[asyncio.Task] = []

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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self._monitoring:
            try:
                # Procesar todos los contenedores usando la función helper
                self.__process_all_containers(loop)

                # Limpiar tareas completadas
                self.__cleanup_finished_tasks()

                # Ejecutar tareas pendientes de expiración
                if self.__expiration_tasks:
                    loop.run_until_complete(
                        asyncio.gather(*self.__expiration_tasks, return_exceptions=True)
                    )

            except Exception as e:
                self.error(f"Monitor containers error: {e}")

            time.sleep(self._interval)

        loop.close()

    def __process_all_containers(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Procesa todos los contenedores conocidos:
          - Actualiza su estado.
          - Expira automáticamente los contenedores JS que superen su lifespan.
          - Guarda las tareas de expiración en self.__expiration_tasks.

        Args:
            loop: Loop de asyncio para crear tareas.
        """
        containers = self.rtb_containers + self.js_containers
        for container_name in containers:
            container = self.__get_container(container_name)
            if not container:
                # Si el contenedor no existe
                if self.__last_statuses.get(container_name) != "not_found":
                    self.change_status(container_name, "not_found")
                    self.warning(f"Container '{container_name}' does not exist.")
                continue

            labels = container.labels or {}

            # Solo contenedores JuiceShop con label program=JS se procesan para expirar
            if labels.get("program") == "JS" and self.__is_container_expired(container):
                # Se crea una tarea asyncio para expirar
                task = loop.create_task(self.__expire_container(container))
                self.__expiration_tasks.append(task)
                continue

            # Procesar estado normal (para RTB o JS que no expiran)
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

    def __is_container_expired(self, container: Container) -> bool:
        """
        Verifica si el contenedor ha superado su tiempo de vida.

        Args:
            container (Container): Contenedor Docker.

        Returns:
            bool: True si ha expirado, False si aún es válido.
        """
        created_at_str = container.attrs.get("Created")
        if not created_at_str:
            return False  # No se puede calcular, se considera activo

        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        lifespan_minutes = int(
            container.labels.get("lifespan", 180)
        )  # predeterminado 180 min
        expire_at = created_at + timedelta(minutes=lifespan_minutes)

        return datetime.now(timezone.utc) > expire_at

    async def __expire_container(self, container: Container) -> None:
        """
        Expira un contenedor de Juice Shop usando la API de JuiceBox Engine y registra el evento.

        Args:
            container (Container): Contenedor Docker.
        """
        try:
            ports_info = container.attrs["NetworkSettings"]["Ports"]
            host_port = None
            for _, mappings in ports_info.items():
                if mappings and isinstance(mappings, list):
                    host_port = mappings[0]["HostPort"]
                    break

            if not host_port:
                raise ValueError(
                    f"No se pudo obtener el puerto del contenedor {container.name}"
                )

            await JuiceBoxAPI.stop_js_container(int(host_port))
            self.info(f"Expired container {container.name} on port {host_port}")

        except Exception as e:
            self.error(f"Failed to expire container {container.name}: {e}")

    def __cleanup_finished_tasks(self) -> None:
        """
        Elimina tareas expiradas completadas de la lista __expiration_tasks.
        """
        self.__expiration_tasks = [t for t in self.__expiration_tasks if not t.done()]

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
