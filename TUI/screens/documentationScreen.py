from textual.app import ComposeResult
from textual.screen import Screen
from ..widgets import get_footer
from ..widgets import get_header
from ..widgets.linkableMarkdownViewer import LinkableMarkdownViewer
from textual.widgets import TabbedContent
from textual.binding import Binding
from importlib.resources import files
from importlib.abc import Traversable
from pathlib import Path


class DocumentationScreen(Screen):
    """
    Pantalla para la visualización de la documentación en formato Markdown.
    """

    CSS_PATH = "../styles/documentation.tcss"
    DOCS_ES: Traversable = files("docs.ES")
    MARKDOWNS = {
        "Motor": Path(str(DOCS_ES.joinpath("JuiceBox/Motor.MD"))),
        "TUI": Path(str(DOCS_ES.joinpath("TUI/Manual.MD"))),
        "Configs": Path(str(DOCS_ES.joinpath("JuiceBox/Configuracion.MD"))),
        "API": Path(str(DOCS_ES.joinpath("JuiceBox/API.MD"))),
        "License": Path(str(DOCS_ES.joinpath("Licencia.MD"))),
    }
    BINDINGS = [
        Binding("ctrl+b", "go_back", "Back | ", show=True),
        Binding("ctrl+q", "quit", "Quit | ", show=True),
        Binding("ctrl+t", "show_hide_toc", "Show/Hide table of content | ", show=True),
    ]

    def compose(self) -> ComposeResult:
        """
        Crea y organiza los elementos de la interfaz de documentación.

        La pantalla se compone de un encabezado, un pie de página y un conjunto de
        pestañas (`TabbedContent`) que contienen visores de Markdown interactivos
        para cada sección del sistema (Motor, TUI, Configuración, API, Licencia).

        Returns:
            ComposeResult: Generador con los widgets que conforman la pantalla.
        """
        self.show_toc = True
        # Header
        yield get_header()

        # Markdowns:
        self.tui = LinkableMarkdownViewer(
            self.get_markdown("TUI"),
            show_table_of_contents=self.show_toc,
            open_links=False,
        )
        self.jb_engine = LinkableMarkdownViewer(
            self.get_markdown("Motor"),
            show_table_of_contents=self.show_toc,
            open_links=False,
        )
        self.configs = LinkableMarkdownViewer(
            self.get_markdown("Configs"),
            show_table_of_contents=self.show_toc,
            open_links=False,
        )
        self.api = LinkableMarkdownViewer(
            self.get_markdown("API"),
            show_table_of_contents=self.show_toc,
            open_links=False,
        )
        self.license = LinkableMarkdownViewer(
            self.get_markdown("License"),
            show_table_of_contents=self.show_toc,
            open_links=False,
        )

        with TabbedContent("Manual", "Motor", "Configuracion", "API", "Licencia"):
            yield self.tui
            yield self.jb_engine
            yield self.configs
            yield self.api
            yield self.license
            self.license.show_table_of_contents = False

        # Footer
        yield get_footer()

    async def return_to_main(self) -> None:
        """
        Regresa a la pantalla principal del menú de JuiceBox.

        Si la pantalla actual no es la principal, la reemplaza mediante el
        sistema de pantallas de la aplicación (`pop_screen` → `push_screen`).
        """
        # Se comprueba que no se esté en la pantalla principal
        if self.screen.id != "main":
            # Se reemplaza la pantalla actual
            await self.app.pop_screen()
            # Se cambia a la nueva pantalla
            await self.app.push_screen("main")

    async def action_go_back(self) -> None:
        """
        Acción asociada al atajo de teclado `Ctrl+B`.

        Llama internamente a `return_to_main()` para regresar al menú principal.
        """
        await self.return_to_main()

    async def action_show_hide_toc(self) -> None:
        """
        Alterna la visibilidad de la tabla de contenidos en todos los visores de Markdown.

        Esta acción se activa con `Ctrl+T` y permite mostrar u ocultar dinámicamente
        los índices laterales de navegación (`table of contents`) de cada pestaña.

        Al cambiar el estado, los visores se actualizan para reflejar la nueva configuración.
        """
        self.show_toc = not self.show_toc

        # Actualiza el estado en cada visor para mostrar u ocultar la tabla de contenido:
        self.tui.show_table_of_contents = self.show_toc
        self.jb_engine.show_table_of_contents = self.show_toc
        self.configs.show_table_of_contents = self.show_toc
        self.api.show_table_of_contents = self.show_toc
        self.license.show_table_of_contents = False

        # Redibuja
        self.tui.refresh()
        self.jb_engine.refresh()
        self.configs.refresh()
        self.api.refresh()
        self.license.refresh()

    def get_markdown(self, markdown: str) -> str:
        """
        Obtiene el contenido de un archivo Markdown del conjunto de documentación.

        Args:
            markdown (str): Clave que identifica el documento a cargar.
                Puede ser "Motor", "TUI", "Configs", "API" o "License".

        Returns:
            str: Contenido del archivo Markdown leído en formato de texto plano.
        """
        self.content = ""
        with open(self.MARKDOWNS[markdown], "r", encoding="utf-8") as file:
            self.content = file.read()
        return self.content
