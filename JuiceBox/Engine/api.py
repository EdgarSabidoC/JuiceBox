import asyncio
import json
from dotenv import dotenv_values
from Models import Response, Status

# Constante con la ruta del Socket del motor de Juice Box.
SOCKET_PATH: str | None = dotenv_values().get(
    "JUICEBOX_SOCKET", "/run/juicebox/engine.sock"
)

# Constante generada dinámicamente con la contraseña de Redis.
REDIS_PASSWORD: str | None = dotenv_values().get("REDIS_PASSWORD", "")


class Programs:
    """
    Constantes de programa.

    * RTB: Root The Box
    * JS: OWASP Juice Shop
    """

    RTB: str = "RTB"
    JS: str = "JS"


class JuiceBoxAPI:
    """
    API que expone las operaciones principales y que permite la comunicación con el motor de Juice Box.
    """

    @staticmethod
    async def __send_command(prog: str, command: str, args: dict = {}) -> Response:
        """
        Envía un comando al motor de Juice Box para un programa específico.

        Args:
            prog (str): Programa destino (RTB | JS).
            command (str): Comando a enviar.
            args (dict, opcional): Argumentos adicionales del comando.

        Returns:
            Response: Objeto con el estado, mensaje y datos devueltos por el motor.
        """
        try:
            reader, writer = await asyncio.open_unix_connection(path=SOCKET_PATH)
        except Exception as e:
            return Response.error(
                message=f"Client connection error: {e}",
                data={},
            )

        payload: dict[str, str | dict[str, str | int]] = {
            "prog": prog,
            "command": command,
        }
        if args:
            payload["args"] = args
        raw = json.dumps(payload)
        writer.write(raw.encode("utf-8") + b"\n")
        await writer.drain()

        try:
            line = await reader.readline()
        except Exception as e:
            return Response.error(f"Error while reading the line: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

        resp = line.decode("utf-8", errors="replace").strip()
        json_resp = json.loads(resp)
        resp = Response(
            status=json_resp.get("status", "error"),
            message=json_resp.get("message", "Something went wrong"),
            data=json_resp["data"],
        )
        return resp

    # GET --------------------------------------------------------------

    @staticmethod
    async def __get_config(prog: str) -> Response:
        """
        Obtiene la configuración del manager de un programa.

        Args:
            prog (str): Programa destino (RTB | JS).

        Returns:
            Response: Configuración del programa si es exitosa, error en caso contrario.
        """
        resp = await JuiceBoxAPI.__send_command(prog, "__CONFIG__")
        if resp.status == Status.OK:
            return Response.ok(data=resp.data)
        return Response.error(message=f"{prog} config couldn't be retrieved", data={})

    @staticmethod
    async def get_rtb_config() -> Response:
        """
        Obtiene la configuración del manager de RTB.

        Returns:
            Response: Configuración de RTB o error.
        """
        return await JuiceBoxAPI.__get_config(Programs.RTB)

    @staticmethod
    async def get_js_config() -> Response:
        """
        Obtiene la configuración del manager de JS.

        Returns:
            Response: Configuración de JS o error.
        """
        return await JuiceBoxAPI.__get_config(Programs.JS)

    @staticmethod
    async def __get_status(prog: str) -> Response:
        """
        Obtiene el estado de un programa.

        Args:
            prog (str): Programa destino (RTB | JS).

        Returns:
            Response: Estado del programa o error.
        """
        resp = await JuiceBoxAPI.__send_command(prog, "__STATUS__")
        if resp.status == Status.OK:
            return Response.ok(data=resp.data)
        return Response.error(message=f"{prog} status couldn't be retrieved", data={})

    @staticmethod
    async def get_rtb_status() -> Response:
        """
        Obtiene el estado del manager de RTB.

        Returns:
            Response: Estado de RTB o error.
        """
        return await JuiceBoxAPI.__get_status(Programs.RTB)

    @staticmethod
    async def get_js_status() -> Response:
        """
        Obtiene el estado del manager de JS.

        Returns:
            Response: Estado de JS o error.
        """
        return await JuiceBoxAPI.__get_status(Programs.JS)

    @staticmethod
    async def get_js_container_status_by_port(port: int) -> Response:
        """
        Obtiene el estado de un contenedor de JS dado su puerto.

        Args:
            port (int): Puerto del contenedor.

        Returns:
            Response: Estado del contenedor o error.
        """
        return await JuiceBoxAPI.__send_command(
            Programs.JS, "__CONTAINER_STATUS__", args={"port": port}
        )

    @staticmethod
    async def get_js_container_status_by_name(name: str) -> Response:
        """
        Obtiene el estado de un contenedor de JS dado su nombre.

        Args:
            name (str): Nombre del contenedor.

        Returns:
            Response: Estado del contenedor o error.
        """
        return await JuiceBoxAPI.__send_command(
            Programs.JS, "__CONTAINER_STATUS__", args={"container": name}
        )

    # RESTART ----------------------------------------------------------

    @staticmethod
    async def __restart_manager(prog: str) -> Response:
        """
        Reinicia el manager de un programa.

        Args:
            prog (str): Programa destino (RTB | JS).

        Returns:
            Response: Resultado de la operación.
        """
        resp = await JuiceBoxAPI.__send_command(prog, "__RESTART__")
        if resp.status == Status.OK:
            return Response.ok(message=f"{prog} has been restarted!")
        return Response.error(message=f"{prog} couldn't be restarted", data={})

    @staticmethod
    async def restart_rtb_status() -> Response:
        """
        Reinicia el manager de RTB.

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__restart_manager(Programs.RTB)

    @staticmethod
    async def restart_js_status() -> Response:
        """
        Reinicia el manager de JS.

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__restart_manager(Programs.JS)

    # SET --------------------------------------------------------------

    @staticmethod
    async def __set_config(prog: str, config: dict) -> Response:
        """
        Modifica la configuración de un programa.

        Args:
            prog (str): Programa destino (RTB | JS).
            config (dict): Nueva configuración.

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__send_command(
            prog=prog, command="__SET_CONFIG__", args=config
        )

    @staticmethod
    async def set_rtb_config(config: dict[str, str | int]) -> Response:
        """
        Modifica la configuración del manager de RTB.

        Args:
            config (dict[str, str | int]): Nueva configuración para RTB.

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__set_config(prog=Programs.RTB, config=config)

    @staticmethod
    async def set_js_config(config: dict[str, str | list[int]]) -> Response:
        """
        Modifica la configuración del manager de JS.

        Args:
            config (dict[str, str | list[int]]): Nueva configuración para JS.

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__set_config(prog=Programs.JS, config=config)

    # START ------------------------------------------------------------

    @staticmethod
    async def __start(prog: str) -> Response:
        """
        Inicia el manager de un programa.

        Args:
            prog (str): Programa destino (RTB | JS).

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__send_command(prog=prog, command="__START__")

    @staticmethod
    async def start_rtb() -> Response:
        """
        Inicia los contenedores de RTB.

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__start(Programs.RTB)

    @staticmethod
    async def start_js_container() -> Response:
        """
        Inicia un contenedor de JS.

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__start(Programs.JS)

    @staticmethod
    async def start_n_js_containers(n: int) -> list[Response]:
        """
        Inicia n contenedores de OWASP Juice Shop de forma secuencial.

        Args:
            n (int): Número de contenedores a iniciar.

        Returns:
            list[Response]: Lista con los resultados de cada operación de inicio.
        """

        __containers: list[Response] = []
        for _ in range(0, n):
            __response: Response = await JuiceBoxAPI.__start(Programs.JS)
            __containers.append(__response)

        return __containers

    # STOP --------------------------------------------------------------

    @staticmethod
    async def __stop_manager(prog: str) -> Response:
        """
        Detiene el manager de un programa.

        Args:
            prog (str): Programa destino (RTB | JS).

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__send_command(prog, "__STOP__")

    @staticmethod
    async def stop_rtb() -> Response:
        """
        Detiene el manager de RTB.

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__stop_manager(Programs.RTB)

    @staticmethod
    async def stop_js() -> Response:
        """
        Detiene el manager de JS.

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__stop_manager(Programs.JS)

    @staticmethod
    async def stop_js_container(port: int) -> Response:
        """
        Detiene un contenedor de JS dado su puerto.

        Args:
            port (int): Puerto del contenedor a detener.

        Returns:
            Response: Resultado de la operación.
        """
        return await JuiceBoxAPI.__send_command(
            Programs.JS, "__STOP_CONTAINER__", args={"port": port}
        )

    # MISCELLANEOUS ----------------------------------------------------

    @staticmethod
    async def generate_xml() -> Response:
        """
        Genera el archivo XML de misiones para Root The Box usando JuiceBoxEngine.

        Returns:
            Response: Resultado de la operación, incluyendo estado y mensaje.
        """
        return await JuiceBoxAPI.__send_command(Programs.JS, "__GENERATE_XML__")

    @staticmethod
    async def get_js_ports_range() -> Response:
        """
        Obtiene el rango de puertos que utiliza el manager de OWASP Juice Shop.

        Returns:
            Response: Resultado de la operación con el rango de puertos o error.
        """
        return await JuiceBoxAPI.__send_command(Programs.JS, "__PORTS_RANGE__")
