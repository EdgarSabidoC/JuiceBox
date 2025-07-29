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
from .utils.config import RTBConfig
from .utils.validator import validate_container


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
            return (True, "Docker compose subprocess succeed")
        except subprocess.CalledProcessError as e:
            return (False, str(e.stdout) + ". " + str(e.stderr))

    def run_containers(self) -> dict:
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

    def __kill_container(self, container, containers):
        # Mata o destruye un contenedor
        _container = containers.get(container)
        _container.stop()
        _container.remove()

    def kill_all(self) -> dict:
        results = []
        overall_ok = True

        # Lista los dos contenedores a procesar
        for name in (self.webapp_container_name, self.cache_container_name):
            try:
                if validate_container(self.client, name):
                    containers = self.client.containers
                    self.__kill_container(name, containers)
                    results.append(
                        {
                            "container": name,
                            "status": "ok",
                            "message": "Container has been stopped and removed from system",
                        }
                    )
                else:
                    # No estaba corriendo
                    overall_ok = False
                    results.append(
                        {
                            "container": name,
                            "status": "error",
                            "message": "Container not found",
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

    def status(self) -> dict[str, Union[str, list]]:
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

    def cleanup(self) -> None:
        """
        Cierra la conexión al Docker client para liberar sockets/tokens y elimina todos los contenedores.
        """
        self.kill_all()
        self.client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="rootTheBoxManager.py",
        description=f"""
{LOGO}
Manage Docker containers for the Root the Box server: run, kill, status, config.
        """,
        epilog=f"""
\t\t    Developed by: {DEVELOPER}
\t\t         github.com/{GITHUB_USER}
        """,
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-r", "--run", action="store_true", help="Run the containers.")
    parser.add_argument(
        "-k", "--kill-all", action="store_true", help="Stop and remove the containers."
    )
    parser.add_argument(
        "-c",
        "--show-config",
        action="store_true",
        help="Shows the configuration for the containers.",
    )
    parser.add_argument(
        "-s",
        "--status",
        action="store_true",
        help="Shows if the RTB containers are running.",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Shows this message and exit.",
        default=argparse.SUPPRESS,
    )

    args = parser.parse_args()

    result: dict = {"status": "ok", "message": "No action or command specified"}

    RTB_CONF_PATH = "configs/rootTheBox.json"
    rtb_config = RTBConfig(RTB_CONF_PATH)
    rtb = RootTheBoxManager(rtb_config)

    result: dict

    if args.show_config:
        result = rtb.show_config()
    elif args.run:
        result = rtb.run_containers()
    elif args.kill_all:
        result = rtb.kill_all()
    elif args.status:
        result = rtb.status()

    # print(json.dumps(result))

    sys.exit(0 if result.get("status") == "ok" else 1)
