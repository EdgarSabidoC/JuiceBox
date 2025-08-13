#!/usr/bin/env python3
"""
Módulo de validación de configuración para interacción con Docker.

Contiene:
- Excepción `InvalidConfiguration` para indicar parámetros erróneos.
- Funciones de validación de puerto, cadena, existencia de contenedor y booleano.
"""

from docker import DockerClient


class InvalidConfiguration(Exception):
    """
    Excepción que se lanza cuando un parámetro de configuración no cumple
    los criterios esperados.
    """

    pass


def validate_port(value: int, name: str) -> int:
    """
    Verifica que un valor sea un entero de puerto válido.

    Parámetros:
    - value (int): El valor a validar como puerto.
    - name (str): Nombre descriptivo del parámetro (para mensajes de error).

    Retorna:
    - int: El mismo valor `value` si es un entero entre 1024 y 65535.

    Lanza:
    - InvalidConfiguration: Si `value` no es entero o no está en el rango permitido.
    """
    if not isinstance(value, int) or not (1024 <= value <= 65535):
        raise InvalidConfiguration(f"{name} must be an integer between 1024 and 65535")
    return value


def validate_str(value: str, name: str) -> str:
    """
    Verifica que un valor sea una cadena no vacía.

    Parámetros:
    - value (str): El texto a validar.
    - name (str): Nombre descriptivo del parámetro (para mensajes de error).

    Retorna:
    - str: La cadena `value` recortada de espacios en los extremos.

    Lanza:
    - InvalidConfiguration: Si `value` no es cadena o resulta vacía tras el strip.
    """
    if not isinstance(value, str) or not value.strip():
        raise InvalidConfiguration(f"{name} must be a non-empty string")
    return value.strip()


def validate_container(client: DockerClient, name: str) -> bool:
    """
    Comprueba si existe un contenedor de Docker con nombre exacto.

    Parámetros:
    - client (DockerClient): Cliente de la API de Docker.
    - name (str): Nombre exacto del contenedor a buscar.

    Retorna:
    - bool: True si existe un contenedor con nombre exactamente igual a `name`,
      False en caso contrario.
    """
    # filters 'name' busca substrings, así que se comprueba el match exacto
    matches = client.containers.list(all=True, filters={"name": name})
    return any(c.name == name for c in matches)


def validate_bool(value: bool | str | int, name: str) -> bool:
    """
    Interpreta y valida distintos tipos como booleano.

    Parámetros:
    - value: Valor a validar (puede ser bool, str o int).
    - name (str): Nombre descriptivo del parámetro (para mensajes de error).

    Retorna:
    - bool: True o False según corresponda.

    Lanza:
    - InvalidConfiguration: Si `value` no se ajusta a formatos booleanos
      válidos ("true"/"false", 1/0, True/False).
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1"}:
            return True
        if lowered in {"false", "0"}:
            return False

    if isinstance(value, int):
        if value == 1:
            return True
        if value == 0:
            return False

    raise InvalidConfiguration(f"{name} must be a boolean (true/false, 1/0)")
