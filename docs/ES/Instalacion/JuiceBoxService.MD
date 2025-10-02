# Juice Box Engine: Despliegue con systemd y activacion del Socket

Este documento detalla todos los pasos necesarios para la instalacion manual del proyecto `Juice Box`, preparar el entorno virtual de Python (venv), crear los scripts de arranque, definir las unidades systemd (socket y servicio) y verificar que todo funcione correctamente.

Si se deasea, se puede realizar la instalacion automatica por medio de los scripts disponibles en `JuiceBox/Install`. Hay scripts disponibles para distros basadas en `Arch` con shell `Fish` y en `Ubuntu/Debian` con shell `Bash`.

---

## 1. Creacion del usuario, carpetas y transferencia de la aplicacion

## Para shell `Bash` (distros basadas en Ubuntu/Debian):

```bash
sudo mkdir -p /opt/juicebox
sudo chown -R juicebox:juicebox /opt/juicebox
sudo usermod -aG docker juicebox
sudo mkdir -p /opt/juicebox/run
sudo chown juicebox:juicebox /opt/juicebox/run
sudo chmod 770 /opt/juicebox/run
newgrp docker
```

## Para shell `Fish` (distros basadas en Arch):

```bash
sudo mkdir -p /opt/juicebox
sudo chown -R juicebox:juicebox /opt/juicebox
sudo usermod -aG docker juicebox
sudo mkdir -p /opt/juicebox/run
sudo chown juicebox:juicebox /opt/juicebox/run
sudo chmod 770 /opt/juicebox/run
newgrp docker
```

**NOTA**: Es importante que los usuarios que vayan a utilizar la app esten dentro del grupo `docker`, esto ya se toma en cuenta para la creacion del usuario `juicebox`.

## 1.2. Transferencia de las carpetas de la aplicacion

### De forma local (dentro de la misma PC)

```bash
sudo rsync -av --exclude venv /ruta/de/la/app/ /opt/juicebox/
```

### De PC a un servidor remoto por medio de SSH:

```bash
rsync -av --exclude venv /ruta/de/la/app/ usuario@servidor:/opt/juicebox/
```

## 1.3 Otorgar los permisos al usuario `juicebox`

```bash
sudo chown -R juicebox:juicebox /opt/juicebox
```

## 2. Configuracion del entorno de Python

### 2.1. Creacion y activacion del entorno virtual (venv)

```bash
cd /opt/juicebox
sudo -u juicebox python3 -m venv /opt/juicebox/venv
sudo -u juicebox /opt/juicebox/venv/bin/python -m ensurepip --upgrade
sudo -u juicebox /opt/juicebox/venv/bin/python -m pip install --upgrade pip
```

### 2.2. Instalacion del paquete de la aplicacion y dependencias en el entorno virtual

Asegurar que el archivo *requirements.txt* en */opt/juicebox* contenga:

```bash
docker
dotenv
textual
textual[syntax]
fastapi
gunicorn
uvicorn
py-cpuinfo
linkify-it-py
systemd-python
redis
pydantic
psutil
PyYAML
```

#### 2.2.1. Activacion del venv

##### Shell `Bash` (distros basadas en Ubuntu/Debian):

```bash
source /opt/juicebox/venv/bin/activate
```

##### Shell `Fish` (distros basadas en Arch):

```bash
source /opt/juicebox/venv/bin/activate.fish
```

#### 2.2.2. Verificacion del python y pip del venv

Para saber si se esta utilizando el Python y pip del entorno virtual (venv), se deben ejecutar los siguientes comandos:

```bash
which python
which pip
```

Una vez ejecutados dichos comandos deberia verse algo asi:

```bash
/opt/juicebox/venv/bin/python
/opt/juicebox/venv/bin/pip
```

Si por el contrario se ve algo asi:

```bash
/usr/bin/python
/usr/bin/pip
```

Quiere decir que no se esta utilizando el entorno virtual (venv).

#### 2.2.3. Instalacion de los paquetes de ***requirements.txt*** en el venv:

Estando en la ruta `/opt/juicebox/` y con el `venv activado`, ejecutar:

