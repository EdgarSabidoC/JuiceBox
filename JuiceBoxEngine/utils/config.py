#!/usr/bin/env python3
import os, json, yaml
from .validator import validate_str, validate_port, validate_bool
from Models import Status
from importlib.resources import files
from pathlib import Path
from typing import Any, TypeGuard


class RTBConfig:
    CONFIG_PATH = CONFIG_PATH = Path(
        str(files("JuiceBoxEngine.configs").joinpath("rootTheBox.json"))
    )

    def __init__(self):
        # Se lee el json
        config_data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))

        # Puerto de la webapp
        self.webapp_port: int = validate_port(
            config_data.get("WEBAPP_PORT", 8888), "WEBAPP_PORT"
        )
        # Puerto del caché
        self.memcached_port: int = validate_port(
            config_data.get("MEMCACHED_PORT", 11211), "MEMCACHED_PORT"
        )
        # Nombre de la red de contenedores
        self.network_name: str = validate_str(
            config_data.get("NETWORK_NAME", "rootthebox_default"), "NETWORK_NAME"
        )
        # Directorio de RootTheBox
        self.rtb_dir: str = validate_str(
            config_data.get("RTB_DIRECTORY", "RootTheBox"), "RTB_DIRECTORY"
        )
        # Nombre del contenedor de la webapp
        self.webapp_container_name: str = validate_str(
            config_data.get("WEB_APP_CONTAINER_NAME", "rootthebox-webapp-1"),
            "WEB_APP_CONTAINER_NAME",
        )
        # Nombre del contenedore del caché
        self.cache_container_name: str = validate_str(
            config_data.get("MEMCACHED_CONTAINER_NAME", "rootthebox-memcached-1"),
            "MEMCACHED_CONTAINER_NAME",
        )

    def show_config(self) -> dict:
        return {
            "status": Status.OK,
            "config": {
                "webapp_container_name": self.webapp_container_name,
                "cache_container_name": self.cache_container_name,
                "webapp_port": self.webapp_port,
                "memcached_port": self.memcached_port,
                "rtb_dir": self.rtb_dir,
            },
        }

    def set_config(self, config: dict[str, str | int]) -> dict:
        # Se validan y actualizan los atributos
        if "webapp_port" in config and isinstance(config["webapp_port"], int):
            self.webapp_port = validate_port(config["webapp_port"], "WEBAPP_PORT")
        if "memcached_port" in config and isinstance(config["memcached_port"], int):
            self.memcached_port = validate_port(
                config["memcached_port"], "MEMCACHED_PORT"
            )
        if "network_name" in config and isinstance(config["network_name"], str):
            self.network_name = validate_str(config["network_name"], "NETWORK_NAME")
        if "rtb_dir" in config and isinstance(config["rtb_dir"], str):
            self.rtb_dir = validate_str(config["rtb_dir"], "RTB_DIRECTORY")
        if "webapp_container_name" in config and isinstance(
            config["webapp_container_name"], str
        ):
            self.webapp_container_name = validate_str(
                config["webapp_container_name"], "WEB_APP_CONTAINER_NAME"
            )
        if "cache_container_name" in config and isinstance(
            config["cache_container_name"], str
        ):
            self.cache_container_name = validate_str(
                config["cache_container_name"], "MEMCACHED_CONTAINER_NAME"
            )

        # Guardar en el archivo JSON
        updated_data = {
            "WEBAPP_PORT": self.webapp_port,
            "MEMCACHED_PORT": self.memcached_port,
            "NETWORK_NAME": self.network_name,
            "RTB_DIRECTORY": self.rtb_dir,
            "WEB_APP_CONTAINER_NAME": self.webapp_container_name,
            "MEMCACHED_CONTAINER_NAME": self.cache_container_name,
        }

        try:
            self.CONFIG_PATH.write_text(
                json.dumps(updated_data, indent=4), encoding="utf-8"
            )

            # Se actualizan los atributos en memoria
            self.__init__()
        except Exception as e:
            return {
                "status": Status.ERROR,
                "message": f"Something happend when updating config: {e}",
                "config": {},
            }
        return {
            "status": Status.OK,
            "message": "Config updated successfully",
            "config": self.show_config()["config"],
        }


