import logging
import sys
from logging.handlers import SysLogHandler


class Logger:
    """
    Crea un logger que envía mensajes a syslog o a la consola.

    Parámetros:
    -----------
    name         : nombre del logger
    to_syslog    : si es True, usa SysLogHandler("/dev/log")
    syslog_addr  : ruta al socket de syslog (por defecto "/dev/log")
    facility     : facility de syslog (por defecto USER)
    level        : nivel mínimo de mensajes (DEBUG, INFO, etc.)

    Métodos:
    --------
    get()
        Retorna el objeto logger configurado para usar en la aplicación.
    """

    # Facilities más comunes
    LOG_KERN = SysLogHandler.LOG_KERN
    LOG_USER = SysLogHandler.LOG_USER
    LOG_LOCAL0 = SysLogHandler.LOG_LOCAL0
    LOG_LOCAL1 = SysLogHandler.LOG_LOCAL1

    def __init__(
        self,
        name: str,
        to_syslog: bool = False,
        syslog_addr="/dev/log",
        facility: int = SysLogHandler.LOG_USER,
        level: int = logging.INFO,
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        if not self.logger.handlers:
            if to_syslog:
                handler = SysLogHandler(address=syslog_addr, facility=facility)
            else:
                handler = logging.StreamHandler(sys.stdout)

            fmt = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
            handler.setFormatter(logging.Formatter(fmt, datefmt))

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
