import asyncio
import json
from dotenv import dotenv_values
from Models import Response, Status

SOCKET_PATH: str | None = dotenv_values().get(
    "JUICEBOX_SOCKET", "/run/juicebox/juicebox.sock"
)


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
    API que expone las operaciones principales y que permite la comunicación con JuiceBoxEngine.
    """

    @staticmethod
    async def __send_command(prog: str, command: str, args: dict = {}) -> Response:
        """
        Envía un comando para un programa al motor JuiceBoxEngine.

        Args:
            prog (str): RTB | JS
            command (str): Comando
            args (dict): Diccionario con argumentos para pasarle al comando.

        Returns:
            Response: Respuesta serializada en formato JSON
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
        writer.write(raw.encode("utf-8") + b"\n")  # Se añade '\n'
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
    # Envía la señarl __CONFIG__ para obtener la configuración del manager de un programa.
    async def __get_config(prog: str) -> Response:
        resp = await JuiceBoxAPI.__send_command(prog, "__CONFIG__")
        if resp.status == Status.OK:
            return Response.ok(data=resp.data)
        return Response.error(message=f"{prog} config couldn't be retrieved", data={})

    @staticmethod
    # Obtener la configuración del manager de RTB
    async def get_rtb_config() -> Response:
        return await JuiceBoxAPI.__get_config(Programs.RTB)

    @staticmethod
    # Obtener la configuración del manager de JS
    async def get_js_config() -> Response:
        return await JuiceBoxAPI.__get_config(Programs.JS)

    @staticmethod
    # Obtener estado de un contenedor
    async def __get_status(prog: str) -> Response:
        resp = await JuiceBoxAPI.__send_command(prog, "__STATUS__")
        if resp.status == Status.OK:
            return Response.ok(data=resp.data)
        return Response.error(message=f"{prog} status couldn't be retrieved", data={})

    @staticmethod
    # Obtener estado del manager de RTB
    async def get_rtb_status() -> Response:
        return await JuiceBoxAPI.__get_status(Programs.RTB)

    @staticmethod
    # Obtener estado del manager de JS
    async def get_js_status() -> Response:
        return await JuiceBoxAPI.__get_status(Programs.JS)

    @staticmethod
    # Obtiene el estado de un contenedor de JS por su puerto
    async def get_js_container_status_by_port(port: int) -> Response:
        return await JuiceBoxAPI.__send_command(
            Programs.JS, "__CONTAINER_STATUS__", args={"port": port}
        )

    @staticmethod
    # Obtiene el estado de un contenedor de JS por su nombre de contenedor
    async def get_js_container_status_by_name(name: str) -> Response:
        return await JuiceBoxAPI.__send_command(
            Programs.JS, "__CONTAINER_STATUS__", args={"container": name}
        )

    # RESTART ----------------------------------------------------------

    @staticmethod
    # Envía la señarl __RESTART__ para reiniciar el manager de un programa.
    async def __restart_manager(prog: str) -> Response:
        resp = await JuiceBoxAPI.__send_command(prog, "__RESTART__")
        if resp.status == Status.OK:
            return Response.ok(message=f"{prog} has been restarted!")
        return Response.error(message=f"{prog} couldn't be restarted", data={})

    @staticmethod
    # Reinicia el manager de RTB
    async def restart_rtb_status() -> Response:
        return await JuiceBoxAPI.__restart_manager(Programs.RTB)

    @staticmethod
    # Reinicia el manager de JS
    async def restart_js_status() -> Response:
        return await JuiceBoxAPI.__restart_manager(Programs.JS)

    # SET --------------------------------------------------------------
    @staticmethod
    # Envía la señal __SET_CONFIG__ para modificar la configuración del manager de un programa.
    async def __set_config(prog: str, config: dict) -> Response:
        return await JuiceBoxAPI.__send_command(
            prog=prog, command="__SET_CONFIG__", args=config
        )

    @staticmethod
    # Modifica la configuración de RTB
    async def set_rtb_config(config: dict[str, str | int]) -> Response:
        return await JuiceBoxAPI.__set_config(prog=Programs.RTB, config=config)

    @staticmethod
    # Modifica la configuración de JS
    async def set_js_config(config: dict[str, str | list[int]]) -> Response:
        return await JuiceBoxAPI.__set_config(prog=Programs.JS, config=config)

    # START ------------------------------------------------------------

    @staticmethod
    # Envía la señal __START__ de un programa al motor para iniciar su manager.
    async def __start(prog: str) -> Response:
        return await JuiceBoxAPI.__send_command(prog=prog, command="__START__")

    @staticmethod
    # Inicia los contenedores de RTB
    async def start_rtb() -> Response:
        return await JuiceBoxAPI.__start(Programs.RTB)

    @staticmethod
    # Inicia los contenedores de JS
    async def start_js_container() -> Response:
        return await JuiceBoxAPI.__start(Programs.JS)

    # STOP --------------------------------------------------------------

    @staticmethod
    # Envía la señal __STOP__ de un programa al motor para detener su manager
    async def __stop_manager(prog: str) -> Response:
        return await JuiceBoxAPI.__send_command(prog, "__STOP__")

    @staticmethod
    # Detiene el manager de RTB
    async def stop_rtb() -> Response:
        return await JuiceBoxAPI.__stop_manager(Programs.RTB)

    @staticmethod
    # Detiene el manager de JS
    async def stop_js() -> Response:
        return await JuiceBoxAPI.__stop_manager(Programs.JS)

    @staticmethod
    # Envía la señal __STOP_CONTAINER__ para detener un contenedor de JS.
    async def stop_js_container(port: int):
        return await JuiceBoxAPI.__send_command(
            Programs.JS, "__STOP_CONTAINER__", args={"port": port}
        )

    # MISCELLANEOUS ----------------------------------------------------

    @staticmethod
    # Envía la señal __GENERATE_XML__ para generar el XML de missions para Root The Box.
    async def generate_xml() -> Response:
        return await JuiceBoxAPI.__send_command(Programs.JS, "__GENERATE_XML__")
