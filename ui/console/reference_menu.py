"""Console menu for catalogs, genres, and tag settings."""

from functools import partial

from common import valid
from ui.console import genre_menu
from ui.console import request
from ui.console import tags_menu
from ui.console import ui


def open_reference_menu() -> None:
    """Open reference data and tag settings menu."""
    while True:
        ui.clean_terminal()
        ui.show_reference_menu()

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 2)])
        if command == "0":
            return
        if command == "1":
            genre_menu.show_dataset_genre_catalog()
        elif command == "2":
            open_tags_menu()

        ui.press_enter()


def open_tags_menu() -> None:
    """Open tag settings menu."""
    while True:
        ui.clean_terminal()
        ui.show_tags_menu()

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 4)])
        if command == "0":
            return
        if command == "1":
            tags_menu.show_tags()
        elif command == "2":
            tags_menu.request_new_tag()
        elif command == "3":
            tags_menu.request_delete_tag()
        elif command == "4":
            tags_menu.request_delete_all_tags()

        ui.press_enter()
