# JUICE BOX

Motor y orquestador para crear competencias CTF basado en Root The Box y OWASP Juice Shop utilizando contenedores de Docker.

---

## COMPONENTES DE JUICE BOX

|       Componente        | Descripcion                                                                              |
| :---------------------: | :--------------------------------------------------------------------------------------- |
|   `Juice Box Engine`    | **Motor** o programa principal que corre en el **servidor/anfitrion**.                   |
|     `Juice Box TUI`     | Interfaz basada en texto para las herramientas administrativas.                          |
|   `Juice Shop Client`   | Interfaz grafica basada en una aplicacion web para los usuarios.                         |
| `Juice Shop Client API` | API REST que conecta la interfaz grafica del JuiceShop_Client con el motor de Juice Box. |
|        `Monitor`        | Monitor y logger del sistema.                                                            |

---

## ARQUITECTURA DE JUICE BOX

```bash
Servidor
├── Juice Box Engine
│   ├── API
│   ├── TUI
│   └── Socket de UNIX
├── Monitor
└── Docker
    ├── Redis (Juice Box Engine)
    ├── Cliente Juice Box
    ├── OWASP Juice Shop (Juice Box Engine)
    └── Root The Box (Juice Box Engine)
```

---

## COMUNICACION POR SOCKET

La comunicacion esta basada en **comandos**, **señales** o **eventos** por medio de un Unix Domain Socket personalizado.

---

## MONITOR

El monitor se encarga de observar e informar cuando sucede algo con los contenedores o algun componente interno del motor de Juice Box.

## TUI

Las herramientas administrativas cuentan con una interfaz de usuario basado en texto (TUI) que es accesible desde la terminal y tiene compatibilidad con SSH.

---

## REDIS

Juice Box Engine corre su propio contenedor de redis.

La comunicacion del estado de los contenedores de Root The Box y OWASP Juice Shop se publica en dos canales: `admin_channel` y `client_channel`.

### admin_channel

Este canal es exclusivo para los usuarios administrativos, ya que contiene informacion de los puertos y el estado de los contenedores de Docker para Root The Box y OWASP Juice Shop.

**NOTA:** Este canal es utilizado para la comunicacion interna entre componentes. No se recomienda utilizar para clientes.

### client_channel

Este canal ofrece informacion parcial sobre los contenedores de OWASP Juice Shop, ya que el estado de estos contenedores son los unicos que deben reflejarse en los clientes con usuarios sin permisos administrativos.

**NOTA:** Es recomendado utilizar este canal para comunicar el estado en tiempo real con los clientes.

---

## LOGS
Los logs de `JuiceBoxEngine` se centralizan en `journald`, el gestor de logs de `systemd`.

### Configuracion

#### Activar persistencia
Por defecto, journald guarda los registros en memoria y no sobreviven a reinicios. Para habilitar almacenamiento persistente:

Modifica el archivo `/etc/systemd/journald.conf`:

```bash
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


# Descomentar las opciones que quieras configurar
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

Luego se debe reiniciar el servicio de `systemd-journald` ejecutando el comando:

```
sudo systemctl restart systemd-journald

```

### Ver los logs

Para ver los logs, ejecutar desde la terminal:

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
