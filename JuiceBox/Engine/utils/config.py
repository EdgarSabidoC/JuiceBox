import json, yaml
from .validator import (
    validate_str,
    validate_port,
    validate_bool,
    validate_ports_range,
    validate_int,
)
from Models import Status, ManagerResult
from importlib.resources import files
from pathlib import Path

RTB_SCHEMA = {
    "webapp_port": ("WEBAPP_PORT", validate_port),
    "memcached_port": ("MEMCACHED_PORT", validate_port),
    "network_name": ("NETWORK_NAME", validate_str),
    "webapp_container_name": ("WEB_APP_CONTAINER_NAME", validate_str),
    "cache_container_name": ("MEMCACHED_CONTAINER_NAME", validate_str),
}

JS_SCHEMA = {
    "containers_name": ("CONTAINERS_NAME", validate_str),
    "ports_range": ("PORTS_RANGE", validate_ports_range),
    "lifespan": ("LIFESPAN", validate_int),
    "ctf_key": ("CTF_KEY", validate_str),
    "node_env": ("NODE_ENV", validate_str),
    "detach_mode": ("DETACH_MODE", validate_bool),
}


class RTBConfig:
    CONFIG_PATH = Path(str(files("Engine.configs").joinpath("rootTheBox.json")))

    def __init__(self) -> None:
        """
        Inicializa la configuración de RootTheBox con valores por defecto.s
        """
        # Valores por defecto
        self.webapp_port: int = 8888
        self.memcached_port: int = 11211
        self.network_name: str = "rootthebox_default"
        self.webapp_container_name: str = "rootthebox-webapp-1"
        self.cache_container_name: str = "rootthebox-memcached-1"
        self.loaded: bool = False
        self.error = None

    def __update_if_present(self, config: dict, key: str) -> None:
        """
        Actualiza el atributo si la clave correspondiente existe en el diccionario de configuración.

        Args:
            config (dict): Diccionario con la configuración cargada desde JSON.
            key (str): Clave interna de la configuración a actualizar.
        """
        json_key, validator = RTB_SCHEMA[key]
        if json_key in config:
            value = validator(config[json_key], json_key)
            setattr(self, key, value)

    def __restart_state(self) -> None:
        """
        Reinicia el estado de carga de la configuración y error.
        """
        self.loaded = False
        self.error = None

    def load_config(self) -> ManagerResult:
        """
        Carga la configuración desde el JSON. Si no existe, lo crea con valores por defecto.

        Returns:
            (ManagerResult): Estado de éxito o fallo de la operación.
        """
        try:
            self.__restart_state()

            # Crea archivo JSON si no existe
            if not self.CONFIG_PATH.exists():
                updated_data = {
                    json_key: getattr(self, key)
                    for key, (json_key, _) in RTB_SCHEMA.items()
                }
                self.CONFIG_PATH.write_text(
                    json.dumps(updated_data, indent=4), encoding="utf-8"
                )
                config_data = updated_data
            else:
                config_data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))

            # Aplica configuración desde JSON
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

            self.loaded = True
            return ManagerResult.ok(
                "RTB config loaded successfully", data=self.get_config()
            )
        except Exception as e:
            self.error = e
            return ManagerResult.failure("Error loading RTB config", error=str(e))

    def set_config(self, config: dict[str, str | int]) -> ManagerResult:
        """
        Aplica cambios parciales o completos a la configuración y recarga el archivo JSON.

        Args:
            config (dict[str, str | int]): Diccionario con valores a actualizar.

        Returns:
            (ManagerResult): Estado de éxito o fallo de la operación.
        """
        try:
            self.__restart_state()
            existing_data = {}
            if self.CONFIG_PATH.exists():
                existing_data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))

            # Aplica cambios
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

            return self.load_config()
        except Exception as e:
            return ManagerResult.failure("Error updating RTB config", error=str(e))

    def get_config(self) -> dict[str, str | int]:
        """
        Devuelve un diccionario con la configuración actual de RootTheBox.

        Returns:
            (dict[str, str | int]): Configuración actual de RTB.
        """
        return {
            "webapp_port": self.webapp_port,
            "memcached_port": self.memcached_port,
            "network_name": self.network_name,
            "webapp_container_name": self.webapp_container_name,
            "cache_container_name": self.cache_container_name,
        }


