# Juice Box

## Dependencias

### Sistema operativo/host/servidor

Para instalar `Juice Box` es necesario tener previamente instalado en el sistema operativo lo siguiente:

- Docker Engine
- Docker-Compose

**NOTA:** Dado que `Juice Box Engine` tiene un componente orquestador de Docker es indispensable instalar el motor de `Docker`, asi como el plugin `docker-compose`.

### Python

El motor de `Juice Box` utiliza Python v3.12+, ademas debe de tener instalados los siguientes paquetes:

- docker
- dotenv
- textual
- textual[syntax]
- fastapi
- gunicorn
- uvicorn
- py-cpuinfo
- linkify-it-py
- systemd-python
- redis
- pydantic
- psutil
- PyYAML

**NOTA:** `Juice Box` cuenta con un entorno virtual con Python y sus respectivos paquetes. Por lo que la informacion previa es netamente informativa.

---

## Instalacion de `Juice Box` como servicio

Para instalar `Juice Box` como servicio en tu servidor o computadora con `Linux (Debian/Ubuntu/Arch)` [ver el siguiente enlace](JuiceBoxService.MD).

---

## Instalacion de la Manager TUI de `Juice Box`

Para instalar la TUI como ejecutable [ver el siguiente enlace](TUI.MD).

---

## Instalacion del WebClient de `Juice Box`

Para instalar el WebClient como servicio [ver el siguiente enlace](WebClient.MD).
