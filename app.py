import asyncio
import hashlib
import shutil
from pathlib import Path
from typing import Set

from components.modals.help_dialog import HelpDialog
from components.modals.output_dialog import OutputDialog
from components.modals.progress_dialog import ProgressDialog
from components.widgets.browser_pane import BrowserPane
from components.widgets.logs import Logs
from components.widgets.staging_area import StagingArea
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import (
    Footer,
    Header,
)

DEFAULT_OUTPUT_DESTINATION = Path.home() / "Desktop" / "backup"


class Scribner(App):
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("space", "toggle_folder", "Stage/Unstage Folder", priority=True),
        Binding("c", "prompt_consolidation", "Consolidate Staged", priority=True),
        Binding("question_mark", "show_help", "Help Menu", priority=True),
        Binding("q", "quit", "Quit"),
        Binding("k", "nav_up", "Up", show=False),
        Binding("j", "nav_down", "Down", show=False),
        Binding("h", "nav_left", "Go to Parent (Left)", show=False),
        Binding("l", "nav_right", "Enter/Inspect (Right)", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.selected_folders = set()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="workspace"):
            yield BrowserPane()
            yield Logs()
            yield StagingArea()
        yield Footer()

    def on_mount(self) -> None:
        browser_pane = self.query_one(BrowserPane)
        browser_pane.focus()
        browser_pane.refresh_columns()

        log = (
            "Initialized storage consolidator.\n"
            "Press [yellow]?[/yellow] to open the guide card.\n"
            f"Default destination: [cyan]{DEFAULT_OUTPUT_DESTINATION}[/cyan]"
        )
        logs = self.query_one(Logs)
        logs.write(log)

    def action_show_help(self) -> None:
        self.app.push_screen(HelpDialog())

    def action_nav_up(self) -> None:
        self.query_one(BrowserPane).nav_up()

    def action_nav_down(self) -> None:
        self.query_one(BrowserPane).nav_down()

    def action_nav_left(self) -> None:
        self.query_one(BrowserPane).nav_left()

    def action_nav_right(self) -> None:
        self.query_one(BrowserPane).nav_right()

    def action_toggle_folder(self) -> None:
        browser_pane = self.query_one(BrowserPane)
        logs = self.query_one(Logs)
        staging_area = self.query_one(StagingArea)

        selected_option = browser_pane.selected_option
        if selected_option is None:
            logs.write(
                "[amber]Warning: Select directories, not individual files.[/amber]"
            )
            return

        path = selected_option.path
        if path in self.selected_folders:
            self.selected_folders.remove(path)
            logs.write(f"[red]Dropped:[/red] {path}")
        else:
            self.selected_folders.add(path)
            logs.write(f"[green]Staged Folder:[/green] {path}")

        updated_set = set(self.selected_folders)
        # this will trigger a watch on the StagingArea widget that refreshes the contents
        staging_area.selected_folders = updated_set
        # this will trigger a watch on the BrowserPane widget that updates the selection accordingly
        browser_pane.selected_folders = updated_set

    def action_prompt_consolidation(self) -> None:
        logs = self.query_one(Logs)
        if not self.selected_folders:
            logs.write(
                "[bold red]Staging space empty. Target folders using spacebar first.[/bold red]"
            )
            return

        self.push_screen(
            OutputDialog(DEFAULT_OUTPUT_DESTINATION), self.__launch_progress_and_run
        )

    def __launch_progress_and_run(self, final_output_path: Path | None) -> None:
        if not final_output_path:
            self.query_one(Logs).write("[amber]Consolidation aborted by user.[/amber]")
            return

        progress_screen = ProgressDialog("Initializing file copying process...")
        self.push_screen(progress_screen)
        asyncio.create_task(
            self.__execute_consolidation_loop(
                progress_screen, final_output_path, self.selected_folders
            )
        )

    async def __execute_consolidation_loop(
        self,
        progress_screen: ProgressDialog,
        output_path: Path,
        selected_folders: Set[Path],
    ) -> None:
        logs = self.query_one(Logs)
        logs.write(
            "\n[bold cyan]============ STARTING CONSOLIDATION ============[/bold cyan]"
        )
        logs.write(f"Target Output Path: [bold green]{output_path}[/bold green]")

        output_path.mkdir(parents=True, exist_ok=True)
        copied_files = {}

        all_work_items = [
            (backup_path, file_path)
            for backup_path in selected_folders
            for file_path in backup_path.rglob("*")
            if not file_path.is_dir()
        ]

        total_files = len(all_work_items)
        if total_files == 0:
            progress_screen.dismiss()
            logs.write(
                "[amber]No target payload files detected inside staged targets.[/amber]"
            )
            return

        progress_screen.total = total_files

        for index, (backup_path, file_path) in enumerate(all_work_items, start=1):
            backup_name = backup_path.name
            rel_path = file_path.relative_to(backup_path)

            progress_screen.current = index
            progress_screen.status_msg = (
                f"Copying ({index}/{total_files}): {file_path.name}"
            )

            file_hash = self.__calculate_md5(file_path)
            if not file_hash:
                continue

            dest_file_path = output_path / rel_path
            try:
                if rel_path not in copied_files:
                    dest_file_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_file_path)
                    copied_files[rel_path] = {file_hash}
                else:
                    if file_hash not in copied_files[rel_path]:
                        stem = dest_file_path.stem
                        suffix = dest_file_path.suffix
                        distinct_dest_path = dest_file_path.with_name(
                            f"{stem}-{backup_name}{suffix}"
                        )
                        distinct_dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, distinct_dest_path)
                        copied_files[rel_path].add(file_hash)
                        logs.write(
                            f"  [bold magenta]Collision Resolution Match:[/bold magenta] Saved -> {distinct_dest_path.name}"
                        )
            except Exception as e:
                logs.write(f"  [red]Copy fault {rel_path}: {e}[/red]")

            await asyncio.sleep(0.005)

        progress_screen.current = total_files
        progress_screen.status_msg = "Running verification integrity check..."
        logs.write(
            "\n[bold cyan]============ RUNNING VERIFICATION CRADLE ============[/bold cyan]"
        )

        consolidated_inventory = set()
        for file_path in output_path.rglob("*"):
            if not file_path.is_dir():
                f_hash = self.__calculate_md5(file_path)
                if f_hash:
                    consolidated_inventory.add(f_hash)

        missing_count = 0
        for backup_path in self.selected_folders:
            for file_path in backup_path.rglob("*"):
                if file_path.is_dir():
                    continue
                src_hash = self.__calculate_md5(file_path)
                if src_hash and src_hash not in consolidated_inventory:
                    logs.write(
                        f"  [bold red]❌ MISSED INTEGRITY CHECK:[/bold red] {file_path.relative_to(backup_path)}"
                    )
                    missing_count += 1

        logs.write("\n-------------------------------------------")
        if missing_count == 0:
            logs.write(
                "[bold green]✅ VALIDATION COMPLETE: Storage matrix verified successfully.[/bold green]"
            )
        else:
            logs.write(
                f"[bold red]❌ INTEG FAULT: {missing_count} payload elements dropped.[/bold red]"
            )

        self.selected_folders.clear()
        self.query_one(StagingArea).selected_folders = set()
        self.query_one(BrowserPane).refresh_columns(select_first=False)
        progress_screen.dismiss()

    def __calculate_md5(self, file_path):
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
