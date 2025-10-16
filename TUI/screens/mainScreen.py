import os
from textual.app import ComposeResult
from ..serverInfo import ServerInfo
from textual.screen import Screen
from ..widgets import get_footer
from ..widgets import get_header
from textual.events import ScreenResume
from textual.containers import Vertical, Horizontal, ScrollableContainer, VerticalScroll
from textual.widgets import Label, Static, OptionList, Link
import importlib.resources as pkg_resources


class MainScreen(Screen):
    CSS_PATH = "../styles/main.tcss"
    JB_LOGO = pkg_resources.read_text("TUI.media", "JuiceBoxLogo.txt")

    JB_LOGO_ALT = pkg_resources.read_text("TUI.media", "JuiceBoxLogoAlt.txt")

    SERVER_INFO = Label(classes="server-info-data")
    FMAT_LOGO = pkg_resources.read_text("TUI.media", "FMATCyberLab.txt")
    FMAT_LOGO_ALT = pkg_resources.read_text("TUI.media", "FMATCyberLabAlt.txt")

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
            with Vertical(classes="vcontainer1") as self.vcontainer1:
                self.vcontainer1.can_focus = False
                # Contenedor vertical 3
                with ScrollableContainer(
                    classes="vinnercontainer"
                ) as self.vinnercontainer:
                    self.vinnercontainer.can_focus = False
                    # Logo de JuiceBox
                    self.jb_logo = Label(self.JB_LOGO, classes="juice-box-logo")
                    self.jb_logo.can_focus = False
                    yield self.jb_logo

                    # Contenedor horizontal interior
                    with Horizontal(classes="hinnercontainer") as self.hinnercontainer:
                        # Espacio vacío
                        empty_space = Static("", classes="empty")
                        empty_space.can_focus = False
                        yield empty_space
                        # Link de Github
                        self.about_link = Link(
                            text="github/EdgarSabidoC",
                            url="https://github.com/EdgarSabidoC",
                            classes="github-link",
                        )
                        self.about_link.can_focus = False
                        self.about_link.border_title = "Developed by"
                        yield self.about_link

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
            with Vertical(classes="vcontainer2") as self.vcontainer2:
                self.vcontainer2.can_focus = False

                self.fmat_logo = Label(self.FMAT_LOGO, classes="fmat-logo-box")
                self.fmat_logo.can_focus = False
                self.fmat_logo_container = ScrollableContainer(
                    classes="fmat-logo-container"
                )
                self.fmat_logo_container.can_focus = False
                with self.fmat_logo_container:
                    yield self.fmat_logo

                # Server info
                self.server_info_container = ScrollableContainer(
                    classes="server-info-container"
                )
                self.server_info_container.can_focus = False
                self.server_info_container.styles.layout = "horizontal"
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

    def on_resize(self, event) -> None:
        """
        Evento que se ejecuta al redimensionar la ventana.
        Ajusta el tamaño de los elementos en pantalla.

        Args:
            event: Evento de redimensionamiento.
        """
        terminal_size = os.get_terminal_size()
        terminal_width = terminal_size.columns  # 112 mínimo recomendado
        terminal_height = terminal_size.lines  # 36 mínimo recomendado

        if terminal_height >= 28 and terminal_height < 36 and terminal_width >= 150:
            self.vinnercontainer.display = True
            self.fmat_logo_container.display = True
            self.fmat_logo_container.styles.height = "50%"
            self.server_info_container.styles.height = "50%"
            self.jb_logo.update(self.JB_LOGO_ALT)
            self.fmat_logo.update(self.FMAT_LOGO_ALT)
            self.jb_logo.styles.height = "60%"
            self.hinnercontainer.styles.height = "40%"
            self.menu.styles.height = "30%"
            self.info.styles.height = "20%"
        elif terminal_height >= 36 and terminal_width >= 112:
            self.vinnercontainer.display = True
            self.fmat_logo_container.display = True
            self.fmat_logo_container.styles.height = "60%"
            self.server_info_container.styles.height = "40%"
            self.jb_logo.update(self.JB_LOGO)
            self.fmat_logo.update(self.FMAT_LOGO)
            self.jb_logo.styles.height = "80%"
            self.hinnercontainer.styles.height = "20%"
            self.menu.styles.height = "30%"
            self.info.styles.height = "20%"
        else:
            self.vinnercontainer.display = False
            self.fmat_logo_container.display = False
            self.menu.styles.height = "60%"
            self.info.styles.height = "40%"
            self.server_info_container.styles.height = "100%"
