from pathlib import Path
from typing import Set

from components.file_option import FileOption
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, OptionList
from textual.widgets.option_list import Option


class StagingArea(Widget):
    selected_folders: reactive[Set[Path]] = reactive(set)

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="staging-area"):
            yield Label("Staged", classes="pane-header")
            yield OptionList(id="staging-list")

    def watch_selected_folders(self, value: Set[Path]) -> None:
        staging_area = self.query_one("#staging-list", OptionList)
        staging_area.clear_options()

        if not value:
            staging_area.add_option(Option("[No Folders Staged]"))
            return

        for folder_path in sorted(value):
            staging_area.add_option(FileOption(folder_path, True))
