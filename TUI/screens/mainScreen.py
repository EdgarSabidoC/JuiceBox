import os
from textual.app import ComposeResult
from ..serverInfo import ServerInfo
from textual.screen import Screen
from ..widgets import get_footer
from ..widgets import get_header
from textual.theme import Theme
from textual.events import ScreenResume
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Static, OptionList, Link
import importlib.resources as pkg_resources


class MainScreen(Screen):
    CSS_PATH = "../styles/main.tcss"
    LOGOS_PATH = "TUI.media"
    # Logos de JuiceBox
    JB_LOGO: str = pkg_resources.read_text(LOGOS_PATH, "JuiceBoxLogo.txt")
    JB_LOGO_ALT: str = pkg_resources.read_text(LOGOS_PATH, "JuiceBoxLogoAlt.txt")

    SERVER_INFO = Label(classes="server-info-data")
    # Logos de FMAT CyberLab
    FMAT_LOGO: str = pkg_resources.read_text(LOGOS_PATH, "FMATCyberLab.txt")
    FMAT_LOGO_ALT: str = pkg_resources.read_text(LOGOS_PATH, "FMATCyberLabAlt.txt")

    use_alt_logo: bool  # Indica si se está usando el logo alternativo

    MENU_OPTIONS = {
        "📦 Root The Box": "Admin tools to manage Root the Box docker containers",
        "🧃 OWASP Juice Shop": "Admin tools to manage OWASP Juice Shop docker containers",
        "🔎 Documentation": "Read the docs",
        "↩  Exit": "Close the app",
    }

    def compose(self) -> ComposeResult:
        """
        Construye y devuelve la jerarquía de widgets que conforman la pantalla principal.

        Este método define la estructura visual de la interfaz: cabecera, menús,
        contenedores, logos y pie de página. Se ejecuta automáticamente al montar
        la pantalla y determina qué widgets se renderizan y en qué orden.

        Returns:
            ComposeResult: Generador que produce los widgets que se añadirán
            al árbol de la aplicación.
        """
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
                    self.jb_logo: Label = Label(self.JB_LOGO, classes="juice-box-logo")
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
                self.menu_info = Static(classes="info-box")
                self.menu_info.can_focus = False
                self.menu_info.border_title = "Menu option info"
                yield self.menu_info

            # Contenedor vertical 2
            with Vertical(classes="vcontainer2") as self.vcontainer2:
                self.vcontainer2.can_focus = False

                self.fmat_logo: Label = Label("", classes="fmat-logo-box")
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

    async def on_mount(self) -> None:
        """
        Evento que se ejecuta cuando la pantalla se monta por primera vez.

        Se utiliza para suscribirse a señales globales de la aplicación,
        como el cambio de tema.
        """
        # Se suscribe a la señal del app
        self.app.theme_changed_signal.subscribe(self, self.on_theme_changed)

    async def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """
        Maneja la selección de una opción en el menú.

        Dependiendo de la opción seleccionada, cambia de pantalla o
        cierra la aplicación.

        Args:
            event (OptionList.OptionSelected): Evento que contiene la opción seleccionada.
        """
        option: str = str(event.option.prompt).strip()

        screen_map = {
            "📦 Root The Box": "root",
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
        """
        Maneja el resaltado de una opción en el menú.

        Actualiza la caja de información con la descripción de la opción
        actualmente resaltada.

        Args:
            event (OptionList.OptionHighlighted): Evento que contiene la opción resaltada.
        """
        option: str = str(event.option.prompt).strip()
        description = self.MENU_OPTIONS.get(option, "No info available.")
        self.menu_info.update(description)

    def get_server_info(self) -> None:
        """
        Obtiene y muestra la información del servidor en la interfaz.

        Llama a la clase `ServerInfo` para recuperar los datos y los
        actualiza en los labels correspondientes.
        """
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
        terminal_width = (
            terminal_size.columns
        )  # 100 chars mínimo recomendado para logo principal
        terminal_height = (
            terminal_size.lines
        )  # 36 chars mínimo recomendado para logo principal

        if terminal_width >= 103 and terminal_height >= 37:
            # Logos principales grandes
            self.vinnercontainer.display = True
            self.fmat_logo_container.display = True
            self.fmat_logo_container.styles.height = "60%"
            self.server_info_container.styles.height = "40%"
            self.jb_logo.update(self.JB_LOGO)
            self.use_alt_logo = False
            self.change_fmat_logo_color()
            self.jb_logo.styles.height = "80%"
            self.hinnercontainer.styles.height = "20%"
            self.menu.styles.height = "30%"
            self.menu_info.styles.height = "20%"
        elif terminal_width >= 150 and terminal_height < 37:
            # Logos alternativos
            self.vinnercontainer.display = True
            self.fmat_logo_container.display = True
            self.fmat_logo_container.styles.height = "50%"
            self.server_info_container.styles.height = "50%"
            self.jb_logo.update(self.JB_LOGO_ALT)
            self.use_alt_logo = True
            self.change_fmat_logo_color()
            self.jb_logo.styles.height = "60%"
            self.hinnercontainer.styles.height = "40%"
            self.menu.styles.height = "30%"
            self.menu_info.styles.height = "20%"
        else:
            # Oculta los logos
            self.vinnercontainer.display = False
            self.fmat_logo_container.display = False
            self.menu.styles.height = "60%"
            self.menu_info.styles.height = "40%"
            self.server_info_container.styles.height = "100%"

    def change_fmat_logo_color(self) -> None:
        """
        Cambia el color del logo de FMAT CyberLab según el tema actual.

        Selecciona la plantilla de logo (principal o alternativo) en función
        de `self.use_alt_logo` y reemplaza el marcador `#color` por el color
        definido en las variables de tema.
        """
        color = self.app.theme_variables["footer-key-foreground"]
        tmp_str: str = self.FMAT_LOGO
        if self.use_alt_logo:
            tmp_str = self.FMAT_LOGO_ALT
        tmp_str = tmp_str.replace("#color", color)
        self.fmat_logo.update(tmp_str)

    def on_theme_changed(self, theme: Theme) -> None:
        """
        Evento que se ejecuta cuando cambia el tema de la aplicación.

        Actualiza el logo de FMAT CyberLab para reflejar el nuevo color
        de acento del tema.

        Args:
            theme (Theme): Objeto que representa el nuevo tema activo.
        """
        self.change_fmat_logo_color()

    async def on_unmount(self) -> None:
        """
        Evento que se ejecuta cuando la pantalla se desmonta.

        Cancela la suscripción a señales globales de la aplicación para
        evitar fugas de memoria o llamadas innecesarias.
        """
        self.app.theme_changed_signal.unsubscribe(self)
