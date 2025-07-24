from textual.app import ComposeResult
from serverInfo import ServerInfo
from textual.screen import Screen
from textual.widgets.option_list import Option
from widgets.footer import get_footer
from widgets.header import get_header
from textual.screen import Screen
from textual.events import ScreenResume
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Static, OptionList, Placeholder, Link
import textual.color as color


class MainScreen(Screen):
    CSS_PATH = "../styles/main.tcss"
    with open("media/JuiceBoxLogo.txt", "r", encoding="utf-8") as file:
        JB_LOGO = file.read()

    server = ServerInfo()
    SERVER_INFO = Static(server.get_all_info_as_str(), id="server_info")
    SYSTEM_ARCH = """
[#4097e2]╔═════════════════════════════════════════════════════╗
║                ┌───────────┐               [#ffffff]Docker[/#ffffff]   ║
║          ┌─────│   [#ffffff]NginX[/#ffffff]   │───────┐     [#ffffff]Containers[/#ffffff] ║
║          │     └───────────┘       │                ║
║    ┌─────┴─────┐           ┌───────┴─────┐          ║
║    │ [#ffffff]JuiceShop[/#ffffff] │           │     [#ffffff]Web[/#ffffff]     │          ║
║    │    [#ffffff]API[/#ffffff]    ├───────────┤    [#ffffff]Client[/#ffffff]   │          ║
║    │           │           │             │          ║
║    └─────┬───┬─┘           └──────┬──────┘          ║
║          │   └──────────────┐     │                 ║
╚═════════════════════════════════════════════════════╝[/#4097e2]
           │                  │     │
    ┌──────┴──────┐         ┌───────┴──────┐
    │             │         │              │
    │ Host/Server ├─────────┤   Monitor    │
    │             │         │              │
    └──────┬──────┘         └───────┬──────┘
           │                        │
     ┌─────┴──────┐                 │
     │   Admin    │                 │
     │   Tools    ├─────────────────┘
     │            │
     └────────────┘
"""

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
                    Option(prompt=" 🐋 Docker".ljust(20)),
                    Option(prompt=" 🔎 Documentation".ljust(20)),
                    Option(prompt=" ↩  Exit".ljust(20)),
                    classes="menu",
                )
                self.menu.border_title = "Menu"
                yield self.menu

                # Información sobre las opciones
                placeholder = Placeholder()
                placeholder.can_focus = False
                placeholder.styles.height = "20%"
                placeholder.styles.width = "100%"
                placeholder.styles.border = ("double", "green")
                placeholder.styles.border_title_background = "green"
                placeholder.styles.border_title_color = color.WHITE
                placeholder.styles.border_title_style = "bold"
                placeholder.border_title = "Info"
                placeholder.styles.padding = (1, 1, 1, 1)
                placeholder.styles.content_align = ("left", "middle")
                yield placeholder

            # Contenedor vertical 2
            with Vertical(classes="vcontainer2") as vcontainer2:
                vcontainer2.can_focus = False
                # System architecture
                self.SYSTEM_ARCH = Static(str(self.SYSTEM_ARCH), expand=True)
                self.SYSTEM_ARCH.styles.content_align = ("center", "middle")
                self.SYSTEM_ARCH.styles.height = "100%"
                self.SYSTEM_ARCH.styles.border = ("double", "green")
                self.SYSTEM_ARCH.styles.border_title_align = "right"
                self.SYSTEM_ARCH.styles.border_title_background = "green"
                self.SYSTEM_ARCH.styles.border_title_color = color.WHITE
                self.SYSTEM_ARCH.border_title = "System architecture"
                self.SYSTEM_ARCH.styles.border_title_style = "bold"
                arch_container = ScrollableContainer(self.SYSTEM_ARCH)
                arch_container.scroll_visible(force=True)
                arch_container.can_focus = False
                arch_container.styles.content_align = ("center", "middle")
                arch_container.styles.height = "70%"
                with arch_container:
                    yield self.SYSTEM_ARCH

                # Server info
                self.SERVER_INFO.styles.content_align = ("left", "middle")
                self.SERVER_INFO.styles.width = "100%"
                self.SERVER_INFO.styles.height = "30%"
                self.SERVER_INFO.styles.padding = (1, 1, 1, 1)
                self.SERVER_INFO.styles.border = ("double", "green")
                self.SERVER_INFO.styles.border_title_align = "right"
                self.SERVER_INFO.styles.border_title_background = "green"
                self.SERVER_INFO.styles.border_title_color = color.WHITE
                self.SERVER_INFO.border_title = "Server info"
                self.SERVER_INFO.styles.border_title_style = "bold"
                self.SERVER_INFO.can_focus = False
                yield self.SERVER_INFO

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
        choice = str(event.option.prompt).strip()

        # No llames a self.app.exit() aquí; sólo asigna None para “Exit”
        screen_map = {
            "📦 Root the Box": "root",
            "🧃 OWASP Juice Shop": "juice",
            "🐋 Docker": "docker",
            "🔎 Documentation": "documentation",
            "↩ Exit": None,
        }

        target = screen_map.get(choice)
        if target is None:
            # Salimos de la aplicación
            self.app.exit()
        else:
            # Se reemplaza la pantalla actual
            await self.app.pop_screen()
            # Se cambia a la nueva pantalla
            await self.app.push_screen(target)
