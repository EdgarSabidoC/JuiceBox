# Acerca de la API

La API de Python ofrece métodos públicos para facilitar la comunicación con el motor de `Juice Box` y clientes hechos con Python.

## Formato de mensaje enviado

```bash
{
  "prog": "RTB | JS",
  "command": "__COMMAND__",
  "args": { "clave": "valor" }
}
```

## Formato de respuesta

```bash
{
  "status": "ok | error",
  "message": "Descripción",
  "data": { ... }
}
```

# Métodos públicos

## get\_rtb\_config()

### Comando

`__CONFIG__`

### Descripción

Obtiene la configuración del manager de Root The Box.

### Argumentos

```
N/A
```

### Ejemplo

```python
await JuiceBoxAPI.get_rtb_config()
```

---

## get\_js\_config()

### Comando

`__CONFIG__`

### Descripción

Obtiene la configuración del manager de OWASP Juice Shop.

### Argumentos

```
N/A
```

### Ejemplo

```python
await JuiceBoxAPI.get_js_config()
```

---

## get\_rtb\_status()

### Comando

`__STATUS__`

### Descripción

Obtiene el estado del manager de Root The Box.

### Argumentos

```
N/A
```

### Ejemplo

```python
await JuiceBoxAPI.get_rtb_status()
```

---

## get\_js\_status()

### Comando

`__STATUS__`

### Descripción

Obtiene el estado del manager de OWASP Juice Shop.

### Argumentos

```
N/A
```

### Ejemplo

```python
await JuiceBoxAPI.get_js_status()
```

---

## get\_js\_container\_status\_by\_port(port: int)

### Comando

`__CONTAINER_STATUS__`

### Descripción

Obtiene el estado de un contenedor de Juice Shop por su puerto.

### Argumentos

```bash
port: int
```

### Ejemplo

```python
await JuiceBoxAPI.get_js_container_status_by_port(3000)
```

---

## get\_js\_container\_status\_by\_name(name: str)

### Comando

`__CONTAINER_STATUS__`

### Descripción

Obtiene el estado de un contenedor de Juice Shop por su nombre.

### Argumentos

```bash
name: str
```

### Ejemplo

```python
await JuiceBoxAPI.get_js_container_status_by_name("juice_container")
```

---

## restart\_rtb\_status()

### Comando

`__RESTART__`

### Descripción

Reinicia el manager de Root The Box.

### Argumentos

```
N/A
```

### Ejemplo

```python
await JuiceBoxAPI.restart_rtb_status()
```

---

## restart\_js\_status()

### Comando

`__RESTART__`

### Descripción

Reinicia el manager de OWASP Juice Shop.

### Argumentos

```
N/A
```

### Ejemplo

```python
await JuiceBoxAPI.restart_js_status()
```

---

## set\_rtb\_config(config: dict)

### Comando

`__SET_CONFIG__`

### Descripción

Modifica la configuración del manager de Root The Box.

### Argumentos

```bash
config: dict[str, str | int]
```

### Ejemplo

```python
await JuiceBoxAPI.set_rtb_config({"max_users": 10})
```

---

## set\_js\_config(config: dict)

### Comando

`__SET_CONFIG__`

### Descripción

Modifica la configuración del manager de OWASP Juice Shop.

### Argumentos

```bash
config: dict[str, str | list[int]]
```

### Ejemplo

```python
await JuiceBoxAPI.set_js_config({"ports": [3000, 3001]})
```

---

## start\_rtb()

### Comando

`__START__`

### Descripción

Inicia los contenedores de Root The Box.

### Argumentos

```
N/A
```

### Ejemplo

```python
await JuiceBoxAPI.start_rtb()
```

---

## start\_js\_container()

### Comando

`__START__`

### Descripción

Inicia los contenedores de OWASP Juice Shop.

### Argumentos

```
N/A
```

### Ejemplo

```python
await JuiceBoxAPI.start_js_container()
```

---

## stop\_rtb()

### Comando

`__STOP__`

### Descripción

Detiene el manager de Root The Box.

### Argumentos

```
N/A
```

### Ejemplo

```python
await JuiceBoxAPI.stop_rtb()
```

---

## stop\_js()

### Comando

`__STOP__`

### Descripción

Detiene el manager de OWASP Juice Shop.

### Argumentos

```
N/A
```

### Ejemplo

```python
await JuiceBoxAPI.stop_js()
```

---

## stop\_js\_container(port: int)

### Comando

`__STOP_CONTAINER__`

### Descripción

Detiene un contenedor de Juice Shop dado su puerto.

### Argumentos

```bash
port: int
```

### Ejemplo

```python
await JuiceBoxAPI.stop_js_container(3000)
```

---

## generate\_xml()

### Comando

`__GENERATE_XML__`

### Descripción

Genera el archivo XML de misiones para Root The Box.

### Argumentos

```
N/A
```

### Ejemplo

```python
await JuiceBoxAPI.generate_xml()
```

---
