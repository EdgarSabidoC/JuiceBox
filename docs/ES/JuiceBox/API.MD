# JuiceBoxAPI — Interfaz de Comunicacion con JuiceBoxEngine

La API de Python ofrece metodos publicos para facilitar la comunicacion con el motor de `Juice Box` y clientes hechos con `Python`.

## Descripcion General

JuiceBoxAPI es una interfaz asincrona que permite comunicarse con el motor principal `Juice Box Engine` mediante sockets UNIX.
Permite `iniciar`, `detener`, `reiniciar` y `consultar` el estado de los programas:

- RTB (Root The Box)
- JS (OWASP Juice Shop)

Internamente, los comandos se envian en formato `JSON` al socket definido en la variable de entorno `JUICEBOX_SOCKET`.

## Configuracion de entorno

El archivo .env define las siguientes variables (son generadas de forma dinamica exceptuando el `JUICEBOX_SOCKET`):

| Variable          | Descripcion                                | Valor por defecto               |
| ----------------- | ------------------------------------------ | ------------------------------- |
| `JUICEBOX_SOCKET` | Ruta del socket UNIX de `Juice Box Engine` | `/opt/juicebox/run/engine.sock` |
| `REDIS_PASSWORD`  | Contraseña para Redis                      | `C5L48`                         |


## Estructura de clases

| Constante      | Programa | Descripcion      |
| -------------- | -------- | ---------------- |
| `Programs.RTB` | `"RTB"`  | Root The Box     |
| `Programs.JS`  | `"JS"`   | OWASP Juice Shop |


## JuiceBoxAPI

Clase estatica que agrupa todas las operaciones disponibles para interactuar con `Juice Box Engine`.

Para importar la API es necesario añadir la carpeta con un `__init__.py` dentro en la carpeta raiz de `Juice Box`, ya que se utiliza un entorno virtual (venv).

Se puede importar en `Python` como:

```python
from JuiceBox.Engine.api import JuiceBoxAPI
```

## Formato de mensaje enviado

```bash
{
  "prog": "RTB | JS",
  "command": "__COMMAND__",
  "args": { "clave": "valor" }
}
```

## Formato de respuesta

Cada metodo devuelve un objeto Response, que no es mas que un JSON con los atributos:

```bash
{
  "status": "ok | error",
  "message": "Descripcion",
  "data": { ... }
}
```

## Notas

- El socket debe existir y ser accesible por el usuario que ejecuta la API.
- Cada operacion es asincrona y debe ejecutarse dentro de un asyncio event loop.
- Si el socket no esta disponible, se devuelve un Response con status="error".

# Metodos publicos

## Metodos GET (consultas)

| Metodo                                  | Descripcion                                 | Programa | Argumentos  | Ejemplo                                                             |
| --------------------------------------- | ------------------------------------------- | -------- | ----------- | ------------------------------------------------------------------- |
| `get_rtb_config()`                      | Obtiene la configuracion del manager de RTB | RTB      | —           | `await JuiceBoxAPI.get_rtb_config()`                                |
| `get_js_config()`                       | Obtiene la configuracion del manager de JS  | JS       | —           | `await JuiceBoxAPI.get_js_config()`                                 |
| `get_rtb_status()`                      | Estado actual del manager de RTB            | RTB      | —           | `await JuiceBoxAPI.get_rtb_status()`                                |
| `get_js_status()`                       | Estado actual del manager de JS             | JS       | —           | `await JuiceBoxAPI.get_js_status()`                                 |
| `get_js_container_status_by_port(port)` | Estado de contenedor JS por puerto          | JS       | `port: int` | `await JuiceBoxAPI.get_js_container_status_by_port(5000)`           |
| `get_js_container_status_by_name(name)` | Estado de contenedor JS por nombre          | JS       | `name: str` | `await JuiceBoxAPI.get_js_container_status_by_name("juice-shop_1")` |

## Metodos RESTART (reinicio)

| Metodo                 | Descripcion                | Programa | Ejemplo                                  |
| ---------------------- | -------------------------- | -------- | ---------------------------------------- |
| `restart_rtb_status()` | Reinicia el manager de RTB | RTB      | `await JuiceBoxAPI.restart_rtb_status()` |
| `restart_js_status()`  | Reinicia el manager de JS  | JS       | `await JuiceBoxAPI.restart_js_status()`  |


## Metodos SET (configuracion)

| Metodo                   | Descripcion                       | Argumentos                    | Ejemplo                                                       |
| ------------------------ | --------------------------------- | ----------------------------- | ------------------------------------------------------------- |
| `set_rtb_config(config)` | Actualiza la configuracion de RTB | `dict[str, str \| int]`       | `await JuiceBoxAPI.set_rtb_config({"sql_dialect": "sqlite"})` |
| `set_js_config(config)`  | Actualiza la configuracion de JS  | `dict[str, str \| list[int]]` | `await JuiceBoxAPI.set_js_config({"ports": [5000, 5001]})`    |


## Metodos START (arranque/inicio)

| Metodo                     | Descripcion                             | Programa | Ejemplo                                      |
| -------------------------- | --------------------------------------- | -------- | -------------------------------------------- |
| `start_rtb()`              | Inicia los contenedores de Root The Box | RTB      | `await JuiceBoxAPI.start_rtb()`              |
| `start_js_container()`     | Inicia un contenedor de Juice Shop      | JS       | `await JuiceBoxAPI.start_js_container()`     |
| `start_n_js_containers(n)` | Inicia `n` contenedores de Juice Shop   | JS       | `await JuiceBoxAPI.start_n_js_containers(3)` |


## Metodos STOP (detencion)

| Metodo                    | Descripcion                                        | Programa | Argumentos  | Ejemplo                                     |
| ------------------------- | -------------------------------------------------- | -------- | ----------- | ------------------------------------------- |
| `stop_rtb()`              | Detiene el manager de Root The Box                 | RTB      | —           | `await JuiceBoxAPI.stop_rtb()`              |
| `stop_js()`               | Detiene el manager de Juice Shop                   | JS       | —           | `await JuiceBoxAPI.stop_js()`               |
| `stop_js_container(port)` | Detiene un contenedor de Juice Shop dado su puerto | JS       | `port: int` | `await JuiceBoxAPI.stop_js_container(5000)` |


## Metodos miscelaneos

| Metodo                 | Descripcion                                                          | Ejemplo                                  |
| ---------------------- | -------------------------------------------------------------------- | ---------------------------------------- |
| `generate_xml()`       | Genera el archivo `missions.xml` para importar retos en Root The Box | `await JuiceBoxAPI.generate_xml()`       |
| `get_js_ports_range()` | Devuelve el rango de puertos usados por Juice Shop                   | `await JuiceBoxAPI.get_js_ports_range()` |
