from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, RichLog


class Logs(Widget):
    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="logs"):
            yield Label("Logs", classes="pane-header")
            yield RichLog(highlight=True, markup=True)

    def write(self, text: str) -> None:
        log = self.query_one(RichLog)
        log.write(text)
