from textual.app import ComposeResult
from ..serverInfo import ServerInfo
from textual.screen import Screen
from textual.widgets.option_list import Option
from ..widgets import get_footer
from ..widgets import get_header
from textual.events import ScreenResume
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Static, OptionList, Link
import importlib.resources as pkg_resources


class MainScreen(Screen):
    CSS_PATH = "../styles/main.tcss"
    JB_LOGO = pkg_resources.read_text("JuiceBox.TUI.media", "JuiceBoxLogo.txt")

    SERVER_INFO = Label(classes="server-info-data")
    SYSTEM_ARCH = pkg_resources.read_text("JuiceBox.TUI.media", "Architecture.txt")

    MENU_OPTIONS = {
        "📦 Root the Box": "Admin tools to manage Root the Box docker containers",
        "🧃 OWASP Juice Shop": "Admin tools to manage OWASP Juice Shop docker containers",
        "🔎 Documentation": "Read the docs",
        "↩  Exit": "Close the app",
    }

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

                # Menú
                self.menu = OptionList(
                    classes="menu",
                )
                self.menu.add_options(self.MENU_OPTIONS.keys())
                self.menu.border_title = "Menu"
                yield self.menu

                # Información sobre las opciones
                self.info = Static(classes="info-box")
                self.info.can_focus = False
                self.info.border_title = "Menu option info"
                yield self.info

            # Contenedor vertical 2
            with Vertical(classes="vcontainer2") as vcontainer2:
                vcontainer2.can_focus = False
                # System architecture
                self.SYSTEM_ARCH = Static(
                    str(self.SYSTEM_ARCH), expand=True, classes="arch-box", markup=True
                )

                self.SYSTEM_ARCH.border_title = "System architecture"
                self.arch_container = ScrollableContainer(
                    self.SYSTEM_ARCH, classes="arch-container"
                )
                self.arch_container.scroll_visible(force=True)
                self.arch_container.can_focus = False
                with self.arch_container:
                    yield self.SYSTEM_ARCH

                # Server info
                self.server_info_container = Horizontal(classes="server-info-container")
                with self.server_info_container:
                    self.SERVER_INFO_KEYS = Label(classes="server-info-keys")
                    yield self.SERVER_INFO_KEYS
                    self.SERVER_INFO.can_focus = False
                    self.SERVER_INFO.border_title = " Server info"
                    yield self.SERVER_INFO
                    self.get_server_info()

        # Footer
        yield get_footer()

    async def on_screen_resume(self, event: ScreenResume) -> None:
        """
        Este evento salta cada vez que la pantalla vuelve a activarse (show).
        Aquí se forza a que la opción 0 quede resaltada y le damos focus.
        """
        # 1) Seleccionar índice 0
        self.menu.highlighted = 0

        # 2) Asegurarnos de que el widget tenga el foco
        self.menu.focus()

    # Permite realizar un cambio de pantalla
    async def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        option: str = str(event.option.prompt).strip()

        screen_map = {
            "📦 Root the Box": "root",
            "🧃 OWASP Juice Shop": "juice",
            "🔎 Documentation": "documentation",
            "↩ Exit": None,
        }

        target = screen_map.get(option)
        if target is None:
            # Salimos de la aplicación
            self.app.exit()
        else:
            # Se reemplaza la pantalla actual
            await self.app.pop_screen()
            # Se cambia a la nueva pantalla
            await self.app.push_screen(target)

    async def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ):
        option: str = str(event.option.prompt).strip()
        description = self.MENU_OPTIONS.get(option, "No info available.")
        self.info.update(description)

    def get_server_info(self) -> None:
        info = ServerInfo().get_all_info()
        if info["Terminal"] != "":
            keys = "\n".join(info.keys())
            data = "\n".join(str(v) for v in info.values())
            self.SERVER_INFO_KEYS.update(str(keys))
            self.SERVER_INFO.update(str(data))
