#

## Instalacion por script

Si se quiere evitar la instalacion manual, se puede optar por utilizar el archivo de instalacion correspondiente en la ruta `/opt/juicebox/Install/`:

### Para distros basadas en Ubuntu/Debian con shell bash:

```bash
chmod +x juicebox_webclient_ubuntu_debian.sh
./juicebox_webclient_ubuntu_debian.sh
```

### Para distros basadas en Arch con shell fish:

```bash
chmod +x juicebox_webclient_arch.fish
./juicebox_webclient_arch.fish
```

## Instalacion manual

### Creacion del servicio systemd para el cliente web (WebClient)

Se debe crear el arhivo de unidad con `sudo nano /etc/systemd/system/juiceboxweb.service`, el cual debe contener:

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
ExecStart=/opt/juicebox/venv/bin/gunicorn -k uvicorn.workers.UvicornWorker WebClient.main:app -b ${HOST}:${PORT} --workers 4
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### Reargar el sistema

```bash
sudo systemctl daemon-reload
sudo systemctl enable juiceboxweb
sudo systemctl start juiceboxweb
```

#### Estado del servicio

`systemctl status juiceboxweb`

#### Logs en tiempo real

`journalctl -u juiceboxweb -f`

#### Probar la API:

```bash
curl http://{HOST}:{PORT}/api/v1/juice-shop
```
