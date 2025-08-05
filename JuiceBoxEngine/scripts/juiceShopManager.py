#!/usr/bin/env python3
"""
juiceShopManager.py

Clase JuiceBoxManager que carga configuración desde JuiceShopConfig
y gestiona los contenedores via Docker SDK.
"""

import os, sys, json
from typing import Union
import docker, argparse
from typing import overload
from docker import errors
from scripts.utils.config import JuiceShopConfig
from scripts.utils.validator import validate_container
from importlib.resources import files
from scripts.utils.schemas import Response, Status

LOGO = """
\t\t  ▄▄▄▄▄   ▄   ▄   ▄▄▄▄▄    ▄▄▄▄   ▄▄▄▄▄
\t\t      █   █   █     █     █       █
\t\t      █   █   █     █     █       ███
\t\t  █   █   █   █     █     █       █
\t\t   ▀▀▀▀    ▀▀▀    ▀▀▀▀▀    ▀▀▀▀   ▀▀▀▀▀
\t\t      ▄▄▄▄▄   ▄   ▄   ▄▄▄▄▄   ▄▄▄▄▄
\t\t      █       █   █   █   █   █   █
\t\t      █▄▄▄▄   █▄▄▄█   █   █   █▄▄▄█
\t\t          █   █   █   █   █   █
\t\t      ▀▀▀▀▀   ▀   ▀   ▀▀▀▀▀   ▀
\t\t▄   ▄  ▄▄▄  ▄   ▄  ▄▄▄   ▄▄▄  ▄▄▄▄▄ ▄▄▄▄
\t\t█▀▄▀█ █   █ █▄  █ █   █ █     █     █   █
\t\t█ █ █ █▀▀▀█ █ ▀▄█ █▀▀▀█ █  ▄▄ ███   ████
\t\t█   █ █   █ █   █ █   █ █   █ █     █   █
\t\t▀   ▀ ▀   ▀ ▀   ▀ ▀   ▀  ▀▀▀  ▀▀▀▀▀ ▀   ▀
"""
DEVELOPER = "Edgar Sabido"
GITHUB_USER = "EdgarSabidoC"


