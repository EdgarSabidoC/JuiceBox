from textual.app import ComposeResult
from textual.screen import Screen
from widgets.footer import get_footer
from widgets.header import get_header
from textual.screen import Screen
from textual.widgets import Markdown, MarkdownViewer, TabbedContent, Tree
from textual.widgets.markdown import MarkdownTableOfContents
from textual.widgets.tree import TreeNode
from textual.binding import Binding


class DocumentationScreen(Screen):
    CSS_PATH = "../styles/documentation.tcss"

    MARKDOWNS = {
        "JuiceBox": "docs/JuiceBox/README.MD",
        "JuiceShop": "docs/JuiceShop/README.MD",
        "RootTheBox": "docs/RootTheBox/README.MD",
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
            self.get_markdown("JuiceBox"),
            show_table_of_contents=self.show_toc,
            open_links=False,
        )
        self.rtb = MarkdownViewer(
            self.get_markdown("RootTheBox"),
            show_table_of_contents=self.show_toc,
            open_links=False,
        )
        self.js = MarkdownViewer(
            self.get_markdown("JuiceShop"),
            show_table_of_contents=self.show_toc,
            open_links=False,
        )
        with TabbedContent("JuiceBox", "JuiceShop", "RootTheBox"):
            yield self.jb_engine
            yield self.rtb
            yield self.js

        # Footer
        yield get_footer()

    def on_mount(self) -> None:
        # Se accede a la TOC de cada viewer tras el compose/mount
        for name, viewer in (
            ("JuiceBox", self.jb_engine),
            ("JuiceShop", self.js),
            ("RootTheBox", self.rtb),
        ):
            toc: MarkdownTableOfContents = viewer.query_one(MarkdownTableOfContents)
            toc.border_title = "Contenido"
            tr: Tree = toc.query_one(Tree)
            tr.ICON_NODE_EXPANDED = "▽ "  # type: ignore[assignment]
            tr.show_guides = True

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
        self.rtb.show_table_of_contents = self.show_toc
        self.js.show_table_of_contents = self.show_toc

        # Redibuja (opcional, dependiendo del comportamiento)
        self.jb_engine.refresh()
        self.rtb.refresh()
        self.js.refresh()

    def get_markdown(self, markdown: str) -> str:
        self.content = ""
        with open(self.MARKDOWNS[markdown], "r", encoding="utf-8") as file:
            self.content = file.read()
        return self.content
