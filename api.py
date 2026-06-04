import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import storage


API_URL = "https://api.poiskkino.dev"
TOKEN = os.getenv("POISKKINO_API_KEY")

if TOKEN is None:
    try:
        from api_token import TOKEN
    except ImportError:
        TOKEN = None

SERIALS = storage.get_all_titles()


def api_request(path: str, params: dict = None) -> dict:
    url = API_URL + path

    if params is not None:
        url += "?" + urlencode(params, doseq=True)

    request = Request(
        url,
        headers={"X-API-KEY": TOKEN}
    )

    with urlopen(request, timeout=20) as response:
        return json.load(response)


def find_serial(title: str) -> dict:
    data = api_request(
        path="/v1.4/movie/search",
        params={
            "query": title,
            "page": 1,
            "limit": 10
        }
    )

    movies = data.get("docs", [])
    title = title.strip().lower()

    for movie in movies:
        if movie.get("name", "").strip().lower() == title:
            return movie

    if len(movies) > 0:
        return movies[0]

    return None


def get_serial_info(movie_id: int) -> dict:
    return api_request(path=f"/v1.4/movie/{movie_id}")


def get_keywords(movie_id: int) -> list:
    data = api_request(
        path="/v1.4/keyword",
        params={
            "movies.id": movie_id,
            "page": 1,
            "limit": 250
        }
    )

    keywords = []
    for keyword in data.get("docs", []):
        title = keyword.get("title")
        if title is not None:
            keywords.append(title)

    return keywords


def get_genres(serial: dict) -> list:
    genres = []

    for genre in serial.get("genres", []):
        name = genre.get("name")
        if name is not None:
            genres.append(name)

    return genres


def get_names(serial: dict, field: str) -> list:
    names = []

    for obj in serial.get(field, []):
        name = obj.get("name")
        if name is not None:
            names.append(name)

    return names


def get_persons(serial: dict, profession: str, limit: int = 5) -> list:
    names = []

    for person in serial.get("persons", []):
        if person.get("profession") == profession:
            name = person.get("name") or person.get("enName")
            if name is not None and name not in names:
                names.append(name)

        if len(names) == limit:
            break

    return names


def get_seasons_count(serial: dict) -> int:
    seasons = serial.get("seasonsInfo", [])
    return len(seasons)


def get_rating(serial: dict, source: str):
    return serial.get("rating", {}).get(source)


def get_votes(serial: dict, source: str):
    return serial.get("votes", {}).get(source)


def get_description(serial: dict) -> str:
    description = serial.get("description") or serial.get("shortDescription")
    if description is None or str(description).strip() == "":
        return "нет данных"
    return str(description).strip()


def show_serial_tags(title: str) -> None:
    print("=" * 60)

    movie = find_serial(title)

    if movie is None:
        print("Название:", title)
        print("Год:", 0)
        print("Описание:", "сериал не найден")
        return

    serial = get_serial_info(movie["id"])

    print("Название:", serial.get("name") or title)
    print("Год:", serial.get("year") or 0)
    print("Описание:", get_description(serial))


def run_test() -> None:
    if TOKEN is None:
        print("Ошибка! Не задана переменная окружения POISKKINO_API_KEY")
        return

    for title in SERIALS:
        try:
            show_serial_tags(title)
        except Exception as error:
            print("Ошибка API:", error)


if __name__ == "__main__":
    run_test()
