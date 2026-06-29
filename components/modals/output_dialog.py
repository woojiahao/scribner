from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Label,
)


class OutputDialog(ModalScreen):
    BINDINGS = [
        Binding("q", "cancel_dialog", "Quit", show=False),
        Binding("escape", "cancel_dialog", "Quit", show=False),
    ]

    CSS_PATH = "output_dialog.tcss"

    def __init__(self, default_path: Path):
        super().__init__()
        self.default_path = default_path

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-box"):
            yield Label("Output destination directory", id="dialog-title")
            yield Input(
                value=str(self.default_path),
                id="output-path-input",
                placeholder="Enter full absolute path...",
            )
            with Horizontal(id="button-row"):
                yield Button("Back", id="btn-cancel", variant="error", compact=True)
                yield Button("Run", id="btn-confirm", variant="success", compact=True)

    def action_cancel_dialog(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm":
            chosen_path = self.query_one("#output-path-input", Input).value.strip()
            if chosen_path:
                self.dismiss(Path(chosen_path))
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        chosen_path = event.value.strip()
        if chosen_path:
            self.dismiss(Path(chosen_path))
