import redis, subprocess, os
from importlib.resources import path
from ..utils import validate_container
from Models import BaseManager, RedisPayload, ManagerResult
from docker.models.containers import Container
from docker.client import DockerClient
from docker.errors import APIError
from importlib.resources import files
from ..utils import validate_container
from pathlib import Path


class JuiceBoxChannels:
    ADMIN = "admin_channel"
    CLIENT = "client_channel"


class RedisManager(BaseManager):
    """
    Clase para gestionar un servidor Redis mediante Docker. Utiliza un archivo
    docker-compose para crear, iniciar y detener el contenedor de Redis.
    Además, permite publicar mensajes en canales Redis.
    ## Características
    - Gestión del contenedor Redis mediante Docker.
    - Publicación de mensajes en canales Redis.
    - Manejo de errores y resultados mediante ManagerResult.
    - Uso de un cliente Docker opcional.
    - Uso de un cliente Redis para la comunicación.
    ## Operaciones
    - **start():** Inicia el contenedor Redis.
    - **stop():** Detiene y elimina el contenedor Redis.
    - **publish(channel, payload):** Publica un mensaje en un canal Redis.
    - **publish_to_admin(payload):** Publica un mensaje en el canal ADMIN.
    - **publish_to_client(payload):** Publica un mensaje en el canal CLIENT.
    - **close():** Cierra la conexión al cliente Redis.
    - **cleanup():** Detiene y elimina el contenedor Redis y cierra la conexión.
    """

    def __init__(
        self,
        # Redis:
        container_name: str = "juicebox-redis",
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        compose_file: str | None = None,
        # Docker:
        docker_client: DockerClient | None = None,
    ) -> None:
        """
        Inicializa el gestor de Redis.
        Args:
            container_name (str): Nombre del contenedor Docker de Redis.
            redis_host (str): Dirección del servidor Redis.
            redis_port (int): Puerto del servidor Redis.
            redis_db (int): Base de datos Redis a usar.
            redis_password (str): Contraseña para el servidor Redis.
            compose_file (str | None): Ruta al archivo docker-compose para Redis.
            docker_client (DockerClient | None): Cliente Docker opcional.
        Raises:
            TypeError: Si docker_client no es una instancia de DockerClient.
        """
        # Si no se especifica la ruta, se carga desde el paquete configs
        if compose_file:
            self.__compose_file = compose_file
        else:
            with path("JuiceBoxEngine.configs", "redis-docker-compose.yml") as p:
                self.__compose_file = str(p)
        self.container_name = container_name

        # Cliente Docker
        if docker_client:
            self.__docker_client: DockerClient = docker_client

        # Cliente Redis
        redis_password: str | None = self.__get_password(
            "JuiceBoxEngine.configs", "redis.conf"
        )
        self.__set_password(redis_password)
        self.__redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
        )

    def __get_password(self, package: str, resource_name: str) -> str | None:
        """
        Lee `resource_name` dentro del paquete `package`
        y extrae el valor de la línea que empieza con `requirepass`.
        """
        recurso = files(package).joinpath(resource_name)
        with recurso.open("r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea.startswith("requirepass"):
                    return linea.split(maxsplit=1)[1]
        return None

    def __set_password(self, password: str | None) -> None:
        """
        Escribe el password en el archivo .env que está en la raíz de JuiceBox.
        """
        if not password:
            return

        # Ruta al archivo .env (dos niveles arriba desde redisManager.py)
        env_path = Path(__file__).resolve().parents[2] / ".env"

        # Leer líneas existentes si el archivo existe
        lines = []
        if env_path.exists():
            with env_path.open("r", encoding="utf-8") as f:
                lines = f.readlines()

        # Reemplaza o agrega REDIS_PASSWORD
        found = False
        for i, line in enumerate(lines):
            if line.startswith("REDIS_PASSWORD="):
                lines[i] = f"REDIS_PASSWORD={password}\n"
                found = True
                break

        if not found:
            lines.append(f"REDIS_PASSWORD={password}\n")

        # Escribe el archivo actualizado
        with env_path.open("w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"[INFO] REDIS_PASSWORD escrito en {env_path}")

    def __create(self) -> ManagerResult:
        """
        Crea el contenedor Redis usando docker-compose.
        Returns:
            ManagerResult: Resultado de la operación.
        Raises:
            subprocess.CalledProcessError: Si ocurre un error al ejecutar docker-compose.
        """
        try:
            # Si no existe el contenedor, se crea:
            base_dir = os.path.dirname(self.__compose_file)
            cmd = ["docker", "compose", "-f", self.__compose_file, "up", "-d"]
            subprocess.run(
                cmd,
                cwd=base_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            if validate_container(self.__docker_client, self.container_name):
                return ManagerResult.ok(
                    message="Redis container created and now is running!"
                )
            else:
                return ManagerResult.failure(
                    message="Redis container couldn't be created."
                )
        except subprocess.CalledProcessError as e:
            return ManagerResult(
                success=False,
                message="Error creating Redis container",
                error=str(e.stdout) + ". " + str(e.stderr),
            )

    def start(self) -> ManagerResult:
        """
        Inicia el contenedor Redis. Si el contenedor ya existe, intenta iniciarlo. Si no existe, lo crea.
        Returns:
            ManagerResult: Resultado de la operación.
        Raises:
            APIError: Si ocurre un error al interactuar con la API de Docker.
        """
        try:
            # Se valida si existe el contenedor
            if validate_container(self.__docker_client, self.container_name):
                # Se obtiene el contenedor si existe
                container: Container = self.__docker_client.containers.get(
                    self.container_name
                )
                if container.status == "running":
                    return ManagerResult.ok(
                        message="Redis container is already running!"
                    )
                container.start()
                if container.status == "running":
                    return ManagerResult.ok(message="Redis container is running!")
                return ManagerResult(
                    success=False,
                    message="Redis container could not run",
                    error=f"Container status is {container.status}",
                )
            # Si el contenedor no existe, se crea:
            return self.__create()
        except APIError as e:
            return ManagerResult.failure(
                message="Redis container could not run", error=str(e)
            )

    def stop(self) -> ManagerResult:
        """
        Detiene y elimina el contenedor Redis.
        Returns:
            ManagerResult: Resultado de la operación.
        Raises:
            Exception: Si ocurre un error al detener o eliminar el contenedor.
        """
        try:
            if validate_container(self.__docker_client, self.container_name):
                # Se obtiene el contenedor:
                container: Container = self.__docker_client.containers.get(
                    self.container_name
                )
                container.stop()
                container.remove()
                return ManagerResult(
                    success=True,
                    message="Redis container has been stopped and removed from system!",
                    data={"container": self.container_name, "status": "removed"},
                )
            return ManagerResult(
                success=True,
                message="No Redis container found to be stopped.",
                data={"container": self.container_name, "status": "removed"},
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                message="Redis container couldn't be stopped or removed!",
                error=str(e),
                data={
                    "container": self.container_name,
                    "status": "error",
                },
            )

    def publish(self, channel: str, payload: RedisPayload) -> ManagerResult:
        """
        Publica un mensaje en un canal Redis.

        Args:
            channel (str): Nombre del canal.
            payload (RedisPayload): Mensaje a publicar.
        Returns:
            ManagerResult: Resultado de la operación.
        Raises:
            Exception: Si ocurre un error al publicar el mensaje.
        """
        try:
            message: str = payload.to_json()
            self.__redis.publish(channel, message)
            return ManagerResult(
                success=True,
                message="Message published successfully!",
                data={"channel": channel},
            )
        except Exception as e:
            return ManagerResult(
                success=True,
                message="Message could not be published!",
                error=str(e),
                data={"channel": channel},
            )

    def publish_to_admin(self, payload: RedisPayload) -> ManagerResult:
        """
        Publica el estatus de un contenedor en el canal ADMIN de Redis.

        Args:
            payload (RedisPayload): Mensaje a publicar.
        Returns:
            ManagerResult: Resultado de la operación.
        Raises:
            Exception: Si ocurre un error al publicar el mensaje.
        """
        return self.publish(JuiceBoxChannels.ADMIN, payload)

    def publish_to_client(self, payload: RedisPayload) -> ManagerResult:
        """
        Publica el estatus de un contenedor en el canal CLIENT de Redis.

        Args:
            payload (RedisPayload): Mensaje a publicar.
        Returns:
            ManagerResult: Resultado de la operación.
        Raises:
            Exception: Si ocurre un error al publicar el mensaje.
        """
        return self.publish(JuiceBoxChannels.CLIENT, payload)

    def close(self) -> ManagerResult:
        """
        Cierra la conexión al cliente Redis.
        Returns:
            ManagerResult: Resultado de la operación.
        Raises:
            Exception: Si ocurre un error al cerrar la conexión.
        """
        try:
            self.__redis.close()
        except Exception:
            return ManagerResult.failure(message="Redis client could not be closed!")
        return ManagerResult.ok(message="Redis client closed successfully!")

    def cleanup(self) -> ManagerResult:
        """
        Destruye el contenedor y libera los recursos.
        Returns:
            ManagerResult: Resultado de la operación.
        Raises:
            Exception: Si ocurre un error durante la limpieza.
        """
        try:
            __res: ManagerResult = self.close()
            if not __res.success:
                return __res
            __res = self.stop()
            if not __res.success:
                return __res
            return ManagerResult.ok(message="Redis cleanup successful!")
        except Exception as e:
            return ManagerResult.failure(
                message="Redis could not be cleaned up", error=str(e)
            )
