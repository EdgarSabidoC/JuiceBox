from textual.widgets import Switch
from textual.reactive import reactive


class CustomSwitch(Switch):
    def on_mount(self):
        self.update_style()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self.update_style()

    def update_style(self):
        # Elimina primero cualquier clase previa personalizada
        self.remove_class("on")
        self.remove_class("off")

        # Aplica clase dependiendo del estado actual
        if self.value == True:
            self.add_class("on")
        else:
            self.add_class("off")
