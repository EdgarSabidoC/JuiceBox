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

JS_CONF_PATH = "configs/juiceShop.json"
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

    def __get_available_port(self) -> tuple:
        for port in self.ports_range:
            __container: str = self.container_prefix + str(port)
            # Se verifica que no exista el contenedor
            if not validate_container(self.client, __container):
                return (port, "available")
        return (1, "not available")

    def is_valid_port(self, port: int) -> bool:
        return port in self.ports_range

    def run_container(self) -> dict:
        __container: str = ""
        __port: int
        try:
            __port, __port_status = self.__get_available_port()  # Se obtiene el puerto
            if __port_status != "available":
                return {"status": "error", "message": "No available ports"}
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
            # Devolver success con el nombre del contenedor
            return {
                "status": "ok",
                "container": __container,
                "message": "Container has been created and now is running",
            }
        except Exception as e:
            # Devolver error con mensaje
            return {"status": "error", "container": __container, "message": str(e)}

    def kill_container(self, container: Union[str, int]) -> dict[str, str]:
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
                return {
                    "container": __container,
                    "status": "ok",
                    "message": "Container has been stopped and removed from system",
                }
            else:
                # No existe el contenedor
                return {
                    "container": __container,
                    "status": "not_found",
                    "message": f"Container not found {__container}",
                }
        except Exception as e:
            return {"container": __container, "status": "error", "message": str(e)}

    def kill_all(self) -> dict:
        # Destruye todos los contenedores de la JuiceShop
        results = []
        overall_ok = True
        for port in self.ports_range:
            res = self.kill_container(self.container_prefix + str(port))

            if res["status"] != "ok" and res["status"] != "not_found":
                overall_ok = False
            elif res["status"] == "ok":
                results.append(res)
        if not results:
            # Si results está vacío
            return {
                "status": "ok" if overall_ok else "error",
                "results": results,
                "message": "There are no Juice Shop running containers",
            }
        return {"status": "ok" if overall_ok else "error", "results": results}

    def show_config(self) -> dict:
        return {
            "status": "ok",
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

    def __is_running(self, container_name: str) -> bool:
        try:
            container = self.client.containers.get(container_name)
            return container.status == "running"
        except errors.NotFound:
            return False

    def status(self, container: Union[int, str]) -> dict[str, Union[str, bool]]:
        __container: str = ""
        try:
            if isinstance(container, str):
                __container = container
            elif isinstance(container, int):
                __container = self.container_prefix + str(container)
            running = self.__is_running(__container)
            if not running:
                return {
                    "container": __container,
                    "status": "error",
                    "running": False,
                    "message": f"Container is not running: {__container}",
                }
            else:
                return {
                    "container": __container,
                    "status": "ok",
                    "running": True,
                    "message": "Container is running",
                }
        except Exception as e:
            return {
                "container": __container,
                "status": "error",
                "running": False,
                "message": str(e),
            }

    def generate_rtb_config(
        self,
        input_filename: str = "juiceShopRTBConfig.yml",
        output_filename: str = "missions.xml",
    ) -> dict:
        """
        Lanza el contenedor juice-shop-ctf y genera el archivo XML de configuración para Root The Box en configs/.
        Es equivalente a:
          `docker run -ti --rm -v $(pwd):/data bkimminich/juice-shop-ctf --config juiceShopRTBConfig.yml --output missions.xml`
        """
        try:
            # Ruta al YAML de entrada dentro de configs/
            full_config_path = os.path.join(self.configs_dir, input_filename)

            if not os.path.isfile(full_config_path):
                return {
                    "status": "error",
                    "message": f"YAML file not found: {full_config_path}",
                }

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

            return {
                "status": "ok",
                "message": f"{output_filename} generated at {self.configs_dir}",
            }

        except Exception as e:
            return {"status": "error", "message": f"No se pudo generar XML: {e}"}

    def cleanup(self) -> None:
        """
        Cierra la conexión al Docker client para liberar sockets/tokens.
        """
        self.kill_all()
        self.client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="juiceShopManager.py",
        description=f"""
{LOGO}
Manage Docker containers for the Juice Shop: run, kill, status, config.
        """,
        epilog=f"""
\t\t    Developed by: {DEVELOPER}
\t\t         github.com/{GITHUB_USER}
        """,
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-r", "--run", action="store_true", help="Run the Juice Shop container."
    )
    parser.add_argument("-p", "--port", help="Port for the container.", type=int)
    parser.add_argument(
        "-n",
        "--name",
        help="Name of the container.",
        type=str,
    )
    parser.add_argument(
        "-a", "--kill-all", action="store_true", help="Stop and remove the containers."
    )
    parser.add_argument(
        "-k",
        "--kill",
        action="store_true",
        help="Stop and remove a specific container. It needs the command [-p/--port | -n/--name].",
    )
    parser.add_argument(
        "-c",
        "--show-config",
        action="store_true",
        help="Shows the configuration for the Juice Shop containers.",
    )
    parser.add_argument(
        "-s",
        "--status",
        action="store_true",
        help="Shows if the Juice Shop container is running. It needs the command [-p/--port | -n/--name].",
    )
    parser.add_argument(
        "-x",
        "--generate-xml",
        action="store_true",
        help="Generates the XML file for Root The Box.",
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

    # Se valida que --port o --name se le pase a los comandos --kill e --is-running:
    if (args.kill or args.status) and (args.port is None and args.name is None):
        result = {
            "status": "error",
            "message": "Argument [-p/--port | -n/--name] is required when using [-k/--kill | -i/--is-running]",
        }
        # print(json.dumps(result))
        sys.exit(1)

    js_config = JuiceShopConfig(JS_CONF_PATH)
    js = JuiceShopManager(js_config)

    # Se valida que el puerto de --port sea válido:
    if args.port and not js.is_valid_port(args.port):
        result = {
            "status": "error",
            "message": f"Argument [-p/--port] should be in range [{js.starting_port},{js.ending_port}]",
        }
        # print(json.dumps(result))
        sys.exit(1)

    if args.show_config:
        result = js.show_config()
    elif args.run:
        result = js.run_container()
    elif args.generate_xml:
        result = js.generate_rtb_config()
    elif args.kill:
        if args.port:
            result = js.kill_container(args.port)
        elif args.name:
            result = js.kill_container(args.name)
    elif args.kill_all:
        result = js.kill_all()
    elif args.status:
        if args.port:
            result = js.status(args.port)
        elif args.name:
            result = js.status(args.name)

    # print(json.dumps(result))

    sys.exit(0 if result["status"] == "ok" else 1)
