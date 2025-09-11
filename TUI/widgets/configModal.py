from textual.screen import ModalScreen
from textual.widgets import TextArea, Button, Static
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from ..widgets.header import get_header
from ..widgets.footer import get_footer


class ConfigModal(ModalScreen[str]):
    """Modal para editar configuración de RTB."""

    CSS_PATH = "../styles/configModal.tcss"

    def __init__(self, config_text: str) -> None:
        super().__init__()
        self.config_text = config_text

    def compose(self) -> ComposeResult:
        # Encabezado
        yield get_header()

        with Vertical(id="config-modal"):
            yield Static("Edit RootTheBox configuration:", classes="modal-title")

            # TextArea para editar config
            self.editor = TextArea(language="json", classes="config-editor")
            self.editor.load_text(self.config_text)
            yield self.editor

            # Botones
            with Horizontal(classes="config-buttons"):
                yield Button("Guardar", id="save", variant="success")
                yield Button("Cancelar", id="cancel", variant="error")

        # Pie de página
        yield get_footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            # Devuelve el texto del editor al cerrar el modal
            self.dismiss(self.editor.text)
        else:
            self.dismiss(None)
