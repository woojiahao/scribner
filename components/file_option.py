from pathlib import Path

from textual.widgets.option_list import Option


class FileOption(Option):
    def __init__(self, path: Path, is_selected: bool):
        self.path = path
        self.is_selected = is_selected

        if path.is_dir():
            if is_selected:
                super().__init__(f"[bold green]{path.name}/[/bold green] ✅")
            else:
                super().__init__(f"[bold green]{path.name}/[/bold green] ")
        else:
            super().__init__(path.name)
