from textual.screen import ModalScreen
from textual.widgets import TextArea, Button, Static
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual import events
from textual.binding import Binding
from ..widgets.header import get_header
from ..widgets.footer import get_footer


class ConfigModal(ModalScreen[str]):
    """Modal para editar configuración de RTB."""

    CSS_PATH = "../styles/configModal.tcss"
    BINDINGS = [
        Binding("ctrl+s", "dismiss_save", "Save ", show=True),
        Binding("ctrl+n", "dismiss_cancel", "Cancel ", show=True),
    ]

    def __init__(self, config_text: str) -> None:
        super().__init__()
        self.config_text = config_text

    def compose(self) -> ComposeResult:
        # Encabezado
        yield get_header()

        with Vertical(id="config-modal", classes="config-modal"):
            yield Static("Edit RootTheBox configuration:", classes="modal-title")

            # Configuración en editor de texto
            self.editor = TextArea(
                language="json",
                theme="css",
                classes="config-editor",
                show_line_numbers=True,
                show_cursor=True,
            )
            self.editor.load_text(self.config_text)
            yield self.editor

            # Botones
            with Horizontal(classes="config-buttons"):
                self.save = Button("Save", id="save", classes="save-button")
                self.cancel = Button("Cancel", id="cancel", classes="cancel-button")
                yield self.save
                yield self.cancel

        # Pie de página
        yield get_footer()

    async def action_dismiss_save(self) -> None:
        self.dismiss(self.editor.text)

    async def action_dismiss_cancel(self) -> None:
        self.dismiss(None)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            # Devuelve el texto del editor con la configuración al cerrar el modal
            self.dismiss(self.editor.text)
        else:
            self.dismiss(None)

    async def on_key(self, event: events.Key) -> None:
        # Obtener todos los botones del modal
        buttons = self.query(Button).results()
        if not buttons:
            return

        if self.save.has_focus:
            if event.key == "right" or event.key == "down":
                self.cancel.focus()
            elif event.key == "up":
                self.editor.focus()
        elif self.cancel.has_focus:
            if event.key == "left" or event.key == "up":
                self.save.focus()
            elif event.key == "down":
                self.editor.focus()
