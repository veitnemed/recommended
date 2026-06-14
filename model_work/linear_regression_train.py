"""Обучает модель линейной регрессией с регуляризацией через scikit-learn."""

from __future__ import annotations

import time

from config import constant
from core import valid
from data_work import storage
from interface import request
from interface import ui
from model_work import model

try:
    from sklearn.linear_model import ElasticNet, Lasso, Ridge, SGDRegressor
except ImportError:  # pragma: no cover
    ElasticNet = None
    Lasso = None
    Ridge = None
    SGDRegressor = None

try:
    import numpy as np
    from scipy.optimize import minimize
except ImportError:  # pragma: no cover
    np = None
    minimize = None


METHODS = {
    "1": ("ridge", "Ridge"),
    "2": ("lasso", "Lasso"),
    "3": ("elasticnet", "ElasticNet"),
    "4": ("mae_sgd", "SGDRegressor (MAE)"),
    "5": ("mae_scipy", "scipy minimize (MAE)"),
}


def is_available() -> bool:
    """Проверяет доступность scikit-learn."""
    return any([
        all(item is not None for item in [Ridge, Lasso, ElasticNet, SGDRegressor]),
        all(item is not None for item in [np, minimize]),
    ])


def is_method_available(method: str) -> bool:
    """Проверяет доступность конкретного линейного метода."""
    if method == "mae_scipy":
        return all(item is not None for item in [np, minimize])
    return all(item is not None for item in [Ridge, Lasso, ElasticNet, SGDRegressor])


def build_xy(data: list) -> tuple[list[list[float]], list[float]]:
    """Преобразует датасет в матрицу признаков и целевые значения."""
    x_data = []
    y_data = []

    for movie in model.iter_movies(data):
        features = model.get_features(movie)
        x_data.append([float(features[feature]) for feature in constant.FEATURES])
        y_data.append(float(model.get_user_score(movie)))

    return x_data, y_data


def build_estimator(method: str, alpha: float, l1_ratio: float, max_iter: int):
    """Создает estimator для выбранного режима линейного обучения."""
    if method == "ridge":
        return Ridge(alpha=alpha, fit_intercept=False)
    if method == "lasso":
        return Lasso(alpha=alpha, fit_intercept=False, max_iter=max_iter, random_state=0)
    if method == "elasticnet":
        return ElasticNet(
            alpha=alpha,
            l1_ratio=l1_ratio,
            fit_intercept=False,
            max_iter=max_iter,
            random_state=0,
        )
    if method == "mae_sgd":
        return SGDRegressor(
            loss="epsilon_insensitive",
            epsilon=0.0,
            penalty="elasticnet",
            alpha=alpha,
            l1_ratio=l1_ratio,
            fit_intercept=False,
            max_iter=max_iter,
            tol=1e-4,
            random_state=0,
        )
    raise ValueError(f"Неизвестный метод линейного обучения: {method}")


def fit_mae_with_scipy(
    x_data: list[list[float]],
    y_data: list[float],
    start_weights: dict,
    alpha: float,
    l1_ratio: float,
    max_iter: int,
) -> dict:
    """Минимизирует MAE с elastic-net регуляризацией через scipy."""
    x_matrix = np.asarray(x_data, dtype=float)
    y_vector = np.asarray(y_data, dtype=float)
    start_vector = np.asarray(
        [float(start_weights.get(feature, 0.0)) for feature in constant.FEATURES],
        dtype=float,
    )

    def objective(vector) -> float:
        prediction = x_matrix @ vector
        mae = np.mean(np.abs(prediction - y_vector))
        l1_penalty = np.sum(np.abs(vector))
        l2_penalty = np.sum(vector * vector)
        regularization = alpha * (l1_ratio * l1_penalty + (1 - l1_ratio) * l2_penalty)
        return float(mae + regularization)

    result = minimize(
        objective,
        start_vector,
        method="Powell",
        options={"maxiter": max_iter, "disp": False},
    )
    best_vector = result.x if result.success or result.x is not None else start_vector

    return {
        feature: float(weight)
        for feature, weight in zip(constant.FEATURES, best_vector)
    }


