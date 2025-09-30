#!/usr/bin/env bash
set -euo pipefail

# 1. Activa el entorno virtual
source /opt/juicebox/venv/bin/activate

# 2. Asegura que Python vea tu paquete Juice Box
export PYTHONPATH=/opt/juicebox

# 3. Opcional: muévete al root del paquete
cd /opt/juicebox

# 4. Arranca tu TUI como módulo, pasando todos los args
exec python3 -m JuiceBox.TUI "$@"
