from urllib.parse import urlparse

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def normalize_url(raw_url: str) -> str:
    stripped = raw_url.strip()
    if not stripped:
        return ""
    if "://" in stripped:
        return stripped
    return f"https://{stripped}"


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.hostname:
        return False
    return all(not character.isspace() and character.isprintable() for character in url)


def validate_upload_size(size_bytes: int) -> None:
    if size_bytes > MAX_UPLOAD_BYTES:
        raise ValueError("Uploaded image must be 5 MB or smaller.")


def logo_risk_level(logo_percent: int) -> str:
    if logo_percent > 30:
        return "strong_warning"
    if logo_percent > 25:
        return "warning"
    return "ok"
