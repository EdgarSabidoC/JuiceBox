# JUICE BOX ENGINE
Este es el **motor** o programa principal y corre directamente en el **host**.

Se comunica a través de **eventos** o **señales** por medio de un custom Unix Domain Socket con los clientes:

- **JuiceBox_TUI:** es la interfaz gráfica para los administradores (Python y Textual).
- **JuiceShop_API:** es la interfaz gráfica para los usuarios/clientes normales (Go).

## Crear y arrancar los contenedores para Root The Box:
Ejecutar el comando `--start-rtb`

### Parar y destruir **TODOS** los contenedores de Root The Box:
Ejecutar el comando `--kill-rtb`

### Configurar los contenedores de Root The Box:
Modificar el archivo dentro de `JuiceBoxEngine/configs/rootTheBox.json`

## Crear y arrancar los contenedores de OWASP Juice Shop (es obligatorio pasar el puerto o nombre del contenedor):
Ejecutar el comando `--start-js [-p/--port | -n/--name]`

### Para y destruir un contenedor en específico de la Juice Shop (es obligatorio pasar el puerto o nombre del contenedor):
Ejecutar el comando `--kill-js [-p/--port | -n/--name]`

### Parar y destruir **TODOS** los contenedores en específico de la Juice Shop (tener la debida precaución):
Ejecutar el comando `--kill-js [-a/--all]`

### Configurar los contenedores de la Juice Shop:
Modificar el archivo dentro de `JuiceBoxEngine/configs/juiceShop.env`

### Generar archivo de configuración XML para Root The Box con misiones/desafíos de la Juice Shop:
Ejecutar el comando `--generate-xml`

**NOTA:** *Debido a que todos los contenedores de la JuiceShop necesitan la misma [ctf_key] al ejecutar este comando todos los contenedores existentes serán eliminados para mantener la coherencia y la cohesión del motor.*

## NOTAS
- Los scripts requieren de una versión de Python que permita el tipado.
- Por la naturaleza de los contenedores cuando se detienen también se realiza la destrucción.
- Si se quiere conservar información es importante que el contenedor cree un volumen para la persistencia de datos.
- Los contenedores se pueden comunicar entre sí de forma predeterminada por medio de la red por defecto de Docker.
- Si se requiere mayor control sobre la comunicación de los contenedores se pueden crear otras redes que sean para los contenedores deseados en específico.