DATA_DIR = 'C:/movies-learn'
FILE_NAME = 'C:/movies-learn/dataset.json'

FEATURES = ["kp_score", "hook", "holding", "tension"]

COMMANDS = ["0", "1", "2", "3", "4"]
BAD_CHARACTERS = ",.'][@#$%^&*()?"
THRESHOLD = 6.5

DEFAULT_WEIGHTS = {
    "kp_score": 0.25,
    "hook": 0.25,
    "holding": 0.25,
    "tension": 0.25
}

STEP = 0.01

