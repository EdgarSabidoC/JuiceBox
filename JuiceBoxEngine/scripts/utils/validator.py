from docker import DockerClient


class InvalidConfiguration(Exception):
    pass


def validate_port(value: int, name: str) -> int:
    if not isinstance(value, int) or not (1024 <= value <= 65535):
        raise InvalidConfiguration(f"{name} must be an integer between 1024 and 65535")
    return value


def validate_str(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidConfiguration(f"{name} must be a non-empty string")
    return value.strip()


def validate_container(client: DockerClient, name: str) -> bool:
    # filters 'name' busca substrings, así que se comprueba el match exacto
    matches = client.containers.list(all=True, filters={"name": name})
    return any(c.name == name for c in matches)


def validate_bool(value, name: str) -> bool:
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
