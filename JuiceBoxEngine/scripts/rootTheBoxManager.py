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
from JuiceBoxEngine.models.schemas import Response, Status
from docker import DockerClient

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


class RootTheBoxManager:
    __rtb_yaml = "rtb-docker-compose.yml"

    def __init__(self, config: RTBConfig) -> None:
        if not isinstance(config, RTBConfig):
            raise TypeError("Required: RTBConfig instance.")

        # Cliente Docker
        self.__docker_client: DockerClient = docker.from_env()

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

    def __generate_docker_compose(self, output_path: str) -> Response:
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
            return Response.ok(message="docker-compose file created", data=compose_dict)
        except (yaml.YAMLError, OSError) as e:
            return Response.error(
                message=f"docker-compose file could not be created: {str(e)}",
                data=compose_dict,
            )

    def __run(self) -> Response:
        try:
            subprocess.run(
                ["docker", "compose", "-f", self.__rtb_yaml, "up", "-d"],
                cwd=self.rtb_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            return Response.ok(message="Docker compose subprocess successful")
        except subprocess.CalledProcessError as e:
            return Response.error(message=str(e.stdout) + ". " + str(e.stderr))

    def run_containers(self) -> Response:
        try:
            __response: Response
            # Se eliminan los contenedores en caso de existir:
            self.kill_all()
            compose_path = os.path.join(self.rtb_dir, self.__rtb_yaml)
            __response = self.__generate_docker_compose(compose_path)
            if __response.status == Status.ERROR:
                return __response
            if not os.path.isfile(compose_path):
                return Response.not_found(message="Docker Compose file not found!")

            __response: Response = self.__run()
            if __response.status == Status.OK:
                return Response.ok(
                    message="Containers started and now are running",
                    data=__response.data,
                )
            else:
                return Response.error(
                    message="Failed to start containers", data=__response.data
                )
        except Exception as e:
            return Response.error(message=str(e))

    def __kill_container(self, container, containers) -> Response:
        try:
            # Mata o destruye un contenedor
            _container = containers.get(container)
            _container.stop()
            _container.remove()
            return Response.ok(
                f"{container} has been stopped and removed from system!",
                data={"container": container},
            )
        except Exception as e:
            return Response.error(
                f"{container} couldn't be stopped or removed: {str(e)}",
                data={"container": container},
            )

    def kill_all(self) -> Response:
        containers_results: list[Response] = []
        overall_ok = True

        # Lista los dos contenedores a procesar
        for name in (self.webapp_container_name, self.cache_container_name):
            try:
                if validate_container(self.__docker_client, name):
                    containers = self.__docker_client.containers
                    __response: Response = self.__kill_container(name, containers)
                    containers_results.append(__response)
                    if __response.status == Status.ERROR:
                        overall_ok = False
                else:
                    # No existe el contenedor
                    containers_results.append(
                        Response.not_found(
                            "Container not found!", data={"container": name}
                        )
                    )
            except Exception as e:
                overall_ok = False
                containers_results.append(
                    Response.error(message=str(e), data={"container": name})
                )
        __resp: Response
        if overall_ok:
            __resp = Response.ok(data={"containers": containers_results})
        else:
            __resp = Response.error(data={"containers": containers_results})
        return __resp

    def show_config(self) -> Response:
        return Response.ok(
            data={
                "config": {
                    "webapp_container_name": self.webapp_container_name,
                    "cache_container_name": self.cache_container_name,
                    "webapp_port": self.webapp_port,
                    "memcached_port": self.memcached_port,
                    "rtb_dir": self.rtb_dir,
                    "network_name": self.network_name,
                },
            }
        )

    def __is_running(self, name: str) -> bool:
        try:
            container = self.__docker_client.containers.get(name)
            return container.status == "running"
        except errors.NotFound:
            return False

    def status(self) -> Response:
        results: list[Response] = []
        overall_ok = True

        for name in (self.webapp_container_name, self.cache_container_name):
            try:
                __running = self.__is_running(name)
                _data: dict[str, str | bool] = {"container": name, "running": __running}
                if not __running:
                    overall_ok = False
                    results.append(Response.error(data=_data))
                else:
                    results.append(Response.ok(data=_data))
            except Exception as e:
                overall_ok = False
                results.append(
                    Response.error(
                        message=str(e), data={"container": name, "running": False}
                    )
                )
        __response: Response
        __data: dict[str, list[Response]] = {"containers": results}
        if overall_ok:
            __response = Response.ok(data=__data)
        else:
            __response = Response.error(data=__data)
        return __response

    def cleanup(self) -> Response:
        """
        Cierra la conexión al Docker __docker_client para liberar sockets/tokens y elimina todos los contenedores.
        """
        try:
            self.kill_all()
            self.__docker_client.close()
            return Response.ok()
        except Exception:
            return Response.error()
