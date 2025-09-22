import time, os, json, asyncio, redis, threading, functools
from textual.app import ComposeResult
from textual.screen import Screen
from ..widgets import get_footer
from ..widgets import get_header
from textual.screen import Screen
from textual.events import ScreenResume
from textual.containers import Vertical, Horizontal, ScrollableContainer, VerticalScroll
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
from asyncio import AbstractEventLoop
from functools import partial

NOT_AVAILABLE = "[red]Not available ✘[/red]"
AVAILABLE = "[green]Active and running ✔[/green]"


class JuiceShopScreen(Screen):
    CSS_PATH = "../styles/juiceShop.tcss"
    JS_LOGO = pkg_resources.read_text("JuiceBox.TUI.media", "JuiceShopLogo.txt")
    SERVICE_LABELS: dict[str, tuple[Horizontal, Label]] = {}

    MENU_OPTIONS = {
        "Start a container": (
            "Start an OWASP Juice Shop container",
            JuiceBoxAPI.start_js_container,
        ),
        "Start n containers": (
            "Start n OWASP Juice Shop containers",
            JuiceBoxAPI.start_n_js_containers,
        ),
        "Stop a container": (
            "Stop an OWASP Juice Shop container",
            JuiceBoxAPI.stop_js_container,
        ),
        "Stop all containers": (
            "Stop all OWASP Juice Shop containers",
            JuiceBoxAPI.stop_js,
        ),
        "Restart": (
            "Restart OWASP Juice Shop services",
            JuiceBoxAPI.restart_js_status,
        ),
        "Generate missions": (
            "Generate new XML with missions for Root The Box (This feature requires internet connection)",
            JuiceBoxAPI.generate_xml,
        ),
        "Configuration": (
            "Configuration file for OWASP Juice Shop services",
            JuiceBoxAPI.set_js_config,
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
                # Logo de JS
                js_logo = Static(self.JS_LOGO, classes="js-logo")
                js_logo.can_focus = False
                yield js_logo

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
            with VerticalScroll(classes="vcontainer2") as vcontainer2:
                vcontainer2.can_focus = False
                self.config_container = VerticalScroll(classes="config-container")
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
                self.services_status = ScrollableContainer(classes="services-status")
                self.services_status.styles.overflow_y = "scroll"
                self.services_status.can_focus = False
                self.services_status.border_title = "Services Status"
                yield self.services_status

        # Footer
        yield get_footer()

    async def on_mount(self) -> None:
        """
        Evento que se ejecuta al montar la pantalla.
        Inicia el listener de Redis que refresca la información inicial de configuración y estado.
        """
        # Obtiene el rango de puertos del manager
        ports_resp = await JuiceBoxAPI.get_js_ports_range()
        if ports_resp.status != Status.OK:
            return
        self.ports_range = ports_resp.data.get("ports_range", [])
        self.__start_redis_listener()  # Se conecta al socket de Redis

        # Ejecuta el resto de acciones con confirmación

    async def __on_config_dismissed(self, result: str | None, description: str) -> None:
        if result:
            try:
                parsed = json.loads(result)
                resp = await JuiceBoxAPI.set_js_config(parsed)
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

                # Actualizar rango de puertos tras la nueva configuración
                resp_ports = await JuiceBoxAPI.get_js_ports_range()
                if resp_ports.status == Status.OK:
                    self.ports_range = resp_ports.data.get("ports_range", [])

                    valid_containers = {
                        f"owasp-juice-shop-{port}" for port in range(*self.ports_range)
                    }

                    # Limpiar labels que ya no aplican
                    to_remove = [
                        cn for cn in self.SERVICE_LABELS if cn not in valid_containers
                    ]
                    for cn in to_remove:
                        h_container, _ = self.SERVICE_LABELS.pop(cn)
                        h_container.remove()

                # Se actualiza la TUI con la nueva configuración
                resp_refresh = await JuiceBoxAPI.get_js_config()
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
                if option == "Generate missions":
                    self.notify(
                        "Please wait while the RTB missions file loads, it may take a while...",
                        severity="warning",
                        title="Patience is a virtue:",
                        timeout=30,
                    )

                if asyncio.iscoroutinefunction(action):
                    resp = await action()
                else:
                    resp = await asyncio.to_thread(action)

                __color, __severity = (
                    ("green", "information")
                    if resp.status == Status.OK
                    else ("red", "error")
                )
                self.menu_info.update(
                    f"{description}\n[{__color}]\n\nOperation {option.upper()}: {resp.status.upper()} [/{__color}]"
                )
                self.notify(
                    f"[b]{option.upper()}[/b] has finished: [b]{resp.status.upper()}[/b]",
                    title="Operation status:",
                    severity=__severity,
                    timeout=10,
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
                resp: Response = await JuiceBoxAPI.get_js_config()
                config_dict = resp.data.get("config", {})
                # Se eliminan las claves que no deben editarse
                config_dict.pop("container_prefix", None)
                config_dict.pop("node_env", None)
                config_dict.pop("detach_mode", None)
                config_dict.pop("image", None)
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
            resp = await JuiceBoxAPI.get_js_config()
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

    async def refresh_status(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.__init_containers_status(loop))

    def __update_ui(self, data: dict) -> None:
        """
        Actualiza el estado de un contenedor en la UI según los datos recibidos.

        Args:
            data (dict): Diccionario con 'container' y 'status'.
        """
        if data["container"] == "juicebox-engine":
            # Refresca la configuración
            asyncio.run_coroutine_threadsafe(
                self.action_refresh(),
                loop=asyncio.get_event_loop(),
            )
        elif "owasp" in data["container"]:
            # Refresca todo el bloque de servicios
            asyncio.run_coroutine_threadsafe(
                self.refresh_status(),
                asyncio.get_event_loop(),
            )

    def __load_config(self, loop: AbstractEventLoop) -> None:
        """
        Obtiene y carga la configuración en la TUI.

        Args:
            loop (AbstractEventLoop): Loop de eventos
        """
        try:
            conf_resp = loop.run_until_complete(JuiceBoxAPI.get_js_config())
            if conf_resp.status == Status.OK:
                config_text = json.dumps(conf_resp.data.get("config", {}), indent=4)
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

    def __init_containers_status(self, loop: AbstractEventLoop) -> None:
        """
        Inicializa o actualiza el estado de los contenedores en la UI.
        """
        future = None
        try:
            # Ejecutar la API de manera segura
            future = asyncio.run_coroutine_threadsafe(JuiceBoxAPI.get_js_status(), loop)
            resp = future.result(timeout=5)

            if resp is None:
                for _, label_status in self.SERVICE_LABELS.values():
                    self.app.call_from_thread(
                        lambda ls=label_status: ls.update(NOT_AVAILABLE)
                    )

            if resp.status != Status.OK:
                return

            containers_list = resp.data.get("containers", [])
            containers_map = {
                entry.get("data", {})
                .get("container"): entry.get("data", {})
                .get("status")
                for entry in containers_list
                if entry.get("data", {}).get("container")
            }

            start, end = self.ports_range
            for port in range(start, end + 1):
                container_name = f"owasp-juice-shop-{port}"
                status_str = containers_map.get(container_name, "not_found")
                status_display = AVAILABLE if status_str == "running" else NOT_AVAILABLE

                # Actualiza UI en hilo principal
                def update_label(cn=container_name, sd=status_display):
                    if cn not in self.SERVICE_LABELS:
                        # Crear nuevos widgets
                        h_container = Horizontal(classes="h_container_services_data")
                        label_name = Label(f"{cn}: ", classes="services-status-key")
                        label_status = Label(sd, classes="services-status-datum")
                        self.SERVICE_LABELS[cn] = (h_container, label_status)
                        self.services_status.mount(h_container)
                        h_container.mount(label_name)
                        h_container.mount(label_status)
                    else:
                        # Solo actualizar texto
                        _, label_status = self.SERVICE_LABELS[cn]
                        label_status.update(sd)

                self.app.call_from_thread(update_label)

        except Exception:
            # Fallback: marcar todos como no disponibles
            for _, label_status in self.SERVICE_LABELS.values():
                self.app.call_from_thread(
                    lambda ls=label_status: ls.update(NOT_AVAILABLE)
                )

    def __listener_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

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
                self.__init_containers_status(loop)

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

                    if self.config_data.loading:
                        self.__load_config(loop)

                    time.sleep(1)

            except ConnectionError:
                # Redis no disponible: marca todos los servicios como no disponibles
                for _, label_status in self.SERVICE_LABELS.values():
                    self.app.call_from_thread(
                        lambda ls=label_status: ls.update(NOT_AVAILABLE)
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
