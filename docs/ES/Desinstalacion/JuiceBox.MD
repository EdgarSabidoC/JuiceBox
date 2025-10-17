# Desinstalación / Reversión de Juice Box Engine con systemd

Este documento detalla los pasos para eliminar la instalación de Juice Box Engine y revertir los cambios realizados durante su despliegue de forma manual.

---

## Desinstalacion por script

Si se quiere evitar la desinstalacion manual, se puede optar por utilizar el archivo de desinstalacion correspondiente en la ruta `/opt/juicebox/Uninstall/`:

### Para distros basadas en Ubuntu/Debian con shell bash:

```bash
chmod +x uninstall_juicebox.sh
./uninstall_juicebox.sh
```

### Para distros basadas en Arch con shell fish:

```bash
chmod +x uninstall_juicebox.fish
./uninstall_juicebox.fish
```

---

## Desinstalacion manual

### 1. Detener y deshabilitar los servicios systemd

Antes de eliminar archivos, detener las unidades systemd:

```bash
sudo systemctl stop juiceboxengine.service
sudo systemctl stop juiceboxweb.service
sudo systemctl disable juiceboxengine.service
sudo systemctl disable juiceboxweb.service
sudo systemctl daemon-reload
```

### 2. Eliminar archivos de las unidades systemd

Para borrar los archivos de configuración creados ejecutar:

```bash
sudo rm -f /etc/systemd/system/juiceboxengine.service
sudo rm -f /etc/systemd/system/juiceboxweb.service
sudo systemctl daemon-reload
```

### 3. Eliminar el warpper de la TUI

```bash
sudo rm -f /usr/local/bin/juicebox-tui
```

### 4. Eliminar el entorno virtual y la aplicación

Para eliminar el directorio completo de Juice Box:

```bash
sudo rm -rf /opt/juicebox
```

Con esto se eliminan:
- El entorno virtual (venv)
- El paquete instalado (pip install -e .)
- Archivos de configuración, logs y scripts de la aplicación

### 5. Eliminar el usuario creado (opcional)

Si se desea eliminar el usuario `juicebox` y su grupo, ejecutar:

#### Para distros basadas en Ubuntu/Debian

```bash
sudo deluser --remove-home juicebox
sudo groupdel juicebox
```

#### Para distros basadas en Arch:

```bash
sudo userdel -r juicebox
sudo groupdel juicebox
```

**NOTA:** Asegura que ningún otro servicio o contenedor dependa del grupo docker o del usuario juicebox.

### 6. Limpieza de logs (opcional)

Si se requiere eliminar los lgos generados por journald para `Juice Box`, ejecutar:

```bash
journalctl SYSLOG_IDENTIFIER=juiceboxengine --rotate
journalctl SYSLOG_IDENTIFIER=juiceboxweb --rotate
journalctl --vacuum-time=1s
```

**NOTA:** Esto eliminará los registros de logs antiguos relacionados con Juice Box.