class JuiceShopConfig:
    CONFIG_PATH = CONFIG_PATH = Path(
        str(files("JuiceBoxEngine.configs").joinpath("juiceShop.json"))
    )

    def __init__(self):
        # Se lee el json
        config_data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))

        # Directorio donde está este script (utils)
        self.utils_dir = os.path.dirname(os.path.abspath(__file__))
        # Directorio padre de utils (contiene 'utils/')
        self.scripts_dir = os.path.dirname(self.utils_dir)
        # Directorio padre del proyecto:
        self.project_root = os.path.dirname(self.scripts_dir)
        # Ruta absoluta a configs/
        self.configs_dir = os.path.join(self.project_root, "configs")

        # Nombre base de contenedores
        self.juice_shop_containers_name: str = validate_str(
            config_data.get("CONTAINERS_NAME", "owasp-juice-shop-"), "CONTAINERS_NAME"
        )

        # Rango de puertos como lista [inicio, fin]
        ports_range = config_data.get("PORTS_RANGE", [])
        self.starting_port, self.ending_port = self.__validate_ports_range(ports_range)

        # Clave CTF
        self.ctf_key: str = validate_str(config_data.get("CTF_KEY", ""), "CTF_KEY")

        # Entorno Node.js
        self.node_env: str = validate_str(
            config_data.get("NODE_ENV", "ctf"), "NODE_ENV"
        )

        # Modo detach
        self.detach_mode: bool = validate_bool(
            config_data.get("DETACH_MODE", True), "DETACH_MODE"
        )

        # Se genera el archivo YAML:
        self.generate_yaml()

    def __is_list_of_int(self, x: Any) -> TypeGuard[list[int]]:
        if not isinstance(x, list):
            return False
        return all(isinstance(item, int) for item in x)

    def __validate_ports_range(self, ports_range: list[int]) -> tuple[int, int]:
        ports = []
        starting_port = 3000
        ending_port: int = 3009
        # Validación de los puertos:
        if (
            isinstance(ports_range, list)
            and len(ports_range) == 2
            and all(isinstance(p, int) for p in ports_range)
        ):
            start, end = ports_range
            if start <= end:
                ports = list(range(start, end + 1))
                starting_port = start
                ending_port = end
            else:
                ports = list(range(end, start + 1))
                starting_port = end
                ending_port = start
        elif ports_range:
            raise ValueError(
                "PORTS_RANGE must be a list with two integers [start, end]"
            )
        if starting_port is not None:
            starting_port = validate_port(starting_port, "STARTING_PORT")
        if ending_port is not None:
            ending_port = validate_port(ending_port, "ENDING_PORT")
        for port in ports:
            validate_port(port, "PORT_IN_RANGE")

        return (starting_port, ending_port)

    def show_config(self) -> dict:
        return {
            "status": Status.OK,
            "config": {
                "containers_name": self.juice_shop_containers_name,
                "ports_range": [self.starting_port, self.ending_port],
                "ctf_key": self.ctf_key,
                "node_env": self.node_env,
                "detach_mode": self.detach_mode,
            },
        }

    def set_config(self, config: dict[str, str | list[int]]) -> dict:
        if "CONTAINERS_NAME" in config and isinstance(config["CONTAINERS_NAME"], str):
            self.juice_shop_containers_name = validate_str(
                config["CONTAINERS_NAME"], "CONTAINERS_NAME"
            )
        if "PORTS_RANGE" in config and self.__is_list_of_int(config["PORTS_RANGE"]):
            self.starting_port, self.ending_port = self.__validate_ports_range(
                config["PORTS_RANGE"]
            )
        if "CTF_KEY" in config and isinstance(config["CTF_KEY"], str):
            self.network_name = validate_str(config["CTF_KEY"], "CTF_KEY")
        if "NODE_ENV" in config and isinstance(config["NODE_ENV"], str):
            self.rtb_dir = validate_str(config["NODE_ENV"], "NODE_ENV")
        if "DETACH_MODE" in config and isinstance(config["DETACH_MODE"], bool):
            self.rtb_dir = validate_bool(config["DETACH_MODE"], "DETACH_MODE")

        # Guardar en el archivo JSON
        updated_data = {
            "CONTAINERS_NAME": self.juice_shop_containers_name,
            "PORTS_RANGE": [self.starting_port, self.ending_port],
            "CTF_KEY": self.ctf_key,
            "NODE_ENV": self.node_env,
            "DETACH_MODE": self.detach_mode,
        }
        try:
            self.CONFIG_PATH.write_text(
                json.dumps(updated_data, indent=4), encoding="utf-8"
            )

            # Se actualizan los atributos en memoria
            self.__init__()
        except Exception as e:
            return {
                "status": Status.ERROR,
                "message": f"Something happend when updating config: {e}",
                "config": {},
            }
        return {
            "status": Status.OK,
            "message": "Config updated successfully",
            "config": self.show_config()["config"],
        }

    def generate_yaml(self, output_filename: str = "juiceShopRTBConfig.yml") -> dict:
        """
        Crea un archivo YAML en configs/ con los campos:
          ctfFramework, juiceShopUrl, ctfKey, countryMapping,
          insertHints, insertHintUrls, insertHintSnippets
        """
        data = {
            "ctfFramework": "RootTheBox",
            "juiceShopUrl": "https://juice-shop.herokuapp.com",
            "ctfKey": self.ctf_key,
            "countryMapping": "https://raw.githubusercontent.com/juice-shop/juice-shop/master/config/fbctf.yml",
            "insertHints": "free",
            "insertHintUrls": "free",
            "insertHintSnippets": "free",
        }
        full_path = os.path.join(self.configs_dir, output_filename)

        # Se genera el YAML
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
            return {
                "status": Status.OK,
                "message": f"YAML file has been created {self.configs_dir}",
            }
        except Exception as e:
            return {
                "status": Status.ERROR,
                "message": f"YAML file could not be created: {e}",
            }
