from textual.app import App
from textual.binding import Binding
from screens.mainScreen import MainScreen
from screens.rootTheBoxScreen import RootTheBoxScreen
from screens.juiceShopScreen import JuiceShopScreen
from screens.documentationScreen import DocumentationScreen
from styles.theme import hacker_light_theme, hacker_dark_theme


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
        self.set_themes()
        await self.push_screen("main")  # inicia en pantalla principal

    def set_themes(self) -> None:
        # Se desactivan los temas por defecto:
        for theme in self.available_themes:
            self.unregister_theme(theme)
        self.register_theme(hacker_light_theme)
        self.register_theme(hacker_dark_theme)
        self.theme = "hacker-dark"


if __name__ == "__main__":
    JuiceBoxApp().run(size=(120, 44))
