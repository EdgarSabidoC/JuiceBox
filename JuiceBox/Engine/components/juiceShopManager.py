#!/usr/bin/env python3
"""
juiceShopManager.py

Clase JuiceBoxManager que carga configuración desde JuiceShopConfig
y gestiona los contenedores via Docker SDK.
"""

import os, atexit, shutil, time, requests, yaml
from docker import errors
from ..utils import JuiceShopConfig
from ..utils import validate_container
from Models import ManagerResult, BaseManager
from docker import DockerClient
from docker.models.containers import Container
from docker.models.networks import Network


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
    Clase que administra instancias de OWASP Juice Shop en contenedores Docker.

    ## Operaciones
    - **start:** Inicia un nuevo contenedor de Juice Shop en un puerto disponible.
    - **stop:** Detiene y elimina todos los contenedores de Juice Shop.
    - **stop_container:** Detiene y elimina un contenedor específico de Juice Shop.
    - **status:** Obtiene el estado de un contenedor específico de Juice Shop.
    - **show_config:** Muestra la configuración actual de Juice Shop.
    - **generate_rtb_config:** Genera el archivo XML de configuración para Root The Box.
    - **cleanup:** Detiene y elimina todos los contenedores de Juice Shop y libera los recursos.
    """

    def __init__(
        self, config: JuiceShopConfig, docker_client: DockerClient | None = None
    ) -> None:
        """
        Inicializa el gestor de Juice Shop con la configuración dada.

        Args:
            config (JuiceShopConfig): Configuración para Juice Shop.
            docker_client (DockerClient | None): Cliente Docker opcional.
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
        # Directorio padre del script
        self.components_dir = os.path.dirname(self.script_dir)
        # Directorio de la carpeta raíz del proyecto
        self.project_root = os.path.abspath(os.path.join(self.script_dir, "../../.."))
        # Directorio de RootTheBox/missions/
        self.missions_dir = os.path.abspath(
            os.path.join(self.project_root, "RootTheBox/missions/")
        )
        # Ruta absoluta a configs/
        self.configs_dir = os.path.join(self.components_dir, "configs")

        self.image = "bkimminich/juice-shop:latest"

        atexit.register(self.cleanup)

    @property
    def container_prefix(self) -> str:
        """
        Prefijo para los nombres de los contenedores de Juice Shop.
        """
        return self.config.containers_name

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
    def lifespan(self) -> int:
        """
        Tiempo de vida de los contenedores de la Juice Shop en minutos.
        """
        return self.config.lifespan

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

    def get_containers(self) -> list[str]:
        """
        Obtiene la lista de contenedores de la configuración actual de la Juice Shop.

        Returns:
          (list[str]): Lista con los nombres de los contenedores
        """
        __containers: list[str] = []
        for port in range(self.starting_port, self.ending_port + 1):
            __container: str = self.container_prefix + str(port)
            __containers.append(__container)
        return __containers

    def __get_available_port(self) -> tuple[int, str]:
        """
        Obtiene un puerto disponible.

        Returns:
            tuple[int, "available" | "not available"]: Puerto y disponibilidad.
        """
        for port in range(self.starting_port, self.ending_port + 1):
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
        """
        Valida si un puerto está dentro del rango de puertos del Juice Shop Manager.

        Returns:
          bool: True si el puerto está dentro del rango, en otro caso, False.
        """
        return port in range(self.starting_port, self.ending_port + 1)

    def start(self) -> ManagerResult:
        """
        Inicia un contenedor de Juice Shop.

        Returns:
            ManagerResult: Resultado de la operación.
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
                labels={"lifespan": str(self.lifespan), "program": "JS"},
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
        """
        # Destruye todos los contenedores de la JuiceShop
        containers_results: list[ManagerResult] = []
        overall_ok = True
        for port in range(self.starting_port, self.ending_port + 1):
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
        """
        return ManagerResult.ok(
            message="Juice Shop configuration retrieved",
            data={
                "config": {
                    "container_prefix": self.container_prefix,
                    "ports_range": self.ports_range,
                    "lifespan": self.lifespan,
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
        """
        try:
            container = self.__docker_client.containers.get(container_name)
            return container.status
        except errors.NotFound:
            return "not_found"

    def __get_port(self, container_name: str) -> int:
        """
        Obtiene el puerto mapeado de un contenedor de Juice Shop.

        Args:
            container_name (str): Nombre del contenedor.

        Returns:
            int: Puerto asignado o -1 si no tiene.
        """
        try:
            container = self.__docker_client.containers.get(container_name)
            ports = container.attrs["NetworkSettings"]["Ports"]
            # ejemplo: {'3000/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '3001'}]}
            bindings = ports.get("3000/tcp")
            if bindings and len(bindings) > 0:
                return int(bindings[0]["HostPort"])
            return -1
        except errors.NotFound:
            return -1
        except Exception as e:
            raise RuntimeError(f"Error getting port for {container_name}: {e}")

    def container_status(self, container: str | int) -> ManagerResult:
        """
        Obtiene el estado actual de un contenedor de la Juice Shop.
        Args:
            container (str | int): Nombre o puerto del contenedor de Docker.

        Returns:
            ManagerResult: Resultado de la operación.
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

    def status(self) -> ManagerResult:
        """
        Obtiene el estado actual de los contenedores de Juice Shop.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        containers_results: list[ManagerResult] = []
        overall_ok = True

        for i in range(self.starting_port, self.ending_port + 1):
            container_name = f"{self.container_prefix}{i}"
            try:
                __status: str = self.__get_status(container_name)
                __port: int = self.__get_port(container_name)
                _data: dict[str, str | int] = {
                    "container": container_name,
                    "status": __status,
                    "port": __port,
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

        __data: dict[str, list[dict]] = {
            "containers": [r.to_dict() for r in containers_results]
        }

        if overall_ok:
            return ManagerResult.ok(
                message="Success at retrieving Juice Shop containers' statuses",
                data=__data,
            )
        else:
            return ManagerResult.failure(
                message="Failure at retrieving some Juice Shop containers' statuses",
                error="Some containers statuses could not be retrieved",
                data=__data,
            )

    def __wait_for_a_juice_shop(self, url: str, timeout=60):
        """
            Espera a que una instancia de Juice Shop esté disponible en la URL especificada.

        Args:
            url (str): URL de la instancia de Juice Shop a verificar.
            timeout (int, opcional): Tiempo máximo en segundos a esperar.
                                     Por defecto es 60.

        Returns:
            str: La URL válida de la instancia de Juice Shop que respondió correctamente.
        """
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    return url
            except requests.exceptions.RequestException:
                continue  # Si aún no responde
            time.sleep(2)  # retry tras revisar todos
        raise TimeoutError(
            f"There was no response from the services in {timeout} seconds"
        )

    def __validate_js_container(
        self, network_name: str, client: DockerClient
    ) -> tuple[str, str | None]:
        """
        Valida un contenedor de OWASP Juice Shop para obtener las misiones del CTF.

        Args:
            network_name (str): Nombre de la red.
            client (DockerClient): Cliente Docker.

        Returns:
            (tuple[str, str | None]): URL válida del contenedor de la OWASP Juice Shop y el nombre del contenedor temporal (en caso de que exista o None).
        """
        # Intentar URL remota primero
        remote_url = "https://juice-shop.herokuapp.com"
        js_container: Container | None = None
        valid_url: str = ""
        try:
            valid_url = self.__wait_for_a_juice_shop(remote_url, timeout=32)
        except TimeoutError:
            # Levanta un contenedor temporal en la red interna de Docker si la remota no responde
            try:
                js_container = client.containers.run(
                    image="bkimminich/juice-shop",
                    name="juice-shop-temp",
                    network=network_name,
                    detach=True,
                )
                valid_url = "http://juice-shop-temp:3000"
                time.sleep(90)
            except Exception:
                if js_container is not None:
                    js_container.stop()
                    js_container.remove()
        if js_container:
            return (valid_url, js_container.name)
        return (valid_url, None)

    def __write_url_in_yaml(self, url: str, full_config_path: str) -> None:
        """
        Escribe una URL en un archivo YAML con el campo `juiceShopUrl`.

        Args:
            url (str): URL validada que será escrita en el YAML.
            full_config_path (str): Ruta absoluta al archivo YAML de configuración.
        """
        with open(full_config_path, "r") as f:
            cfg = yaml.safe_load(f) or {}
        cfg["juiceShopUrl"] = url  # Se actualiza la URL
        with open(full_config_path, "w") as f:
            yaml.safe_dump(cfg, f)

    def __run_js_cli_container(
        self,
        output_filename: str,
        full_config_path: str,
        network_name: str,
        docker_net: Network,
        client: DockerClient,
    ) -> None:
        """
        Corre un contenedor de Docker con las herramientas CLI de OWASP Juice Shop CTF para generar las misiones.

        Args:
            output_filename (str): Nombre del archivo de salida.
            full_config_path (str): Ruta absoluta al archivo de configuración.
            network_name (str): Nombre de la red de contenedores de Docker.
            docker_net (Network): Red de Docker.
            client (DockerClient): Cliente Docker.
        """
        try:
            client.containers.run(
                image="bkimminich/juice-shop-ctf",
                command=[
                    "--config",
                    os.path.basename(full_config_path),
                    "--output",
                    output_filename,
                ],
                volumes={self.configs_dir: {"bind": "/data", "mode": "rw"}},
                working_dir="/data",
                network=network_name,
                tty=True,
                stdin_open=True,
                remove=True,
            )
        except Exception as e:
            print(f"Error en CLI CTF: {e}")
        finally:
            # Elimina la red si no tiene contenedores
            if docker_net is not None:
                try:
                    docker_net.reload()
                    if not docker_net.containers:
                        docker_net.remove()
                except Exception:
                    pass

    def __move_XML_file(self, output_filename: str) -> ManagerResult:
        """
        Mueve el archivo XML generado a RootTheBox/missions/.

        Args:
            output_filename (str): Nombre del archivo de salida.

        Returns:
            ManagerResult: Resultado de la operación.
        """
        output_path = os.path.join(self.configs_dir, output_filename)
        if os.path.isfile(output_path):
            dest_path = os.path.join(self.missions_dir, output_filename)
            if os.path.isfile(dest_path):
                os.remove(dest_path)
            shutil.move(output_path, dest_path)
            return ManagerResult.ok(
                message=f"{output_filename} file saved in {self.missions_dir}",
                data={"path": self.missions_dir},
            )
        else:
            return ManagerResult.failure(
                message=f"{output_filename} couldn't be generated",
                error="Non-existent file",
            )

    def generate_rtb_config(
        self, input_filename="juiceShopRTBConfig.yml", output_filename="missions.xml"
    ) -> ManagerResult:
        """
        Genera un archvivo de misiones de OWASP Juice Shop para un CTF.

        Args:
            input_filename (str, optional): Nombre del archivo de entrada. Predeterminado: "juiceShopRTBConfig.yml".
            output_filename (str, optional): Nombre del archivo de salida. Predeterminado: "missions.xml".

        Returns:
            ManagerResult: Resultado de la operación.
        """
        js_container: str | None = None
        try:
            full_config_path = os.path.join(self.configs_dir, input_filename)
            if not os.path.isfile(full_config_path):
                return ManagerResult.failure(
                    message="YAML file not found", error=full_config_path
                )

            client: DockerClient = self.__docker_client
            network_name: str = "juice-net"

            # Crea la red Docker si no existe
            __net: Network
            try:
                __net = client.networks.get(network_name)
            except errors.NotFound:
                __net = client.networks.create(network_name)

            # Prueba un contenedor de la Juice Shop remoto o uno temporal
            valid_url, js_container = self.__validate_js_container(
                network_name=network_name, client=client
            )

            # Reescribe el YAML con la URL válida
            self.__write_url_in_yaml(url=valid_url, full_config_path=full_config_path)

            # Ejecuta el CLI juice-shop-ctf
            self.__run_js_cli_container(
                output_filename=output_filename,
                full_config_path=full_config_path,
                network_name=network_name,
                docker_net=__net,
                client=client,
            )

            # Mueve el archivo XML generado a missions/
            return self.__move_XML_file(output_filename=output_filename)

        except Exception as e:
            return ManagerResult.failure(
                message="Error while generating XML file", error=str(e)
            )
        finally:
            # Limpia el contenedor temporal siempre
            if js_container is not None:
                try:
                    container: Container = self.__docker_client.containers.get(
                        js_container
                    )
                    container.stop()
                    container.remove()
                except Exception:
                    pass

    def cleanup(self) -> ManagerResult:
        """
        Detiene y elimina todos los contenedores Juice Shop y libera los recursos.

        Returns:
            ManagerResult: Resultado de la operación.
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
