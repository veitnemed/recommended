DATA_DIR = 'C:/movies-learn'
FILE_NAME = 'C:/movies-learn/dataset.json'
WEIGHTS_JSON = 'C:/movies-learn/weights.json'
BACKUP_DIR = 'C:/backup-movies-learn/'
DIR_META = 'C:/meta-movies-learn/'
META_JSON = 'C:/meta-movies-learn/meta_data.json'
TXT_INPUT = 'C:/movies-learn/input.txt'

MAIN_INFO = ["title", "user_score"]
RAW_SCORES = ["kp_score", "year", "imdb_votes", "first_episode_score", "last_episode_score"]
COMPUTED_SCORES = ["kp_score", "imdb_popularity", "delta_score", "last_episode_score" ]
subjective_scores
SUBJECTIVE_SCORES = ["holding", "hook", "tension"]
'''{
  "main_info": {
    "title": "Триггер",
    "user_score": 8.0
  },
  "raw_scores": {
    "year": 2021,
    "imdb_votes": 2010,
    "first_episode_score": 8.0,
    "last_episode_score": 7.0
  },
  "computed_scores": {
    "kp_score": 8.0,
    "imdb_popularity": 7.0,
    "delta_score": 4.0,
    "last_episode_score": 7.0
  },
  "subjective_scores": {
    "holding": 7.0,
    "hook": 6.0,
    "tension": 9.0
  }
}'''
   
DEFAULT_WEIGHTS = {
    feature: round(1 / len(FEATURES), 4)
    for feature in FEATURES
}

TRANSLATION = {
    'features': {
        "kp_score": "Рейтинг Кинопоиска",
        "popularity_score": "Популярность с поправкой на год и голоса IMDb",
        "first_episode_score": "Оценка первой серии",
        "last_episode_score": "Оценка последней серии",
        "hook": "Сюжетная завязка",
        "holding": "Удержание за просмотром",
        "tension": "Напряжение"
        },
    'meta features': {
        "kp_score": "Рейтинг Кинопоиска",
        "popularity_score": "Популярность с поправкой на год и голоса IMDb",
        "first_episode_score": "Оценка первой серии",
        "last_episode_score": "Оценка последней серии",
        "hook": "Сюжетная завязка",
        "holding": "Удержание за просмотром",
        "tension": "Напряжение"
    }
} 

COMMANDS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9","10"]
BAD_CHARACTERS = ",.'][@#$%^&*()?"
THRESHOLD = 6.5
NOW_YEAR = 2026


STEP = 0.01

