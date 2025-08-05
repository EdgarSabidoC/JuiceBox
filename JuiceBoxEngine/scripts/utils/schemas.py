from typing import Optional, Literal, Union, List, Dict, Any
import json

"""
Módulo de utilidades para generar respuestas estándar en JSON o diccionario
con un formato consistente: status, message y datos opcionales.
"""


class Status:
    """
    Constantes de estado para la clase Response.

    Atributos:
        OK (str): Operación exitosa.
        ERROR (str): Error genérico.
        NOT_FOUND (str): Recurso no encontrado.
    """

    OK = "ok"
    ERROR = "error"
    NOT_FOUND = "not_found"


class Response:
    """
    Representa una respuesta estándar con un código de estado, un mensaje
    descriptivo y datos adicionales.

    Atributos:
        status (str): Código de estado (Status.OK, Status.ERROR, etc.).
        message (str): Mensaje legible para el usuario.
        data (dict): Carga útil con información adicional.
    """

    def __init__(self, status: str, message: str, data: dict = {}):
        """
        Inicializa una instancia de Response.

        Args:
            status (str): Código de estado (p.ej., Status.OK).
            message (str): Mensaje descriptivo.
            data (dict, opcional): Datos extra. Por defecto {}.

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
    def ok(cls, message: str = "Success", data: Dict[str, Any] = {}) -> "Response":
        """
        Crea una respuesta con estado OK.

        Args:
            message (str, opcional): Mensaje descriptivo. Por defecto "Success".
            data (Dict[str, Any], opcional): Datos extra. Por defecto {}.

        Returns:
            Response: Instancia con status Status.OK.
        """
        return cls(Status.OK, message, data)

    @classmethod
    def error(
        cls, message: str = "Something went wrong", data: Dict[str, Any] = {}
    ) -> "Response":
        """
        Crea una respuesta con estado ERROR.

        Args:
            message (str, opcional): Mensaje descriptivo. Por defecto "Something went wrong".
            data (Dict[str, Any], opcional): Datos extra. Por defecto {}.

        Returns:
            Response: Instancia con status Status.ERROR.
        """
        return cls(Status.ERROR, message, data)

    @classmethod
    def not_found(
        cls, message: str = "Not found", data: Dict[str, Any] = {}
    ) -> "Response":
        """
        Crea una respuesta con estado NOT_FOUND.

        Args:
            message (str, opcional): Mensaje descriptivo. Por defecto "Not found".
            data (Dict[str, Any], opcional): Datos extra. Por defecto {}.

        Returns:
            Response: Instancia con status Status.NOT_FOUND.
        """
        return cls(Status.NOT_FOUND, message, data)


class ContainerData:
    id: str | None
    name: str | None
    status: str | None


class RedisResponse:
    """
    Representa una respuesta estándar para Redis con un código de estado, un mensaje
    descriptivo y datos adicionales.

    Atributos:
        status (str): Código de estado (Status.OK, Status.ERROR, etc.).
        message (str): Mensaje legible para el usuario.
        data (dict): Carga útil con información adicional.
    """

    def __init__(self, status: str, message: str, data: dict = {}):
        """
        Inicializa una instancia de Response.

        Args:
            status (str): Código de estado (p.ej., Status.OK).
            message (str): Mensaje descriptivo.
            data (dict, opcional): Datos extra. Por defecto {}.

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
