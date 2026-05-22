DATA_DIR = 'C:/movies-learn'
FILE_NAME = 'C:/movies-learn/dataset.json'
WEIGHTS_JSON = 'C:/movies-learn/weights.json'
BACKUP_DIR = 'C:/backup-movies-learn/'
DIR_META = 'C:/meta-movies-learn/'
META_JSON = 'C:/meta-movies-learn/meta_data.json'
TXT_INPUT = 'C:/movies-learn/input.txt'

OBJECTIVE_FEATURES = [
    "kp_score",
    "popularity_score",
    "first_episode_score",
    "last_episode_score"
]

LLM_FEATURES = ["hook", "holding", "tension"]

FEATURES = OBJECTIVE_FEATURES + LLM_FEATURES

RAW_META_FIELDS = [
    "kp_score",
    "imdb_votes",
    "year",
    "first_episode_score",
    "last_episode_score"
]
FEATURES_CONST = OBJECTIVE_FEATURES

RAW_META_RUSSIAN = {
    "kp_score": "Рейтинг Кинопоиска",
    "imdb_votes": "Количество голосов IMDb",
    "year": "Год выхода",
    "first_episode_score": "Оценка первой серии IMDb",
    "last_episode_score": "Оценка последней серии IMDb"
}
     
DEFAULT_WEIGHTS = {
    feature: round(1 / len(FEATURES), 4)
    for feature in FEATURES
}
RAW_META_RUSSIAN = {
    "kp_score": "Рейтинг Кинопоиска",
    "imdb_votes": "Количество голосов IMDb",
    "year": "Год выхода",
    "first_episode_score": "Оценка первой серии IMDb",
    "last_episode_score": "Оценка последней серии IMDb"
}

FEATURES_RUSSIAN = {
    "kp_score": "Рейтинг Кинопоиска",
    "popularity_score": "Популярность с поправкой на год и голоса IMDb",
    "first_episode_score": "Оценка первой серии",
    "last_episode_score": "Оценка последней серии",
    "hook": "Сюжетная завязка",
    "holding": "Удержание за просмотром",
    "tension": "Напряжение"
}
COMMANDS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9","10"]
BAD_CHARACTERS = ",.'][@#$%^&*()?"
THRESHOLD = 6.5
NOW_YEAR = 2026


STEP = 0.01

