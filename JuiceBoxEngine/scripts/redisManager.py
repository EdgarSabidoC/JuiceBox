import redis, subprocess, os
from JuiceBoxEngine.models.schemas import BaseManager
from importlib.resources import path
from scripts.utils.validator import validate_container
from JuiceBoxEngine.models.schemas import RedisResponse, ManagerResult
from docker.models.containers import Container
from docker.client import DockerClient
from docker.errors import APIError


class JuiceBoxChannels:
    ADMIN = "admin_channel"
    CLIENT = "client_channel"


class RedisManager(BaseManager):

    def __init__(
        self,
        # Redis:
        container_name: str = "juicebox-redis",
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: str = "C5L48",
        compose_file: str | None = None,
        # Docker:
        docker_client: DockerClient | None = None,
    ) -> None:
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
        self.__redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
        )

    def __create(self) -> ManagerResult:
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
                # Se obtiene el contenedor
                self.__container: Container = self.__docker_client.containers.get(
                    self.container_name
                )
            return ManagerResult(
                success=True, message="Redis container created and now is running!"
            )
        except subprocess.CalledProcessError as e:
            return ManagerResult(
                success=False,
                message="Error creating Redis container",
                error=str(e.stdout) + ". " + str(e.stderr),
            )

    def start(self) -> ManagerResult:
        try:
            # Se valida si existe el contenedor
            if validate_container(self.__docker_client, self.container_name):
                # Se obtiene el contenedor si existe
                container: Container = self.__docker_client.containers.get(
                    self.container_name
                )
                self.__container: Container = container
                if container.status == "running":
                    return ManagerResult(
                        success=True, message="Redis container is already running!"
                    )
                container.start()
                if container.status == "running":
                    return ManagerResult(
                        success=True, message="Redis container is running!"
                    )
                return ManagerResult(
                    success=False,
                    message="Redis container could not run",
                    error=f"Container status is {container.status}",
                )
            # Si el contenedor no existe, se crea:
            return self.__create()
        except APIError as e:
            return ManagerResult(
                success=False, message="Redis container could not run", error=str(e)
            )

    def stop(self) -> ManagerResult:
        try:
            # Mata o destruye el contenedor de Redis
            self.__container.stop()
            self.__container.remove()
            return ManagerResult(
                success=True,
                message="Redis container has been stopped and removed from system!",
                data={"container": self.container_name, "status": "removed"},
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                message=f"Redis container couldn't be stopped or removed!",
                error=str(e),
                data={
                    "container": self.container_name,
                    "status": self.__container.status,
                },
            )

    def publish(self, channel: str, payload: RedisResponse) -> ManagerResult:
        """
        Publica un mensaje en un canal Redis.

        Args:
            channel (str): Nombre del canal.
            payload (RedisResponse): Mensaje a publicar.
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

    def publish_to_admin(self, payload: RedisResponse) -> ManagerResult:
        """
        Publica el estatus de un contenedor en el canal ADMIN de Redis.

        Args:
            response (Response): Mensaje a publicar.
        """
        return self.publish(JuiceBoxChannels.ADMIN, payload)

    def publish_to_client(self, payload: RedisResponse) -> ManagerResult:
        """
        Publica el estatus de un contenedor en el canal CLIENT de Redis.

        Args:
            container (Container): Mensaje a publicar.
        """
        return self.publish(JuiceBoxChannels.CLIENT, payload)

    def close(self) -> ManagerResult:
        """
        Cierra la conexión al cliente Redis.
        """
        try:
            self.__redis.close()
        except Exception:
            return ManagerResult(
                success=False, message="Redis client could not be closed!"
            )
        return ManagerResult(success=True, message="Redis client closed successfully!")

    def cleanup(self) -> ManagerResult:
        """
        Destruye el contenedor y libera los recursos.
        """
        try:
            __res: ManagerResult = self.close()
            if not __res.success:
                return __res
            __res = self.stop()
            if not __res.success:
                return __res
            return ManagerResult(success=True, message="Redis cleanup successful!")
        except Exception as e:
            return ManagerResult(
                success=False, message=f"Redis could not be cleaned up", error=str(e)
            )