class JuiceShopConfig:
    CONFIG_PATH = Path(str(files("Engine.configs").joinpath("juiceShop.json")))

    def __init__(self) -> None:
        """
        Inicializa la configuración de JuiceShop con valores por defecto.
        """
        self.utils_dir = Path(__file__).resolve().parent
        self.scripts_dir = self.utils_dir.parent
        self.project_root = self.scripts_dir.parent
        self.configs_dir = self.project_root / "Engine" / "configs"

        # Valores por defecto
        self.containers_name: str = "owasp-juice-shop-"
        self.ports_range: list[int] = [3000, 3009]
        self.ctf_key: str = "test"
        self.node_env: str = "ctf"
        self.lifespan: int = 180
        self.detach_mode: bool = True
        self.loaded: bool = False
        self.error = None

    @property
    def starting_port(self) -> int:
        """
        Puerto inicial del rango de puertos de JuiceShop.

        Returns:
            (int): Puerto inicial.
        """
        return self.ports_range[0]

    @property
    def ending_port(self) -> int:
        """
        Puerto final del rango de puertos de JuiceShop.

        Returns:
            (int): Puerto final.
        """
        return self.ports_range[1]

    def __update_if_present(self, config: dict, key: str) -> None:
        """
        Actualiza el atributo si la clave correspondiente existe en el diccionario de configuración.

        Args:
            config (dict): Diccionario con la configuración cargada desde JSON.
            key (str): Clave interna de la configuración a actualizar.
        """
        json_key, validator = JS_SCHEMA[key]
        if json_key in config:
            setattr(self, key, validator(config[json_key], json_key))

    def __restart_state(self) -> None:
        """
        Reinicia el estado de carga y error de JuiceShop.
        """
        self.loaded = False
        self.error = None

    def load_config(self) -> ManagerResult:
        """
        Carga la configuración desde JSON, aplica validaciones y genera el archivo YAML.
        Si no existe el JSON, se crea automáticamente con valores por defecto.

        Returns:
            (ManagerResult): Estado de éxito o fallo de la operación.
        """
        try:
            self.__restart_state()

            # Crea archivo JSON si no existe
            if not self.CONFIG_PATH.exists():
                updated_data = {
                    json_key: getattr(self, key)
                    for key, (json_key, _) in JS_SCHEMA.items()
                }
                self.CONFIG_PATH.write_text(
                    json.dumps(updated_data, indent=4), encoding="utf-8"
                )
                config_data = updated_data
            else:
                config_data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))

            # Aplica configuración desde JSON
            for key in JS_SCHEMA:
                self.__update_if_present(config_data, key)

            # Escribe JSON actualizado
            updated_data = {
                json_key: getattr(self, key) for key, (json_key, _) in JS_SCHEMA.items()
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

            self.loaded = True
            return ManagerResult.ok(
                "JuiceShop config loaded successfully", data=self.get_config()
            )
        except Exception as e:
            self.error = e
            return ManagerResult.failure("Error loading JuiceShop config", error=str(e))

    def set_config(
        self, config: dict[str, str | int | list[int] | bool]
    ) -> ManagerResult:
        """
        Aplica cambios a la configuración y recarga JSON y YAML.

        Args:
            config (dict[str, str | int | list[int] | bool]): Diccionario con valores a actualizar.

        Returns:
            (ManagerResult): Estado de éxito o fallo de la operación.
        """
        try:
            self.__restart_state()
            existing_data = {}
            if self.CONFIG_PATH.exists():
                existing_data = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))

            # Aplica cambios
            for key in JS_SCHEMA:
                json_key, validator = JS_SCHEMA[key]
                if key in config:
                    setattr(self, key, validator(config[key], json_key))
                elif json_key in existing_data:
                    setattr(self, key, existing_data[json_key])

            # Escribe JSON actualizado
            updated_data = {
                json_key: getattr(self, key) for key, (json_key, _) in JS_SCHEMA.items()
            }
            self.CONFIG_PATH.write_text(
                json.dumps(updated_data, indent=4), encoding="utf-8"
            )

            return self.load_config()
        except Exception as e:
            return ManagerResult.failure("Error updating JS config", error=str(e))

    def __generate_yaml(self, output_filename: str = "juiceShopRTBConfig.yml") -> dict:
        """
        Genera el archivo YAML para JuiceShop a partir de la configuración actual.

        Args:
            output_filename (str): Nombre del archivo YAML a generar. Default es "juiceShopRTBConfig.yml".

        Returns:
            (dict): Diccionario con estado y mensaje de la operación.
        """
        data = {
            "ctfFramework": "RootTheBox",
            "ctfKey": self.ctf_key,
            "countryMapping": "https://raw.githubusercontent.com/juice-shop/juice-shop/master/config/fbctf.yml",
            "insertHints": "free",
            "insertHintUrls": "free",
            "insertHintSnippets": "free",
            "juiceShopUrl": "",
        }
        self.configs_dir.mkdir(
            parents=True, exist_ok=True
        )  # Se asegura que el directorio exista
        full_path = (
            self.configs_dir / output_filename
        )  # Directorio completo del archivo
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
            return {"status": Status.OK, "message": f"YAML file created at {full_path}"}
        except Exception as e:
            return {
                "status": Status.ERROR,
                "message": f"YAML file could not be created: {e}",
            }

    def get_config(self) -> dict[str, str | int | list[int] | bool]:
        """
        Devuelve un diccionario con la configuración actual de JuiceShop.

        Returns:
            (dict[str, str | int | list[int] | bool]): Configuración actual de JuiceShop.
        """
        return {
            "containers_name": self.containers_name,
            "ports_range": self.ports_range,
            "lifespan": self.lifespan,
            "ctf_key": self.ctf_key,
            "node_env": self.node_env,
            "detach_mode": self.detach_mode,
        }
