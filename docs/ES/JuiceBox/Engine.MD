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
│   └── Socket de UNIX
├── TUI
├── WebClient
│   └── API REST
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
