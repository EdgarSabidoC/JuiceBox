from textual.app import ComposeResult
from textual.screen import Screen
from ..widgets import get_footer
from ..widgets import get_header
from textual.widgets import MarkdownViewer, TabbedContent
from textual.binding import Binding
from importlib.resources import files
from importlib.abc import Traversable
from pathlib import Path


class DocumentationScreen(Screen):
    CSS_PATH = "../styles/documentation.tcss"
    DOCS: Traversable = files("JuiceBox.docs.ES.JuiceBox")
    MARKDOWNS = {
        "Motor": Path(str(DOCS.joinpath("Engine.MD"))),
        "API": Path(str(DOCS.joinpath("API.MD"))),
        "Configs": Path(str(DOCS.joinpath("ConfigFiles.MD"))),
    }
    BINDINGS = [
        Binding("ctrl+b", "go_back", "Back", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+t", "show_hide_toc", "Show/Hide table of content", show=True),
    ]

    def compose(self) -> ComposeResult:
        self.show_toc = True
        # Header
        yield get_header()

        # Markdowns:
        self.jb_engine = MarkdownViewer(
            self.get_markdown("Motor"),
            show_table_of_contents=self.show_toc,
            open_links=False,
        )
        self.api = MarkdownViewer(
            self.get_markdown("API"),
            show_table_of_contents=self.show_toc,
            open_links=False,
        )
        self.configs = MarkdownViewer(
            self.get_markdown("Configs"),
            show_table_of_contents=self.show_toc,
            open_links=False,
        )

        with TabbedContent("Motor", "API", "Configs"):
            yield self.jb_engine
            yield self.api
            yield self.configs
        # Footer
        yield get_footer()

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

    async def action_show_hide_toc(self) -> None:
        """Alterna la visibilidad de la tabla de contenidos en todos los MarkdownViewer."""
        self.show_toc = not self.show_toc

        # Actualiza el estado en cada visor para mostrar u ocultar la tabla de contenido:
        self.jb_engine.show_table_of_contents = self.show_toc
        self.api.show_table_of_contents = self.show_toc
        self.configs.show_table_of_contents = self.show_toc

        # Redibuja (opcional, dependiendo del comportamiento)
        self.jb_engine.refresh()
        self.api.refresh()
        self.configs.refresh()

    def get_markdown(self, markdown: str) -> str:
        self.content = ""
        with open(self.MARKDOWNS[markdown], "r", encoding="utf-8") as file:
            self.content = file.read()
        return self.content