```bash
pip install -r requirements.txt
```

#### Desactivacion del entorno virtual:

Para poder salir o desactivar el entorno virtual basta con utilizar el comando `deactivate`.

```bash
deactivate
```

## 3. Instalaciones de la aplicacion y de Root The Box

### 3.1. Instalacion de la aplicacion

Una vez preparado el entorno virtual y aun dentro de este, se debe instalar el paquete de `Juice Box` en Python utilizando la herramienta `pip`.

Se debe estar en la ruta `/opt/juicebox/` y ejecutar:

```bash
/opt/juicebox/venv/bin/pip install -e .
```

En caso de no estar en `/opt/juicebox/`, utilizar:

```bash
/opt/juicebox/venv/bin/pip install -e /opt/juicebox
```

**NOTA:** La bandera `-e` permite instalar el paquete de la aplicacion en modo editable.

Una vez instalado el paquete, puede ser llamado desde el shell del entorno virtual (venv) utilizando el comando `juicebox`. De igual forma se puede utilizar el comando `python3 -m JuiceBox` para llamar a la aplicacion del motor.

#### 3.1.1. Verificacion de la instalacion

```bash
/opt/juicebox/venv/bin/pip list | grep juicebox
```

### 3.2. Instalacion de Root The Box

Para instalar `Root The Box` [ver el siguiente enlace](RootTheBox.MD).

## 4. Creacion de la unidad systemd

### 4.1. Servicio: /etc/systemd/system/juiceboxengine.service

#### 4.1.1. Creacion del archivo `juiceboxengine.service`

Crear el archivo con `Nano` utilizando

```bash
sudo nano /etc/systemd/system/juiceboxengine.service
```

Posteriormente copiar dentro el contenido del archivo y darle a `ctrl+o`, `enter` y luego `ctrl+x`.

##### Contenido del archivo `juiceboxengine.service`

```bash
[Unit]
Description=JuiceBox CTF Orchestrator for Root The Box & OWASP Juice Shop
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=juicebox
Group=juicebox
WorkingDirectory=/opt/juicebox
ExecStart=/opt/juicebox/venv/bin/juicebox
Environment=JUICEBOX_SOCKET=/opt/juicebox/run/engine.sock
UMask=007
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## 5. Habilitacion, arranque y verificacion del servicio

### 5.1. Recargar unidad y habilitar el servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now juiceboxengine.service
```

### 5.2. Comprobacion del estado del servicio

```bash
systemctl status juiceboxengine.service --no-pager
```

## 6. Logs del servicio

## 6.1. Seguimiento en tiempo real:

```bash
journalctl -u juiceboxengine.service -f
```

### 6.1.1. Filtrado por SYSLOG_IDENTIFIER:

```bash
journalctl SYSLOG_IDENTIFIER=juiceboxengine -f

```

**Nota:** La bandera `-f` permite seguir en tiempo real. Mientras que `-u` se usa solo para unidades systemd, que en el caso de `Juice Box` seria `juiceboxengine.service`.

### 6.2. Filtrado de logs por nivel de severidad (prioridad)

Los logs pueden ser utilizados con banderas como:

```bash
journalctl -u juiceboxengine.service -p err        # Solo errores
journalctl -u juiceboxengine.service -p warning    # Warnings y mas graves
journalctl -u juiceboxengine.service -p info       # Info y mas graves
```

Los niveles disponibles son: `emerg`, `alert`, `crit`, `err`, `warning`, `notice`, `info`, `debug`.

### 6.3. Filtrado por tiempo

journal tambien permite filtrar por tiempo, por ejemplo:

```bash
journalctl -u juiceboxengine.service --since today
journalctl -u juiceboxengine.service --since "2025-09-22 10:00:00" --until "2025-09-22 12:00:00"
journalctl -u juiceboxengine.service --since "1 hour ago"
```

---

Con esto Juice Box debera estar desplegado en ***/opt/juicebox*** y gestionado por ***systemd***, las conexiones se recibiran por medio del ***socket UNIX*** en la siguiente ruta: `/run/juicebox/engine.sock`.