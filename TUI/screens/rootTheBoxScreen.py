import time, os, json, asyncio, redis, threading
from textual.app import ComposeResult
from textual.screen import Screen
from ..widgets import get_footer
from ..widgets import get_header
from textual.screen import Screen
from textual.events import ScreenResume
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Static, OptionList
from textual.binding import Binding
from ..widgets import ReactiveMarkdown
from rich.text import Text
from ...Models import Status, Response
from ...JuiceBoxEngine.api import JuiceBoxAPI
from ..widgets.confirmModal import ConfirmModal
import importlib.resources as pkg_resources
from ..widgets.configModal import ConfigModal
from dotenv import load_dotenv
from redis.exceptions import ConnectionError

NOT_AVAILABLE = "[red]Not available ✘[/red]"
AVAILABLE = "[green]Active and running ✔[/green]"


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
        Binding("ctrl+r", "refresh", "Refresh", show=True),
    ]

    __skip_resume: bool = (
        False  # Variable para evitar que on_screen_resume se dispare con los modal screens
    )

    def compose(self) -> ComposeResult:
        """
        Composición inicial de la pantalla.
        Configura header, footer, menú, logos, contenedores y estado de servicios.

        Returns:
            ComposeResult: Generador de widgets a mostrar en la pantalla.
        """
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

            # Configuración y estado de servicios
            with Vertical(classes="vcontainer2") as vcontainer2:
                vcontainer2.can_focus = False
                self.config_container = ScrollableContainer(classes="config-container")
                self.config_container.border_title = "Configuration"
                self.config_data = ReactiveMarkdown(data="Loading configuration…")
                self.config_data.can_focus = False
                self.config_data.styles.color = "white"
                self.config_container.can_focus = False
                self.config_data.visible = False
                self.config_data.loading = True
                # Configuración
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
        """
        Evento que se ejecuta al montar la pantalla.
        Inicia el listener de Redis que refresca la información inicial de configuración y estado.
        """
        self.__start_redis_listener()  # Se conecta al socket de Redis

        # Ejecuta el resto de acciones con confirmación

    async def __on_config_dismissed(self, result: str | None, description: str) -> None:
        if result:
            try:
                parsed = json.loads(result)
                resp = await JuiceBoxAPI.set_rtb_config(parsed)
                __color, __severity = (
                    ("green", "information")
                    if resp.status == Status.OK
                    else ("red", "error")
                )
                self.menu_info.update(
                    f"{description}\n[{__color}]\nOperation CONFIGURATION: {resp.status.upper()} [/{__color}]"
                )
                self.notify(
                    f"[b]CONFIGURATION[/b] editing has finished: [b]{resp.status.upper()}[/b]",
                    title="Operation Status:",
                    severity=__severity,
                )
                # Se actualiza la TUI con la nueva configuración
                resp_refresh = await JuiceBoxAPI.get_rtb_config()
                if resp_refresh.status == Status.OK:
                    config_text = json.dumps(
                        resp_refresh.data.get("config", {}), indent=4
                    )
                    self.config_data.update_content(config_text, is_json=True)
            except Exception as e:
                self.menu_info.update(
                    f"{description}\n[red]\n\nOperation CONFIGURATION: {e}[/red]"
                )
        else:
            self.menu_info.update(
                "[yellow]Operation CONFIGURATION: Canceled ⚠︎[/yellow]"
            )
            self.notify(
                "[b]CONFIGURATION[/b] editing has been [b]canceled[/b]",
                title="Operation Status:",
                severity="warning",
            )
        self.__skip_resume = False

    async def __handle_confirm(self, option: str, description: str, action) -> None:
        """
        Muestra la confirmación y ejecuta la acción seleccionada.
        """
        self.__skip_resume = True
        result = await self.app.push_screen_wait(
            ConfirmModal(f"¿Are you sure you want to execute: {option.upper()}?")
        )
        if result == "yes":
            try:
                if asyncio.iscoroutinefunction(action):
                    resp = await action()
                else:
                    resp = await asyncio.to_thread(action)

                __color, __severity = (
                    ("green", "information") if resp.status == Status.OK else ("red"),
                    "error",
                )
                self.menu_info.update(
                    f"{description}\n[{__color}]\n\nOperation {option.upper()}: {resp.status.upper()} [/{__color}]"
                )
                self.notify(
                    f"[b]{option.upper()}[/b] has finished: [b]{resp.status.upper()}[/b]",
                    title="Operation status:",
                    severity=__severity,
                )
            except Exception as e:
                self.menu_info.update(
                    f"{description}\n[red]\n\nOperation {option.upper()}: {e}[/red]"
                )
        else:
            self.menu_info.update(
                f"[yellow]Operation {option.upper()}: Canceled ⚠︎[/yellow]"
            )
            self.notify(
                f"[b]{option.upper()}[/b] has been [b]canceled[/b]",
                title="Operation status:",
                severity="warning",
            )
        self.__skip_resume = False

    async def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """
        Ejecuta la acción correspondiente a la opción seleccionada en el menú.

        Args:
            event (OptionList.OptionSelected): Evento que contiene la opción seleccionada.
        """
        option: str = str(event.option.prompt).strip()
        description, action = self.MENU_OPTIONS.get(option, (None, None))

        # Regresa al menú principal
        if action is None:
            await self.return_to_main()
            return

        # Edita la configuración
        if option == "Configuration":
            try:
                resp: Response = await JuiceBoxAPI.get_rtb_config()
                config_dict = resp.data.get("config", {})
                # Se eliminan las claves que no deben editarse
                config_dict.pop("network_name", None)
                config_dict.pop("webapp_container_name", None)
                config_dict.pop("cache_container_name", None)
                config_dict.pop("rtb_dir", None)
                config_text = json.dumps(config_dict, indent=4)

                async def __run_handle_config():
                    result = await self.app.push_screen_wait(ConfigModal(config_text))
                    await self.__on_config_dismissed(result, description)

                self.__skip_resume = True
                self.run_worker(__run_handle_config)
            except Exception as e:
                self.menu_info.update(f"[red]Config couldn't be loaded: {e}[/red]")
            return

        async def __run_handle_confirm():
            await self.__handle_confirm(option, description, action)

        self.run_worker(__run_handle_confirm)

    async def on_screen_resume(self, event: ScreenResume) -> None:
        """
        Evento que se ejecuta cuando la pantalla vuelve a mostrarse.

        Args:
            event (ScreenResume): Evento que indica que la pantalla ha sido reactivada.
        """
        if not self.__skip_resume:
            # Selecciona el índice 0
            self.menu.highlighted = 0

            # Se asegura que el widget tenga el enfoque
            self.menu.focus()

    async def return_to_main(self) -> None:
        """
        Regresa a la pantalla principal del menú.
        """
        # Opcional: comprueba que no estés en la pantalla raíz
        if self.screen.id != "main":
            # Se reemplaza la pantalla actual
            await self.app.pop_screen()
            # Se cambia a la nueva pantalla
            await self.app.push_screen("main")

    async def action_go_back(self) -> None:
        """
        Acción para regresar a la pantalla principal desde cualquier opción.
        """
        await self.return_to_main()

    async def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ):
        """
        Actualiza la información mostrada al resaltar una opción.

        Args:
            event (OptionList.OptionHighlighted): Evento de opción resaltada.
        """
        option: str = str(event.option.prompt).strip()
        description = self.MENU_OPTIONS.get(option, "No menu_info available.")[0]
        self.menu_info.update(description)

    async def get_conf(self) -> str:
        """
        Obtiene la configuración actual de RootTheBox.

        Returns:
            str: Configuración como string JSON, o un string de error si falla.
        """
        try:
            resp = await JuiceBoxAPI.get_rtb_config()
            if resp.status == Status.OK:
                self.config_data.loading = False
                self.config_data.visible = True
            else:
                self.config_data.visible = False
                self.config_data.loading = True
            return str(resp.data["config"])
        except Exception:
            return '"status": "error"'

    async def action_refresh(self) -> None:
        """
        Recarga la configuración y el estado de los servicios.
        """
        if not self.config_data.visible:
            new_conf = await self.get_conf()
            self.config_data.update_content(new_conf, is_json=True)
            self.menu_info.update("[yellow]Data refreshed[/yellow]")

    def __update_ui(self, data: dict) -> None:
        """
        Actualiza el estado de los servicios en la UI según datos recibidos.

        Args:
            data (dict): Diccionario con 'container' y 'status'.
        """
        status = AVAILABLE if data["status"] == "running" else NOT_AVAILABLE
        if data["container"] == "juicebox-engine":
            # Refresca la configuración
            asyncio.run_coroutine_threadsafe(
                self.action_refresh(),
                loop=asyncio.get_event_loop(),
            )
        elif data["container"] == "rootthebox-webapp-1":
            self.SERVICES_STATUS_DATA_WEBAPP.update(status)
        elif data["container"] == "rootthebox-memcached-1":
            self.SERVICES_STATUS_DATA_CACHE.update(status)

    def __listener_thread(self):
        """
        Hilo que mantiene conexión con Redis, actualiza estado de servicios
        y refresca la configuración mientras Redis está activo.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Carga el .env cada vez antes de usar la contraseña
        env_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../.env")
        )
        load_dotenv(env_path)
        redis_pass = os.getenv("REDIS_PASSWORD")

        while True:
            try:
                client = redis.Redis(
                    host="localhost",
                    port=6379,
                    db=0,
                    password=redis_pass,
                    decode_responses=True,
                )
                pubsub = client.pubsub()
                pubsub.subscribe("admin_channel", "client_channel")

                # Estado inicial
                self.app.call_from_thread(
                    lambda: setattr(self.config_data, "loading", True)
                )

                # Intenta obtener el estado inicial de los contenedores
                try:
                    resp = loop.run_until_complete(JuiceBoxAPI.get_rtb_status())
                    if resp.status == Status.OK:
                        containers = resp.data.get("containers", [])
                        status = (
                            AVAILABLE
                            if containers[0]["data"]["status"] == "running"
                            else NOT_AVAILABLE
                        )
                        self.app.call_from_thread(
                            lambda status=status: self.SERVICES_STATUS_DATA_WEBAPP.update(
                                status
                            )
                        )
                        status = (
                            AVAILABLE
                            if containers[1]["data"]["status"] == "running"
                            else NOT_AVAILABLE
                        )
                        self.app.call_from_thread(
                            lambda status=status: self.SERVICES_STATUS_DATA_CACHE.update(
                                status
                            )
                        )
                    else:
                        status = NOT_AVAILABLE
                except Exception:
                    pass  # Mantiene estado Unvailable si falla

                # Loop principal de mensajes
                while True:
                    message = pubsub.get_message(timeout=0.5)
                    if message and message.get("type") == "message":
                        try:
                            data = json.loads(message["data"])
                        except Exception:
                            continue

                        self.app.call_from_thread(
                            lambda data=data: self.__update_ui(data)
                        )

                    # Intenta cargar la configuración si está en loading
                    if self.config_data.loading:
                        try:
                            conf_resp = loop.run_until_complete(
                                JuiceBoxAPI.get_rtb_config()
                            )
                            if conf_resp.status == Status.OK:
                                config_text = json.dumps(
                                    conf_resp.data.get("config", {}), indent=4
                                )
                                self.app.call_from_thread(
                                    lambda: setattr(self.config_data, "loading", False)
                                )
                                self.app.call_from_thread(
                                    lambda: setattr(self.config_data, "visible", True)
                                )
                                self.app.call_from_thread(
                                    lambda config_text=config_text: self.config_data.update_content(
                                        config_text, is_json=True
                                    )
                                )
                        except Exception:
                            pass

                    # Tiempo para reintentar la reconexión a Redis
                    time.sleep(1)

            except ConnectionError:
                # Redis no está disponible
                self.app.call_from_thread(
                    lambda: self.SERVICES_STATUS_DATA_WEBAPP.update(NOT_AVAILABLE)
                )
                self.app.call_from_thread(
                    lambda: self.SERVICES_STATUS_DATA_CACHE.update(NOT_AVAILABLE)
                )
                self.app.call_from_thread(
                    lambda: setattr(self.config_data, "loading", True)
                )
                time.sleep(5)
                continue

    def __start_redis_listener(self):
        """
        Inicia un hilo en segundo plano para escuchar a Redis y mantener la UI actualizada.
        """
        threading.Thread(target=self.__listener_thread, daemon=True).start()
