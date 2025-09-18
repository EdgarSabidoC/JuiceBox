from textual.app import ComposeResult
from textual.screen import Screen
from ..widgets import get_footer
from ..widgets import get_header
from textual.screen import Screen
from textual.events import ScreenResume
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Static, OptionList, Button, RichLog
from textual.binding import Binding
from typing import Union
import json, asyncio
from ..widgets import CustomSwitch
from textual.reactive import reactive
from ..widgets import ReactiveMarkdown
from rich.text import Text
from ...Models import Status, Response
import redis, threading
from ...JuiceBoxEngine.api import JuiceBoxAPI
from ..widgets.confirmModal import ConfirmModal
import importlib.resources as pkg_resources
from dotenv import dotenv_values


class JuiceShopScreen(Screen):
    CSS_PATH = "../styles/main.tcss"
    JB_LOGO = pkg_resources.read_text("JuiceBox.TUI.media", "JuiceBoxLogo.txt")

    MENU_OPTIONS = {
        "Start": ("Start Root The Box services", JuiceBoxAPI.start_js_container),
        "Stop": ("Stop Root The Box services", JuiceBoxAPI.stop_js_container),
        "Restart": ("Restart Root The Box services", JuiceBoxAPI.restart_js_status),
        "Configuration": (
            "Configuration file for Root The Box services",
            JuiceBoxAPI.set_js_config,
        ),
        "Return": ("Return to main menu", None),
    }

    BINDINGS = [
        Binding("ctrl+b", "go_back", "Back", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        # Header
        yield get_header()

        with Horizontal(classes="hcontainer") as hcontainer:
            hcontainer.can_focus = False

            with Vertical(classes="vcontainer1") as vcontainer1:
                vcontainer1.can_focus = False
                # Logo de RTB
                jb_logo = Static(self.JB_LOGO, classes="rtb-logo")
                jb_logo.can_focus = False
                yield jb_logo

                # Menú
                self.menu = OptionList(classes="menu")
                self.menu.add_options(self.MENU_OPTIONS.keys())
                yield self.menu

                # Información sobre las opciones
                self.menu_info = Static(classes="info-box")
                self.menu_info.can_focus = False
                self.menu_info.border_title = "Output"
                yield self.menu_info

            with Vertical(classes="vcontainer2") as vcontainer2:
                vcontainer2.can_focus = False
                self.config_container = ScrollableContainer(classes="config-container")
                self.config_container.border_title = "Configuration"
                self.config_data = ReactiveMarkdown(data="Loading configuration…")
                self.config_data.can_focus = False
                self.config_data.styles.color = "white"
                self.config_container.can_focus = False
                with self.config_container:
                    yield self.config_data

                # Services status
                with Horizontal() as server_status:
                    server_status.can_focus = False
                    server_status.styles.content_align = ("center", "middle")
                    server_status.styles.align = ("center", "middle")
                    server_status.styles.border
                    with Vertical(classes="services-status-keys") as server_info_keys:
                        server_info_keys.can_focus = False
                        self.SERVICES_STATUS_KEYS_WEBAPP = Label(
                            classes="services-status-key"
                        )
                        self.SERVICES_STATUS_KEYS_WEBAPP.update("Webapp: ")
                        yield self.SERVICES_STATUS_KEYS_WEBAPP
                        self.SERVICES_STATUS_KEYS_CACHE = Label(
                            classes="services-status-key"
                        )
                        self.SERVICES_STATUS_KEYS_CACHE.update("Caché: ")
                        yield self.SERVICES_STATUS_KEYS_CACHE
                    with Vertical(
                        classes="services-status-data"
                    ) as services_status_values:
                        services_status_values.can_focus = False
                        services_status_values.border_title = " Services Status"
                        self.SERVICES_STATUS_DATA_WEBAPP = Label(
                            classes="services-status-datum"
                        )
                        self.SERVICES_STATUS_DATA_WEBAPP.can_focus = False
                        yield self.SERVICES_STATUS_DATA_WEBAPP
                        self.SERVICES_STATUS_DATA_CACHE = Label(
                            classes="services-status-datum"
                        )
                        self.SERVICES_STATUS_DATA_CACHE.can_focus = False
                        yield self.SERVICES_STATUS_DATA_CACHE

        # Footer
        yield get_footer()

    # Permite realizar un cambio de pantalla
    async def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        choice = str(event.option.prompt).strip()

        # No llames a self.app.exit() aquí; sólo asigna None para “Exit”
        screen_map = {
            "📦 Root the Box": "root",
            "🧃 OWASP Juice Shop": "juice",
            "🐋 Docker": "docker",
            "↩  Return": "main",
        }

        target = screen_map.get(choice)
        if target == "main":
            await self.return_to_main()
        elif target is not None:
            # Se reemplaza la pantalla actual
            await self.app.pop_screen()
            # Se cambia a la nueva pantalla
            await self.app.push_screen(target)

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
