from textual.app import ComposeResult
from serverInfo import ServerInfo
from textual.screen import Screen
from textual.widgets.option_list import Option
from widgets.footer import get_footer
from widgets.header import get_header
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Static, OptionList, Placeholder, Link
import textual.color as color
from textual.binding import Binding


class RootTheBoxScreen(Screen):
    CSS_PATH = "../styles/main.tcss"
    with open("media/JuiceBoxLogo.txt", "r", encoding="utf-8") as file:
        JB_LOGO = file.read()

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("^q", "quit", "Quit", show=True),
    ]

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
                    Option(prompt=" ▶️ Start".ljust(20)),
                    Option(prompt=" ⏹️ Stop".ljust(20)),
                    Option(prompt=" 📡 Status".ljust(20)),
                    Option(prompt=" ⚙️ Configuration".ljust(20)),
                    Option(prompt=" ↩  Return".ljust(20)),
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
                pass

        # Footer
        yield get_footer()

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
            "↩  Return": "main",
        }

        target = screen_map.get(choice)
        if target == "main":
            await self.return_to_main()
        elif target is not None:
            # Se reemplaza la pantalla actual
            await self.app.pop_screen()
            # Se cambia a la nueva pantalla
            await self.app.push_screen(target)

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
