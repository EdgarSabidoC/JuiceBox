# Manual de la OWASP Juice Shop

## Generalidades

De forma predeterminada existen `10` contenedores de Docker que corren la OWASP Juice Shop.

Cada uno de estos contenedores corre en el rango de puertos que van del `3001` al `3010`

## Acceso al sitio de los contenedores

Para poder acceder a alguno de los sitios de la OWASP Juice Shop es necesario que el contenedor del servicio este activo en el puerto correspondiente.

Para acceder al sitio web de alguno de los contenedores basta con utilizar el enlace:

`http://ctf.uady:{puerto}`

O utilizar el enlace por medio de la IP:

`172.16.200.11:{puerto}`

## Mas informacion

Para mas informacion visitar [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/)