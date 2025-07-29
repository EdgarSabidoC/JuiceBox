from .utils.logger import Logger


class Monitor:
    """
    Clase para monitorear y registrar eventos importantes del sistema JuiceBoxEngine,
    usando un logger configurado.

    Proporciona métodos para registrar distintos niveles de mensajes y eventos comunes,
    como conexión de clientes o recepción de comandos.

    Parámetros:
    -----------
    name : str, opcional (default="JuiceBoxEngine")
        Nombre del logger que se usará para identificar los mensajes de log.
    use_syslog : bool, opcional (default=False)
        Si es True, el logger enviará los logs a syslog del sistema; si es False,
        los enviará a la consola estándar.

    Métodos:
    --------
    info(message: str)
        Registra un mensaje informativo (nivel INFO).
    warning(message: str)
        Registra un mensaje de advertencia (nivel WARNING).
    error(message: str)
        Registra un mensaje de error (nivel ERROR).
    command_received(prog: str, command: str)
        Registra un evento indicando que se recibió un comando, con el programa y el comando.
    client_connected(address: Optional)
        Registra la conexión de un nuevo cliente, opcionalmente indicando su dirección.
    client_error(err: Exception)
        Registra un error relacionado con un cliente.
    """

    def __init__(
        self,
        name: str = "JuiceBoxEngine",
        use_syslog: bool = False,
        syslog_addr="/dev/log",
        facility: int = Logger.LOG_USER,  # usa el mismo facility por defecto
    ):
        self.logger = Logger(
            name=name,
            to_syslog=use_syslog,
            syslog_addr=syslog_addr,
            facility=facility,
        ).get()

    def info(self, message: str):
        """Registra un mensaje informativo."""
        self.logger.info(message)

    def warning(self, message: str):
        """Registra un mensaje de advertencia."""
        self.logger.warning(message)

    def error(self, message: str):
        """Registra un mensaje de error."""
        self.logger.error(message)

    def command_received(self, prog: str, command: str, address: str):
        """Registra la recepción de un comando específico."""
        self.logger.info(f"[{address}] {prog} -> {command}")

    def client_connected(self, address=None):
        """
        Registra la conexión de un nuevo cliente.

        Parámetros:
        -----------
        address : Optional
            Dirección o información adicional del cliente que se conectó.
        """
        suffix = f" desde {address}" if address else ""
        self.logger.info(f"New client connected: {suffix}")

    def client_error(self, err: Exception):
        """Registra un error que ocurrió en la conexión o interacción con un cliente."""
        self.logger.warning(f"Client error: {err}")
