"""Console menu for read-only search and inspection workflows."""

from functools import partial

from common import valid
from ui.console import interface_funcs
from ui.console import request
from ui.console import search_menu
from ui.console import sql_tools
from ui.console import ui


def open_search_menu() -> None:
    """Open read-only search and inspection menu."""
    while True:
        ui.clean_terminal()
        ui.show_search_menu()

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 4)])
        if command == "0":
            return
        if command == "1":
            search_menu.show_global_candidate_search()
        elif command == "2":
            sql_tools.search_sql_title_by_name()
        elif command == "3":
            interface_funcs.show_dataset_genres()
        elif command == "4":
            interface_funcs.show_api_features()

        ui.press_enter()
