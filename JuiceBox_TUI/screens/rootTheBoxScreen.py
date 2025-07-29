from textual.app import ComposeResult
from serverInfo import ServerInfo
from textual.screen import Screen
from textual.widgets.option_list import Option
from widgets.footer import get_footer
from widgets.header import get_header
from textual.screen import Screen
from textual.events import Mount, ScreenResume
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Static, OptionList, Link, Switch
from textual.binding import Binding
from typing import Optional, Union
import socket, json, asyncio

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

    SERVER_INFO = Label(classes="server-info-data")
    with open("media/Architecture.txt", "r", encoding="utf-8") as file:
        SYSTEM_ARCH = file.read()

    def compose(self) -> ComposeResult:
        # Header
        yield get_header()

        # Contenedor horizontal 1
        with Horizontal(classes="hcontainer") as hcontainer:
            hcontainer.can_focus = False
            # Contenedor vertical 1
            with Vertical(classes="vcontainer1") as vcontainer1:
                vcontainer1.can_focus = False
                # Contenedor vertical 3
                with Vertical(classes="vinnercontainer") as vinnercontainer:
                    vinnercontainer.can_focus = False
                    # Logo de JuiceBox
                    jb_logo = Static(self.JB_LOGO, classes="juice-box-logo")
                    jb_logo.can_focus = False
                    yield jb_logo
                    # Contenedor horizontal interior
                    with Horizontal(classes="hinnercontainer"):
                        # Espacio vacío
                        empty_space = Static("", classes="empty")
                        empty_space.can_focus = False
                        yield empty_space
                        # Link de Github
                        about_link = Link(
                            text="github/EdgarSabidoC",
                            url="https://github.com/EdgarSabidoC",
                            classes="github-link",
                        )
                        about_link.can_focus = False
                        about_link.border_title = "Developed by"
                        yield about_link

                self.power = Switch(value=True, name="power")
                self.power.border_title = "Menu"
                yield self.power

                # Información sobre las opciones
                self.info = Static(classes="info-box")
                self.info.can_focus = False
                self.info.border_title = "Output"
                yield self.info

            # Contenedor vertical 2
            with Vertical(classes="vcontainer2") as vcontainer2:
                vcontainer2.can_focus = False
                # System architecture
                self.SYSTEM_ARCH = Static(
                    str(self.SYSTEM_ARCH), expand=True, classes="arch-box"
                )

                self.SYSTEM_ARCH.border_title = "System architecture"
                arch_container = ScrollableContainer(self.SYSTEM_ARCH)
                arch_container.scroll_visible(force=True)
                arch_container.can_focus = True
                arch_container.styles.content_align = ("center", "middle")
                arch_container.styles.height = "68%"
                arch_container.styles.overflow_x = "auto"
                arch_container.styles.overflow_y = "auto"
                with arch_container:
                    yield self.SYSTEM_ARCH

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
        __resp: str = await self.send_command("RTB", "__STATUS__")

        if "ok" in __resp:
            self.power.value = True
            self.SERVER_INFO.update("Webapp: ✔")
        else:
            self.power.value = False
            self.SERVER_INFO.update("Webapp: ✘")

    async def on_switch_changed(self, event: Switch.Changed) -> None:
        # 1) Solo nos interesan eventos del switch "power"
        if event.switch.name != "power":
            return

        # 2) Si ya estamos procesando, ignoramos nuevas pulsaciones
        if self._power_busy:
            return

        # 3) Bloqueamos internamente y en la UI
        self._power_busy = True
        event.switch.disabled = True

        try:
            if event.value:
                await self.send_command("RTB", "__START__")
                self.info.update("Se mandó __START__")
                self.SERVER_INFO.update("Running ✔")
            else:
                await self.send_command("RTB", "__KILL__")
                self.info.update("Se mandó __KILL__")
                self.SERVER_INFO.update("Stopped ✘")
        except Exception as e:
            # Si falla, revertimos el valor y mostramos error
            event.switch.value = not event.value
            self.info.update(f"Error en comando: {e}")
        finally:
            # 4) Siempre reactivamos el switch y el lock
            event.switch.disabled = False
            self._power_busy = False

    async def on_screen_resume(self, event: ScreenResume) -> None:
        """
        Este evento salta cada vez que la pantalla vuelve a activarse (show).
        Aquí forzamos que la opción 0 quede highlighted y le damos focus.
        """
        # Se asegura de que el widget tenga el foco
        self.power.focus()

    async def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ):
        option: str = str(event.option.prompt).strip()
        option_map = {
            "📦 Root the Box": "Admin tools to manage Root the Box docker containers",
            "🧃 OWASP Juice Shop": "Admin tools to manage OWASP Juice Shop docker containers",
            "🔎 Documentation": "Read the docs",
            "↩  Exit": "Close the app",
        }
        description = option_map.get(option, "No info available.")
        self.info.update(description)

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
        reader, writer = await asyncio.open_unix_connection(path=SOCKET_PATH)
        payload: dict[str, Union[str, dict[str, Union[str, int]]]] = {
            "prog": prog,
            "command": command,
        }
        if args is not None:
            payload["args"] = args

        data = json.dumps(payload).encode()
        writer.write(data)
        await writer.drain()

        # lee hasta EOF o máximo 4096 bytes
        response = await reader.read(4096)
        writer.close()
        await writer.wait_closed()

        return response.decode()
