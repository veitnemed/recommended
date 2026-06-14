"""Содержит циклы главного меню и подменю приложения."""

from functools import partial

from config import constant
from data_work import excel_work
from data_work import storage
from interface import backup_menu
from interface import interface_funcs
from interface import menu_state
from interface import request
from interface import tags_menu
from interface import train_params
from interface import ui
from model_work import linear_regression_train
from model_work import model
from model_work import train_report
from model_work import train_modes
from core import valid


def open_data_menu():
    """Открывает меню работы с данными."""
    while True:
        ui.clean_terminal()
        data, weights, movies_counter, abs_error = menu_state.get_menu_state()
        ui.show_data_menu(movies_counter, round(abs_error, 2))

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 8)])
        if command == "0":
            return
        if command == "1":
            if excel_work.export_dataset_to_excel():
                storage.open_file(constant.EDIT_EXCEL)
        elif command == "2":
            excel_work.replace_dataset_from_excel()
        elif command == "3":
            interface_funcs.request_object()
        elif command == "4":
            interface_funcs.show_all_movies()
        elif command == "5":
            interface_funcs.show_data_info()
        elif command == "6":
            interface_funcs.read_tst_scores()
        elif command == "7":
            backup_menu.open_backup_menu()
        elif command == "8":
            interface_funcs.rename_movie_record()

        ui.press_enter()


def open_train_menu():
    """Открывает меню обучения модели."""
    while True:
        ui.clean_terminal()
        data, weights, movies_counter, abs_error = menu_state.get_menu_state()
        ui.show_train_menu(
            movies_counter,
            round(abs_error, 2),
            train_params.TRAIN_STEP,
            train_params.TRAIN_PLATEAU_SCORE
        )

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 6)])
        if command == "0":
            return
        if command == "1":
            train_modes.train_model(
                data=data,
                weights=weights,
                fit_func=model.fit_weights,
                title='Быстрое обучение',
                step=train_params.TRAIN_STEP
            )
        elif command == "2":
            train_modes.train_model(
                data=data,
                weights=weights,
                fit_func=model.fit_weights_until_plateau,
                title='Случайная оптимизация',
                step=train_params.TRAIN_STEP,
                score=train_params.TRAIN_PLATEAU_SCORE
            )
        elif command == "3":
            train_modes.auto_train_grid_steps(
                data=data,
                weights=weights,
                title='Многошаговый координатный поиск'
            )
        elif command == "4":
            train_modes.auto_train_mix_mode(
                data=data,
                weights=weights,
                title='Гибридная оптимизация'
            )
        elif command == "5":
            linear_regression_train.train_linear_model(
                data=data,
                weights=weights,
            )
        elif command == "6":
            train_params.setup_train_params()

        ui.press_enter()


def open_feature_menu():
    """Открывает меню признаков модели."""
    while True:
        ui.clean_terminal()
        ui.show_feature_menu()

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 5)])
        if command == "0":
            return
        if command == "1":
            open_tags_menu()
        elif command == "2":
            interface_funcs.load_genre_markup()
            ui.press_enter()
        elif command == "3":
            data, weights, movies_counter, abs_error = menu_state.get_menu_state()
            interface_funcs.show_weights_model(weights)
            ui.press_enter()
        elif command == "4":
            interface_funcs.reset_weights_model()
            ui.press_enter()


def open_efficiency_menu():
    """Открывает меню тестов эффективности модели."""
    while True:
        ui.clean_terminal()
        data, weights, movies_counter, abs_error = menu_state.get_menu_state()
        ui.show_efficiency_menu(movies_counter, round(abs_error, 2))

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 6)])
        if command == "0":
            return
        if command == "1":
            interface_funcs.show_feature_importance(weights, abs_error)
        elif command == "2":
            top_n = request.loop_input(
                text="Топ N ошибок >> ",
                funcs_list=[valid.is_correct_top_n]
            )
            model.top_prediction_errors(data, weights, int(top_n))
        elif command == "3":
            top_n = request.loop_input(
                text="Топ N ошибок >> ",
                funcs_list=[valid.is_correct_top_n]
            )
            model.one_to_one_error(data, int(top_n))
        elif command == "4":
            train_modes.run_noise_sensitivity(
                data=data,
                weights=weights,
                step=train_params.TRAIN_STEP
            )
        elif command == "5":
            interface_funcs.votes_impact()
        elif command == "6":
            updated_count = storage.rework_formated_scores()
            print(f'Пересчитано записей: {updated_count}')

        ui.press_enter()


def open_model_menu():
    """Открывает меню модели."""
    while True:
        ui.clean_terminal()
        data, weights, movies_counter, abs_error = menu_state.get_menu_state()
        ui.show_model_menu(movies_counter, round(abs_error, 2))

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 3)])
        if command == "0":
            return
        if command == "1":
            open_feature_menu()
        elif command == "2":
            open_efficiency_menu()
        elif command == "3":
            interface_funcs.get_predict(weights)
            ui.press_enter()


def open_extra_menu():
    """Открывает дополнительное меню."""
    while True:
        ui.clean_terminal()
        data, weights, movies_counter, abs_error = menu_state.get_menu_state()
        ui.show_extra_menu(movies_counter, round(abs_error, 2))

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 5)])
        if command == "0":
            return
        if command == "1":
            interface_funcs.show_api_features()
        elif command == "2":
            interface_funcs.show_dataset_genres()
        elif command == "3":
            interface_funcs.votes_impact()
        elif command == "4":
            updated_count = storage.rework_formated_scores()
            print(f'Пересчитано записей: {updated_count}')
        elif command == "5":
            interface_funcs.show_kino_teatr_scraper_test()

        ui.press_enter()


def open_candidate_pool_menu():
    """Открывает меню работы с общим пулом кандидатов."""
    while True:
        ui.clean_terminal()
        data, weights, movies_counter, abs_error = menu_state.get_menu_state()
        candidates_count = len(storage.load_candidate_pool())
        ui.show_candidate_pool_menu(movies_counter, round(abs_error, 2), candidates_count)

        command = request.loop_input(text=">> ", funcs_list=[partial(valid.is_correct_select_menu, 6)])
        if command == "0":
            return
        if command == "1":
            interface_funcs.collect_candidate_pool()
        elif command == "2":
            interface_funcs.show_candidate_pool()
        elif command == "3":
            interface_funcs.show_global_candidate_top()
        elif command == "4":
            interface_funcs.delete_candidate_pool()
        elif command == "5":
            interface_funcs.mark_candidate_as_watched()
        elif command == "6":
            interface_funcs.show_suspicious_candidate_duplicates()

        ui.press_enter()


def export_report():
    """Выгружает отчет по текущему состоянию модели."""
    train_report.export_train_report(
        train_params.TRAIN_STEP,
        train_params.TRAIN_PLATEAU_SCORE
    )


def open_tags_menu():
    """Открывает меню настройки тегов."""
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
