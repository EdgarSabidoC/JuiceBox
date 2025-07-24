from textual.app import App
from textual.screen import Screen
from textual.reactive import reactive
from textual.binding import Binding

from textual.widgets import Label, Static, OptionList, Footer, Header, Placeholder, Link

from screens.mainScreen import MainScreen
from screens.rootTheBoxScreen import RootTheBoxScreen
from screens.juiceShopScreen import JuiceShopScreen
from screens.documentationScreen import DocumentationScreen


class JuiceBoxApp(App):
    BINDINGS = [
        Binding(key="^q", action="quit", description="Quit", show=True),
    ]
    VERSION: float = 1.1
    TITLE = "JuiceBox Manager 🍊"
    SUB_TITLE = f"v.{VERSION}"
    SCREENS = {
        "main": MainScreen,
        "root": RootTheBoxScreen,
        "juice": JuiceShopScreen,
        "documentation": DocumentationScreen,
    }

    async def on_mount(self) -> None:
        await self.push_screen("main")  # inicia en pantalla principal


if __name__ == "__main__":
    JuiceBoxApp().run()
