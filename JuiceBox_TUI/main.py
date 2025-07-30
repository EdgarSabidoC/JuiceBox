#!/usr/bin/env python3
from textual.app import App
from textual.binding import Binding
from screens.mainScreen import MainScreen
from screens.rootTheBoxScreen import RootTheBoxScreen
from screens.juiceShopScreen import JuiceShopScreen
from screens.documentationScreen import DocumentationScreen
from styles.theme import (
    juice_box_theme,
    hacker_dark_blue_theme,
    hacker_dark_green_theme,
    synthwave_80s_theme,
)


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
    SOCKET_PATH = "/tmp/juiceboxengine.sock"

    async def on_mount(self) -> None:
        self.set_themes()
        await self.push_screen("main")  # inicia en pantalla principal

    def set_themes(self) -> None:
        self.register_theme(juice_box_theme)
        self.register_theme(hacker_dark_blue_theme)
        self.register_theme(hacker_dark_green_theme)
        self.register_theme(synthwave_80s_theme)
        # Se desactivan los temas light:
        for theme in self.available_themes:
            current = self.get_theme(theme)
            if current and not current.dark:
                self.unregister_theme(theme)
        self.theme = "juice-box"


if __name__ == "__main__":
    JuiceBoxApp().run()
