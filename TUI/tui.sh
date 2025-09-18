#!/usr/bin/env bash
set -euo pipefail

# 1. Activa el entorno virtual
source /opt/JuiceBox/venv/bin/activate

# 2. Asegura que Python vea tu paquete JuiceBox
export PYTHONPATH=/opt/JuiceBox

# 3. Opcional: muévete al root del paquete
cd /opt/JuiceBox

# 4. Arranca tu TUI como módulo, pasando todos los args
exec python -m JuiceBox.JuiceBox_TUI "$@"
