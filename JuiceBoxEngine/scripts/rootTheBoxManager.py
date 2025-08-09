#!/usr/bin/env python3
"""
rootTheBoxManager.py

Clase RootTheBoxManager que carga configuración desde rootTheBox.json
y gestiona los contenedores via Docker Compose y Docker SDK.
"""

import os, subprocess, atexit
import docker, yaml
from docker import errors
from scripts.utils.config import RTBConfig
from scripts.utils.validator import validate_container
from JuiceBoxEngine.models.schemas import ManagerResult, BaseManager
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
    Clase módulo para administrar los contenedores de Root The Box.

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
        Raises:
            TypeError: Si config no es una instancia de RTBConfig.
        """
        if not isinstance(config, RTBConfig):
            raise TypeError("Required: RTBConfig instance.")

        # Cliente Docker
        if docker_client:
            self.__docker_client: DockerClient = docker_client

        # Directorio donde está este script
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        # Directorio padre del proyecto (contiene 'scripts/' y 'configs/')
        self.project_root = os.path.dirname(self.script_dir)
        # Ruta absoluta a configs/
        self.configs_dir = os.path.join(self.project_root, "configs")

        # Configuración
        self.webapp_port: int = config.webapp_port
        self.memcached_port: int = config.memcached_port
        self.network_name: str = config.network_name
        self.rtb_dir: str = config.rtb_dir
        self.webapp_container_name: str = config.webapp_container_name
        self.cache_container_name: str = config.cache_container_name

        atexit.register(self.cleanup)

    def __generate_docker_compose(self, output_path: str) -> ManagerResult:
        """
        Genera el archivo docker-compose.yml para Root The Box.

        Args:
            output_path (str): Ruta donde guardar el archivo docker-compose.yml.

        Returns:
            ManagerResult: Resultado de la operación.

        Raises:
            Exception: Si ocurre un error al crear el archivo.
        """
        if not output_path:
            output_path = os.path.join(self.rtb_dir, self.__rtb_yaml)

        compose_dict = {
            "services": {
                "memcached": {
                    "image": "memcached:latest",
                    "ports": [f"{self.memcached_port}:11211"],
                },
                "webapp": {
                    "build": ".",
                    "ports": [f"{self.webapp_port}:8888"],
                    "volumes": ["./files:/opt/rtb/files:rw"],
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

        Raises:
            Exception: Si ocurre un error al crear los contenedores.
        """
        try:
            subprocess.run(
                ["docker", "compose", "-f", self.__rtb_yaml, "up", "-d"],
                cwd=self.rtb_dir,
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

        Raises:
            Exception: Si ocurre un error al iniciar los contenedores.
        """
        try:
            __result: ManagerResult
            # Se eliminan los contenedores en caso de existir:
            self.stop()
            compose_path = os.path.join(self.rtb_dir, self.__rtb_yaml)
            __result = self.__generate_docker_compose(compose_path)
            if not __result.success:
                return __result
            if not os.path.isfile(compose_path):
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

        Raises:
            Exception: Si ocurre un error al detener o eliminar el contenedor.
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
                message=f"Container couldn't be stopped or removed!",
                error=str(e),
                data={"container": container_name},
            )

    def stop(self) -> ManagerResult:
        """
        Detiene y elimina los contenedores de Root The Box.

        Returns:
            ManagerResult: Resultado de la operación.

        Raises:
            Exception: Si ocurre un error al detener los contenedores.
        """
        containers_results: list[ManagerResult] = []
        overall_ok = True

        # Lista los dos contenedores a procesar
        for name in (self.webapp_container_name, self.cache_container_name):
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

    def show_config(self) -> ManagerResult:
        """
        Muestra la configuración actual del manager de Root The Box.

        Returns:
            ManagerResult: Resultado de la operación.

        Raises:
            Exception: Si ocurre un error al obtener la configuración.
        """
        return ManagerResult.ok(
            message="Root The Box configuration retrieved",
            data={
                "config": {
                    "webapp_container_name": self.webapp_container_name,
                    "cache_container_name": self.cache_container_name,
                    "webapp_port": self.webapp_port,
                    "memcached_port": self.memcached_port,
                    "rtb_dir": self.rtb_dir,
                    "network_name": self.network_name,
                },
            },
        )

    def __get_status(self, container_name: str) -> str:
        """
        Obtiene el estado de un contenedor dado su nombre.

        Args:
            container_name (str): Nombre del contenedor.

        Returns:
            str: Estado del contenedor ('running', 'exited', 'not_found', etc.).

        Raises:
            errors.NotFound: Si el contenedor no existe.
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

        Raises:
            Exception: Si ocurre un error al obtener el estado de los contenedores.
        """
        containers_results: list[ManagerResult] = []
        overall_ok = True

        for container_name in (self.webapp_container_name, self.cache_container_name):
            try:
                __status: str = self.__get_status(container_name)
                _data: dict[str, str | bool] = {
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

        Raises:
            Exception: Si ocurre un error al limpiar los recursos.
        """
        try:
            self.stop()
            return ManagerResult.ok(message="RTB cleanup successful!")
        except Exception as e:
            return ManagerResult.failure(
                message="RTB could not be cleaned up", error=str(e)
            )
