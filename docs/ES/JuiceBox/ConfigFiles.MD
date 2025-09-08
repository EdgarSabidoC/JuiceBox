# Archivos de configuración (Config files)

Los archivos de configuración de `Juice Box Engine` se encuentran en la ruta: `JuiceBox/JuiceBoxEngine/configs`.

**NOTA:** NO se recomienda modificar los archivos de configuración directamente, lo recomendable es utilizar la interfaz basada en texto (TUI). La leyenda `[NO MODIFICAR]` aparecerá junto a los nombres de los archivos que bajo ninguna circunstancia deben ser modificados, ya que estos son generados de manera automática por el motor o son utilizados por partes críticas del motor.

## juiceShop.json
Contiene las variables para la configuración y creación de los contenedores de la OWASP Juice Shop.

### Ejemplo

```
{
  "CONTAINERS_NAME": "owasp-juice-shop-",
  "PORTS_RANGE": [
    3000,
    3004
  ],
  "CTF_KEY": "test",
  "NODE_ENV": "ctf",
  "DETACH_MODE": true
}
```

## juiceShopRTBConfig.yml
Contiene la configuración para el contenedor de Docker que genera el archivo XML con los desafíos/misiones y las banderas de la JuiceShop para Root The Box.

### Ejemplo

```
ctfFramework: RootTheBox
juiceShopUrl: https://juice-shop.herokuapp.com
ctfKey: test
countryMapping: https://raw.githubusercontent.com/juice-shop/juice-shop/master/config/fbctf.yml
insertHints: free
insertHintUrls: free
insertHintSnippets: free
```

## missions.xml [NO MODIFICAR]
Archivo de configuración para importar las misiones/desafíos y banderas de la JuiceShop en el motor CTF de Root The Box.

## rootTheBox.json
Contiene las variables para la configuración y creación de los contenedores de Root The Box.

### Ejemplo

```
{
  "WEBAPP_PORT": 8888,
  "MEMCACHED_PORT": 11211,
  "NETWORK_NAME": "rootthebox_default",
  "RTB_DIRECTORY": "RootTheBox",
  "WEB_APP_CONTAINER_NAME": "rootthebox-webapp-1",
  "MEMCACHED_CONTAINER_NAME": "rootthebox-memcached-1"
}
```

## redis-docker-compose.yml [NO MODIFICAR]
Instrucciones para que Docker Compose cree el contenedor de Redis.

### Ejemplo

```
services:
  redis:  # Definición del servicio Redis
    image: redis:7-alpine
    # Usa la imagen oficial de Redis en su versión 7 sobre Alpine Linux (ligera).
    container_name: juicebox-redis
    # Nombre fijo del contenedor. Facilita comandos como `docker ps` o `docker logs`.
    restart: unless-stopped
    # Política de reinicio:
    # - always: reinicia siempre cuando el contenedor pare inesperadamente.
    # - unless-stopped: idem, pero no tras un `docker stop`.
    command: ["redis-server", "/usr/local/etc/redis/redis.conf"]
    # Sobrescribe el comando por defecto, apuntando a tu archivo de configuración.
    ports:
      - "127.0.0.1:6379:6379"
    # Mapea el puerto 6379 del contenedor al mismo puerto en localhost del host.
    # Queda inaccesible desde otras interfaces de red externas.
    volumes:
      - redis-data:/data
      # Volumen nombrado para persistir los datos de Redis.
      # Docker gestiona su ubicación interna automáticamente.
      - ./redis.conf:/usr/local/etc/redis/redis.conf:ro
    # Monta tu archivo local `redis.conf` como solo lectura dentro del contenedor.
    healthcheck:
      # Verifica periódicamente que Redis responda al comando PING.
      test: ["CMD", "redis-cli", "-a", "C5L48", "ping"]
      interval: 10s   # Tiempo entre cada comprobación.
      timeout: 5s     # Tiempo máximo de espera de una sola comprobación.
      retries: 5      # Reintentos antes de marcar el contenedor como “unhealthy”.

volumes:
  redis-data:
    driver: local
      # Controlador por defecto. Los datos quedan en el host bajo
      # /var/lib/docker/volumes/redis-data/_data (o ruta configurada en el Docker daemon).
```

## redis.conf [NO MODIFICAR]
Archivo de configuración para redis

### Ejemplo

```
# Solo escucha en localhost
bind 0.0.0.0

# Si alguien accidentalmente cambia bind, este modo repele conexiones externas
protected-mode no

# Contraseña de autenticación
requirepass C5L48

# Persistencia AOF
appendonly yes
```
