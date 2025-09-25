#!/usr/bin/env python3
from textual.app import App
from textual.binding import Binding
from .screens import MainScreen
from .screens import RootTheBoxScreen
from .screens import JuiceShopScreen
from .screens import DocumentationScreen
from .styles.theme import (
    juice_box_theme,
    hacker_dark_blue_theme,
    hacker_dark_green_theme,
    synthwave_80s_theme,
)
from dotenv import dotenv_values


class JuiceBoxApp(App):
    BINDINGS = [
        Binding(key="^q", action="quit", description="Quit", show=True),
    ]
    VERSION: str = "1.1.0"
    TITLE = "JuiceBox Manager 🍊"
    SUB_TITLE = f"v.{VERSION}"
    SCREENS = {
        "main": MainScreen,
        "root": RootTheBoxScreen,
        "juice": JuiceShopScreen,
        "documentation": DocumentationScreen,
    }
    SOCKET_PATH = dotenv_values().get("JUICEBOX_SOCKET") or "/run/juicebox/engine.sock"

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


def main():
    JuiceBoxApp().run()
