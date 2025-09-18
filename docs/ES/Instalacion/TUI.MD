# Juice Box Engine TUI

## JuiceBox TUI como ejecutable

### Crear un script ejecutable */opt/JuiceBox/TUI/tui.sh* con lo siguiente

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Activar el entorno virtual
source /opt/JuiceBox/venv/bin/activate

# 2. Asegurar que Python vea tu paquete JuiceBox
export PYTHONPATH=/opt/JuiceBox

# 3. Opcional: moverse al root del paquete
cd /opt/JuiceBox

# 4. Arrancar la TUI como módulo, pasando todos los args
exec python -m JuiceBox.TUI "$@"

```

### Otorgar permiso de ejecución

```bash
sudo chmod 750 /opt/JuiceBox/TUI/juicebox_tui.sh
```

### Crea un enlace simbólico en un directorio del PATH

```bash
sudo ln -s /opt/JuiceBox/TUI/tui.sh /usr/local/bin/juicebox
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
sudo chown root:juicebox /opt/JuiceBox/TUI/juicebox_tui.sh
sudo chmod 750 /opt/JuiceBox/TUI/juicebox_tui.sh
```

### Opcional (recomendado): controlar ejecución del binario desde /usr/local/bin/juicebox

```bash
sudo chown root:juicebox /usr/local/bin/juicebox
sudo chmod 750 /usr/local/bin/juicebox
```

**NOTA:** Como el enlace simbólico apunta al script, heredará permisos. Pero si quieres seguridad adicional, esta parte opcional permite que el enlace simbólico sea propiedad de root y grupo juicebox y permisos 750 también.