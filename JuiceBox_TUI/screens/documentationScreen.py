from textual.app import ComposeResult
from serverInfo import ServerInfo
from textual.screen import Screen
from textual.widgets.option_list import Option
from widgets.footer import get_footer
from widgets.header import get_header
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import (
    Label,
    Static,
    OptionList,
    Placeholder,
    Link,
    MarkdownViewer,
    Markdown,
    TabbedContent,
)
import textual.color as color
from textual.binding import Binding


class DocumentationScreen(Screen):
    CSS_PATH = "../styles/documentation.tcss"
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
    MARKDOWNS = {
        "JuiceBoxEngine": "docs/JuiceBoxEngine/README.MD",
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
        self.jb_engine = MarkdownViewer(
            self.get_markdown("JuiceBoxEngine"), show_table_of_contents=self.show_toc
        )
        self.rtb = MarkdownViewer(
            self.get_markdown("RootTheBox"), show_table_of_contents=self.show_toc
        )
        self.js = MarkdownViewer(
            self.get_markdown("JuiceShop"), show_table_of_contents=self.show_toc
        )
        with TabbedContent("JuiceBoxEngine", "JuiceShop", "RootTheBox"):
            yield self.jb_engine
            yield self.rtb
            yield self.js
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

        # Actualiza el estado en cada visor
        self.jb_engine.show_table_of_contents = self.show_toc
        self.js.show_table_of_contents = self.show_toc
        self.rtb.show_table_of_contents = self.show_toc

        # Redibuja (opcional, dependiendo del comportamiento)
        self.jb_engine.refresh()
        self.js.refresh()
        self.rtb.refresh()

    def get_markdown(self, markdown: str) -> str:
        self.content = ""
        with open(self.MARKDOWNS[markdown], "r", encoding="utf-8") as file:
            self.content = file.read()
        return self.content
