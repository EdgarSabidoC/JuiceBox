# JUICE BOX

Conjunto de herramientas para la orquestacion de contenedores de Docker para los servicios de OWASP Juice Shop y Root The Box.

La comunicacion esta basada **eventos** o **señales** por medio de un Unix Domain Socket personalizado.

---

## COMPONENTES DE JUICE BOX

|       Componente        | Descripcion                                                                                   |
| :---------------------: | :-------------------------------------------------------------------------------------------- |
|   `Juice Box Engine`    | **Motor** o programa principal que corre en el **servidor/anfitrion**.                        |
|     `Juice Box TUI`     | Interfaz basada en texto para las herramientas administrativas (Python y Textual).            |
|   `Juice Shop Client`   | Interfaz grafica basada en una aplicacion web para los usuarios (HTML+CSS+JS).                |
| `Juice Shop Client API` | API REST que conecta la interfaz grafica del JuiceShop_Client con el motor de Juice Box (Go). |
|        `Monitor`        | Monitor y logger del sistema.                                                                 |

---

## ARQUITECTURA DE JUICE BOX

```
Contenedores de Docker
├── NginX
│   ├── Web Client
│   │   └──> Monitor
│   └── JuiceShop API
│       └─(UNIX socket)─> Juice Box Engine API
└── Host/Server
    ├── TUI (herramientas administrativas)
    │   └─(UNIX socket)─> JuiceBox Engine API
    ├── JuiceBox Engine
    │   └──> Monitor
    └── Monitor
```

---

## JUICE BOX ENGINE API

### Estructura de mensajes de la API
- ***prog:*** Utiliza las constantes `"JS"` (Juice Shop) o `"RTB"` (Root The Box) para indicar el programa dentro del motor que sera utilizado.
- ***command:*** Cadena del comando, escrito en mayusculas y utiliza como prefijo y sufijo `"__"`, por ejemplo: `__START_CONTAINER__`.
- ***args:*** Argumentos del comando, aqui se debe añadir el numero de puerto del contenedor o su nombre.
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

**NOTA:** *Al reiniciar el servicio tambien se eliminan todos los contenedores de Juice Shop (utiliza internamente el comando `__KILL_ALL__`).*

[`Ver: Detener y destruir TODOS los contenedores`](#detener-y-destruir-todos-los-contenedores)

#### Detener un contenedor especifico
Señal:  `__KILL_CONTAINER__`

Args: (`port` | `name`)

#### Detener **TODOS** los contenedores
Señal: `__KILL_ALL__`

#### Ver estado del servicio
Señal: `__STATUS__`

#### Configurar los contenedores
Señal: `__CONFIG__`

Modifica el archivo dentro de `JuiceBoxEngine/configs/juiceShop.json`

**NOTA:** *Los cambios realizados en los archivos de configuracion solo surtiran efecto al reiniciar los servicios. Debido a que todos los contenedores de la JuiceShop necesitan la misma **ctf_key** al ejecutar este comando todos los contenedores existentes seran eliminados para mantener la coherencia y la cohesion del motor.* [`Ver: Reiniciar el servicio`](#reiniciar-el-servicio)

#### Archivo de configuracion XML (RTB)
Señal: `__GENERATE_XML__`

**NOTA:** *Este archivo contiene las misiones/desafios de la Juice Shop. Utiliza internamente el comando `__RESET__`.* [`Ver: Reiniciar el servicio`](#reiniciar-el-servicio)

### Notas Adicionales
- Los scripts requieren de una version de Python (v. 3.9+) que permita el tipado.
- Por la naturaleza de los contenedores cuando se detienen tambien se realiza la destruccion.
- Si se quiere conservar informacion es importante que el contenedor cree un volumen para la persistencia de datos.
- Los contenedores se pueden comunicar entre si de forma predeterminada por medio de la red por defecto de Docker.
- Si se requiere mayor control sobre la comunicacion de los contenedores se pueden crear otras redes que sean para los contenedores deseados en especifico.

---

## LOGS
Los logs de `JuiceBoxEngine` se centralizan en `journald`, el gestor de logs de `systemd`.

### Configuracion

#### Activar persistencia
Por defecto, journald guarda los registros en memoria y no sobreviven a reinicios. Para habilitar almacenamiento persistente:

Modifica el archivo `/etc/systemd/journald.conf`:

```
[Journal]
# Activa la persistencia
Storage=persistent

# Habilita la compresion
Compress=yes
SystemMaxUse=500M
SystemKeepFree=100M
SystemMaxFileSize=50M

# Rotar cada dia
SystemMaxFileSec=1day

# Conservar hasta 7 archivos/dias
SystemMaxFiles=7

# Borrar entradas mayores a 7 dias
MaxRetentionSec=7day


# Descoomentar las opciones que quieras configurar
#Seal=yes
#SplitMode=uid
#SyncIntervalSec=5m
#RateLimitIntervalSec=30s
#RateLimitBurst=10000
#RuntimeMaxUse=
#RuntimeKeepFree=
#RuntimeMaxFileSize=
#RuntimeMaxFiles=100
#MaxRetentionSec=0
#MaxFileSec=1month
#ForwardToSyslog=no
#ForwardToKMsg=no
#ForwardToConsole=no
#ForwardToWall=yes
#TTYPath=/dev/console
#MaxLevelStore=debug
#MaxLevelSyslog=debug
#MaxLevelKMsg=notice
#MaxLevelConsole=info
#MaxLevelWall=emerg
#MaxLevelSocket=debug
#LineMax=48K
#ReadKMsg=yes
#Audit=yes
```

Luego reinicia el servicio de `systemd-journald` ejecutando el comando:

```
sudo systemctl restart systemd-journald

```

#### Envolver la app con `systemd-cat` (opcional)

Si no se puede instalar el paquete `python-systemd`, entonces desde la carpeta raiz de JuiceBox ejecuta en la terminal el comando:

```
systemd-cat -t JuiceBoxEngine python3 JuiceBoxEngine/main.py
```

Este comando permite redirigir el stdout y stderr al journal bajo la etiqueta `JuiceBoxEngine`.

### Ver los logs
Para ver los logs ejecutar desde la terminal:

#### Ver todas las entradas
```
sudo journalctl -t JuiceBoxEngine
```

#### Ver en tiempo real
```
sudo journalctl -t JuiceBoxEngine -f
```

#### Ver solo errores
```
sudo journalctl -t JuiceBoxEngine -p err
```