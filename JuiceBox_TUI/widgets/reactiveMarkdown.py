from textual.widget import Widget
from textual.widgets import Markdown


class ReactiveMarkdown(Markdown):
    def __init__(self, data: str = "…", **kwargs) -> None:
        super().__init__(data, **kwargs)

    def update_content(self, new_data: str) -> None:
        self.update(new_data)
