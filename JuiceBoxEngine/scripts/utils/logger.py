import logging
import sys
from logging.handlers import SysLogHandler


class Logger:
    """
    Clase envoltorio para crear un logger configurado para escribir mensajes
    ya sea a syslog de Linux (/dev/log) o a la salida estándar (consola).

    Parámetros:
    -----------
    name : str
        Nombre del logger (usualmente el nombre del módulo o componente).
    to_syslog : bool, opcional (default=False)
        Si es True, el logger enviará los mensajes a syslog usando SysLogHandler
        apuntando a /dev/log. Si es False, se enviarán a la consola estándar (stdout).
    level : int, opcional (default=logging.INFO)
        Nivel mínimo de mensajes que serán registrados. Ejemplos: DEBUG, INFO, WARNING, ERROR.

    Métodos:
    --------
    get()
        Retorna el objeto logger configurado para usar en la aplicación.
    """

    def __init__(self, name: str, to_syslog=False, level=logging.INFO):
        # Obtiene o crea un logger con el nombre dado
        self.logger = logging.getLogger(name)
        # Configura el nivel mínimo de severidad para el logger
        self.logger.setLevel(level)

        # Evita añadir múltiples handlers si ya hay alguno configurado
        if not self.logger.handlers:
            # Elige el handler: SysLogHandler para syslog o StreamHandler para consola
            handler = (
                SysLogHandler(address="/dev/log")
                if to_syslog
                else logging.StreamHandler(sys.stdout)
            )

            # Define el formato de los mensajes de log con fecha, nivel, nombre y mensaje
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
                "%Y-%m-%d %H:%M:%S",
            )
            # Asocia el formato al handler
            handler.setFormatter(formatter)
            # Añade el handler al logger
            self.logger.addHandler(handler)

    def get(self):
        """
        Retorna el logger configurado.

        Returns:
        --------
        logging.Logger
            Objeto logger listo para ser utilizado para registrar mensajes.
        """
        return self.logger
