import redis, subprocess, os, docker, atexit
from JuiceBoxEngine.models.schemas import Response, BaseManager
from importlib.resources import path
from scripts.utils.validator import validate_container
from JuiceBoxEngine.models.schemas import RedisResponse, Response
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

    def __create(self) -> Response:
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
            return Response.ok(message="Redis container created and now is running!")
        except subprocess.CalledProcessError as e:
            return Response.error(message=str(e.stdout) + ". " + str(e.stderr))

    def start(self) -> Response:
        try:
            # Se valida si existe el contenedor
            if validate_container(self.__docker_client, self.container_name):
                # Se obtiene el contenedor
                container: Container = self.__docker_client.containers.get(
                    self.container_name
                )
                self.__container: Container = container
                if container.status == "running":
                    return Response.ok(message="Redis container is already running!")
                container.start()
                if container.status == "running":
                    return Response.ok(message="Redis container is running!")
                return Response.error(message="Redis container could not run")
            # Si el contenedor no existe, se crea:
            return self.__create()
        except APIError as e:
            return Response.error(str(e))

    def stop(self) -> Response:
        try:
            # Mata o destruye el contenedor de Redis
            self.__container.stop()
            self.__container.remove()
            return Response.ok(
                "Redis container has been stopped and removed from system!",
                data={"container": self.container_name, "status": "removed"},
            )
        except Exception as e:
            return Response.error(
                f"Redis container couldn't be stopped or removed: {str(e)}",
                data={
                    "container": self.container_name,
                    "status": self.__container.status,
                },
            )

    def publish(self, channel: str, payload: RedisResponse) -> Response:
        """
        Publica un mensaje en un canal Redis.

        Args:
            channel (str): Nombre del canal.
            payload (RedisResponse): Mensaje a publicar.
        """
        try:
            message: str = payload.to_json()
            self.__redis.publish(channel, message)
            return Response.ok(data={"channel": channel})
        except Exception as e:
            return Response.error(message=f"Redis publish failed: {e}")

    def publish_to_admin(self, payload: RedisResponse) -> Response:
        """
        Publica el estatus de un contenedor en el canal ADMIN de Redis.

        Args:
            response (Response): Mensaje a publicar.
        """
        return self.publish(JuiceBoxChannels.ADMIN, payload)

    def publish_to_client(self, payload: RedisResponse) -> Response:
        """
        Publica el estatus de un contenedor en el canal CLIENT de Redis.

        Args:
            container (Container): Mensaje a publicar.
        """
        return self.publish(JuiceBoxChannels.CLIENT, payload)

    def close(self) -> bool:
        """
        Cierra la conexión al cliente Redis.
        """
        try:
            self.__redis.close()
        except Exception:
            return False
        return True

    def cleanup(self) -> Response:
        """
        Destruye el contenedor y libera los recursos.
        """
        try:
            self.close()
            self.stop()
            return Response.ok(message="Redis cleanup successful!")
        except Exception as e:
            return Response.error(message=f"Redis could not be cleaned up: {str(e)}")
