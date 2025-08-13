from textual.widget import Widget
from textual.reactive import reactive
from textual.widgets import Label


class ReactiveLabel(Widget):
    text: reactive[str] = reactive("Loading...")

    def compose(self):
        self.label = Label(self.text)
        yield self.label

    def watch_text(self, value: str) -> None:
        self.label.update(value)
