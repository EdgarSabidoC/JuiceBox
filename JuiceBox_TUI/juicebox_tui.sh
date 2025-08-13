#!/usr/bin/env bash
# Activa el entorno virtual de JuiceBox
source /opt/JuiceBox/venv/bin/activate

# Ejecuta la TUI, pasando todos los argumentos
python /opt/JuiceBox/JuiceBox_TUI/main.py "$@"