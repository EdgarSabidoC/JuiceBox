from textual.app import ComposeResult
from textual.screen import Screen
from widgets.footer import get_footer
from widgets.header import get_header
from textual.screen import Screen
from textual.events import ScreenResume
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Static, Switch, Button
from textual.binding import Binding
from typing import Union
import json, asyncio
from widgets.customSwitch import CustomSwitch

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

    SERVER_INFO = Label(classes="server-info-data")

    def compose(self) -> ComposeResult:
        # Header
        yield get_header()

        # Contenedor horizontal 1
        with Horizontal(classes="hcontainer") as hcontainer:
            hcontainer.can_focus = False
            # Contenedor vertical 1
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
                        self.power = CustomSwitch(value=True, name="power")
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

            # Contenedor vertical 2
            with Vertical(classes="vcontainer2") as vcontainer2:
                vcontainer2.can_focus = False
                self.config_container = ScrollableContainer()
                self.config_static = Static()
                self.config_container.can_focus = False
                self.config_static.can_focus = False
                with self.config_container:
                    yield self.config_static

                # Server info
                with Horizontal():
                    self.SERVER_INFO_KEYS = Label(classes="server-info-keys")
                    self.SERVER_INFO_KEYS.update("Webapp: ")
                    yield self.SERVER_INFO_KEYS
                    self.SERVER_INFO.can_focus = False
                    self.SERVER_INFO.border_title = " Services Status"
                    yield self.SERVER_INFO

        # Footer
        yield get_footer()

    async def on_mount(self) -> None:
        await self.init()

    async def on_switch_changed(self, event: Switch.Changed) -> None:
        # 1) Solo nos interesan eventos del switch "power"
        if event.switch.name != "power" or self._ignore_switch_event:
            return

        # 2) Si ya estamos procesando, ignoramos nuevas pulsaciones
        if self._power_busy:
            return

        # 3) Bloqueamos internamente y en la UI
        self._power_busy = True
        event.switch.disabled = True

        try:
            if event.value:
                __resp = await self.send_command("RTB", "__START__")
                __resp = json.loads(__resp)
                if __resp["status"] == "ok":
                    self.info.update("Se mandó __START__")
                    self.SERVER_INFO.update("[green]✔[/green]")
                else:
                    self.info.update("Se mandó __START__")
                    self.SERVER_INFO.update("[red]✘[red]")
            else:
                __resp = await self.send_command("RTB", "__KILL__")
                self.info.update("Se mandó __KILL__")
                self.SERVER_INFO.update("[red]✘[/red]")
        except Exception as e:
            # Si falla, revertimos el valor y mostramos error
            event.switch.value = not event.value
            self.SERVER_INFO.update(f"Error en comando: {e}")
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
        try:
            __resp = await self.send_command("RTB", "__STATUS__")
            __resp = json.loads(__resp)
            if __resp["status"] == "ok":
                self._ignore_switch_event = True
                self.power.value = True
                self.SERVER_INFO.update("[green]✔[/green]")
            else:
                self._ignore_switch_event = True
                self.power.value = False
                self.SERVER_INFO.update("[red]✘[/red]")

            __resp = await self.send_command("RTB", "__CONFIG__")
            __resp = json.loads(__resp)
            if __resp["status"] == "ok":
                self.config_static.update(f"{__resp}")
            else:
                self.config_static.update(f"{__resp}")
        except Exception:
            pass
        finally:
            self._ignore_switch_event = False
