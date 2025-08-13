import asyncio
import json
from dotenv import dotenv_values
from Models import Response, Status

SOCKET_PATH: str | None = dotenv_values().get(
    "JUICEBOX_SOCKET", "/run/juicebox/juicebox.sock"
)


class JuiceBoxAPI:
    """
    API que expone las operaciones principales y que permite la comunicación con JuiceBoxEngine.
    """

    @staticmethod
    # Envía un comando para un programa al JuiceBoxEngine
    async def __send_command(prog: str, command: str, args: dict = {}) -> Response:
        # 1) DEBUG: indicar que vamos a conectar
        try:
            reader, writer = await asyncio.open_unix_connection(path=SOCKET_PATH)
        except Exception as e:
            return Response.error(
                message=f"Client connection error: {e}",
                data={},
            )

        # 2) Montar payload y añadir '\n'
        payload: dict[str, str | dict[str, str | int]] = {
            "prog": prog,
            "command": command,
        }
        if args:
            payload["args"] = args
        raw = json.dumps(payload)
        writer.write(raw.encode("utf-8") + b"\n")
        await writer.drain()

        # 3) Leer hasta la línea
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
            data=json_resp.data,
        )
        return resp

    # GET --------------------------------------------------------------

    @staticmethod
    # Obtener configuración de un manager (RTB o JS)
    async def __get_config(prog: str) -> Response:
        resp = await JuiceBoxAPI.__send_command(prog, "__CONFIG__")
        if resp.status == Status.OK:
            return Response.ok(data=resp.data)
        return Response.error(message=f"{prog} config couldn't be retrieved", data={})

    @staticmethod
    # Obtener la configuración del manager de RTB
    async def get_rtb_config() -> Response:
        return await JuiceBoxAPI.__get_config("RTB")

    @staticmethod
    # Obtener la configuración del manager de JS
    async def get_js_config() -> Response:
        return await JuiceBoxAPI.__get_config("JS")

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
        return await JuiceBoxAPI.__get_status("RTB")

    @staticmethod
    # Obtener estado del manager de JS
    async def get_js_status() -> Response:
        return await JuiceBoxAPI.__get_status("JS")

    @staticmethod
    # Obtiene el estado de un contenedor de JS por su puerto
    async def get_js_container_status_by_port(port: int) -> Response:
        return await JuiceBoxAPI.__send_command(
            "JS", "__CONTAINER_STATUS__", args={"port": port}
        )

    @staticmethod
    # Obtiene el estado de un contenedor de JS por su nombre de contenedor
    async def get_js_container_status_by_name(name: str) -> Response:
        return await JuiceBoxAPI.__send_command(
            "JS", "__CONTAINER_STATUS__", args={"container": name}
        )

    @staticmethod
    # Reiniciar manager
    async def __restart_manager(prog: str) -> Response:
        resp = await JuiceBoxAPI.__send_command(prog, "__RESTART__")
        if resp.status == Status.OK:
            return Response.ok(message=f"{prog} has been restarted!")
        return Response.error(message=f"{prog} couldn't be restarted", data={})

    @staticmethod
    # Reinicia el manager de RTB
    async def restart_rtb_status() -> Response:
        return await JuiceBoxAPI.__restart_manager("RTB")

    @staticmethod
    # Reinicia el manager de JS
    async def restart_js_status() -> Response:
        return await JuiceBoxAPI.__restart_manager("JS")

    # SET --------------------------------------------------------------
    @staticmethod
    # Modifica la configuración de RTB
    async def set_rtb_config(config: dict[str, str | int]) -> Response:
        return await JuiceBoxAPI.__send_command(
            prog="RTB", command="__SET_CONFIG__", args=config
        )

    @staticmethod
    # Modifica la configuración de RTB
    async def set_js_config(config: dict[str, str | list[int]]) -> Response:
        return await JuiceBoxAPI.__send_command(
            prog="JS", command="__SET_CONFIG__", args=config
        )

    # START ------------------------------------------------------------

    @staticmethod
    # Inicia los contenedores de RTB
    async def start_rtb() -> Response:
        return await JuiceBoxAPI.__send_command(prog="RTB", command="__START__")

    @staticmethod
    # Inicia los contenedores de JS
    async def start_js_container() -> Response:
        return await JuiceBoxAPI.__send_command(prog="JS", command="__START__")

    # STOP --------------------------------------------------------------

    @staticmethod
    # Detiene un manager (RTB o JS)
    async def __stop_manager(prog: str) -> Response:
        return await JuiceBoxAPI.__send_command(prog, "__STOP__")

    @staticmethod
    # Detiene el manager de RTB
    async def stop_rtb() -> Response:
        return await JuiceBoxAPI.__stop_manager("RTB")

    @staticmethod
    # Detiene el manager de JS
    async def stop_js() -> Response:
        return await JuiceBoxAPI.__stop_manager("JS")

    @staticmethod
    # Detiene un contenedor de JS
    async def stop_js_container(port: int):
        return await JuiceBoxAPI.__send_command(
            "JS", "__STOP__CONTAINER", args={"port": port}
        )

    # MISCELLANEOUS ----------------------------------------------------

    @staticmethod
    # Genera el XML de missions para Root The Box
    async def generate_xml() -> Response:
        return await JuiceBoxAPI.__send_command("JS", "__GENERATE_XML__")
