# Juice Box Engine TUI

## JuiceBox TUI como ejecutable

### Crear un script ejecutable */opt/JuiceBox/JuiceBox_TUI/juicebox_tui.sh* con lo siguiente

```bash
#!/usr/bin/env bash
# Activa el entorno virtual de JuiceBox
source /opt/JuiceBox/venv/bin/activate

# Ejecuta la TUI, pasando todos los argumentos
python /opt/JuiceBox/JuiceBox_TUI/main.py "$@"
```

### Otorgar permiso de ejecución

```bash
sudo chmod +x /opt/JuiceBox/JuiceBox_TUI/juicebox_tui.sh
```

### Crea un enlace simbólico en un directorio del PATH

```bash
sudo ln -s /opt/JuiceBox/JuiceBox_TUI/juicebox_tui.sh /usr/local/bin/juicebox
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
sudo chown root:juicebox /opt/JuiceBox/JuiceBox_TUI/juicebox_tui.sh
sudo chmod 750 /opt/JuiceBox/JuiceBox_TUI/juicebox_tui.sh
```

### Opcional (recomendado): controlar ejecución del binario desde /usr/local/bin/juicebox

```bash
sudo chown root:juicebox /usr/local/bin/juicebox
sudo chmod 750 /usr/local/bin/juicebox
```

**NOTA:** Como el enlace simbólico apunta al script, heredará permisos. Pero si quieres seguridad adicional, esta parte opcional permite que el enlace simbólico sea propiedad de root y grupo juicebox y permisos 750 también.