# Juice Box Engine TUI

## Juice Box TUI como ejecutable

### Crear un script ejecutable */opt/juicebox/TUI/tui.sh* con lo siguiente

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Activar el entorno virtual
source /opt/juicebox/venv/bin/activate

# 2. Asegurar que Python vea el paquete Juice Box
export PYTHONPATH=/opt/juicebox

# 3. Opcional: moverse al root del paquete
cd /opt/juicebox

# 4. Arrancar la TUI como modulo, pasando todos los args
exec python3 -m JuiceBox.TUI "$@"

```

### Otorgar permiso de ejecucion

```bash
sudo chmod 750 /opt/juicebox/TUI/juicebox_tui.sh
```

### Crea un enlace simbolico en un directorio del PATH

```bash
sudo ln -s /opt/juicebox/TUI/tui.sh /usr/local/bin/juicebox
```

## Grupo juicebox para controlar acceso a la TUI

```bash
sudo groupadd juicebox
newgrp juicebox
```

### Añadir usuarios que quieres que tengan acceso a la TUI

```bash
sudo usermod -aG juicebox el_usuario
```

### Cambiar grupo y permisos del script para que solo el grupo juicebox pueda ejecutarlo

```bash
sudo chown root:juicebox /opt/juicebox/TUI/juicebox_tui.sh
sudo chmod 750 /opt/juicebox/TUI/juicebox_tui.sh
```

### Opcional (recomendado): controlar ejecucion del binario desde /usr/local/bin/juicebox

```bash
sudo chown root:juicebox /usr/local/bin/juicebox
sudo chmod 750 /usr/local/bin/juicebox
```

**NOTA:** Como el enlace simbolico apunta al script, heredara permisos. Pero si quieres seguridad adicional, esta parte opcional permite que el enlace simbolico sea propiedad de root y grupo juicebox y permisos 750 tambien.