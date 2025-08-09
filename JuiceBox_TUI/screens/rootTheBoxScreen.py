from textual.app import ComposeResult
from textual.screen import Screen
from widgets.footer import get_footer
from widgets.header import get_header
from textual.screen import Screen
from textual.events import ScreenResume
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Static, Switch, Button, RichLog
from textual.binding import Binding
from typing import Union
import json, asyncio
from widgets.customSwitch import CustomSwitch
from textual.reactive import reactive
from widgets.reactiveMarkdown import ReactiveMarkdown
from rich.text import Text
from Models.schemas import Status
import redis, threading

SOCKET_PATH = "/tmp/juiceboxengine.sock"


class RootTheBoxScreen(Screen):
    CSS_PATH = "../styles/rootTheBox.tcss"
    with open("media/RootTheBoxLogo.txt", "r", encoding="utf-8") as file:
        JB_LOGO = file.read()

    BINDINGS = [
        Binding("ctrl+b", "go_back", "Back", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    _power_busy: bool = False
    _ignore_switch_event: bool = True

    def compose(self) -> ComposeResult:
        # Header
        yield get_header()

        with Horizontal(classes="hcontainer") as hcontainer:
            hcontainer.can_focus = False

            with Vertical(classes="vcontainer1") as vcontainer1:
                vcontainer1.can_focus = False
                # Logo de RTB
                jb_logo = Static(self.JB_LOGO, classes="rtb-logo")
                jb_logo.can_focus = False
                yield jb_logo

                self.controllers_container = Vertical(classes="controllers-container")
                with self.controllers_container:
                    with Horizontal(classes="controllers"):
                        yield Label("Power:", classes="controller-label")
                        self.power = Switch(value=True, name="power")
                        yield self.power
                    with Horizontal(classes="controllers"):
                        self.reset = Button(
                            label="Restart",
                            variant="default",
                            name="reset",
                        )
                        yield self.reset

                # Información sobre las opciones
                self.info = Static(classes="info-box")
                self.info.can_focus = False
                self.info.border_title = "Output"
                yield self.info

            with Vertical(classes="vcontainer2") as vcontainer2:
                vcontainer2.can_focus = False
                self.config_container = ScrollableContainer(classes="config-container")
                self.config_container.border_title = "Configuration"
                self.config_data = ReactiveMarkdown(data="Loading configuration…")
                self.config_data.can_focus = False
                self.config_data.styles.color = "white"
                self.config_container.can_focus = False
                with self.config_container:
                    yield self.config_data

                # Services status
                with Horizontal() as server_status:
                    server_status.can_focus = False
                    server_status.styles.content_align = ("center", "middle")
                    server_status.styles.align = ("center", "middle")
                    server_status.styles.border
                    with Vertical(classes="services-status-keys") as server_info_keys:
                        server_info_keys.can_focus = False
                        self.SERVICES_STATUS_KEYS_WEBAPP = Label(
                            classes="services-status-key"
                        )
                        self.SERVICES_STATUS_KEYS_WEBAPP.update("Webapp: ")
                        yield self.SERVICES_STATUS_KEYS_WEBAPP
                        self.SERVICES_STATUS_KEYS_CACHE = Label(
                            classes="services-status-key"
                        )
                        self.SERVICES_STATUS_KEYS_CACHE.update("Caché: ")
                        yield self.SERVICES_STATUS_KEYS_CACHE
                    with Vertical(
                        classes="services-status-data"
                    ) as services_status_values:
                        services_status_values.can_focus = False
                        services_status_values.border_title = " Services Status"
                        self.SERVICES_STATUS_DATA_WEBAPP = Label(
                            classes="services-status-datum"
                        )
                        self.SERVICES_STATUS_DATA_WEBAPP.can_focus = False
                        yield self.SERVICES_STATUS_DATA_WEBAPP
                        self.SERVICES_STATUS_DATA_CACHE = Label(
                            classes="services-status-datum"
                        )
                        self.SERVICES_STATUS_DATA_CACHE.can_focus = False
                        yield self.SERVICES_STATUS_DATA_CACHE

        # Footer
        yield get_footer()

    async def on_mount(self) -> None:
        self._start_redis_listener()  # Se conecta al socket de Redis
        await self.init()

    async def on_switch_changed(self, event: Switch.Changed) -> None:
        # 1) Solo interesan eventos del switch "power"
        if event.switch.name != "power" or self._ignore_switch_event:
            self.info.update("No entró")
            self._ignore_switch_event = (
                False  # Se reactivan los eventos del switch después del init().
            )
            return

        # 2) Si ya se está procesando, se ignoran nuevas pulsaciones
        if self._power_busy:
            return

        # 3) Se bloquea internamente y en la UI
        self._power_busy = True
        event.switch.disabled = True

        try:
            if event.value:
                __resp = await self.send_command("RTB", "__START__")
                __resp = json.loads(__resp)
                self.info.update("Se mandó __START__")
            else:
                __resp = await self.send_command("RTB", "__STOP__")
                self.info.update("Se mandó __STOP__")
        except Exception:
            # Si falla, revertimos el valor y mostramos error
            event.switch.value = not event.value
        finally:
            # 4) Siempre reactivamos el switch y el lock
            event.switch.disabled = False
            self._power_busy = False

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.name != "reset":
            return
        # Se presionó el botón
        try:
            event.button.disabled = True
            resp = await self.send_command("RTB", "__RESTART__")
            resp = json.loads(resp)
            if resp["status"] == "ok":
                self.notify(
                    title="Successful reset!",
                    message="Root The Box services reseted.",
                    severity="information",
                    timeout=5,
                    markup=True,
                )
            else:
                self.notify(
                    title="Reset ERROR!",
                    message=f"{resp["status"]}",
                    severity="error",
                    timeout=10,
                    markup=True,
                )
        except Exception as e:
            self.notify(title="Error!", message=str(e), severity="error", timeout=10)
        finally:
            await self.init()
            await self.power.recompose()
            event.button.disabled = False
            self.set_focus(self.power)

    async def on_screen_resume(self, event: ScreenResume) -> None:
        """
        Este evento salta cada vez que la pantalla vuelve a activarse (show).
        Aquí forzamos que la opción 0 quede highlighted y le damos focus.
        """
        # Se asegura de que el widget tenga el foco
        self.power.focus()

    async def return_to_main(self) -> None:
        """Regresa a la pantalla del menú principal."""
        # Opcional: comprueba que no estés en la pantalla raíz
        if self.screen.id != "main":
            # Se reemplaza la pantalla actual
            await self.app.pop_screen()
            # Se cambia a la nueva pantalla
            await self.app.push_screen("main")

    async def action_go_back(self) -> None:
        """Regresa a la pantalla del menú principal."""
        await self.return_to_main()

    async def send_command(
        self, prog: str, command: str, args: dict | None = None
    ) -> str:
        # 1) DEBUG: indicar que vamos a conectar
        self.log(f"CLIENTE: intentando conectar al socket… {SOCKET_PATH}")
        try:
            reader, writer = await asyncio.open_unix_connection(path=SOCKET_PATH)
        except Exception as e:
            self.log(f"CLIENTE: error al conectar: {e}")
            raise

        # 2) Montar payload y añadir '\n'
        payload: dict[str, Union[str, dict[str, Union[str, int]]]] = {
            "prog": prog,
            "command": command,
        }
        if args:
            payload["args"] = args
        raw = json.dumps(payload)
        self.log(f"CLIENTE: enviando JSON: {raw}")
        writer.write(raw.encode("utf-8") + b"\n")
        await writer.drain()

        # 3) Leer hasta la línea
        try:
            line = await reader.readline()
        except Exception as e:
            self.log(f"CLIENTE: error al leer respuesta: {e}")
            raise
        finally:
            writer.close()
            await writer.wait_closed()

        resp = line.decode("utf-8", errors="replace").strip()
        self.log(f"CLIENTE: respuesta cruda: {repr(resp)}")
        return resp

    async def get_conf(self) -> str:
        try:
            resp = await self.send_command("RTB", "__CONFIG__")
            return str(json.loads(resp))
        except Exception:
            return '"status": "error"'

    async def init(self) -> None:
        self._ignore_switch_event = True
        try:
            __resp = await self.send_command("RTB", "__STATUS__")
            __resp = json.loads(__resp)
            if __resp["status"] == Status.OK:
                self.power.value = True
                # self.info.update("Power value True")
            else:
                self.power.value = False
                # self.info.update("Power value False")

            __resp = await self.send_command("RTB", "__CONFIG__")
            __resp = json.loads(__resp)
            if __resp["status"] == Status.OK:
                config_data = __resp["data"]["config"]
                pretty_json = json.dumps(config_data, indent=4)
                md_content = f"```json\n{pretty_json}\n```"
                self.config_data.update_content(md_content)
            else:
                self.config_data.update_content("Nothing to show")

        except Exception:
            pass
        finally:
            await asyncio.sleep(0.1)  # Espera para evitar problemas de UI

    def _start_redis_listener(self) -> None:
        """Crea y arranca el hilo que escucha Redis."""
        # guardamos la referencia para que no se recoja
        self._redis_thread = threading.Thread(
            target=self._listen_to_redis_sync, daemon=True
        )
        self._redis_thread.start()

    def _listen_to_redis_sync(self) -> None:
        """Hilo de escucha que nunca debe tocar la UI directamente."""
        client = redis.Redis(
            host="localhost", port=6379, db=0, password="C5L48", decode_responses=True
        )
        pubsub = client.pubsub()
        pubsub.subscribe("admin_channel", "client_channel")

        # mensaje de arranque
        self.app.call_from_thread(
            lambda: self.SERVICES_STATUS_DATA_WEBAPP.update("Listener started")
        )

        for message in pubsub.listen():
            # mensaje de confirmación de subscribe, unsubscribe, etc
            mtype = message.get("type")
            # actualiza tipo (ejemplo)
            self.app.call_from_thread(
                lambda m=mtype: self.SERVICES_STATUS_DATA_WEBAPP.update(
                    f"Message type: {m}"
                )
            )

            if mtype != "message":
                continue

            try:
                data = json.loads(message["data"])
            except Exception:
                continue

            def _update():
                status = (
                    "[green]✔[/green]"
                    if data["status"] == "running"
                    else "[red]✘[/red]"
                )
                self.SERVICES_STATUS_DATA_WEBAPP.update(status)

                status = (
                    "[green]✔[/green]"
                    if data["status"] == "running"
                    else "[red]✘[/red]"
                )
                self.SERVICES_STATUS_DATA_CACHE.update(status)

            self.app.call_from_thread(_update)
