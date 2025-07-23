# JUICE BOX ENGINE
This app run on a **host** machine.

Se comunica a través de **eventos** o **señales** por medio de un custom Unix Domain Socket con los clientes:

- **JuiceBox_TUI:** Text User Interface for admins (Python y Textual).
- **JuiceShop_API:** es la interfaz gráfica para los usuarios/clientes normales (Go).

### Estructura de los mensajes para la API de Juice Box Engine:
    {
      "prog": ("JS" | "RTB"),
      "command": <string>,
      [ "args": { ("port": <integer> | "name": <string> ) } ]
    }

- ***prog:*** Utiliza las constantes `"JS"` (Juice Shop) o `"RTB"` (Root The Box) para indicar el programa dentro del motor que será utilizado.
- ***command:*** Cadena del comando, escrito en mayúsculas y utiliza como prefijo y sufijo `"__"`, por ejemplo: `__START_CONTAINER__`.
- ***args:*** Argumentos del comando, aquí se debe añadir el número de puerto del contenedor o su nombre.

## Root The Box

### Iniciar el servicio:
Comando: `__START__`.

### Reiniciar el servicio:
Comando: `__RESTART__`.

### Detener el servicio:
Comando: `__KILL__`.

**NOTA:** *Destruye **TODOS** los contenedores relacionados a Root The Box.*

### Ver estado del servicio:
Comando: `__STATUS__`

### Configurar los contenedores:
Comando: `__CONFIG__`

Modificar el archivo dentro de `JuiceBoxEngine/configs/rootTheBox.json`.

## OWASP Juice Shop

### Iniciar un contenedor:
Comando: `__START_CONTAINER__`.

<h3 id="js-reiniciar-el-sevicio">Reiniciar el servicio:</h3>

Comando: `__RESTART__`.

**NOTA:** *Al reiniciar el servicio también se eliminan todos los contenedores de Juice Shop (utiliza internamente el comando `__KILL_ALL__`).*

[`Ver: Detener y destruir TODOS los contenedores`](#detener-y-destruir-todos-los-contenedores)

### Para y destruir un contenedor en específico:
Comando:  `__KILL_CONTAINER__`

Args: (`port` | `name`)

### Detener y destruir **TODOS** los contenedores:
Comando: `__KILL_ALL__`

### Ver estado del servicio:
Comando: `__STATUS__`

### Configurar los contenedores:
Comando: `__CONFIG__`

Modificar el archivo dentro de `JuiceBoxEngine/configs/juiceShop.json`

**NOTA:** *Los cambios realizados en los archivos de configuración solo surtirán efecto al reiniciar los servicios. Debido a que todos los contenedores de la JuiceShop necesitan la misma **ctf_key** al ejecutar este comando todos los contenedores existentes serán eliminados para mantener la coherencia y la cohesión del motor.* [`Ver: Reiniciar el servicio`](#js-reiniciar-el-sevicio)

### Generar archivo de configuración XML para Root The Box con misiones/desafíos de la Juice Shop:
Ejecutar el comando `__GENERATE_XML__`

**NOTA:** *Utiliza internamente el comando `__RESET__`.* [`Ver: Reiniciar el servicio`](#js-reiniciar-el-sevicio)

## NOTAS
- Los scripts requieren de una versión de Python (v. 3.9+) que permita el tipado.
- Por la naturaleza de los contenedores cuando se detienen también se realiza la destrucción.
- Si se quiere conservar información es importante que el contenedor cree un volumen para la persistencia de datos.
- Los contenedores se pueden comunicar entre sí de forma predeterminada por medio de la red por defecto de Docker.
- Si se requiere mayor control sobre la comunicación de los contenedores se pueden crear otras redes que sean para los contenedores deseados en específico.