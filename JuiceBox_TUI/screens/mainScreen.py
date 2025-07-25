from textual.app import ComposeResult
from serverInfo import ServerInfo
from textual.screen import Screen
from textual.widgets.option_list import Option
from widgets.footer import get_footer
from widgets.header import get_header
from textual.screen import Screen
from textual.events import ScreenResume
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Static, OptionList, Link


class MainScreen(Screen):
    CSS_PATH = "../styles/main.tcss"
    with open("media/JuiceBoxLogo.txt", "r", encoding="utf-8") as file:
        JB_LOGO = file.read()

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

                # Menú
                self.menu = OptionList(
                    Option(prompt=" 📦 Root the Box".ljust(20)),
                    Option(prompt=" 🧃 OWASP Juice Shop".ljust(20)),
                    Option(prompt=" 🔎 Documentation".ljust(20)),
                    Option(prompt=" ↩  Exit".ljust(20)),
                    classes="menu",
                )
                self.menu.border_title = "Menu"
                self.menu.styles.color = "#19E6F3"
                yield self.menu

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
                arch_container.can_focus = False
                arch_container.styles.content_align = ("center", "middle")
                arch_container.styles.height = "68%"
                with arch_container:
                    yield self.SYSTEM_ARCH

                # Server info
                with Horizontal():
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
        Aquí forzamos que la opción 0 quede highlighted y le damos focus.
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
        option_map = {
            "📦 Root the Box": "Admin tools to manage Root the Box docker containers",
            "🧃 OWASP Juice Shop": "Admin tools to manage OWASP Juice Shop docker containers",
            "🔎 Documentation": "Read the docs",
            "↩  Exit": "Close the app",
        }
        description = option_map.get(option, "No info available.")
        self.info.update(description)

    def get_server_info(self) -> None:
        info = ServerInfo().get_all_info()
        if info["Terminal"] != "":
            keys = "\n".join(info.keys())
            data = "\n".join(str(v) for v in info.values())
            # __keys_str: str =
            self.SERVER_INFO_KEYS.update(str(keys))
            self.SERVER_INFO.update(str(data))
