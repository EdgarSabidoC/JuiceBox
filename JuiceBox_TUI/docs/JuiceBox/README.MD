# JUICE BOX

Conjunto de herramientas para la orquestación de contenedores de Docker para los servicios de OWASP Juice Shop y Root The Box.

La comunicación está basada **eventos** o **señales** por medio de un Unix Domain Socket personalizado.

---

## COMPONENTES DE JUICE BOX

|       Componente        | Descripción                                                                                   |
| :---------------------: | :-------------------------------------------------------------------------------------------- |
|   `Juice Box Engine`    | **Motor** o programa principal que corre en el **servidor/anfitrión**.                        |
|     `Juice Box TUI`     | Interfaz basada en texto para las herramientas administrativas (Python y Textual).            |
|   `Juice Shop Client`   | Interfaz gráfica basada en una aplicación web para los usuarios (HTML+CSS+JS).                |
| `Juice Shop Client API` | API REST que conecta la interfaz gráfica del JuiceShop_Client con el motor de Juice Box (Go). |
|        `Monitor`        | Monitor y logger del sistema.                                                                 |

---

## ARQUITECTURA DE JUICE BOX

```
Contenedores de Docker
├── NginX
│   ├── Web Client
│   │   └── Monitor
│   └── JuiceShop API
│       └── Juice Box Engine API
└── Host/Server
    ├── TUI (herramientas administrativas)
    │   └── JuiceBox Engine API
    └── Monitor
```

---

## JUICE BOX ENGINE API

### Estructura de mensajes de la API
- ***prog:*** Utiliza las constantes `"JS"` (Juice Shop) o `"RTB"` (Root The Box) para indicar el programa dentro del motor que será utilizado.
- ***command:*** Cadena del comando, escrito en mayúsculas y utiliza como prefijo y sufijo `"__"`, por ejemplo: `__START_CONTAINER__`.
- ***args:*** Argumentos del comando, aquí se debe añadir el número de puerto del contenedor o su nombre.
```
{
  "prog": ("JS" | "RTB"),
  "command": <string>,
  [ "args": { ("port": <integer> | "name": <string> ) } ]
}
```

### Comandos de Root The Box

#### Iniciar servicio
Señal: `__START__`.

#### Reiniciar servicio
Señal: `__RESTART__`.

#### Detener servicio
Señal: `__KILL__`.

**NOTA:** *Destruye **TODOS** los contenedores relacionados a Root The Box.*

#### Ver estado del servicio
Señal: `__STATUS__`

#### Configurar los contenedores
Señal: `__CONFIG__`

Modifica el archivo dentro de `JuiceBoxEngine/configs/rootTheBox.json`.

### Comandos de OWASP Juice Shop

#### Iniciar un contenedor
Señal: `__START_CONTAINER__`.

#### Reiniciar el servicio

Señal: `__RESTART__`.

**NOTA:** *Al reiniciar el servicio también se eliminan todos los contenedores de Juice Shop (utiliza internamente el comando `__KILL_ALL__`).*

[`Ver: Detener y destruir TODOS los contenedores`](#detener-y-destruir-todos-los-contenedores)

#### Detener y destruir un contenedor específico
Señal:  `__KILL_CONTAINER__`

Args: (`port` | `name`)

#### Detener y destruir **TODOS** los contenedores
Señal: `__KILL_ALL__`

#### Ver estado del servicio
Señal: `__STATUS__`

#### Configurar los contenedores
Señal: `__CONFIG__`

Modifica el archivo dentro de `JuiceBoxEngine/configs/juiceShop.json`

**NOTA:** *Los cambios realizados en los archivos de configuración solo surtirán efecto al reiniciar los servicios. Debido a que todos los contenedores de la JuiceShop necesitan la misma **ctf_key** al ejecutar este comando todos los contenedores existentes serán eliminados para mantener la coherencia y la cohesión del motor.* [`Ver: Reiniciar el servicio`](#reiniciar-el-servicio)

#### Archivo de configuración XML (RTB)
Señal: `__GENERATE_XML__`

**NOTA:** *Este archivo contiene las misiones/desafíos de la Juice Shop. Utiliza internamente el comando `__RESET__`.* [`Ver: Reiniciar el servicio`](#reiniciar-el-servicio)

### Notas Adicionales
- Los scripts requieren de una versión de Python (v. 3.9+) que permita el tipado.
- Por la naturaleza de los contenedores cuando se detienen también se realiza la destrucción.
- Si se quiere conservar información es importante que el contenedor cree un volumen para la persistencia de datos.
- Los contenedores se pueden comunicar entre sí de forma predeterminada por medio de la red por defecto de Docker.
- Si se requiere mayor control sobre la comunicación de los contenedores se pueden crear otras redes que sean para los contenedores deseados en específico.