"""Read-only formatters for the Settings/Tools tab."""

from __future__ import annotations

KP_RETRY_BATCH_SIZE = 10


def format_pool_stats_block(stats_view: dict) -> list[str]:
    lines = list(stats_view.get("lines") or [])
    summary = str(stats_view.get("summary") or "").strip()
    if summary and summary not in lines:
        lines.append(summary)
    return lines


def format_dedupe_preview_lines(title_view: dict, suspicious_view: dict) -> list[str]:
    lines: list[str] = []
    summary = title_view.get("summary") or {}
    group_count = int(summary.get("group_count") or 0)
    extra_entries = int(summary.get("extra_entries") or 0)
    if group_count > 0:
        lines.append(f"Групп дублей по названию: {group_count} · лишних записей: {extra_entries}")
    else:
        lines.append("Групп дублей по названию не найдено.")

    suspicious_count = int(suspicious_view.get("count") or 0)
    if suspicious_count > 0:
        lines.append(f"Подозрительных пар: {suspicious_count}")
    return lines


def format_retry_kp_preview_line(retry_view: dict) -> str:
    count = int(retry_view.get("incomplete_count") or 0)
    if count <= 0:
        return "Неполных карточек для KP retry нет."
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
