# Juice Box Manager TUI: Despliegue como ejecutable (wrapper)

Este documento detalla todos los pasos necesarios para la instalacion manual de la `Juice Box Manager TUI` como ejecutable, asi como verificar que todo funcione correctamente.

**NOTA:** Es necesario instalar previamente el servicio de `Juice Box Engine`. Para ello [ver el enlace](JuiceBoxService.MD).

Si se deasea, se puede realizar la instalacion automatica por medio de los scripts disponibles en el directorio `Install` de la carpeta raiz. Hay scripts disponibles para distros basadas en `Arch` con shell `Fish` y en `Ubuntu/Debian` con shell `Bash`.

**NOTA:** Los scripts automaticos instalan por defecto `Juice Box Engine`, `Juice Box Manager TUI` y `Juice Box WebClient`.

---

# 1. Crear el archivo para el wrapper ejecutable

El wrapper se instala en `/usr/local/bin` para que este disponible `globalmente` en el `PATH`.

```bash
sudo nano /usr/local/bin/juicebox-tui
```

## 1.1 Contenido Wrapper para ejecutar la TUI como el usuario juicebox

### Para distros basadas en Ubuntu/Debian con shell Bash

```bash
#!/usr/bin/env bash
exec sudo -u juicebox /opt/juicebox/venv/bin/juicebox-tui "$@"
```

### Para distros basadas en Arch con shell Fish

```bash
#!/usr/bin/env fish
exec sudo -u juicebox /opt/juicebox/venv/bin/juicebox-tui $argv
```

**NOTA:** Despues de copiar el contenido en el archivo creado, utilizar `ctrl+o` para guardar y luego `ctrl+x` para cerrar el editor `nano`.

## 1.2 Otorgamiento de permisos de ejecucion

```bash
sudo chmod +x /usr/local/bin/juicebox-tui
```

## 2.0 Ejecucion de la `Juice Box Manager TUI`

Una vez instalada la TUI, basta con abrir una terminal y ejecutar el comando `juicebox-tui` para iniciarla.