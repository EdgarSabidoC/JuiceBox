#!/usr/bin/env python3
"""
rootTheBoxManager.py

Clase RootTheBoxManager que carga configuración desde rootTheBox.json
y gestiona los contenedores via Docker Compose y Docker SDK.
"""

import os, sys, subprocess, json
import docker, argparse, yaml
from typing import Union
from docker import errors
from scripts.utils.config import RTBConfig
from scripts.utils.validator import validate_container
from importlib.resources import files

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
        self.client = docker.from_env()

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

    def __generate_docker_compose(self, output_path: str) -> tuple[bool, str]:
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
            return (True, "Dockercompose file created")
        except (yaml.YAMLError, OSError) as e:
            return (False, str(e))

    def __run(self) -> tuple[bool, str]:
        try:
            subprocess.run(
                ["docker", "compose", "-f", self.__rtb_yaml, "up", "-d"],
                cwd=self.rtb_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            return (True, "Docker compose subprocess successful")
        except subprocess.CalledProcessError as e:
            return (False, str(e.stdout) + ". " + str(e.stderr))

    def run_containers(self) -> dict[str, str]:
        try:
            # Se eliminan los contenedores en caso de existir:
            self.kill_all()
            compose_path = os.path.join(self.rtb_dir, self.__rtb_yaml)
            __status, __message = self.__generate_docker_compose(compose_path)
            if not __status:
                return {
                    "status": "error",
                    "message": f"Docker Compose could not be created: {__message}",
                }
            if not os.path.isfile(compose_path):
                return {
                    "status": "error",
                    "message": "Docker Compose file not found",
                }

            __status, __message = self.__run()
            if __status:
                return {
                    "status": "ok",
                    "message": f"Containers started and now are running. {__message}",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to start containers. {__message}",
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def __kill_container(self, container, containers) -> tuple[bool, str]:
        try:
            # Mata o destruye un contenedor
            _container = containers.get(container)
            _container.stop()
            _container.remove()
            return (True, f"{container} has been stopped and removed from system!")
        except Exception as e:
            return (False, f"{container} couldn't be stopped or removed: {str(e)}")

    def kill_all(self) -> dict[str, str | list[dict[str, str]]]:
        results: list[dict[str, str]] = []
        overall_ok = True

        # Lista los dos contenedores a procesar
        for name in (self.webapp_container_name, self.cache_container_name):
            try:
                if validate_container(self.client, name):
                    containers = self.client.containers
                    res = self.__kill_container(name, containers)
                    # Se valida que se haya eliminado correctamente el contenedor
                    if res[0] == True:
                        results.append(
                            {
                                "container": name,
                                "status": "ok",
                                "message": res[1],
                            }
                        )
                    else:
                        results.append(
                            {
                                "container": name,
                                "status": "error",
                                "message": res[1],
                            }
                        )
                else:
                    # No estaba corriendo el contenedor
                    overall_ok = False
                    results.append(
                        {
                            "container": name,
                            "status": "error",
                            "message": "Container not found!",
                        }
                    )
            except Exception as e:
                overall_ok = False
                results.append(
                    {"container": name, "status": "error", "message": str(e)}
                )

        return {"status": "ok" if overall_ok else "error", "details": results}

    def show_config(self) -> dict:
        return {
            "status": "ok",
            "config": {
                "webapp_container_name": self.webapp_container_name,
                "cache_container_name": self.cache_container_name,
                "webapp_port": self.webapp_port,
                "memcached_port": self.memcached_port,
                "rtb_dir": self.rtb_dir,
                "network_name": self.network_name,
            },
        }

    def __is_running(self, name: str) -> bool:
        try:
            container = self.client.containers.get(name)
            return container.status == "running"
        except errors.NotFound:
            return False

    def status(self) -> dict[str, str | list]:
        results: list[dict] = []
        overall_ok = True

        for name in (self.webapp_container_name, self.cache_container_name):
            try:
                running = self.__is_running(name)
                if not running:
                    overall_ok = False
                results.append({"container": name, "running": running})
            except Exception as e:
                overall_ok = False
                results.append({"container": name, "running": False, "message": str(e)})

        return {"status": "ok" if overall_ok else "error", "containers": results}

    def cleanup(self) -> bool:
        """
        Cierra la conexión al Docker client para liberar sockets/tokens y elimina todos los contenedores.
        """
        try:
            self.kill_all()
            self.client.close()
            return True
        except Exception:
            return False
