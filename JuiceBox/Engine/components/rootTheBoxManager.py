import os, subprocess, atexit
import yaml
from docker import errors
from ..utils import RTBConfig
from ..utils import validate_container
from Models import ManagerResult, BaseManager
from docker import DockerClient
from docker.models.containers import ContainerCollection

LOGO = """
\t\t        ▄▄▄▄   ▄▄▄▄▄  ▄▄▄▄▄  ▄▄▄▄▄
\t\t        █   █  █   █  █   █    █
\t\t        ████   █   █  █   █    █
\t\t        █   █  █   █  █   █    █
\t\t        ▀   ▀  ▀▀▀▀▀  ▀▀▀▀▀    ▀
\t\t          ▄▄▄▄▄  ▄   ▄  ▄▄▄▄▄
\t\t            █    █   █  █
\t\t            █    █▄▄▄█  ███
\t\t            █    █   █  █
\t\t            ▀    ▀   ▀  ▀▀▀▀▀
\t\t          ▄▄▄▄   ▄▄▄▄▄  ▄   ▄
\t\t          █   █  █   █   █ █
\t\t          ████   █   █    █
\t\t          █   █  █   █   █ █
\t\t          ▀▀▀▀   ▀▀▀▀▀  ▀   ▀
\t\t▄   ▄  ▄▄▄  ▄   ▄  ▄▄▄   ▄▄▄  ▄▄▄▄▄ ▄▄▄▄
\t\t█▀▄▀█ █   █ █▄  █ █   █ █     █     █   █
\t\t█ █ █ █▀▀▀█ █ ▀▄█ █▀▀▀█ █  ▄▄ ███   ████
\t\t█   █ █   █ █   █ █   █ █   █ █     █   █
\t\t▀   ▀ ▀   ▀ ▀   ▀ ▀   ▀  ▀▀▀  ▀▀▀▀▀ ▀   ▀
"""
DEVELOPER = "Edgar Sabido"
GITHUB_USER = "EdgarSabidoC"


