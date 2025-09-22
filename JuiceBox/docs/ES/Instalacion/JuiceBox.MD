# Juice Box

## Proceso de instalación

### Dependencias

#### Sistema operativo/host/servidor

Para instalar `Juice Box` es necesario tener previamente instalado en el sistema operativo lo siguiente:

- Docker Engine
- Docker-Compose

**NOTA:** Dado que `Juice Box Engine` tiene un componente orquestador de Docker es indispensable instalar el motor de `Docker`, así como el plugin `docker-compose`.

#### Python

El motor de `Juice Box` utiliza Python v3.12+, además debe de tener instalados los siguientes paquetes:

- docker
- dotenv
- textual
- textual[syntax]
- py-cpuinfo
- linkify-it-py
- systemd-python
- redis
- pydantic
- psutil
- PyYAML

**NOTA:** `Juice Box` cuenta con un entorno virtual con Python y sus respectivos paquetes. Por lo que la información previa es netamente informativa.

---

### Instalación de `Juice Box` como servicio

Para instalar `Juice Box` como servicio en tu servidor [ver el siguiente enlace](JuiceBoxService.MD).

**NOTA:** El script `tui.sh` se encuentra en la ruta `JuiceBox/TUI/tui.sh`.

---

### Instalación de la TUI de `Juice Box` como servicio

Para instalar la TUI como servicio [ver el siguiente enlace](TUI.MD).

**NOTA:** El script `tui.sh` se encuentra en la ruta `JuiceBox/TUI/tui.sh`.