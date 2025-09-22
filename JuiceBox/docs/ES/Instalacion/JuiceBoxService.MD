# Juice Box Engine: Despliegue con systemd y Socket Activation

Este documento detalla todos los pasos necesarios para copiar el proyecto `JuiceBox`, preparar el entorno de Python, crear los scripts de arranque, definir las unidades systemd (socket y servicio) y verificar que todo funcione correctamente.

---

## 1. Crear usuario, carpeta y copiar el proyecto

```bash
sudo adduser --system --group juicebox
sudo mkdir -p /opt/juicebox
sudo chown -R juicebox:juicebox /opt/juicebox
sudo usermod -aG docker juicebox
```
**NOTA**: Es importante que los usuarios que vayan a utilizar la app estén dentro del grupo `docker`.

## 2. Configurar el entorno Python
### 2.1 Crear y activar el entorno virtual

```bash
cd /opt/JuiceBox
sudo -u juicebox python3 -m venv /opt/juicebox/venv
```

### 2.2. Instalar el paquete y dependencias
Asegura que el archivo *requirements.txt* en */opt/JuiceBox* contenga:

```
docker
dotenv
textual
textual[syntax]
py-cpuinfo
linkify-it-py
systemd-python
redis
pydantic
psutil
PyYAML
```

Activa el entorno virtual con el shell de Bash:
```bash
source /opt/juicebox/venv/bin/activate
```

Si el intérprete del shell es Fish utilizar:
```bash
source /opt/juicebox/venv/bin/activate.fish
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

## 3. Define las unidades systemd
### 3.1. Socket: /etc/systemd/system/juiceboxengine.socket

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

### 3.2. Servicio: /etc/systemd/system/juiceboxengine.service

```
[Unit]
Description=JuiceBox CTF Orchestrator for Root The Box & OWASP Juice Shop
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=juicebox
Group=juicebox
WorkingDirectory=/opt/juicebox
ExecStart=/opt/juicebox/venv/bin/python -m JuiceBox
Environment="JUICEBOX_SOCKET=/run/juicebox/engine.sock"
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## 4. Habilita, arranca y verifica el servicio
### 4.1. Recargar unidades y habilitar el servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable juiceboxengine.socket
sudo systemctl enable juiceboxengine.service
```

### 4.2. Iniciar el socket

```bash
sudo systemctl start juiceboxengine.socket
```
El servicio se activará automáticamente en el primer acceso al socket.

### 4.3. Comprobar estado y logs

```bash
systemctl status juiceboxengine.socket
systemctl status juiceboxengine.service
journalctl -u juiceboxengine.service -f
```
---

Con estos pasos JuiceBox Engine quedará desplegado en ***/opt/JuiceBox***, gestionado por ***systemd*** y preparado para recibir conexiones vía ***socket UNIX***.