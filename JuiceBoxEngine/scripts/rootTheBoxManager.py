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
from docker.models.containers import Container

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
    __rtb_yaml = "rtb-docker-compose.yml"

    def __init__(
        self, config: RTBConfig, docker_client: DockerClient | None = None
    ) -> None:
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
            return ManagerResult(
                success=True,
                message="RTB docker-compose file created",
                data=compose_dict,
            )
        except (yaml.YAMLError, OSError) as e:
            return ManagerResult(
                success=False,
                message="The RTB docker-compose file could not be created",
                error=str(e),
            )

    def __create(self) -> ManagerResult:
        try:
            subprocess.run(
                ["docker", "compose", "-f", self.__rtb_yaml, "up", "-d"],
                cwd=self.rtb_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            return ManagerResult(
                success=True, message="Docker compose subprocess successful"
            )
        except subprocess.CalledProcessError as e:
            return ManagerResult(
                success=False,
                message="Error found during subprocess execution",
                error=str(e.stdout) + ". " + str(e.stderr),
            )

    def start(self) -> ManagerResult:
        try:
            __response: ManagerResult
            # Se eliminan los contenedores en caso de existir:
            self.stop()
            compose_path = os.path.join(self.rtb_dir, self.__rtb_yaml)
            __response = self.__generate_docker_compose(compose_path)
            if not __response.success:
                return __response
            if not os.path.isfile(compose_path):
                return ManagerResult(
                    success=False,
                    message="Docker Compose file not found!",
                    error="The manager could not find the docker-compose file.",
                )

            __response: ManagerResult = self.__create()
            if __response.success:
                return ManagerResult(
                    success=True,
                    message="Containers started and now are running",
                )
            else:
                return ManagerResult(
                    success=False,
                    message="Failed to start containers",
                    error=__response.error,
                )
        except Exception as e:
            return ManagerResult(success=False, message="Error found!", error=str(e))

    def __stop_container(self, container_name: str, containers) -> ManagerResult:
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
                        ManagerResult(
                            success=True,
                            message="Container not found!",
                            data={"container": name},
                        )
                    )
            except Exception as e:
                overall_ok = False
                containers_results.append(
                    ManagerResult(
                        success=False,
                        message="Failed to stop container",
                        error=str(e),
                        data={"container": name},
                    )
                )
        __result: ManagerResult
        if overall_ok:
            __result = ManagerResult(
                success=True,
                message="All Root The Box containers stopped successfully",
                data={
                    "containers": [
                        container.to_dict() for container in containers_results
                    ]
                },
            )
        else:
            __result = ManagerResult(
                success=False,
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
        return ManagerResult(
            success=True,
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
        try:
            if not validate_container(self.__docker_client, container_name):
                return "not_found"
            container = self.__docker_client.containers.get(container_name)
            return container.status
        except errors.NotFound as e:
            return str(e)

    def status(self) -> ManagerResult:
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
                    ManagerResult(
                        success=True,
                        message="Container status retrieved",
                        data=_data,
                    )
                )
            except Exception as e:
                overall_ok = False
                containers_results.append(
                    ManagerResult(
                        success=False,
                        message="Error getting container status",
                        error=str(e),
                        data={"container": container_name, "status": "error"},
                    )
                )
        __response: ManagerResult
        __data: dict[str, list[dict]] = {
            "containers": [r.to_dict() for r in containers_results]
        }
        if overall_ok:
            __response = ManagerResult(
                success=True,
                message="Success at retrieving containers' statuses",
                data=__data,
            )
        else:
            __response = ManagerResult(
                success=False,
                message="Failure at retrieving containers' statuses",
                error="Some containers statuses could not be retrieved",
                data=__data,
            )
        return __response

    def cleanup(self) -> ManagerResult:
        """
        Detiene y elimina todos los contenedores Root The Box y libera los recursos.
        """
        try:
            self.stop()
            return ManagerResult(success=True, message="RTB cleanup successful!")
        except Exception as e:
            return ManagerResult(
                success=False, message="RTB could not be cleaned up", error=str(e)
            )
