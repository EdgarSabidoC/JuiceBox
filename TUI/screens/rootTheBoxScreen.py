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
from JuiceBox.Models import Status, Response
from JuiceBox.Engine.api import JuiceBoxAPI, REDIS_PASSWORD
from ..widgets.confirmModal import ConfirmModal
import importlib.resources as pkg_resources
from ..widgets.configModal import ConfigModal
from redis.exceptions import ConnectionError
from asyncio import AbstractEventLoop
from redis.client import PubSub

NOT_AVAILABLE = "[red]Not available ✘[/red]"
AVAILABLE = "[green]Active and running ✔[/green]"


class RootTheBoxScreen(Screen):
    CSS_PATH = "../styles/rootTheBox.tcss"
    RTB_LOGO = pkg_resources.read_text("TUI.media", "RootTheBoxLogo.txt")

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
                rtb_logo = Static(self.RTB_LOGO, classes="rtb-logo")
                rtb_logo.can_focus = False
                yield rtb_logo

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
                with Horizontal() as self.services_status:
                    self.services_status.can_focus = False
                    self.services_status.styles.content_align = ("center", "middle")
                    self.services_status.styles.align = ("center", "middle")
                    self.services_status.styles.border
                    self.services_status.visible = False
                    self.services_status.loading = True
                    with Vertical(
                        classes="services-status-keys"
                    ) as services_status_keys:
                        services_status_keys.can_focus = False
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
        __color: str = "gold"
        __severity: str = "warning"
        __op_status: str = "Operation Status:"
        if result:
            try:
                self.notify(
                    message="Please wait for the CONFIGURATION operation to finish, it may take a while...",
                    severity=__severity,
                    title="Patience is a virtue:",
                    timeout=5,
                )
                parsed = json.loads(result)
                resp = await JuiceBoxAPI.set_rtb_config(parsed)
                __color, __severity = (
                    ("green", "information")
                    if resp.status == Status.OK
                    else ("red", "error")
                )
                self.notify(
                    message=f"[b]CONFIGURATION[/b] editing has finished: [b][{__color}]{resp.status.upper()}[/{__color}][/b]",
                    title=__op_status,
                    severity=__severity,
                    timeout=5,
                )
                # Se actualiza la TUI con la nueva configuración
                resp_refresh = await JuiceBoxAPI.get_rtb_config()
                if resp_refresh.status == Status.OK:
                    config_text = json.dumps(
                        resp_refresh.data.get("config", {}), indent=4
                    )
                    self.config_data.update_content(config_text, is_json=True)
            except Exception as e:
                __severity = "error"
                __color = "red"
                self.notify(
                    f"[b]CONFIGURATION[/b] editing has finished with error: [b][{__color}]{e}[/{__color}][/b]",
                    title=__op_status,
                    severity=__severity,
                    timeout=5,
                )
        else:
            self.notify(
                f"[b]CONFIGURATION[/b] editing has been [b][{__color}]canceled ⚠︎[/{__color}][/b]",
                title=__op_status,
                severity=__severity,
                timeout=5,
            )
        self.__skip_resume = False

    async def __handle_confirm(self, option: str, description: str, action) -> None:
        """
        Muestra la confirmación y ejecuta la acción seleccionada.
        Refresca la UI de servicios si se trata de un restart.
        """
        __color: str = "gold"
        __severity: str = "warning"
        __op_status: str = "Operation Status:"
        option = option.upper()
        self.__skip_resume = True
        result = await self.app.push_screen_wait(
            ConfirmModal(
                f"¿Are you sure you want to execute: [b][{__color}]{option}[/b][/{__color}]?"
            )
        )
        if result == "yes":
            try:
                self.notify(
                    f"Please wait for the {option} operation to finish, it may take a while...",
                    severity=__severity,
                    title="Patience is a virtue:",
                    timeout=5,
                )
                # Ejecuta la acción, ya sea coroutine o función síncrona
                if asyncio.iscoroutinefunction(action):
                    resp = await action()
                else:
                    resp = await asyncio.to_thread(action)

                __color, __severity = (
                    ("green", "information")
                    if resp.status == Status.OK
                    else ("red", "error")
                )

                self.notify(
                    f"[b]{option}[/b] has finished: [b]{resp.status.upper()}[/b]",
                    title=__op_status,
                    severity=__severity,
                    timeout=5,
                )

                # --- REFRESCO PARA RESTART ---
                if option == "Restart" and resp.status == Status.OK:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, lambda: self.__init_containers_status(loop)
                    )

            except Exception as e:
                __severity = "error"
                __color = "red"
                self.notify(
                    f"{description} -> [b]{option}[/b] has finished with error:\n[b][{__color}]{e}[/{__color}][/b]",
                    title=__op_status,
                    severity=__severity,
                    timeout=5,
                )
        else:
            self.notify(
                f"[b]{option}[/b] has been been [b][{__color}]canceled ⚠︎[/{__color}][/b]",
                title=__op_status,
                severity=__severity,
                timeout=5,
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
            await self.__return_to_main()
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
                config_text = json.dumps(config_dict, indent=4)

                async def __run_handle_config():
                    result = await self.app.push_screen_wait(ConfigModal(config_text))
                    await self.__on_config_dismissed(result, description)

                self.__skip_resume = True
                self.run_worker(__run_handle_config)
            except Exception as e:
                self.notify(
                    message=f"{e}",
                    title="Config couldn't be loaded:",
                    severity="error",
                    timeout=5,
                )
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

    async def __return_to_main(self) -> None:
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
        await self.__return_to_main()

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

    async def __get_conf(self) -> str:
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

    async def __config_refresh(self) -> None:
        """
        Recarga la configuración.
        """
        if not self.config_data.visible:
            new_conf = await self.__get_conf()
            self.config_data.update_content(new_conf, is_json=True)
            await self.__get_container_status()

            self.notify(
                message="Data now has been refreshed",
                title="Data refreshed:",
                severity="warning",
                timeout=5,
            )

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
                self.__config_refresh(),
                loop=asyncio.get_event_loop(),
            )
        elif data["container"] == "rootthebox-webapp-1":
            self.SERVICES_STATUS_DATA_WEBAPP.update(status)
        elif data["container"] == "rootthebox-memcached-1":
            self.SERVICES_STATUS_DATA_CACHE.update(status)

    def __init_containers_status(self, loop: AbstractEventLoop) -> None:
        """
        Obtiene el estado inicial de los contenedores y los inicializa en la TUI.

        Args:
            loop (AbstractEventLoop): Loop de eventos.
        """
        try:
            resp = loop.run_until_complete(JuiceBoxAPI.get_rtb_status())
            if resp.status == Status.OK:
                containers = resp.data.get("containers", [])
                for c in containers:
                    name = c["data"]["container"]
                    status = (
                        AVAILABLE if c["data"]["status"] == "running" else NOT_AVAILABLE
                    )
                    if name == "rootthebox-webapp-1":
                        self.app.call_from_thread(
                            lambda status=status: self.SERVICES_STATUS_DATA_WEBAPP.update(
                                status
                            )
                        )
                    elif name == "rootthebox-memcached-1":
                        self.app.call_from_thread(
                            lambda status=status: self.SERVICES_STATUS_DATA_CACHE.update(
                                status
                            )
                        )
        except Exception:
            pass

    def __load_config(self, loop: AbstractEventLoop) -> None:
        """
        Obtiene y carga la configuración en la TUI.
        """
        try:
            conf_resp = loop.run_until_complete(JuiceBoxAPI.get_rtb_config())
            if conf_resp.status == Status.OK:
                config_text = json.dumps(conf_resp.data.get("config", {}), indent=4)
                # Se actualiza la UI
                self.__set_loading_states(state=False)
                self.__set_visible_states(state=True)
                self.app.call_from_thread(
                    lambda config_text=config_text: self.config_data.update_content(
                        config_text, is_json=True
                    )
                )
        except Exception:
            pass

    def __mark_services_unvailable(self) -> None:
        self.app.call_from_thread(
            lambda: self.SERVICES_STATUS_DATA_WEBAPP.update(NOT_AVAILABLE)
        )
        self.app.call_from_thread(
            lambda: self.SERVICES_STATUS_DATA_CACHE.update(NOT_AVAILABLE)
        )

    async def __refresh_status(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.__init_containers_status(loop))

    async def __get_container_status(self) -> None:
        """
        Obtiene el estado actual de los contenedores de Root The Box.

        Returns:
            str: Configuración como string JSON, o un string de error si falla.
        """
        try:
            resp = await JuiceBoxAPI.get_js_ports_range()
            if resp.status == Status.OK:
                self.services_status.loading = False
                self.services_status.visible = True
                await self.__refresh_status()
            else:
                self.services_status.visible = False
                self.services_status.loading = True
        except Exception:
            return

    def __set_loading_states(self, state: bool):
        """
        Cambia estado de carga de los widgets config_data y services_status.
        """
        self.app.call_from_thread(lambda: setattr(self.config_data, "loading", state))
        self.app.call_from_thread(
            lambda: setattr(self.services_status, "loading", state)
        )

    def __set_visible_states(self, state: bool) -> None:
        """
        Cambia estado de visibilidad de los widgets config_data y services_status.
        """
        self.app.call_from_thread(lambda: setattr(self.config_data, "visible", state))
        self.app.call_from_thread(
            lambda: setattr(self.services_status, "visible", state)
        )

    def __subscribe_to_redis(self) -> PubSub:
        client = redis.Redis(
            host="localhost",
            port=6379,
            db=0,
            password=REDIS_PASSWORD,
            decode_responses=True,
        )
        pubsub: PubSub = client.pubsub()
        pubsub.subscribe("admin_channel", "client_channel")

        return pubsub

    def __listen_to_redis(self, pubsub: PubSub) -> None:
        # Escucha en Redis
        for message in pubsub.listen():
            if message.get("type") == "message":
                try:
                    data = json.loads(message["data"])
                    self.app.call_from_thread(lambda d=data: self.__update_ui(d))
                except Exception:
                    continue

    def __listener_thread(self):
        """
        Hilo que mantiene conexión con Redis, actualiza estado de servicios
        y refresca la configuración mientras Redis está activo.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while True:
            try:
                pubsub = self.__subscribe_to_redis()

                # Carga config y status de contenedores con reintento hasta tener éxito
                while True:
                    try:
                        self.__set_loading_states(state=True)

                        # Se carga la configuración
                        self.__load_config(loop)
                        self.__init_containers_status(loop)
                        break  # Se sale del retry
                    except Exception:
                        # Si no hay respuesta del engine todavía
                        time.sleep(5)

                # Escucha a Redis
                self.__listen_to_redis(pubsub=pubsub)
            except ConnectionError:
                # Redis no está disponible
                self.__mark_services_unvailable()
                self.__set_loading_states(state=True)
                time.sleep(5)

    def __start_redis_listener(self):
        """
        Inicia un hilo en segundo plano para escuchar a Redis y mantener la UI actualizada.
        """
        threading.Thread(target=self.__listener_thread, daemon=True).start()
