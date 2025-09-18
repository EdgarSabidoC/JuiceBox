from textual.widgets import Markdown


class ReactiveMarkdown(Markdown):
    def __init__(self, data: str = "…", **kwargs) -> None:
        super().__init__(data, **kwargs)

    def update_content(self, new_data: str, is_json: bool = False) -> None:
        if is_json:
            self.update("```json\n" + new_data + "\n```")
            return
        self.update(new_data)
