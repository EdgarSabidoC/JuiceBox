# screens/confirm_modal.py
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual import events
from textual.binding import Binding
from ..widgets import get_footer
from ..widgets import get_header


class ConfirmModal(ModalScreen[str]):
    """
    Modal de confirmación con Sí/No.
    """

    CSS_PATH = "../styles/confirmModal.tcss"

    BINDINGS = [
        Binding("ctrl+y", "dismiss_yes", "Yes", show=True),
        Binding("ctrl+n", "dismiss_no", "No", show=True),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        # Header
        yield get_header()

        with Horizontal(classes="confirm-modal"):
            with Vertical(classes="confirm-box"):
                yield Static(self.message, classes="confirm-message")
                with Horizontal(classes="confirm-buttons"):
                    self.yes: Button = Button(
                        "Yes", variant="default", id="yes", classes="yes-button"
                    )
                    self.no: Button = Button(
                        "No", variant="default", id="no", classes="no-button"
                    )
                    yield self.yes
                    yield self.no
                    self.yes.focus()
        # Footer
        yield get_footer()

    async def action_dismiss_yes(self) -> None:
        self.dismiss("yes")

    async def action_dismiss_no(self) -> None:
        self.dismiss("no")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss("yes")
        else:
            self.dismiss("no")

    async def on_key(self, event: events.Key) -> None:
        # Obtener todos los botones del modal
        buttons = self.query(Button).results()
        if not buttons:
            return

        if self.yes.has_focus and (event.key == "right" or event.key == "down"):
            self.no.focus()
        elif self.no.has_focus and (event.key == "left" or event.key == "up"):
            self.yes.focus()
