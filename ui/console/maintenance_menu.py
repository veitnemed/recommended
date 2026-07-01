"""Maintenance-first console menu for local data health operations."""

from functools import partial
from pathlib import Path

from candidates import service as candidate_service
from common import valid
from storage import runtime as storage_runtime
from ui.console import api_tools
from ui.console import backup_menu
from ui.console import candidate_pool_tools
from ui.console import interface_funcs
from ui.console import menu_state
from ui.console import pool_menu
from ui.console import poster_tools
from ui.console import request
from ui.console import tmdb_pool_tools
from ui.console import ui


def open_maintenance_menu() -> None:
    """Open the main maintenance hub."""
    while True:
        ui.clean_terminal()
        _data, movies_counter = menu_state.get_menu_state()
        pool_stats_view = candidate_service.get_pool_stats_view()
        ui.show_maintenance_menu(movies_counter, pool_stats_view["summary"])

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 6)])
        if command == "0":
            return
        if command == "1":
            show_project_status()
        elif command == "2":
            backup_menu.open_backup_menu()
        elif command == "3":
            open_metadata_maintenance_menu()
        elif command == "4":
            pool_menu.open_candidate_pool_cleanup_menu()
        elif command == "5":
            open_maintenance_diagnostics_menu()
        elif command == "6":
            show_refactoring_checklist()

        ui.press_enter()


def show_project_status() -> None:
    """Print compact local runtime health status."""
    ui.clean_terminal()
    storage_runtime.ensure_runtime_data_layout()
    _data, movies_counter = menu_state.get_menu_state()
    pool_stats_view = candidate_service.get_pool_stats_view()

    print("Состояние проекта\n")
    print(f"Просмотрено записей: {movies_counter}")
    print(f"Candidate pool: {pool_stats_view['summary']}")
    print("Runtime data layout: OK")
    print("")
    interface_funcs.show_data_info()


def open_metadata_maintenance_menu() -> None:
    """Open watched metadata and poster-cache maintenance actions."""
    while True:
        ui.clean_terminal()
        ui.show_metadata_maintenance_menu()

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 5)])
        if command == "0":
            return
        if command == "1":
            poster_tools.sync_watched_descriptions_and_posters()
        elif command == "2":
            poster_tools.fetch_watched_tmdb_metadata()
        elif command == "3":
            poster_tools.fetch_tmdb_poster_metadata()
        elif command == "4":
            poster_tools.download_poster_images_local()
        elif command == "5":
            poster_tools.diagnose_unresolved_watched_tmdb_metadata()

        ui.press_enter()


def open_maintenance_diagnostics_menu() -> None:
    """Open diagnostics that do not create new watched records or pools."""
    while True:
        ui.clean_terminal()
        ui.show_maintenance_diagnostics_menu()

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 5)])
        if command == "0":
            return
        if command == "1":
            api_tools.ping_external_apis()
        elif command == "2":
            interface_funcs.show_api_features()
        elif command == "3":
            interface_funcs.show_dataset_genres()
        elif command == "4":
            tmdb_pool_tools.show_tmdb_dataset_genre_diagnostics()
        elif command == "5":
            candidate_pool_tools.show_candidate_poster_diagnostics()

        ui.press_enter()


def show_refactoring_checklist() -> None:
    """Print short local checks to run before ending structural refactoring."""
    ui.clean_terminal()
    checklist_path = Path("docs/REFACTORING_CHECKLIST.md")
    print("Проверки перед завершением рефакторинга\n")
    if checklist_path.is_file() is False:
        print("docs/REFACTORING_CHECKLIST.md не найден.")
        return

    print(checklist_path.read_text(encoding="utf-8").strip())
