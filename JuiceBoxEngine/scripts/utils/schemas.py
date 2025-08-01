from pydantic import BaseModel
from typing import Optional, Literal, Union, List, Dict, Any


# ----------- ENTRADA: COMANDOS ------------


class RTBCommand(BaseModel):
    prog: Literal["RTB"]
    command: Literal["__START__", "__KILL__", "__RESTART__", "__CONFIG__", "__STATUS__"]
    args: Optional[dict] = None


class JSCommand(BaseModel):
    prog: Literal["JS"]
    command: Literal[
        "__RESTART__",
        "__CONFIG__",
        "__STATUS__",
        "__START_CONTAINER__",
        "__KILL_CONTAINER__",
        "__KILL_ALL__",
        "__GENERATE_XML__",
    ]
    args: Optional[dict] = None


# Unión de ambos tipos de entrada
CommandRequest = Union[RTBCommand, JSCommand]


# ----------- RESPUESTA: MODELOS BASE Y EXTENDIDOS ------------


class BaseResponse(BaseModel):
    status: Literal["ok", "error"]
    message: str


class GenericResponse(BaseResponse):
    data: Optional[Dict[str, Any]] = None


# ---------- RESPUESTAS ESPECÍFICAS (data con estructura definida) ----------


class ContainerStatus(BaseModel):
    """Estado específico de un contenedor va dentro de data"""

    container: str
    status: str
    message: str
    running: Optional[bool] = None


class ContainerRunResponse(BaseResponse):
    container: str


class KillAllResponse(BaseResponse):
    results: List[ContainerStatus]


class ConfigResponse(BaseResponse):
    config: Dict[str, Any]


# ---------- OPCIONAL: RESPUESTA UNION (para tipar salidas variadas) ----------

ResponseUnion = Union[
    GenericResponse,
    ContainerRunResponse,
    KillAllResponse,
    ConfigResponse,
]
