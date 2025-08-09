from __future__ import annotations
from typing import Dict, Any
import json, time
from dataclasses import dataclass, asdict
from docker.models.containers import Container

"""
Módulo de utilidades con modelos para generar respuestas estándar en JSON o diccionarios
con un formato consistente.
"""


class Status:
    """
    Constantes de estado para la clase Response.

    - **OK (str):** Operación exitosa.
    - **ERROR (str):** Error genérico.
    - **NOT_FOUND (str):** Recurso no encontrado.
    - **SUCCESS (bool):** Indicador booleano de éxito.
    - **FAILURE (bool):** Indicador booleano de fallo.
    """

    OK = "ok"
    ERROR = "error"
    NOT_FOUND = "not_found"
    SUCCESS = True
    FAILURE = False


class BaseManager:
    """
    Clase base para los Manager.
    """

    def start(self) -> ManagerResult:
        raise NotImplementedError

    def stop(self) -> ManagerResult:
        raise NotImplementedError

    def cleanup(self) -> ManagerResult:
        raise NotImplementedError


@dataclass
class ManagerResult:
    """
    Representa un resultado estándar obtenido de un Manager con un código de éxito, un mensaje
    descriptivo, error (opcional), datos adicionales (opcional) y un timestamp.

    ## Atributos
      - **success (bool):** Código de éxito.
      - **message (str):** Mensaje descriptivo.
      - **error (str, None):** Descripción del error.
      - **data (Dict[str, Any], None):** Datos extra.
      - **timestamp (str):** Timestamp
    """

    success: bool
    message: str
    error: str | None = None
    data: dict[str, Any] | None = None
    timestamp: str = time.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def ok(
        cls, message: str = "Success", data: Dict[str, Any] | None = {}
    ) -> ManagerResult:
        """
        Crea una respuesta con estado SUCCESS (True).

        Args:
            message (str, None): Mensaje descriptivo. Por defecto "Success".
            data (Dict[str, Any], None): Datos extra. Por defecto {}.

        Returns:
            ManagerResult: Instancia con status Status.SUCCESS.
        """
        return cls(success=Status.SUCCESS, message=message, data=data)

    @classmethod
    def failure(
        cls,
        message: str = "Failure",
        error: str | None = "Error",
        data: Dict[str, Any] | None = None,
    ) -> ManagerResult:
        """
        Crea una respuesta con estado FAILURE (False).

        Args:
            message (str): Mensaje descriptivo. Por defecto "Failure".
            error (str, None): Descripción del error. Por defecto "Error".
            data (Dict[str, Any], None): Datos extra. Por defecto None.

        Returns:
            ManagerResult: Instancia con status Status.SUCCESS.
        """
        return cls(success=Status.FAILURE, message=message, error=error, data=data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la ManagerResult a un diccionario.

        Returns:
            Dict[str, Any]: Estructura con las claves "success", "message", "data" y "error".
        """
        return asdict(self)


class Response:
    """
    Representa una respuesta estándar con un código de estado, un mensaje
    descriptivo y datos adicionales.

    ## Atributos
      - **status (str):** Código de estado (Status.OK, Status.ERROR, etc.).
      - **message (str):** Mensaje legible para el usuario.
      - **data (dict):** Carga útil con información adicional.
    """

    def __init__(self, status: str, message: str, data: dict = {}):
        """
        Inicializa una instancia de Response.

        Args:
            status (str): Código de estado (p.ej., Status.OK).
            message (str): Mensaje descriptivo.
            data (dict, None): Datos extra. Por defecto {}.

        Nota:
            Se usa `data or {}` para evitar que self.data quede como None
            o que varios objetos compartan la misma referencia a un dict.
        """
        self.status = status
        self.message = message
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la respuesta a un diccionario.

        Returns:
            Dict[str, Any]: Estructura con las claves "status", "message" y "data".
        """
        return {"status": self.status, "message": self.message, "data": self.data}

    def to_json(self) -> str:
        """
        Serializa la respuesta a JSON.

        Returns:
            str: Cadena JSON con la estructura de to_dict().
        """
        return json.dumps(self.to_dict())

    @classmethod
    def ok(cls, message: str = "Success", data: Dict[str, Any] = {}) -> Response:
        """
        Crea una respuesta con estado OK.

        Args:
            message (str, None): Mensaje descriptivo. Por defecto "Success".
            data (Dict[str, Any], None): Datos extra. Por defecto {}.

        Returns:
            Response: Instancia con status Status.OK.
        """
        return cls(Status.OK, message, data)

    @classmethod
    def error(
        cls, message: str = "Something went wrong", data: Dict[str, Any] = {}
    ) -> Response:
        """
        Crea una respuesta con estado ERROR.

        Args:
            message (str, None): Mensaje descriptivo. Por defecto "Something went wrong".
            data (Dict[str, Any], None): Datos extra. Por defecto {}.

        Returns:
            Response: Instancia con status Status.ERROR.
        """
        return cls(Status.ERROR, message, data)

    @classmethod
    def not_found(
        cls, message: str = "Not found", data: Dict[str, Any] = {}
    ) -> Response:
        """
        Crea una respuesta con estado NOT_FOUND.

        Args:
            message (str, None): Mensaje descriptivo. Por defecto "Not found".
            data (Dict[str, Any], None): Datos extra. Por defecto {}.

        Returns:
            Response: Instancia con status Status.NOT_FOUND.
        """
        return cls(Status.NOT_FOUND, message, data)


@dataclass
class RedisPayload:
    """
    Modelo para serializar respuestas de estado de contenedores
    que se publicarán en Redis.

    ## Atributos
      - **container (str):** Nombre del contenedor.
      - **status (str):** Estado/status del contenedor.
      - **timestamp (str):** Timestamp.
    """

    container: str | None
    status: str
    timestamp: str

    @classmethod
    def from_container(cls, container: Container) -> RedisPayload:
        """
        Construye un RedisPayload a partir de Container.

        Args:
          container (Container): Objeto contenedor de Docker.

        Returns:
          RedisPayload: Payload formateado para Redis.
        """
        return cls(
            container=container.name,
            status=container.status,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    @classmethod
    def from_dict(cls, container: dict) -> RedisPayload:
        """
        Construye un RedisPayload a partir de un dict.

        Args:
          container (dict): Diccionario con datos del contenedor de Docker [container, status].

        Returns:
          RedisPayload: Payload formateado para Redis.
        """
        return cls(
            container=container["container"],
            status=container["status"],
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la RedisPayload a un diccionario.

        Returns:
            Dict[str, Any]: Estructura con las claves "status", "message" y "data".
        """
        return asdict(self)

    def to_json(self) -> str:
        """
        Serializa la RedisPayload a JSON.

        Returns:
            str: Cadena JSON con la estructura de to_dict().
        """
        return json.dumps(self.to_dict())
