import scheme

DATA_DIR = 'C:/movies-learn'
FILE_NAME = 'C:/movies-learn/dataset.json'
WEIGHTS_JSON = 'C:/movies-learn/weights.json'
BACKUP_DIR = 'C:/backup-movies-learn/'
DIR_META = 'C:/meta-movies-learn/'
META_JSON = 'C:/meta-movies-learn/meta_data.json'
TXT_INPUT = 'C:/movies-learn/input.txt'
CSV_INPUT = 'C:/movies-learn/input.csv'



MAIN_INFO = scheme.get_fields("main_info")
RAW_SCORES = scheme.get_fields("raw_scores")
SUBJECTIVE_SCORES = scheme.get_fields("subjective_scores")

COMPUTED_SCORES = scheme.get_fields("computed_scores")

CSV_FIELDS = MAIN_INFO + RAW_SCORES + SUBJECTIVE_SCORES
FEATURES = COMPUTED_SCORES + SUBJECTIVE_SCORES
RAW_META_FIELDS = RAW_SCORES
FEATURES_CONST = COMPUTED_SCORES

DEFAULT_WEIGHTS = {
    feature: round(1 / len(FEATURES), 4)
    for feature in FEATURES
}

TRANSLATION = {
    'features': {
        "kp_score": "Рейтинг Кинопоиска",
        "imdb_popularity": "Популярность IMDb",
        "delta_score": "Разница оценки первой и последней серии",
        "first_episode_score": "Оценка первой серии",
        "last_episode_score": "Оценка последней серии",
        "hook": "Сюжетная завязка",
        "holding": "Удержание за просмотром",
        "tension": "Напряжение"
    },
    'meta features': {
        "kp_score": "Рейтинг Кинопоиска",
        "year": "Год выхода",
        "imdb_votes": "Количество голосов IMDb",
        "first_episode_votes": "Оценка первой серии",
        "last_episode_votes": "Оценка последней серии"
    }
}

TRANSLATION = {
    'features': {
        "kp_score": "Kinopoisk score",
        "kp_popularity": "Kinopoisk popularity",
        "imdb_score": "IMDb score",
        "imdb_popularity": "IMDb popularity",
        "hook": "Hook",
        "holding": "Holding",
        "tension": "Tension"
    },
    'meta features': {
        "year": "Year",
        "kp_score": "Kinopoisk score",
        "kp_votes": "Kinopoisk votes",
        "imdb_score": "IMDb score",
        "imdb_votes": "IMDb votes"
    }
}

COMMANDS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
BAD_CHARACTERS = ",.'][@#$%^&*()?"
THRESHOLD = 6.5
NOW_YEAR = 2026
STEP = 0.001
