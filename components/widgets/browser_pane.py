import os
from pathlib import Path
from typing import List, Optional, Set

from components.file_option import FileOption
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import OptionList
from textual.widgets.option_list import Option


class BrowserPane(Widget):
    DEFAULT_CSS = """
    BrowserPane {
        width: 100%;
        height: 100%;
    }

    .column {
        width: 1fr;
        height: 100%;
        padding: 2;
    }

    .border {
        border-right: solid rgba(255, 255, 255, 0.1);
    }

    OptionList {
        border: none;
    }
    """

    selected_folders: reactive[Set[Path]] = reactive(set)

    def __init__(self) -> None:
        super().__init__()
        try:
            self.curr_dir = (
                Path("/").resolve() if os.name != "nt" else Path("C:\\").resolve()
            )
        except Exception:
            self.curr_dir = Path.home().resolve()

    def compose(self) -> ComposeResult:
        with Horizontal(id="browser-pane"):
            with Vertical(classes="column border"):
                yield OptionList(id="parent-col")
            with Vertical(classes="column border"):
                yield OptionList(id="current-col")
            with Vertical(classes="column"):
                yield OptionList(id="preview-col")

    @on(OptionList.OptionHighlighted)
    def handle_option_highlight(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id == "current-col":
            self.__update_preview_col()

    def watch_selected_folders(self, _value: Set[Path]) -> None:
        if self.is_mounted:
            self.refresh_columns(select_first=False)

    def nav_up(self) -> None:
        current_col = self.__current_col()
        if current_col.highlighted is not None and current_col.highlighted > 0:
            current_col.action_cursor_up()
            current_col.scroll_to_highlight()

    def nav_down(self) -> None:
        current_col = self.__current_col()
        if (
            current_col.highlighted is not None
            and current_col.highlighted < current_col.option_count - 1
        ):
            current_col.action_cursor_down()
            current_col.scroll_to_highlight()

    def nav_left(self) -> None:
        if self.curr_dir.parent and self.curr_dir.parent != self.curr_dir:
            old_dir = self.curr_dir
            self.curr_dir = self.curr_dir.parent
            self.refresh_columns(select_first=False)

            current_col = self.__current_col()
            for idx in range(current_col.option_count):
                opt = current_col.get_option_at_index(idx)
                if isinstance(opt, FileOption) and opt.path == old_dir:
                    current_col.highlighted = idx
                    current_col.scroll_to_highlight()
                    break

    def nav_right(self) -> None:
        current_col = self.__current_col()
        if current_col.highlighted is not None:
            option = current_col.get_option_at_index(current_col.highlighted)
            if isinstance(option, FileOption) and option.path.is_dir():
                self.curr_dir = option.path
                self.refresh_columns(select_first=True)

    def refresh_columns(self, select_first: bool = True) -> None:
        parent_col = self.__parent_col()
        current_col = self.__current_col()
        preview_col = self.__preview_col()

        old_highlight = current_col.highlighted

        parent_col.clear_options()
        current_col.clear_options()
        preview_col.clear_options()

        self.__update_parent_col()
        self.__update_current_col(select_first)
        self.__update_preview_col()

        if not select_first and old_highlight is not None:
            current_col.highlighted = min(old_highlight, current_col.option_count - 1)
            current_col.scroll_to_highlight()

    @property
    def selected_option(self) -> Optional[FileOption]:
        current_col = self.__current_col()
        if current_col.highlighted is None:
            return None

        idx = current_col.highlighted
        option = current_col.get_option_at_index(idx)
        if not isinstance(option, FileOption) or not option.path.is_dir():
            return None

        return option

    def __update_parent_col(self) -> None:
        parent_col = self.__parent_col()
        parent_col.clear_options()

        parent_dir = self.curr_dir.parent
        if parent_dir and parent_dir != self.curr_dir:
            try:
                options = [
                    FileOption(entry, self.__is_path_selected(entry))
                    for entry in self.__sort_dir(parent_dir)
                    if entry.is_dir()
                ]
                parent_col.add_options(options)
            except PermissionError:
                parent_col.add_option(Option("Access Denied"))

    def __update_current_col(self, select_first: bool) -> None:
        current_col = self.__current_col()
        current_col.clear_options()

        has_entries = False
        try:
            entries = self.__sort_dir(self.curr_dir)
            if not entries:
                current_col.add_option(Option("Empty folder"))
            else:
                has_entries = True
                options = [
                    FileOption(entry, self.__is_path_selected(entry))
                    for entry in entries
                ]
                current_col.add_options(options)
        except PermissionError:
            current_col.add_option(Option("Access Denied"))

        if select_first and has_entries:
            current_col.highlighted = 0
            current_col.scroll_to_highlight()

    def __update_preview_col(self) -> None:
        current_col = self.__current_col()
        preview_col = self.__preview_col()
        preview_col.clear_options()

        if current_col.highlighted is not None:
            option = current_col.get_option_at_index(current_col.highlighted)
            if not isinstance(option, FileOption):
                return

            if option.path.is_dir():
                try:
                    preview_entries = len(list(option.path.iterdir()))
                    if preview_entries == 0:
                        preview_col.add_option(Option("Empty folder"))
                        return

                    options = [
                        FileOption(sub_entry, self.__is_path_selected(sub_entry))
                        for sub_entry in self.__sort_dir(option.path)[:30]
                    ]
                    preview_col.add_options(options)
                except PermissionError:
                    preview_col.add_option(Option("Access Denied"))
            else:
                try:
                    preview_col.add_option(
                        Option(f"Size: {option.path.stat().st_size} bytes")
                    )
                except (PermissionError, FileNotFoundError):
                    preview_col.add_option(Option("Access Denied"))

    def __sort_dir(self, dir: Path) -> List[Path]:
        return sorted(dir.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

    def __current_col(self) -> OptionList:
        return self.__col("#current-col")

    def __parent_col(self) -> OptionList:
        return self.__col("#parent-col")

    def __preview_col(self) -> OptionList:
        return self.__col("#preview-col")

    def __col(self, id: str) -> OptionList:
        return self.query_one(id, OptionList)

    def __is_path_selected(self, path: Path) -> bool:
        return path in self.selected_folders
