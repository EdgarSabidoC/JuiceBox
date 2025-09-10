# screens/confirm_modal.py
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual import events


class ConfirmModal(ModalScreen[str]):
    """
    Modal de confirmación con Sí/No.
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-modal"):
            yield Static(self.message, classes="confirm-message")
            with Horizontal(classes="confirm-buttons"):
                self.yes: Button = Button("Sí", variant="default", id="yes")
                self.no: Button = Button("No", variant="default", id="no")
                yield self.yes
                yield self.no
                self.yes.focus()

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
