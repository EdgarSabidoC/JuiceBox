import logging
from systemd.journal import JournalHandler, LOG_INFO, LOG_DEBUG, LOG_WARNING, LOG_ERR


class Logger:
    """
    Logger que envía mensajes directamente a journald a través de JournalHandler
    o, en caso de no usar journald, a la salida estándar.

    Permite configurar:
      - Nombre del logger.
      - Nivel de logging.
      - Uso de journald o StreamHandler.
      - Identificador SYSLOG_IDENTIFIER para journald.
    """

    def __init__(
        self,
        name: str,
        to_journal: bool = True,
        identifier: str | None = None,
        level: int = logging.INFO,
    ):
        """
        Inicializa un logger personalizado.

        Args:
            name (str): Nombre del logger.
            to_journal (bool, opcional): Si se debe enviar mensajes a journald. Por defecto True.
            identifier (str | None, opcional): Identificador SYSLOG_IDENTIFIER para journald. Por defecto None.
            level (int, opcional): Nivel de logging (e.g., logging.INFO, logging.DEBUG). Por defecto logging.INFO.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        if not self.logger.handlers:
            if to_journal:
                # Crea un JournalHandler con SYSLOG_IDENTIFIER
                handler = JournalHandler(SYSLOG_IDENTIFIER=identifier or name)
            else:
                # Fallback a salida estándar si no quieres journald
                handler = logging.StreamHandler()

            # Formateo (opcional, journald ya añade timestamp y levels)
            fmt = "[%(levelname)s] %(name)s: %(message)s"
            handler.setFormatter(logging.Formatter(fmt))
            self.logger.addHandler(handler)

    def get(self) -> logging.Logger:
        """
        Retorna el logger configurado.

        Returns:
            logging.Logger: Objeto logger listo para ser utilizado para registrar mensajes.
        """
        return self.logger
