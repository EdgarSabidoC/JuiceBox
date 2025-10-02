# Uso de Juice Box Manager TUI

## Correr la aplicacion Juice Box Manager TUI

Para correr la apliacion solo es necesario ejecutar el comando:

```bash
juicebox-tui
```

## Herramientas administrativas de Root The Box

### Comandos

- `Start`: Inicia los contenedores del servicio de Root The Box (webapp y cache).
- `Stop`: Detiene el servicio de Root The Box (manejador y contenedores).
- `Restart`: Reinicia el servicio (manejador) de Root The Box y el contenedor de la webapp y el cache.
- `Configuration`: Permite cambiar la configuracion del manejador de Root The Box dentro del motor.

### Configuracion

La configuracion del manejador de la OWASP Juice Shop, permite configurar los siguientes campos:

```bash
{
    "webapp_port": int,
    "memcached_port": int,
}
```
Donde:

- `webapp_port`: Puerto del host que se expone para el contenedor de la aplicacion web (webapp) de Root The Box.
- `memcached_port`: Puerto del host que se expone para el contenedor del cache de Root The Box.

## Herramientas administrativas de Juice Shop

### Comandos

- `Start a container`: Inicia un contenedor de la OWASP Juice Shop en un puerto disponible.
- `Start n containers`: Inicializa N contenedores de la OWASP Juice Shop dentro de los puertos disponibles.
- `Stop a container`: Detiene un contenedor en especifico a traves de su puerto.
- `Stop all containers`: Detiene todos los contenedores que esten activos.
- `Restart`: Reinicia el servicio (manejador) de la OWASP Juice Shop.
- `Configuration`: Permite cambiar la configuracion del manejador de la OWASP Juice Shop dentro del motor.
- `Generate missions`: Genera el archivo XML de misiones de la OWASP Juice Shop para Root The Box.

### Configuracion

La configuracion del manejador de la OWASP Juice Shop, permite configurar los siguientes campos:

```bash
{
    "ports_range": [int, int],
    "lifespan": int,
    "ctf_key": str
}
```
Donde:

- `ports_range`: Es una lista de dos enteros [min, max] que representa el intervalo de puertos disponibles para la creacion de los contenedores de la OWASP Juice Shop.
- `lifespan`: Tiempo de vida en minutos de los contenedores de la OWASP Juice Shop.
- `ctf_key`: Clave utilizada para generar el archivo XML de las misiones de la OWASP Juice Shop para Root The Box.

### Archivo de misiones XML

Para poder generar un nuevo archivo XML con las misiones de la Juice Shop para Root The Box, se deben seguir los siguientes pasos:

1. Entrar a la pantalla `Juice Shop`.
2. `[ OPCIONAL ]` Cambiar la `ctf_key`, se utiliza el comando `Configuration`, desde donde se accede a la configuracion actual, se realiza el cambio y se elige la opcion `save` para guardar los cambios de la configuracion. Una vez hecho esto es necesario reiniciar con el comando `Restart` y arrancar de nuevo los contenedores de la `OWASP Juice Shop`.
3. Utilizar el comando `Generate missions` y esperar a que se genere y actualice el archvo XML para Root The Box.
4. Entrar a la pantalla `Root The Box` y ejecutar el comando `Restart`, el cual cargara el nuevo archivo XML y arrancara de nuevo los contenedores de la aplicacion web y el cache.
5. Listo, ahora ya debe estar configurado `Root The Box` con las misiones generadas de la OWASP Juice Shop. Con esto las banderas (flags) deben estar sincronizadas entre los contenedores de la `OWASP Juice Shop` y `Root The Box`.