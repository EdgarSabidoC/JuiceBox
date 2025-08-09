#!/usr/bin/env python3
import os, json, yaml
from .validator import validate_str, validate_port, validate_bool
from importlib.resources import files


class RTBConfig:
    def __init__(self):
        # Se lee el json
        config_data = json.loads(
            files("JuiceBoxEngine.configs")
            .joinpath("rootTheBox.json")
            .read_text(encoding="utf-8")
        )

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
            config_data.get("RTB_DIRECTORY", "../RootTheBox"), "RTB_DIRECTORY"
        )
        # Nombre del contenedor de la webapp
        self.webapp_container_name: str = validate_str(
            config_data.get("WEB_APP_CONTAINER_NAME", "rootthebox-webapp"),
            "WEB_APP_CONTAINER_NAME",
        )
        # Nombre del contenedore del caché
        self.cache_container_name: str = validate_str(
            config_data.get("MEMCACHED_CONTAINER_NAME", "rootthebox-memcached"),
            "MEMCACHED_CONTAINER_NAME",
        )

    def show_config(self) -> dict:
        return {
            "status": "ok",
            "config": {
                "webapp_container_name": self.webapp_container_name,
                "cache_container_name": self.cache_container_name,
                "webapp_port": self.webapp_port,
                "memcached_port": self.memcached_port,
                "rtb_dir": self.rtb_dir,
            },
        }


class JuiceShopConfig:
    def __init__(self):
        # Se lee el json
        config_data = json.loads(
            files("JuiceBoxEngine.configs")
            .joinpath("juiceShop.json")
            .read_text(encoding="utf-8")
        )
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
        self.ports = []
        self.starting_port: int
        self.ending_port: int
        # Validación de los puertos:
        if (
            isinstance(ports_range, list)
            and len(ports_range) == 2
            and all(isinstance(p, int) for p in ports_range)
        ):
            start, end = ports_range
            if start <= end:
                self.ports = list(range(start, end + 1))
                self.starting_port = start
                self.ending_port = end
            else:
                self.ports = list(range(end, start + 1))
                self.starting_port = end
                self.ending_port = start
        elif ports_range:
            raise ValueError(
                "PORTS_RANGE must be a list with two integers [start, end]"
            )
        if self.starting_port is not None:
            self.starting_port = validate_port(self.starting_port, "STARTING_PORT")
        if self.ending_port is not None:
            self.ending_port = validate_port(self.ending_port, "ENDING_PORT")
        for port in self.ports:
            validate_port(port, "PORT_IN_RANGE")

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

    def show_config(self) -> dict:
        return {
            "status": "ok",
            "juice_shop_containers_name": self.juice_shop_containers_name,
            "starting_port": self.starting_port,
            "ending_port": self.ending_port,
            "ports": self.ports,
            "ctf_key": self.ctf_key,
            "node_env": self.node_env,
            "detach_mode": self.detach_mode,
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
                "status": "ok",
                "message": f"YAML file has been created {self.configs_dir}",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"YAML file could not be created: {e}",
            }
