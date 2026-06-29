from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Label,
)


class HelpDialog(ModalScreen):
    BINDINGS = [
        Binding("q", "dismiss", "Quit", show=False),
        Binding("escape", "dismiss", "Quit", show=False),
    ]

    CSS_PATH = "help_dialog.tcss"

    ESCAPE_TO_MINIMIZE = True

    def compose(self) -> ComposeResult:
        instructions_text = (
            "[bold yellow]h j k l[/bold yellow] or [bold yellow]Arrows[/bold yellow] : Move around panes\n"
            "[bold cyan]h[/bold cyan] : Back out to parent directory\n"
            "[bold cyan]l[/bold cyan] : Enter highlighted directory\n"
            "[bold green]Space[/bold green] : Stage / unstage selected folder\n"
            "[bold green]c[/bold green] : Process and compile staged folders\n"
            "[bold green]?[/bold green] : View this shortcut help card\n"
            "[bold red]q[/bold red] : Exit program safely"
        )

        with Container(id="help-dialog"):
            yield Label("Shortcuts", id="help-title")
            yield Label(instructions_text, id="help-text")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close-help":
            self.dismiss()
