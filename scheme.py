
import copy

SHEME_VALIDATORS  = {
    "main_info": {
        "title": (["title"], str),
        "user_score": (["score"], float)
    },
    "raw_scores": {
        "year": (["year"], int),
        "kp_score": (["score"], float),
        "kp_votes": (["votes"], int),
        "imdb_score": (["score"], float),
        "imdb_votes": (["votes"], int),
    },
    "subjective_scores": {
        "holding": (["score"], float),
        "hook": (["score"], float),
        "tension": (["score"], float),
    },
    "computed_scores": {
        "kp_score": (["score"], float),
        "imdb_score": (["score"], float),
        "kp_popularity": (["score"], float),
        "imdb_popularity": (["score"], float)     
    }
}

SHEME_ADD = copy.deepcopy(SHEME_VALIDATORS)
SHEME_ADD["main_info"]["title"][0].append("origin_title")


def get_fields(selection_name: str) -> list:
    sheme_copy = copy.deepcopy(SHEME_VALIDATORS)
    return list(sheme_copy[selection_name].keys())

def get_schema(selection_name: str) -> dict:
    sheme_copy = copy.deepcopy(SHEME_VALIDATORS)
    return sheme_copy[selection_name]