def fit_linear_weights(
    data: list,
    method: str,
    start_weights: dict | None = None,
    alpha: float = 0.1,
    l1_ratio: float = 0.5,
    max_iter: int = 5000,
) -> dict:
    """Обучает линейную модель и возвращает словарь весов."""
    x_data, y_data = build_xy(data)
    if len(x_data) == 0:
        return constant.DEFAULT_WEIGHTS.copy()

    if start_weights is None:
        start_weights = constant.DEFAULT_WEIGHTS.copy()

    if method == "mae_scipy":
        return fit_mae_with_scipy(x_data, y_data, start_weights, alpha, l1_ratio, max_iter)

    estimator = build_estimator(method, alpha, l1_ratio, max_iter)
    estimator.fit(x_data, y_data)

    return {
        feature: float(coef)
        for feature, coef in zip(constant.FEATURES, estimator.coef_)
    }


def choose_method() -> tuple[str, str] | None:
    """Запрашивает у пользователя конкретный линейный метод."""
    print("Линейные методы обучения:\n")
    for key, (_, label) in METHODS.items():
        print(f" {key} >> {label}")
    print(" 0 >> Назад\n")

    command = request.loop_input(
        text=">> ",
        funcs_list=[lambda value: value in {"0", "1", "2", "3", "4", "5"}],
    )
    if command == "0":
        return None
    return METHODS[command]


def request_float(text: str, default_value: float) -> float:
    """Запрашивает float-параметр с дефолтным значением."""
    def is_valid_value(raw: str) -> bool:
        if raw.strip() == "":
            return True
        try:
            return valid.parse_float(raw) >= 0
        except ValueError:
            return False

    value = request.loop_input(
        text=f"{text} [{default_value}] >> ",
        funcs_list=[is_valid_value],
    )
    if value.strip() == "":
        return default_value
    return valid.parse_float(value)


def request_int(text: str, default_value: int) -> int:
    """Запрашивает integer-параметр с дефолтным значением."""
    value = request.loop_input(
        text=f"{text} [{default_value}] >> ",
        funcs_list=[lambda raw: raw.strip() == "" or (raw.isdigit() and int(raw) > 0)],
    )
    if value.strip() == "":
        return default_value
    return int(value)


def train_linear_model(data, weights) -> None:
    """Запускает отдельный режим линейного обучения через sklearn."""
    if len(data) == 0:
        print("Датасет пуст.")
        return

    if is_available() is False:
        print("Режим линейной регрессии недоступен: не установлены sklearn/scipy.")
        print("Установите зависимости из requirements.txt и запустите снова.")
        return

    chosen = choose_method()
    if chosen is None:
        return

    method, label = chosen
    if is_method_available(method) is False:
        print(f"Выбранный режим недоступен в текущем окружении: {label}")
        return

    alpha = request_float("Alpha регуляризации", 0.1)
    l1_ratio = 0.5
    if method in {"elasticnet", "mae_sgd", "mae_scipy"}:
        l1_ratio = request_float("L1 ratio", 0.5)
    max_iter = request_int("Максимум итераций", 5000)

    start_time = time.perf_counter()
    old_error = model.mean_absolute_error(data, weights)
    new_weights = fit_linear_weights(
        data=data,
        method=method,
        start_weights=weights,
        alpha=alpha,
        l1_ratio=l1_ratio,
        max_iter=max_iter,
    )
    new_error = model.mean_absolute_error(data, new_weights)

    if new_error <= old_error:
        storage.save_weights(new_weights)
    else:
        new_weights = weights
        new_error = old_error
        print("Новые веса не сохранены: ошибка модели увеличилась.")

    delta_time = time.perf_counter() - start_time
    ui.show_result_train(new_weights, old_error, new_error, delta_time)
    print(f"Линейный режим: {label}")
    print(f"Сумма весов: {round(sum(new_weights.values()), 4)}")
