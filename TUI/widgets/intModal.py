from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Select, Button
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual import events
from ..widgets import get_footer
from ..widgets import get_header


class IntModal(ModalScreen[dict[str, str | int]]):
    """
    Modal para elegir un número dentro de un rango fijo (puede ser un puerto o una cantidad que haya dentro del rango).
    """

    CSS_PATH = "../styles/intModal.tcss"

    BINDINGS = [
        Binding("ctrl+y", "dismiss_yes", "Yes ", show=True),
        Binding("ctrl+n", "dismiss_no", "No ", show=True),
    ]

    def __init__(
        self,
        ports_range: list[int],
        header_title: str = "Choose a number",
        prompt: str = "Select a port",
        return_ports: bool = False,
    ):
        super().__init__()
        self.header_title = header_title
        self.ports_range: list[int] = ports_range
        self.selector: Select[int] | None = None
        self.prompt = prompt
        self.return_ports = return_ports

    def compose(self) -> ComposeResult:
        # Header
        yield get_header()

        # Select con las opciones del rango
        if self.return_ports:
            # Se muestran los puertos
            options = [
                (str(i), i) for i in range(self.ports_range[0], self.ports_range[1] + 1)
            ]
        else:
            # Se muestra la cantidad de elementos que hay dentro del rango:
            __count = self.ports_range[1] - self.ports_range[0] + 1
            options = [(str(i), i) for i in range(1, __count + 1)]
        self.selector = Select(options=options, prompt=self.prompt)

        with Horizontal(classes="confirm-modal"):
            with Vertical(classes="confirm-box"):
                yield Static(self.header_title or "", classes="confirm-message")
                with Horizontal(classes="selector"):
                    yield self.selector
                with Horizontal(classes="confirm-buttons") as self.buttons_container:
                    self.yes = yield Button("Yes", id="yes", classes="yes-button")
                    self.no = yield Button("No", id="no", classes="no-button")

        # Footer
        yield get_footer()

    async def on_mount(self):
        self.yes = self.query_one("#yes", Button)
        self.no = self.query_one("#no", Button)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes" and self.selector:
            __value = self.selector.value
            if __value and isinstance(__value, int):
                self.dismiss({"button": "yes", "number": __value})
            else:
                self.app.notify("You must choose a number", severity="warning")
        elif event.button.id == "no":
            self.dismiss({"button": "no", "number": -1})

    async def action_dismiss_yes(self) -> None:
        if self.selector:
            __value = self.selector.value
            if __value and isinstance(__value, int):
                self.dismiss({"button": "yes", "number": __value})

    async def action_dismiss_no(self) -> None:
        self.dismiss({"button": "no", "number": -1})

    async def on_key(self, event: events.Key) -> None:
        if not self.selector:
            return

        # Referencias a los widgets
        yes = self.yes
        no = self.no
        sel = self.selector

        # Mapas de navegación: {widget actual: {tecla: widget a enfocar}}
        navigation = {
            yes: {"right": no, "down": no, "up": sel, "left": sel},
            no: {"left": yes, "up": yes, "down": sel, "right": sel},
            sel: {"left": no, "right": yes},
        }

        # Obtiene el widget enfocado actualmente
        focused = next((w for w in [yes, no, sel] if w.has_focus), None)
        if not focused:
            return

        # Cambia el focus si la tecla existe en el mapa
        target = navigation.get(focused, {}).get(event.key)
        if target:
            target.focus()