class RootTheBoxManager(BaseManager):
    """
    Clase que administra la instancia de Root The Box en contenedores Docker.

    ## Operaciones
    - **start:** Inicia los contenedores de Root The Box.
    - **stop:** Detiene y elimina los contenedores de Root The Box.
    - **status:** Obtiene el estado de los contenedores.
    - **show_config:** Muestra la configuración actual.
    - **cleanup:** Detiene y elimina los contenedores y libera recursos.
    """

    __rtb_yaml = "rtb-docker-compose.yml"

    def __init__(
        self, config: RTBConfig, docker_client: DockerClient | None = None
    ) -> None:
        """
        Inicializa el gestor de Root The Box con la configuración dada.

        Args:
            config (RTBConfig): Configuración para Root The Box.
            docker_client (DockerClient | None): Cliente Docker opcional.
        """
        if not isinstance(config, RTBConfig):
            raise TypeError("Required: RTBConfig instance.")

        # Configuración:
        self.config: RTBConfig = config

        # Cliente Docker
        if docker_client:
            self.__docker_client: DockerClient = docker_client

        # Directorio donde está este script
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        # Directorio padre del script
        self.components_dir = os.path.dirname(self.script_dir)
        # Directorio de la carpeta raíz del proyecto
        self.project_root = os.path.abspath(os.path.join(self.script_dir, "../../.."))
        # Directorio de RootTheBox/
        self.rtb_dir = os.path.abspath(os.path.join(self.project_root, "RootTheBox/"))
        # Ruta absoluta a configs/
        self.configs_dir = os.path.join(self.components_dir, "configs")

        atexit.register(self.cleanup)

    @property
    def web_app_port(self) -> int:
        """
        Puerto para la aplicación web de Root The Box.
        """
        return self.config.webapp_port

    @property
    def memcached_port(self) -> int:
        """
        Puerto para la caché de Root The Box.
        """
        return self.config.memcached_port

    @property
    def network_name(self) -> str:
        """
        Nombre de la red de contenedores de Root The Box.
        """
        return self.config.network_name

    @property
    def webapp_container_name(self) -> str:
        """
        Nombre para el contenedor de la aplicación web de Root The Box.
        """
        return self.config.webapp_container_name

    @property
    def cache_container_name(self) -> str:
        """
        Nombre para el contenedor de la caché de Root The Box.
        """
        return self.config.cache_container_name

    @property
    def compose_file_path(self) -> str:
        """
        Ruta al docker-compose.yml de RootTheBox, usando la configuración actual.
        """
        return os.path.join(self.rtb_dir, self.__rtb_yaml)

    def get_containers(self) -> list[str]:
        """
        Obtiene la lista de contenedores de la configuración actual de Root The Box.

        Returns:
          (list[str]): Lista con los nombres de los contenedores
        """
        return [self.webapp_container_name, self.cache_container_name]

    def __generate_docker_compose(self, output_path: str) -> ManagerResult:
        """
        Genera el archivo docker-compose.yml para Root The Box.

        Args:
            output_path (str): Ruta donde guardar el archivo docker-compose.yml.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        if not output_path:
            output_path = self.compose_file_path

        compose_dict = {
            "services": {
                "memcached": {
                    "image": "memcached:latest",
                    "ports": [f"{self.config.memcached_port}:11211"],
                },
                "webapp": {
                    "build": ".",
                    "ports": [f"{self.config.webapp_port}:8888"],
                    "volumes": [
                        "./files:/opt/rtb/files:rw",
                        "./missions:/opt/rtb/missions:rw",
                    ],
                    "environment": ["COMPOSE_CONVERT_WINDOWS_PATHS=1"],
                },
            },
        }
        try:
            with open(output_path, "w") as f:
                yaml.dump(compose_dict, f, sort_keys=False)
            return ManagerResult.ok(
                message="RTB docker-compose file created",
                data=compose_dict,
            )
        except (yaml.YAMLError, OSError) as e:
            return ManagerResult.failure(
                message="The RTB docker-compose file could not be created",
                error=str(e),
            )

    def __create(self) -> ManagerResult:
        """
        Crea e inicia los contenedores de Root The Box usando Docker Compose.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        try:
            subprocess.run(
                ["docker", "compose", "-f", self.compose_file_path, "up", "-d"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )
            return ManagerResult.ok(message="Docker compose subprocess successful")
        except subprocess.CalledProcessError as e:
            err: str = ""
            if e.stdout:
                err += str(e.stdout)
            if e.stderr:
                err += ". " + str(e.stderr)
            if not err and e:
                err = str(e)
            return ManagerResult.failure(
                message="Error found during subprocess execution",
                error=err,
            )

    def start(self) -> ManagerResult:
        """
        Inicia los contenedores de Root The Box.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        try:
            __result: ManagerResult
            # Se eliminan los contenedores en caso de existir:
            self.stop()
            __result = self.__generate_docker_compose(self.compose_file_path)
            if not __result.success:
                return __result
            if not os.path.isfile(self.compose_file_path):
                return ManagerResult(
                    success=False,
                    message="Docker Compose file not found!",
                    error="The manager could not find the docker-compose file.",
                )

            __result: ManagerResult = self.__create()
            if __result.success:
                return ManagerResult.ok(
                    message="Containers started and now are running",
                )
            else:
                return ManagerResult.failure(
                    message="Failed to start containers",
                    error=__result.error,
                )
        except Exception as e:
            return ManagerResult(success=False, message="Error found!", error=str(e))

    def __stop_container(
        self, container_name: str, containers: ContainerCollection
    ) -> ManagerResult:
        """
        Detiene y elimina un contenedor dado su nombre.

        Args:
            container_name (str): Nombre del contenedor a detener y eliminar.
            containers: Colección de contenedores del cliente Docker.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        try:
            # Mata o destruye un contenedor
            _container = containers.get(container_name)
            _container.stop()
            _container.remove()
            return ManagerResult(
                success=True,
                message="Container has been stopped and removed from system!",
                data={"container": container_name},
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                message="Container couldn't be stopped or removed!",
                error=str(e),
                data={"container": container_name},
            )

    def stop(self) -> ManagerResult:
        """
        Detiene y elimina los contenedores de Root The Box.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        containers_results: list[ManagerResult] = []
        overall_ok = True

        # Lista los dos contenedores a procesar
        for name in (
            self.config.webapp_container_name,
            self.config.cache_container_name,
        ):
            try:
                if validate_container(self.__docker_client, name):
                    containers = self.__docker_client.containers
                    __result: ManagerResult = self.__stop_container(name, containers)
                    containers_results.append(__result)
                    if not __result.success:
                        overall_ok = False
                else:
                    # No existe el contenedor
                    containers_results.append(
                        ManagerResult.ok(
                            message="Container not found!",
                            data={"container": name},
                        )
                    )
            except Exception as e:
                overall_ok = False
                containers_results.append(
                    ManagerResult.failure(
                        message="Failed to stop container",
                        error=str(e),
                        data={"container": name},
                    )
                )
        __result: ManagerResult
        if overall_ok:
            __result = ManagerResult.ok(
                message="All Root The Box containers stopped successfully",
                data={
                    "containers": [
                        container.to_dict() for container in containers_results
                    ]
                },
            )
        else:
            __result = ManagerResult.failure(
                message="Error at stopping Root The Box containers",
                error="Some containers could not be stopped",
                data={
                    "containers": [
                        container.to_dict() for container in containers_results
                    ]
                },
            )
        return __result

    def set_config(self, config: dict) -> ManagerResult:
        """
        Cambia la configuración del Root The Box Manager.

        Args:
            config (dict): Diccionario con la configuración.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        try:
            self.config.set_config(config=config)
            return ManagerResult.ok(
                message="Root The Box Manager config setted successfully!",
                data=self.show_config().data,
            )
        except Exception as e:
            return ManagerResult.failure(
                message=f"Error when trying to set config for Root The Box Manager -> {e}"
            )

    def show_config(self) -> ManagerResult:
        """
        Muestra la configuración actual del manager de Root The Box.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        return ManagerResult.ok(
            message="Root The Box configuration retrieved",
            data={"config": self.config.get_config()},
        )

    def __get_status(self, container_name: str) -> str:
        """
        Obtiene el estado de un contenedor dado su nombre.

        Args:
            container_name (str): Nombre del contenedor.

        Returns:
            str: Estado del contenedor ('running', 'exited', 'not_found', etc.).
        """
        try:
            if not validate_container(self.__docker_client, container_name):
                return "not_found"
            container = self.__docker_client.containers.get(container_name)
            return container.status
        except errors.NotFound as e:
            return str(e)

    def status(self) -> ManagerResult:
        """
        Obtiene el estado actual de los contenedores de Root The Box.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        containers_results: list[ManagerResult] = []
        overall_ok = True

        for container_name in (
            self.config.webapp_container_name,
            self.config.cache_container_name,
        ):
            try:
                __status: str = self.__get_status(container_name)
                _data: dict[str, str] = {
                    "container": container_name,
                    "status": __status,
                }
                containers_results.append(
                    ManagerResult.ok(
                        message="Container status retrieved",
                        data=_data,
                    )
                )
            except Exception as e:
                overall_ok = False
                containers_results.append(
                    ManagerResult.failure(
                        message="Error getting container status",
                        error=str(e),
                        data={"container": container_name, "status": "error"},
                    )
                )
        __result: ManagerResult
        __data: dict[str, list[dict]] = {
            "containers": [r.to_dict() for r in containers_results]
        }
        if overall_ok:
            __result = ManagerResult.ok(
                message="Success at retrieving containers' statuses",
                data=__data,
            )
        else:
            __result = ManagerResult.failure(
                message="Failure at retrieving containers' statuses",
                error="Some containers statuses could not be retrieved",
                data=__data,
            )
        return __result

    def cleanup(self) -> ManagerResult:
        """
        Detiene y elimina todos los contenedores Root The Box y libera los recursos.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        try:
            self.stop()
            return ManagerResult.ok(message="RTB cleanup successful!")
        except Exception as e:
            return ManagerResult.failure(
                message="RTB could not be cleaned up", error=str(e)
            )
