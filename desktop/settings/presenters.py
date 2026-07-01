"""Read-only formatters for the Settings/Tools tab."""

from __future__ import annotations

KP_RETRY_BATCH_SIZE = 10

POOL_KPI_ICONS = {
    "Всего": "▦",
    "Готовые": "✓",
    "Неполные": "…",
    "Дубли": "≈",
}


def format_pool_kpi_items(stats: dict) -> list[tuple[str, str, str]]:
    """Return (label, value, icon) tuples for pool KPI tiles."""
    unique = int(stats.get("unique_total", stats.get("storage_total", 0)) or 0)
    ready = int(stats.get("ready_total", 0) or 0)
    incomplete = int(stats.get("incomplete_total", 0) or 0)
    duplicates = int(stats.get("duplicate_entries", 0) or 0)
    duplicates += int(stats.get("similar_duplicate_total", 0) or 0)
    duplicates += int(stats.get("cross_year_duplicate_total", 0) or 0)
    return [
        ("Всего", str(unique), POOL_KPI_ICONS["Всего"]),
        ("Готовые", str(ready), POOL_KPI_ICONS["Готовые"]),
        ("Неполные", str(incomplete), POOL_KPI_ICONS["Неполные"]),
        ("Дубли", str(duplicates), POOL_KPI_ICONS["Дубли"]),
    ]


def format_dedupe_preview_lines(title_view: dict, suspicious_view: dict) -> list[str]:
    lines: list[str] = []
    summary = title_view.get("summary") or {}
    group_count = int(summary.get("group_count") or 0)
    extra_entries = int(summary.get("extra_entries") or 0)
    if group_count > 0:
        lines.append(f"Групп по названию: {group_count} · лишних записей: {extra_entries}")
    else:
        lines.append("Групп дублей по названию не найдено.")

    suspicious_count = int(suspicious_view.get("count") or 0)
    if suspicious_count > 0:
        lines.append(f"Подозрительных пар: {suspicious_count}")
    return lines


def format_retry_kp_preview_line(retry_view: dict) -> str:
    count = int(retry_view.get("incomplete_count") or 0)
    if count <= 0:
        return "Неполных карточек для добора KP нет."
    batch = min(KP_RETRY_BATCH_SIZE, count)
    return f"Неполных карточек: {count}. Следующий запуск обработает до {batch}."


def format_clean_duplicates_status(result: dict) -> str:
    if not result.get("changed"):
        return "Дубли в pool не найдены, изменений нет."
    removed_exact = int(result.get("removed_exact") or 0)
    removed_similar = int(result.get("removed_similar") or 0)
    removed_cross = int(result.get("removed_cross_year") or 0)
    unique_total = int(result.get("unique_total") or 0)
    return (
        f"Pool обновлён: уникальных {unique_total}. "
        f"Удалено exact {removed_exact}, похожих {removed_similar}, cross-year {removed_cross}."
    )


def format_retry_kp_status(result: dict) -> str:
    stats = result.get("stats") or {}
    attempted = int(stats.get("attempted") or result.get("attempted") or 0)
    if attempted <= 0:
        return "KP retry: нечего обрабатывать."
    kp_found = int(stats.get("kp_found") or 0)
    became_complete = int(stats.get("became_complete") or 0)
    remaining = int(stats.get("remaining_incomplete") or 0)
    return (
        f"KP retry: обработано {attempted}, найдено KP {kp_found}, "
        f"стало complete {became_complete}, осталось incomplete {remaining}."
    )


def format_clear_pool_status(result: dict) -> str:
    cleared = int(result.get("cleared") or 0)
    if cleared <= 0:
        return "Pool уже был пуст."
    return f"Pool очищен: удалено {cleared} записей."


def format_tmdb_files_empty_hint() -> str:
    return "TMDb result JSON в data/exports/candidate_pool не найдены."


def format_tmdb_import_preview(preview: dict, *, include_filename: bool = False) -> str:
    if preview.get("ok") is False:
        error = preview.get("error") or "неизвестная ошибка"
        return f"Не удалось прочитать файл: {error}"

    count = int(preview.get("candidate_count") or 0)
    criteria = str(preview.get("default_criteria_name") or "—")
    lines = []
    if include_filename:
        path = preview.get("result_path")
        file_name = path.name if hasattr(path, "name") else str(path)
        lines.append(f"Файл: {file_name}")
    lines.append(f"Кандидатов в файле: {count}")
    lines.append(f"Критерий: {criteria}")
    lines.append("Записи будут добавлены или обновлены в общем pool после дедупликации.")
    return "\n".join(lines)


def format_tmdb_import_status(import_result: dict) -> str:
    if import_result.get("ok") is False:
        return f"Импорт не выполнен: {import_result.get('error') or 'неизвестная ошибка'}"

    stats = import_result.get("stats") or {}
    skipped_watched = stats.get("skipped_watched", stats.get("watched_skipped", 0))
    skipped_duplicates = stats.get("skipped_duplicates", stats.get("duplicates", 0))
    pool_after = stats.get("pool_size_after", stats.get("pool_size", 0))
    return (
        f"Импорт завершён: прочитано {stats.get('read', 0)}, "
        f"добавлено {stats.get('added', 0)}, обновлено {stats.get('updated', 0)}, "
        f"пропущено watched {skipped_watched}, дублей {skipped_duplicates}, "
        f"ошибок {stats.get('errors', 0)}. Pool: {pool_after}."
    )
