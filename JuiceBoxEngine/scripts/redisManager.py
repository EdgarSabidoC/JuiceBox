import redis, subprocess, os, docker
from scripts.utils.schemas import Response
from importlib.resources import path
from scripts.utils.validator import validate_container
from scripts.utils.schemas import RedisResponse


class JuiceBoxChannels:
    ADMIN = "admin_channel"
    CLIENT = "client_channel"


class RedisManager:

    def __init__(
        self,
        container_name: str = "juicebox-redis",
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: str = "C5L48",
        compose_file: str | None = None,
    ) -> None:
        # Si no se especifica la ruta, se carga desde el paquete configs
        if compose_file:
            self.__compose_file = compose_file
        else:
            with path("JuiceBoxEngine.configs", "redis-docker-compose.yml") as p:
                self.__compose_file = str(p)
        self.container_name = container_name
        # Arranca el servicio:
        self.__run()

        # Cliente Redis
        self._redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
        )

    def __run(self) -> Response:
        try:
            docker_client = docker.from_env()
            if validate_container(docker_client, self.container_name):
                if (
                    docker_client.containers.get(self.container_name).status
                    == "running"
                ):
                    return Response.ok(message="Redis container is already running!")
                else:
                    docker_client.containers.get(self.container_name).start()
                    return Response.ok(message="Redis container is running!")
            base_dir = os.path.dirname(self.__compose_file)
            cmd = ["docker", "compose", "-f", self.__compose_file, "up", "-d"]
            subprocess.run(
                cmd,
                cwd=base_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            return Response.ok(message="Redis container created and now is running!")
        except subprocess.CalledProcessError as e:
            return Response.error(message=str(e.stdout) + ". " + str(e.stderr))

    def __publish(self, channel: str, payload: str) -> Response:
        """
        Publica un mensaje en un canal Redis.

        Args:
            channel (str): Nombre del canal.
            payload (dict[str, Any]): Mensaje a publicar.
        """
        try:
            self._redis.publish(channel, payload)
            return Response.ok(data={"channel": channel})
        except Exception as e:
            return Response.error(message=f"Redis publish failed: {e}")

    def publish_to_admin(self, response: str) -> Response:
        """
        Publica un mensaje en el canal ADMIN de Redis.

        Args:
            response (Response): Mensaje a publicar.
        """
        return self.__publish(JuiceBoxChannels.ADMIN, response)

    def publish_to_client(self, response: str) -> Response:
        """
        Publica un mensaje en el canal CLIENT de Redis.

        Args:
            response (Response): Mensaje a publicar.
        """
        return self.__publish(JuiceBoxChannels.CLIENT, response)
