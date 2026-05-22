import math
import constant


def clip_0_10(value: float) -> float:
    return max(0, min(10, value))


def popularity_score(imdb_votes: int, year: int) -> float:
    age = max(1, constant.NOW_YEAR - year)

    adjusted_votes = imdb_votes / (age ** 0.5)

    min_votes = 50
    max_votes = 5000

    if adjusted_votes <= min_votes:
        return 0

    score = math.log(adjusted_votes / min_votes) / math.log(max_votes / min_votes) * 15

    return clip_0_10(score)

print(popularity_score(300,2025))
print(popularity_score(1100,2021))
def build_const_features(raw: dict) -> dict:
    return {
        "kp_score": float(raw["kp_score"]),
        "popularity_score": popularity_score(
            imdb_votes=int(raw["imdb_votes"]),
            year=int(raw["year"])
        ),
        "first_episode_score": float(raw["first_episode_score"]),
        "last_episode_score": float(raw["last_episode_score"])
    }