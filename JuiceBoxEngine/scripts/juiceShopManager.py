#!/usr/bin/env python3
"""
juiceShopManager.py

Clase JuiceBoxManager que carga configuración desde JuiceShopConfig
y gestiona los contenedores via Docker SDK.
"""

import os, atexit
from docker import errors
from scripts.utils.config import JuiceShopConfig
from scripts.utils.validator import validate_container
from JuiceBoxEngine.models.schemas import ManagerResult, Status, BaseManager
from docker import DockerClient
from docker.models.containers import Container


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


class JuiceShopManager(BaseManager):
    def __init__(
        self, config: JuiceShopConfig, docker_client: DockerClient | None = None
    ) -> None:
        if not isinstance(config, JuiceShopConfig):
            raise TypeError("Required: JuiceShopConfig instance.")

        # Configuración:
        self.config = config

        # Cliente Docker
        if docker_client:
            self.__docker_client: DockerClient = docker_client

        # Directorio donde está este script
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        # Directorio padre del proyecto (contiene 'scripts/' y 'configs/')
        self.project_root = os.path.dirname(self.script_dir)
        # Ruta absoluta a configs/
        self.configs_dir = os.path.join(self.project_root, "configs")

        self.image = "bkimminich/juice-shop:latest"

        atexit.register(self.cleanup)

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
            if not validate_container(self.__docker_client, __container):
                return (port, "available")
        return (1, "not available")

    def __get_port_from_container(self, container_name: str) -> int:
        """
        Extrae el número de puerto de un nombre de contenedor.
        Ejemplo: "juice-shop-3000" -> 3000
        """
        return int(container_name[len(self.container_prefix) :])

    def is_valid_port(self, port: int) -> bool:
        return port in self.ports_range

    def start(self) -> ManagerResult:
        __container_name: str = ""
        __port: int | None = None
        try:
            __port, __port_status = self.__get_available_port()  # Se obtiene el puerto
            if __port_status != "available":
                return ManagerResult(success=True, message="No available ports")
            __container_name = self.container_prefix + str(__port)
            __res: Container | bytes = self.__docker_client.containers.run(
                image=self.image,
                name=__container_name,
                detach=self.detach_mode,
                ports={"3000/tcp": __port},
                environment=[
                    f"CTF_KEY={self.ctf_key}",
                    f"NODE_ENV={self.node_env}",
                ],
            )
            return ManagerResult(
                success=True,
                message="Container has been created and now is running",
                data={
                    "container": __container_name,
                    "status": __res.status if isinstance(__res, Container) else None,
                    "port": __port,
                },
            )
        except Exception as e:
            # Devolver error con mensaje
            return ManagerResult(
                success=False,
                message="Container could not be created or started",
                error=str(e),
                data={"container": __container_name, "status": "error", "port": __port},
            )

    def stop_container(self, container: str | int) -> ManagerResult:
        __container_name: str = ""
        __port: int | None = None
        try:
            if isinstance(container, int):
                __container_name = self.container_prefix + str(container)
                __port = container
            elif isinstance(container, str):
                __container_name = container
                __port = self.__get_port_from_container(container)
            # Se verifica que exista el contenedor
            if validate_container(self.__docker_client, __container_name):
                containers = self.__docker_client.containers
                _container = containers.get(__container_name)
                _container.stop()
                _container.remove()
                return ManagerResult(
                    success=True,
                    message="Container has been stopped and removed from system",
                    data={
                        "container": __container_name,
                        "status": "removed",
                        "port": __port,
                    },
                )
            else:
                # No existe el contenedor
                return ManagerResult(
                    success=True,
                    message="Container could not be found",
                    data={
                        "container": __container_name,
                        "status": "not_found",
                        "port": __port,
                    },
                )
        except Exception as e:
            return ManagerResult(
                success=False,
                message="Container could not be stopped or removed",
                error=str(e),
                data={"container": __container_name, "status": "error", "port": __port},
            )

    def stop(self) -> ManagerResult:
        # Destruye todos los contenedores de la JuiceShop
        containers_results: list[ManagerResult] = []
        overall_ok = True
        for port in self.ports_range:
            result = self.stop_container(self.container_prefix + str(port))

            if not result.success:
                overall_ok = False
            else:
                containers_results.append(result)
        if not containers_results and overall_ok:
            # Si results está vacío
            return ManagerResult(
                success=True,
                message="No Juice Shop containers found to be stopped",
                data={
                    "containers": [
                        container.to_dict() for container in containers_results
                    ],
                },
            )
        elif overall_ok:
            return ManagerResult(
                success=True,
                message="All Juice Shop containers stopped successfully",
                data={
                    "containers": [
                        container.to_dict() for container in containers_results
                    ],
                },
            )
        return ManagerResult(
            success=False,
            message="Error at stopping Juice Shop containers",
            error="Some containers could not be stopped",
            data={
                "containers": [container.to_dict() for container in containers_results]
            },
        )

    def show_config(self) -> ManagerResult:
        return ManagerResult(
            success=True,
            message="Juice Shop configuration retrieved",
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
            },
        )

    def __get_status(self, container_name: str) -> str:
        try:
            container = self.__docker_client.containers.get(container_name)
            return container.status
        except errors.NotFound as e:
            return str(e)

    def status(self, container: int | str) -> ManagerResult:
        container_name: str = ""
        try:
            if isinstance(container, str):
                container_name = container
            elif isinstance(container, int):
                container_name = self.container_prefix + str(container)
            status: str = self.__get_status(container_name)
            return ManagerResult(
                success=True,
                message="Container status retrieved",
                data={
                    "container": container_name,
                    "status": status,
                },
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                message="Error getting container status",
                error=str(e),
                data={
                    "container": container_name,
                    "status": "error",
                },
            )

    def generate_rtb_config(
        self,
        input_filename: str = "juiceShopRTBConfig.yml",
        output_filename: str = "missions.xml",
    ) -> ManagerResult:
        """
        Lanza el contenedor juice-shop-ctf y genera el archivo XML de configuración para Root The Box en configs/.
        Es equivalente a:
          `docker run -ti --rm -v $(pwd):/data bkimminich/juice-shop-ctf --config juiceShopRTBConfig.yml --output missions.xml`
        """
        try:
            # Ruta al YAML de entrada dentro de configs/
            full_config_path = os.path.join(self.configs_dir, input_filename)

            if not os.path.isfile(full_config_path):
                return ManagerResult(
                    success=False,
                    message="YAML file not found",
                    error=f"YAML file could not be found at {full_config_path}",
                )

            # Monta configs/ en /data, usa /data como working_dir
            self.__docker_client.containers.run(
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

            return ManagerResult(
                success=True,
                message=f"{output_filename} generated at {self.configs_dir}",
            )

        except Exception as e:
            return ManagerResult(
                success=False, message="XML file could not be generated", error=str(e)
            )

    def cleanup(self) -> ManagerResult:
        """
        Detiene y elimina todos los contenedores Juice Shop y libera los recursos.
        """
        try:
            __res: ManagerResult = self.stop()
            if not __res.success:
                return __res
            return ManagerResult(success=True, message="Juice Shop cleanup successful!")
        except Exception as e:
            return ManagerResult(
                success=False,
                message="Juice Shop could not be cleaned up",
                error=str(e),
            )