class JuiceShopManager:
    def __init__(self, config: JuiceShopConfig) -> None:
        if not isinstance(config, JuiceShopConfig):
            raise TypeError("Required: JuiceShopConfig instance.")

        # Configuración:
        self.config = config

        # Cliente Docker
        self.client = docker.from_env()

        # Directorio donde está este script
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        # Directorio padre del proyecto (contiene 'scripts/' y 'configs/')
        self.project_root = os.path.dirname(self.script_dir)
        # Ruta absoluta a configs/
        self.configs_dir = os.path.join(self.project_root, "configs")

        self.image = "bkimminich/juice-shop:latest"

    @property
    def container_prefix(self) -> str:
        return self.config.juice_shop_containers_name

    @property
    def ports_range(self) -> list[int]:
        return self.config.ports

    @property
    def starting_port(self) -> int:
        return self.config.starting_port

    @property
    def ending_port(self) -> int:
        return self.config.ending_port

    @property
    def ctf_key(self) -> str:
        return self.config.ctf_key

    @property
    def node_env(self) -> str:
        return self.config.node_env

    @property
    def detach_mode(self) -> bool:
        return self.config.detach_mode

    def __get_available_port(self) -> tuple[int, str]:
        for port in self.ports_range:
            __container: str = self.container_prefix + str(port)
            # Se verifica que no exista el contenedor
            if not validate_container(self.client, __container):
                return (port, "available")
        return (1, "not available")

    def is_valid_port(self, port: int) -> bool:
        return port in self.ports_range

    def run_container(self) -> Response:
        __container: str = ""
        __port: int
        try:
            __port, __port_status = self.__get_available_port()  # Se obtiene el puerto
            if __port_status != "available":
                return Response.error(message="No available ports")
            __container = self.container_prefix + str(__port)
            self.client.containers.run(
                image=self.image,
                name=__container,
                detach=self.detach_mode,
                ports={"3000/tcp": __port},
                environment=[
                    f"CTF_KEY={self.ctf_key}",
                    f"NODE_ENV={self.node_env}",
                ],
            )
            return Response.ok(
                message="Container has been created and now is running",
                data={"container": __container},
            )
        except Exception as e:
            # Devolver error con mensaje
            return Response.error(message=str(e), data={"container": __container})

    def kill_container(self, container: str | int) -> Response:
        __container: str = ""
        try:
            if isinstance(container, int):
                __container = self.container_prefix + str(container)
            elif isinstance(container, str):
                __container = container
            # Se verifica que exista el contenedor
            if validate_container(self.client, __container):
                containers = self.client.containers
                _container = containers.get(__container)
                _container.stop()
                _container.remove()
                return Response.ok(
                    message="Container has been stopped and removed from system",
                    data={"container": __container},
                )
            else:
                # No existe el contenedor
                return Response.not_found(
                    message="Container not found",
                    data={
                        "container": __container,
                    },
                )
        except Exception as e:
            return Response.error(message=str(e), data={"container": __container})

    def kill_all(self) -> Response:
        # Destruye todos los contenedores de la JuiceShop
        containers: list[Response] = []
        overall_ok = True
        for port in self.ports_range:
            res = self.kill_container(self.container_prefix + str(port))

            if res.status == Status.ERROR:
                overall_ok = False
            elif res.status == Status.OK:
                containers.append(res)
        if not containers and overall_ok:
            # Si results está vacío
            return Response.ok(
                message="There are no Juice Shop running containers",
                data={
                    "containers": containers,
                },
            )
        elif not containers and not overall_ok:
            return Response.error(
                message="Something went wrong with Juice Shop containers",
                data={
                    "containers": containers,
                },
            )
        elif overall_ok:
            return Response.ok(
                data={
                    "containers": containers,
                },
            )
        return Response.error(
            data={
                "containers": containers,
            },
        )

    def show_config(self) -> Response:
        return Response.ok(
            data={
                "config": {
                    "container_prefix": self.container_prefix,
                    "ports_range": self.ports_range,
                    "starting_port": self.starting_port,
                    "ending_port": self.ending_port,
                    "ctf_key": self.ctf_key,
                    "node_env": self.node_env,
                    "detach_mode": self.detach_mode,
                    "image": self.image,
                },
            }
        )

    def __is_running(self, container_name: str) -> bool:
        try:
            container = self.client.containers.get(container_name)
            return container.status == "running"
        except errors.NotFound:
            return False

    def status(self, container: Union[int, str]) -> Response:
        __container: str = ""
        try:
            if isinstance(container, str):
                __container = container
            elif isinstance(container, int):
                __container = self.container_prefix + str(container)
            running = self.__is_running(__container)
            if not running:
                return Response.error(
                    message="Container is not running",
                    data={"container": __container, "status": False},
                )
            else:
                return Response.ok(
                    message="Container is running",
                    data={
                        "container": __container,
                        "status": True,
                    },
                )
        except Exception as e:
            return Response.error(
                message=str(e),
                data={
                    "container": __container,
                    "status": False,
                },
            )

    def generate_rtb_config(
        self,
        input_filename: str = "juiceShopRTBConfig.yml",
        output_filename: str = "missions.xml",
    ) -> Response:
        """
        Lanza el contenedor juice-shop-ctf y genera el archivo XML de configuración para Root The Box en configs/.
        Es equivalente a:
          `docker run -ti --rm -v $(pwd):/data bkimminich/juice-shop-ctf --config juiceShopRTBConfig.yml --output missions.xml`
        """
        try:
            # Ruta al YAML de entrada dentro de configs/
            full_config_path = os.path.join(self.configs_dir, input_filename)

            if not os.path.isfile(full_config_path):
                return Response.error(f"YAML file not found: {full_config_path}")

            # Monta configs/ en /data, usa /data como working_dir
            self.client.containers.run(
                image="bkimminich/juice-shop-ctf",
                command=[
                    "--config",
                    os.path.basename(full_config_path),
                    "--output",
                    output_filename,
                ],
                volumes={self.configs_dir: {"bind": "/data", "mode": "rw"}},
                working_dir="/data",
                tty=True,  # -t
                stdin_open=True,  # -i
                remove=True,  # --rm
            )

            return Response.ok(f"{output_filename} generated at {self.configs_dir}")

        except Exception as e:
            return Response.error(f"No se pudo generar XML: {e}")

    def cleanup(self) -> Response:
        """
        Cierra la conexión al Docker client para liberar sockets/tokens.
        """
        try:
            self.kill_all()
            self.client.close()
            return Response.ok()
        except Exception:
            return Response.error()
