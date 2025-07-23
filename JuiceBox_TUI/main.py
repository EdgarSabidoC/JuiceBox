from textual.app import App
from textual.screen import Screen
from textual.reactive import reactive
from textual.binding import Binding

from textual.widgets import Label, Static, OptionList, Footer, Header, Placeholder, Link

from screens.mainScreen import MainScreen
# from screens.rootTheBoxScreen import RootTheBox
# from screens.juiceShopScreen import JuiceShop
# from screens.dockerScreen import Docker
# from screens.documentationScreen import Documentation


class JuiceBoxApp(App):
    BINDINGS = [
      Binding(key="^q", action="quit", description="Quit", show=True),
      # Binding(key="^r", action="refresh", description="Reload data", show=True),
      # Binding(key="^h", action="help", description="Help", show=True)
    ]
    VERSION = 1.1
    TITLE = "JuiceBox Manager 🍊"
    SUB_TITLE = f"v.{VERSION}"
    SCREENS = {
      "main": MainScreen,
      # "root": RootTheBox,
      # "juice": JuiceShop,
      # "docker": Docker,
      # "documentation": Documentation
    }

    async def on_mount(self) -> None:
        await self.push_screen("main")  # inicia en pantalla principal


if __name__ == "__main__":
  JuiceBoxApp().run()