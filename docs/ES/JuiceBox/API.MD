# Acerca de la API

La API de `JuiceBoxEngine` ofrece métodos publicos para facilitar la comunicación.

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

## get_rtb_config()

### Comando
`__CONFIG__`

### Descripción
Obtiene la configuración del manager de Root The Box.

### Argumentos
```
N/A
```

### Ejemplo

`await JuiceBoxAPI.get_rtb_config()`

---

## get_js_config()

### Comando
`__CONFIG__`

### Descripción
Obtiene la configuración del manager de la OWASP Juice Shop.

### Argumentos
```
N/A
```

### Ejemplo

`await JuiceBoxAPI.get_js_config()`

---

## MÉTODO

### Comando
`__ __`

### Descripción


### Argumentos

```bash
N/A
```

### Ejemplo
`await `

---