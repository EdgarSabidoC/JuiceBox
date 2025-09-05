#!/usr/bin/env python3
import os, json, yaml
from .validator import validate_str, validate_port, validate_bool, validate_ports_range
from Models import Status, ManagerResult
from importlib.resources import files
from pathlib import Path

RTB_SCHEMA = {
    "webapp_port": ("WEBAPP_PORT", validate_port),
    "memcached_port": ("MEMCACHED_PORT", validate_port),
    "network_name": ("NETWORK_NAME", validate_str),
    "rtb_dir": ("RTB_DIRECTORY", validate_str),
    "webapp_container_name": ("WEB_APP_CONTAINER_NAME", validate_str),
    "cache_container_name": ("MEMCACHED_CONTAINER_NAME", validate_str),
}

JUICESHOP_SCHEMA = {
    "juice_shop_containers_name": ("CONTAINERS_NAME", validate_str),
    "ports_range": ("PORTS_RANGE", validate_ports_range),
    "ctf_key": ("CTF_KEY", validate_str),
    "node_env": ("NODE_ENV", validate_str),
    "detach_mode": ("DETACH_MODE", validate_bool),
}


class RTBConfig:
    CONFIG_PATH = Path(str(files("JuiceBoxEngine.configs").joinpath("rootTheBox.json")))

    def __init__(self):
        # Valores por defecto
        self.webapp_port = 8888
        self.memcached_port = 11211
        self.network_name = "rootthebox_default"
        self.rtb_dir = "RootTheBox"
        self.webapp_container_name = "rootthebox-webapp-1"
        self.cache_container_name = "rootthebox-memcached-1"
        self.error = None

    def __update_if_present(self, config: dict, key: str):
        if key in config:
            json_key, validator = RTB_SCHEMA[key]
            setattr(self, key, validator(config[key], json_key))

    def load_config(self) -> ManagerResult:
        """
        Carga el JSON y aplica la config.
        """
        try:
            config_data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))
            for key in RTB_SCHEMA:
                self.__update_if_present(config_data, key)

            # Escribe JSON actualizado
            updated_data = {
                json_key: getattr(self, key)
                for key, (json_key, _) in RTB_SCHEMA.items()
            }
            self.CONFIG_PATH.write_text(
                json.dumps(updated_data, indent=4), encoding="utf-8"
            )

            return ManagerResult.ok(
                "RTB config loaded successfully", data=self.get_config()
            )
        except Exception as e:
            self.error = e
            return ManagerResult.failure("Error loading RTB config", error=str(e))

    def set_config(self, config: dict[str, str | int]) -> ManagerResult:
        """
        Aplica cambios y recarga la configuración completa.
        """
        try:
            # Carga JSON existente
            existing_data = {}
            if self.CONFIG_PATH.exists():
                existing_data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))

            # Aplica solo cambios recibidos
            for key in RTB_SCHEMA:
                json_key, validator = RTB_SCHEMA[key]
                if key in config:
                    setattr(self, key, validator(config[key], json_key))
                elif json_key in existing_data:
                    setattr(self, key, existing_data[json_key])

            # Escribe JSON actualizado
            updated_data = {
                json_key: getattr(self, key)
                for key, (json_key, _) in RTB_SCHEMA.items()
            }
            self.CONFIG_PATH.write_text(
                json.dumps(updated_data, indent=4), encoding="utf-8"
            )

            # Recarga config completa para asegurar consistencia
            return self.load_config()
        except Exception as e:
            return ManagerResult.failure("Error updating RTB config", error=str(e))

    def get_config(self) -> dict[str, str | int]:
        """
        Devuelve la configuración actual de RTB.
        """
        return {
            "webapp_port": self.webapp_port,
            "memcached_port": self.memcached_port,
            "network_name": self.network_name,
            "rtb_dir": self.rtb_dir,
            "webapp_container_name": self.webapp_container_name,
            "cache_container_name": self.cache_container_name,
        }


class JuiceShopConfig:
    CONFIG_PATH = Path(str(files("JuiceBoxEngine.configs").joinpath("juiceShop.json")))

    def __init__(self):
        self.utils_dir = Path(__file__).resolve().parent
        self.scripts_dir = self.utils_dir.parent
        self.project_root = self.scripts_dir.parent
        self.configs_dir = self.project_root / "JuiceBoxEngine" / "configs"

        # Valores por defecto
        self.juice_shop_containers_name = "owasp-juice-shop-"
        self.ports_range = [3000, 3009]
        self.ctf_key = "test"
        self.node_env = "ctf"
        self.detach_mode = True
        self.error = None

    @property
    def starting_port(self) -> int:
        return self.ports_range[0]

    @property
    def ending_port(self) -> int:
        return self.ports_range[1]

    def __update_if_present(self, config: dict, key: str):
        if key in config:
            json_key, validator = JUICESHOP_SCHEMA[key]
            setattr(self, key, validator(config[key], json_key))

    def load_config(self) -> ManagerResult:
        """
        Carga la config JSON y genera YAML.
        """
        try:
            config_data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))
            for key in JUICESHOP_SCHEMA:
                self.__update_if_present(config_data, key)

            # Escribe JSON actualizado
            updated_data = {
                json_key: getattr(self, key)
                for key, (json_key, _) in JUICESHOP_SCHEMA.items()
            }
            self.CONFIG_PATH.write_text(
                json.dumps(updated_data, indent=4), encoding="utf-8"
            )

            # Genera YAML
            yaml_result = self.__generate_yaml()
            if yaml_result["status"] == Status.ERROR:
                return ManagerResult.failure(
                    f"YAML generation failed: {yaml_result['message']}"
                )

            return ManagerResult.ok(
                "JuiceShop config loaded successfully", data=self.get_config()
            )
        except Exception as e:
            self.error = e
            return ManagerResult.failure("Error loading JuiceShop config", error=str(e))

    def set_config(self, config: dict[str, str | list[int] | bool]) -> ManagerResult:
        """
        Aplica cambios y recarga la config completa.
        """
        try:
            existing_data = {}
            if self.CONFIG_PATH.exists():
                existing_data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))

            for key in JUICESHOP_SCHEMA:
                json_key, validator = JUICESHOP_SCHEMA[key]
                if key in config:
                    setattr(self, key, validator(config[key], json_key))
                elif json_key in existing_data:
                    setattr(self, key, existing_data[json_key])

            # Escribe JSON actualizado
            updated_data = {
                json_key: getattr(self, key)
                for key, (json_key, _) in JUICESHOP_SCHEMA.items()
            }
            self.CONFIG_PATH.write_text(
                json.dumps(updated_data, indent=4), encoding="utf-8"
            )

            # Recarga config completa y genera YAML
            return self.load_config()
        except Exception as e:
            return ManagerResult.failure(
                "Error updating JuiceShop config", error=str(e)
            )

    def __generate_yaml(self, output_filename: str = "juiceShopRTBConfig.yml") -> dict:
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
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
            return {"status": Status.OK, "message": f"YAML file created at {full_path}"}
        except Exception as e:
            return {
                "status": Status.ERROR,
                "message": f"YAML file could not be created: {e}",
            }

    def get_config(self) -> dict[str, str | list[int] | bool]:
        """
        Devuelve la configuración actual de Juice Shop.
        """
        return {
            "containers_name": self.juice_shop_containers_name,
            "ports_range": self.ports_range,
            "ctf_key": self.ctf_key,
            "node_env": self.node_env,
            "detach_mode": self.detach_mode,
        }
