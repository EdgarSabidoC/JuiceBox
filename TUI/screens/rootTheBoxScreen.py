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

SOCKET_PATH = dotenv_values().get("JUICEBOX_SOCKET") or "/run/juicebox/juicebox.sock"


class RootTheBoxScreen(Screen):
    CSS_PATH = "../styles/rootTheBox.tcss"
    JB_LOGO = pkg_resources.read_text("JuiceBox.TUI.media", "RootTheBoxLogo.txt")

    MENU_OPTIONS = {
        "Start": ("Start Root The Box services", JuiceBoxAPI.start_rtb),
        "Stop": ("Stop Root The Box services", JuiceBoxAPI.stop_rtb),
        "Restart": ("Restart Root The Box services", JuiceBoxAPI.restart_rtb_status),
        "Configuration": (
            "Configuration file for Root The Box services",
            JuiceBoxAPI.set_rtb_config,
        ),
        "Return": ("Return to main menu", None),
    }

    BINDINGS = [
        Binding("ctrl+b", "go_back", "Back", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    __skip_resume: bool = (
        False  # Variable para evitar que on_screen_resume se dispare con los modal screens
    )

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

    async def on_mount(self) -> None:
        self._start_redis_listener()  # Se conecta al socket de Redis
        # await self.init()

    # Permite realizar una acción al presionar una opción del menú
    async def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        option: str = str(event.option.prompt).strip()
        description, action = self.MENU_OPTIONS.get(option, (None, None))

        if action is None:
            await self.return_to_main()
            return

        async def handle_confirm():
            self.__skip_resume = True
            result = await self.app.push_screen_wait(
                ConfirmModal(f"¿Seguro que deseas ejecutar: {option}?")
            )
            if result == "yes":
                try:
                    if asyncio.iscoroutinefunction(action):
                        resp = await action()
                    else:
                        resp = await asyncio.to_thread(action)

                    __color: str = "green" if resp.status == Status.OK else "red"
                    self.menu_info.update(
                        f"{description}\n[{__color}]\n\nOperation {option}: {resp.status.upper()} [/{__color}]"
                    )
                except Exception as e:
                    self.menu_info.update(
                        f"{description}\n[red]\n\nOperation {option}: {e}[/red]"
                    )
            else:
                self.menu_info.update(
                    f"[yellow]Operation {option}: Cancelled ⚠︎[/yellow]"
                )
            self.__skip_resume = False

        self.run_worker(handle_confirm())

    async def on_screen_resume(self, event: ScreenResume) -> None:
        """
        Este evento salta cada vez que la pantalla vuelve a activarse (show).
        Aquí se forza a que la opción 0 quede resaltada y se le da el focus.
        """
        if not self.__skip_resume:
            # Selecciona el índice 0
            self.menu.highlighted = 0

            # Se asegura que el widget tenga el enfoque
            self.menu.focus()

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

    async def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ):
        option: str = str(event.option.prompt).strip()
        description = self.MENU_OPTIONS.get(option, "No menu_info available.")[0]
        self.menu_info.update(description)

    async def get_conf(self) -> str:
        try:
            resp = await JuiceBoxAPI.get_rtb_config()
            return str(resp.data["config"])
        except Exception:
            return '"status": "error"'

    def _start_redis_listener(self) -> None:
        """Crea y arranca el hilo que escucha Redis."""
        # guardamos la referencia para que no se recoja
        self._redis_thread = threading.Thread(
            target=self._listen_to_redis_sync, daemon=True
        )
        self._redis_thread.start()

    def _listen_to_redis_sync(self) -> None:
        """Hilo de escucha que nunca debe tocar la UI directamente."""
        client = redis.Redis(
            host="localhost", port=6379, db=0, password="C5L48", decode_responses=True
        )
        pubsub = client.pubsub()
        pubsub.subscribe("admin_channel", "client_channel")

        # Mensaje de arranque
        self.app.call_from_thread(
            lambda: self.SERVICES_STATUS_DATA_WEBAPP.update("Listener started")
        )

        for message in pubsub.listen():
            # Mensaje de confirmación de subscribe, unsubscribe, etc
            mtype = message.get("type")
            # Actualiza el tipo (ejemplo)
            self.app.call_from_thread(
                lambda m=mtype: self.SERVICES_STATUS_DATA_WEBAPP.update(
                    f"Message type: {m}"
                )
            )

            if mtype != "message":
                continue

            try:
                data = json.loads(message["data"])
            except Exception:
                continue

            def _update():
                status = (
                    "[green]✔[/green]"
                    if data["status"] == "running"
                    else "[red]✘[/red]"
                )
                self.SERVICES_STATUS_DATA_WEBAPP.update(status)

                status = (
                    "[green]✔[/green]"
                    if data["status"] == "running"
                    else "[red]✘[/red]"
                )
                self.SERVICES_STATUS_DATA_CACHE.update(status)

            self.app.call_from_thread(_update)
