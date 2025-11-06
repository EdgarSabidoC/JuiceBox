
# API REST

La URL tiene la estructura: `http://{HOST}:{PORT}/api/v1/juice-shop`

La URL de forma predeterminada se encuentra en: `http://ctf.uady:8080/api/v1/juice-shop`

O tambien se puede acceder por medio de la IP predeterminada: `172.16.200.11:8080/api/v1/juice-shop`

El `HOST` donde corre la API REST de forma predeterminada es: `172.16.200.11`. Con el `PORT` predeterminado: `8080`.

## GET

Una peticion GET obtiene el estado (status) de todos los contenedores dentro del *rango de puertos disponible* para la `OWASP Juice Shop`.

### Ejemplo

#### Peticion

```bash
curl http://ctf.uady:8080/api/v1/juice-shop/
```

### Estructura de la respuesta

La respuesta tiene el siguiente formato:

```json
{
  "status": string,
  "message": string,
  "data": {
    "containers": [
      {
        "success": bool,
        "message": string,
        "error": string | null,
        "data": {
          "container": string,
          "status": string,
          "port": number
        },
          "timestamp": string
      }
    ]
  }
}
```

**Nota:** Dentro del atributo `containers` dentro de `data` estara la lista con todos los contenedores.

**Nota:** Cuando no haya un error se recibira `null`.

## POST

Una peticion `POST` permite iniciar un contenedor de la `OWASP Juice Shop` si el puerto esta `disponible`.

### Ejemplo

#### Peticion

```bash
curl -X POST http://ctf.uady:8080/api/v1/juice-shop/
```

### Estructura de la respuesta

La respuesta tiene el siguiente formato:

```json
{
    "status": string,
    "message": string,
    "data": {
        "container": string,
        "status": string,
        "port": number
    }
}
```

POST recibira como respuesta dentro de `data` la informacion del contenedor iniciado, si no se puede iniciar se recibira un `data` vacio.