# Juice Box WebClient: Despliegue con systemd

Este documento detalla todos los pasos necesarios para la instalacion manual de la `Juice Box WebClient` como servicio, definir la unidad systemd (servicio) y verificar que todo funcione correctamente.

**NOTA:** Es necesario instalar previamente el servicio de `Juice Box Engine`. Para ello [ver el enlace](JuiceBoxService.MD). De igual forma es necesario instalar `Juice Box Manager TUI` para administrar el sistema: [ver el enlace](ManagerTUI.MD).

Si se deasea, se puede realizar la instalacion automatica por medio de los scripts disponibles en el directorio `Install` de la carpeta raiz. Hay scripts disponibles para distros basadas en `Arch` con shell `Fish` y en `Ubuntu/Debian` con shell `Bash`.

**NOTA:** Los scripts automaticos instalan por defecto `Juice Box Engine`, `Juice Box Manager TUI` y `Juice Box WebClient`.

---

# 1. Crear la unidad Systemd para el cliente web

## 1.1 Crear el archivo de la unidad

```bash
sudo nano /etc/systemd/system/juiceboxweb.service
```

## 1.2. Contenido

```bash
[Unit]
Description=JuiceBox WebClient API (FastAPI)
After=network.target juiceboxengine.service
Requires=juiceboxengine.service

[Service]
Type=simple
User=juicebox
Group=juicebox
WorkingDirectory=/opt/juicebox
EnvironmentFile=/opt/juicebox/WebClient/.env
ExecStart=/opt/juicebox/venv/bin/gunicorn -k uvicorn.workers.UvicornWorker WebClient.main:app -b \${HOST}:\${PORT} --workers 4
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**NOTA:** Asegura que el archivo `.env` exista en `/opt/juicebox/WebClient/.env` y contenga al menos las variables `HOST` y `PORT`, ademas de `JUICEBOX_SOCKET` si quieres forzar la ruta del socket.

# 2. Recargar systemd y habilitar el servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable juiceboxweb.service
sudo systemctl start juiceboxweb.service
```

# 3. Verificar el estado del servicio

```bash
systemctl status juiceboxweb.service --no-pager
```

Si todo esta correcto, el servicio deberia verse activo y escuchando en el puerto definido en el archivo `.env`.

# 4. Probar la API REST

## 4.1 Peticion GET

Para conocer el estado de todos los contenedores disponibles para la OWASP Juice Shop, utilizar una petcion `GET`:

```bash
curl http://{HOST}:{PORT}/api/v1/juice-shop/
```

## 4.2 Peticion POST

Para iniciar un contenedor OWASP Juice Shop (si hay algun puerto disponible), utilizar una petcion `POST`:

```bash
curl -X POST http://{HOST}:{PORT}/api/v1/juice-shop/ \
     -H "Content-Type: application/json"
```
