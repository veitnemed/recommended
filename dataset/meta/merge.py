"""Extract enrichment fields from a meta payload."""


def extract_extra_meta(meta_payload) -> dict:
    """Return meta fields other than main_info and raw_scores."""
    if isinstance(meta_payload, dict) is False:
        return {}

    extra_meta = {}
    for key, value in meta_payload.items():
        if key in {"main_info", "raw_scores"}:
            continue
        extra_meta[key] = value
    return extra_meta
