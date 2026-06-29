"""Консольный entry flow приложения."""

from functools import partial

from candidates.tmdb_candidate_pool import set_progress_reporter
from common import valid
from storage import files as storage_files
from ui.console import global_menu
from ui.console import menu_state
from ui.console import request
from ui.console import ui


def run_console_app():
    """Запускает главный цикл консольного приложения."""
    storage_files.init_all_dates()
    set_progress_reporter(lambda source, status: print(f"{source}: {status}"))

    while True:
        ui.clean_terminal()
        _data, _weights, movies_counter, _abs_error = menu_state.get_menu_state()
        ui.show_global_menu(movies_counter)

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 4)])
        if command == "0":
            break
        elif command == "1":
            global_menu.open_data_menu()
        elif command == "2":
            global_menu.open_candidate_pool_menu()
        elif command == "3":
            global_menu.open_genres_menu()
        elif command == "4":
            global_menu.open_extra_menu()
