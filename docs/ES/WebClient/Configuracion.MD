# Archivos de configuracion

El `Juice Box WebClient` solo tiene un archivo `.env` de configuracion para las variables de entorno.

# Configuracion de las variables de entorno

```bash
HOST=str
PORT=int
DEBUG=str(bool)
```

Donde:

- `HOST`: Es una cadena con la IP en la escuchara el servicio de la API REST.
- `PORT`: Es un entero que indica el puerto donde escuchara el servcio.
- `DEBUG`: Indica si el servicio esta corriendo en modo debug utilizando `uvicorn` para el entorno de desarrollo. No es relevante si se instala como servicio, ya que este correra a traves de `systemd` utilizando `gunicorn`.
