"""Console actions for watched metadata and poster maintenance."""


def sync_watched_descriptions_and_posters() -> None:
    """Backfills meta descriptions and poster-cache for watched dataset records."""
    from posters.sync_watched import sync_watched_metadata

    print("Обновление описаний и poster-cache для просмотренных...\n")

    def progress(current: int, total: int, title: str) -> None:
        print(f"{current}/{total} | {title}")

    stats = sync_watched_metadata(write_meta=True, progress_callback=progress)
    print("\nИтог:")
    print(f"  Записей: {stats['total']}")
    print(f"  Описаний найдено: {stats['description_found']}")
    print(f"  Описаний записано в meta: {stats['description_updated']}")
    print(f"  Poster found: {stats['poster_found']}")
    print(f"  Poster missing: {stats['poster_missing']}")


def fetch_tmdb_poster_metadata() -> None:
    """Fetches missing poster metadata from TMDb cache/API into poster-cache."""
    from posters.fetch_metadata import fetch_poster_metadata_for_watched

    print("Загрузка poster metadata из TMDb...\n")

    def progress(current: int, total: int, title: str) -> None:
        print(f"{current}/{total} | {title}")

    stats = fetch_poster_metadata_for_watched(use_api=True, progress_callback=progress)
    print("\nИтог:")
    print(f"  Записей dataset: {stats['total']}")
    print(f"  Уже было poster: {stats['skipped_found']}")
    print(f"  Обновлено из TMDb cache: {stats['updated_from_cache']}")
    print(f"  Обновлено через TMDb API: {stats['updated_from_api']}")
    print(f"  Без tmdb_id: {stats['missing_tmdb_id']}")
    print(f"  Всё ещё missing: {stats['still_missing']}")


def download_poster_images_local() -> None:
    """Downloads poster images for poster-cache entries with poster_url."""
    from posters.download_images import download_poster_images

    print("Скачивание poster images в data/cache/posters/images/...\n")

    def progress(current: int, total: int, title: str) -> None:
        print(f"{current}/{total} | {title}")

    stats = download_poster_images(progress_callback=progress)
    print("\nИтог:")
    print(f"  Записей в cache: {stats['total_entries']}")
    print(f"  Кандидатов на скачивание: {stats['candidates']}")
    print(f"  Скачано: {stats['downloaded']}")
    print(f"  Уже были локально: {stats['skipped_existing']}")
    print(f"  Ошибок: {stats['failed']}")


def fetch_watched_tmdb_metadata() -> None:
    """Loads TMDb metadata for watched records by title + year."""
    from posters.fetch_watched_tmdb import (
        fetch_watched_tmdb_metadata as run_fetch,
        format_watched_tmdb_unresolved_report,
    )

    print("Загрузка TMDb metadata для просмотренных...\n")

    def progress(current: int, total: int, title: str) -> None:
        print(f"{current}/{total} | {title}")

    stats = run_fetch(progress_callback=progress)
    print("\nИтог:")
    print(f"  Проверено записей: {stats['checked']}")
    print(f"  Уже были tmdb_id: {stats['already_had_tmdb_id']}")
    print(f"  Найдено tmdb_id: {stats['found_tmdb_id']}")
    print(f"  Добавлено description: {stats['added_description']}")
    print(f"  Добавлено poster_url: {stats['added_poster_url']}")
    print(f"  Обновлено poster-cache: {stats['poster_cache_updated']}")
    print(f"  Manual overrides успешно: {stats['manual_overrides_used']}")
    print(f"  Manual overrides ошибка: {stats['manual_overrides_failed']}")
    print(f"  Пропущено, не найдено: {stats['skipped_not_found']}")
    print(f"  Пропущено, сомнительный match: {stats['skipped_uncertain_match']}")
    print(f"  Ошибки сети: {stats['network_errors']}")
    print()
    print(format_watched_tmdb_unresolved_report(stats.get("unresolved") or []))


def diagnose_unresolved_watched_tmdb_metadata() -> None:
    """Print read-only diagnostics for unresolved watched TMDb metadata."""
    from posters.tmdb_diagnostic import (
        diagnose_watched_tmdb_unresolved,
        format_watched_tmdb_diagnostic_report,
    )

    print("Диагностика unresolved TMDb metadata (read-only)...\n")

    def progress(current: int, total: int, title: str) -> None:
        print(f"{current}/{total} | {title}")

    report = diagnose_watched_tmdb_unresolved(progress_callback=progress)
    print()
    print(format_watched_tmdb_diagnostic_report(report))
