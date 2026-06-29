from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import Reactive, reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Label,
    ProgressBar,
)


class ProgressDialog(ModalScreen):
    CSS_PATH = "progress_dialog.tcss"

    current: Reactive[int] = reactive(0)
    total: Reactive[int] = reactive(100)
    status_msg: Reactive[str] = reactive("")

    def __init__(self, title: str = "Consolidating elements..."):
        super().__init__()
        self.title_text = title

    def compose(self) -> ComposeResult:
        with Vertical(id="progress-box"):
            yield Label(self.title_text, id="progress-label")
            yield ProgressBar(total=100, show_eta=True)

    def watch_current(self, value: int) -> None:
        pbar = self.query_one(ProgressBar)
        pbar.update(progress=value)

    def watch_total(self, value: int) -> None:
        pbar = self.query_one(ProgressBar)
        pbar.update(total=value)

    def watch_status_msg(self, value: str) -> None:
        self.query_one("#progress-label", Label).update(value)
