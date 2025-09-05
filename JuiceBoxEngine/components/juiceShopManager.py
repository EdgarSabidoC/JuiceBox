#!/usr/bin/env python3
"""
juiceShopManager.py

Clase JuiceBoxManager que carga configuración desde JuiceShopConfig
y gestiona los contenedores via Docker SDK.
"""

import os, atexit
from docker import errors
from ..utils import JuiceShopConfig
from ..utils import validate_container
from Models import ManagerResult, Status, BaseManager
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
    """
    Clase módulo para administrar los contenedores de Juice Shop.

    ## Operaciones
    - **start:** Inicia un nuevo contenedor de Juice Shop en un puerto disponible.
    - **stop:** Detiene y elimina todos los contenedores de Juice Shop.
    - **stop_container:** Detiene y elimina un contenedor específico de Juice Shop.
    - **status:** Obtiene el estado de un contenedor específico de Juice Shop.
    - **show_config:** Muestra la configuración actual de Juice Shop.
    - **generate_rtb_config:** Genera el archivo XML de configuración para Root The Box.
    - **cleanup:** Detiene y elimina todos los contenedores de Juice Shop y libera los
    """

    def __init__(
        self, config: JuiceShopConfig, docker_client: DockerClient | None = None
    ) -> None:
        """
        Inicializa el gestor de Juice Shop con la configuración dada.
        Args:
            config (JuiceShopConfig): Configuración para Juice Shop.
            docker_client (DockerClient | None): Cliente Docker opcional.
        Raises:
            TypeError: Si config no es una instancia de JuiceShopConfig.
        """
        if not isinstance(config, JuiceShopConfig):
            raise TypeError("Required: JuiceShopConfig instance.")

        # Configuración:
        self.config: JuiceShopConfig = config

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
        """
        Prefijo para los nombres de los contenedores de Juice Shop.
        """
        return self.config.juice_shop_containers_name

    @property
    def ports_range(self) -> list[int]:
        """
        Rango de puertos disponibles para los contenedores de Juice Shop.
        """
        return [self.config.starting_port, self.config.ending_port]

    @property
    def starting_port(self) -> int:
        """
        Puerto inicial del rango de puertos.
        """
        return self.config.starting_port

    @property
    def ending_port(self) -> int:
        """
        Puerto final del rango de puertos.
        """
        return self.config.ending_port

    @property
    def ctf_key(self) -> str:
        """
        Clave CTF para Juice Shop.
        """
        return self.config.ctf_key

    @property
    def node_env(self) -> str:
        """Variable de entorno de Node."""
        return self.config.node_env

    @property
    def detach_mode(self) -> bool:
        """
        Modo detach para los contenedores de Juice Shop
        """
        return self.config.detach_mode

    def __get_available_port(self) -> tuple[int, str]:
        """
        Obtiene un puerto disponible.

        Returns:
            tuple[int, "available" | "not available"]: Puerto y disponibilidad.
        """
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

        Args:
            container_name (str): Nombre del contenedor de Docker.

        Returns:
            int: Puerto del contenedor.
        """
        return int(container_name[len(self.container_prefix) :])

    def is_valid_port(self, port: int) -> bool:
        return port in self.ports_range

    def start(self) -> ManagerResult:
        """
        Inicia un contenedor de Juice Shop.

        Returns:
            ManagerResult: Resultado de la operación.

        Raises:
            Exception: Si ocurre un error al iniciar el contenedor.
        """
        __container_name: str = ""
        __port: int | None = None
        try:
            __port, __port_status = self.__get_available_port()  # Se obtiene el puerto
            if __port_status != "available":
                return ManagerResult.ok(message="No available ports")
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
            return ManagerResult.ok(
                message="Container has been created and now is running",
                data={
                    "container": __container_name,
                    "status": __res.status if isinstance(__res, Container) else None,
                    "port": __port,
                },
            )
        except Exception as e:
            # Devolver error con mensaje
            return ManagerResult.failure(
                message="Container could not be created or started",
                error=str(e),
                data={"container": __container_name, "status": "error", "port": __port},
            )

    def stop_container(self, container: str | int) -> ManagerResult:
        """
        Detiene y destruye un contenedor de la Juice Shop.

        Args:
            container (str | int): Nombre o puerto del contenedor de Docker.

        Returns:
            ManagerResult: Resultado de la operación.

        Raises:
            Exception: Si ocurre un error al detener el contenedor.
        """
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
                return ManagerResult.ok(
                    message="Container has been stopped and removed from system",
                    data={
                        "container": __container_name,
                        "status": "removed",
                        "port": __port,
                    },
                )
            else:
                # No existe el contenedor
                return ManagerResult.ok(
                    message="Container could not be found",
                    data={
                        "container": __container_name,
                        "status": "not_found",
                        "port": __port,
                    },
                )
        except Exception as e:
            return ManagerResult.failure(
                message="Container could not be stopped or removed",
                error=str(e),
                data={"container": __container_name, "status": "error", "port": __port},
            )

    def stop(self) -> ManagerResult:
        """
        Detiene y destruye todos los contenedores de la Juice Shop.

        Returns:
            ManagerResult: Resultado de la operación.

        Raises:
            Exception: Si ocurre un error al detener los contenedores.
        """
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
            return ManagerResult.ok(
                message="No Juice Shop containers found to be stopped",
                data={
                    "containers": [
                        container.to_dict() for container in containers_results
                    ],
                },
            )
        elif overall_ok:
            return ManagerResult.ok(
                message="All Juice Shop containers stopped successfully",
                data={
                    "containers": [
                        container.to_dict() for container in containers_results
                    ],
                },
            )
        return ManagerResult.failure(
            message="Error at stopping Juice Shop containers",
            error="Some containers could not be stopped",
            data={
                "containers": [container.to_dict() for container in containers_results]
            },
        )

    def show_config(self) -> ManagerResult:
        """
        Muestra la configuración actual del manager de la Juice Shop.
        Returns:
            ManagerResult: Resultado de la operación.
        Raises:
            Exception: Si ocurre un error al obtener la configuración.
        """
        return ManagerResult.ok(
            message="Juice Shop configuration retrieved",
            data={
                "config": {
                    "container_prefix": self.container_prefix,
                    "ports_range": self.ports_range,
                    "ctf_key": self.ctf_key,
                    "node_env": self.node_env,
                    "detach_mode": self.detach_mode,
                    "image": self.image,
                },
            },
        )

    def set_config(self, config: dict) -> ManagerResult:
        """
        Cambia la configuración del Juice Shop Manager.

        Args:
            config (dict): Diccionario con la configuración.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        try:
            self.config.set_config(config=config)
            return ManagerResult.ok(
                message="Juice Shop Manager config setted successfully!",
                data=self.show_config().data,
            )
        except Exception as e:
            return ManagerResult.failure(
                message=f"Error when trying to set config for Juice Shop Manager -> {e}"
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
            container = self.__docker_client.containers.get(container_name)
            return container.status
        except errors.NotFound as e:
            return str(e)

    def status(self, container: str | int) -> ManagerResult:
        """
        Obtiene el estado actual de un contenedor de la Juice Shop.
        Args:
            container (str | int): Nombre o puerto del contenedor de Docker.

        Returns:
            ManagerResult: Resultado de la operación.

        Raises:
            Exception: Si ocurre un error al obtener el estado de los contenedores.
        """
        container_name: str = ""
        try:
            if isinstance(container, str):
                container_name = container
            elif isinstance(container, int):
                container_name = self.container_prefix + str(container)
            status: str = self.__get_status(container_name)
            return ManagerResult.ok(
                message="Container status retrieved",
                data={
                    "container": container_name,
                    "status": status,
                },
            )
        except Exception as e:
            return ManagerResult.failure(
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

        Args:
            input_filename (str): Nombre del archivo YAML de entrada en configs/.
            output_filename (str): Nombre del archivo XML de salida a generar en configs/.

        Returns:
            ManagerResult: Resultado de la operación.

        Raises:
            Exception: Si ocurre un error al generar el archivo.
        """
        try:
            # Ruta al YAML de entrada dentro de configs/
            full_config_path = os.path.join(self.configs_dir, input_filename)

            if not os.path.isfile(full_config_path):
                return ManagerResult.failure(
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
            return ManagerResult.ok(
                message=f"{output_filename} generated at {self.configs_dir}",
                data={"path": self.configs_dir},
            )

        except Exception as e:
            return ManagerResult.failure(
                message="XML file could not be generated",
                error=f"{e}",
            )

    def cleanup(self) -> ManagerResult:
        """
        Detiene y elimina todos los contenedores Juice Shop y libera los recursos.

        Returns:
            ManagerResult: Resultado de la operación.

        Raises:
            Exception: Si ocurre un error durante la limpieza.
        """
        try:
            __res: ManagerResult = self.stop()
            if not __res.success:
                return __res
            return ManagerResult.ok(message="Juice Shop cleanup successful!")
        except Exception as e:
            return ManagerResult.failure(
                message="Juice Shop could not be cleaned up",
                error=str(e),
            )
