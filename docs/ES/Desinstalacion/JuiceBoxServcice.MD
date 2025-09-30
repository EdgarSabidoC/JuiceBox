# Desinstalación / Reversión de Juice Box Engine con systemd

Este documento detalla los pasos para eliminar la instalación de Juice Box Engine y revertir los cambios realizados durante su despliegue de forma manual.

Si quiere evitar hacerlo de forma manual, puede optar por alguno de los scripts de desinstalación que se encuentran en la carpeta `Uninstall/` dentro de la raíz del proyecto.

---

## 1. Detener el servicio y el socket

Antes de eliminar archivos, detener las unidades systemd:

```bash
sudo systemctl stop juiceboxengine.service
sudo systemctl stop juiceboxengine.socket
sudo systemctl disable juiceboxengine.service
sudo systemctl disable juiceboxengine.socket
sudo systemctl daemon-reload
```

## 2. Eliminar archivos de las unidades systemd

Para borrar los archivos de configuración creados ejecutar:

```bash
sudo rm -f /etc/systemd/system/juiceboxengine.service
sudo rm -f /etc/systemd/system/juiceboxengine.socket
sudo systemctl daemon-reload
```

## 3. Eliminar el entorno virtual y la aplicación

Para eliminar el directorio completo de Juice Box:

```bash
sudo rm -rf /opt/juicebox
```

Con esto se eliminan:
- El entorno virtual (venv)
- El paquete instalado (pip install -e .)
- Archivos de configuración, logs y scripts de la aplicación

## 4. Eliminar el suuario creado (opcional)

Si se desea eliminar el usuario `juicebox` y su grupo, ejecutar:

### Para distros basadas en Ubuntu/Debian

```bash
sudo deluser --remove-home juicebox
sudo groupdel juicebox
```

### Para distros basadas en Arch:

```bash
sudo userdel -r juicebox
sudo groupdel juicebox
```

**NOTA:** Asegura que ningún otro servicio o contenedor dependa del grupo docker o del usuario juicebox.

## 5. Limpieza de logs (opcional)

Si se requiere eliminar los lgos generados por journald para `Juice Box`, ejecutar:

```bash
journalctl SYSLOG_IDENTIFIER=juiceboxengine --rotate
journalctl --vacuum-time=1s
```

**NOTA:** Esto eliminará los registros antiguos relacionados con Juice Box.