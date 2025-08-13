# JuiceBox Engine: Despliegue con systemd y Socket Activation

Este documento detalla todos los pasos necesarios para copiar el proyecto JuiceBox, preparar el entorno de Python, crear los scripts de arranque, definir las unidades systemd (socket y servicio) y verificar que todo funcione correctamente.

---

## 1. Crear usuario, carpeta y copiar el proyecto

```bash
sudo adduser --system --group juicebox
sudo mkdir -p /opt/JuiceBox
sudo cp -R ~/JuiceBox/. /opt/JuiceBox
sudo chown -R juicebox:juicebox /opt/JuiceBox
sudo usermod -aG docker juicebox
```
**NOTA**: Es importante que los usuarios que vayan a utilizar la app estén dentro del grupo `docker`.

## 2. Configurar el entorno Python
### 2.1 Crear y activar el entorno virtual

```bash
cd /opt/JuiceBox
python3 -m venv venv
```

### 2.2. Instalar dependencias
Asegura que el archivo *requirements.txt* en */opt/JuiceBox* contenga:

```
docker
dotenv
textual
py-cpuinfo
linkify-it-py
systemd-python
redis
pydantic
psutil
```

Activa el entorno virtual con el shell de Bash:
```bash
source venv/bin/activate
```

Si el intérprete del shell es Fish utilizar:
```bash
source venv/bin/activate.fish
```

Instala los paquetes de ***requirements.txt***:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Desactiva el entorno virtual:
```bash
deactivate
```

## 3. Crear el script de entrada
### 3.1. Archivo /opt/JuiceBox/entrypoint.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Activa el entorno virtual
source /opt/JuiceBox/venv/bin/activate

# 2. Ajusta PYTHONPATH
export PYTHONPATH=/opt/JuiceBox

# 3. Ejecuta la aplicación
exec python /opt/JuiceBox/JuiceBoxEngine/main.py
```

### 3.2. Dar permisos de ejecución al archivo

```bash
sudo chmod +x /opt/JuiceBox/entrypoint.sh

```

## 4. Define las unidades systemd
### 4.1. Socket: /etc/systemd/system/juiceboxengine.socket

```
[Unit]
Description=Socket for JuiceBox Engine
PartOf=juiceboxengine.service

[Socket]
ListenStream=/run/juicebox/engine.sock
SocketMode=0660
SocketUser=juicebox
SocketGroup=docker
RuntimeDirectory=juicebox
RuntimeDirectoryMode=0755

[Install]
WantedBy=sockets.target
```

### 4.2. Servicio: /etc/systemd/system/juiceboxengine.service

```
[Unit]
Description=JuiceBox CTF Orchestrator for Root The Box & OWASP Juice Shop
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=juicebox
Group=juicebox
WorkingDirectory=/opt/JuiceBox
ExecStart=/opt/JuiceBox/entrypoint.sh
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## 5. Habilita, arranca y verifica el servicio
### 5.1. Recargar unidades y habilitar el servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable juiceboxengine.socket
sudo systemctl enable juiceboxengine.service
```

### 5.2. Iniciar el socket

```bash
sudo systemctl start juiceboxengine.socket
```
El servicio se activará automáticamente en el primer acceso al socket.

### 5.3. Comprobar estado y logs

```bash
sudo systemctl status juiceboxengine.socket
sudo systemctl status juiceboxengine.service
sudo journalctl -u juiceboxengine.service -f
```
---

Con estos pasos JuiceBox Engine quedará desplegado en ***/opt/JuiceBox***, gestionado por ***systemd*** y preparado para recibir conexiones vía ***socket UNIX***.