import pytest

from validation import (
    MAX_UPLOAD_BYTES,
    is_valid_url,
    logo_risk_level,
    normalize_url,
    validate_upload_size,
)


def test_normalize_url_adds_https_to_bare_domain():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_url_preserves_existing_scheme_and_strips_spaces():
    assert normalize_url("  http://example.com/path  ") == "http://example.com/path"


def test_normalize_url_empty_string_returns_empty_string():
    assert normalize_url("   ") == ""


@pytest.mark.parametrize(
    "url",
    ["https://example.com", "http://example.com/path?x=1", "https://sub.example.co.uk"],
)
def test_is_valid_url_accepts_http_urls(url):
    assert is_valid_url(url)


@pytest.mark.parametrize("url", ["", "not a url", "ftp://example.com", "https://"])
def test_is_valid_url_rejects_invalid_or_unsupported_urls(url):
    assert not is_valid_url(url)


def test_validate_upload_size_accepts_5_mb_limit():
    validate_upload_size(MAX_UPLOAD_BYTES)


def test_validate_upload_size_rejects_above_5_mb_limit():
    with pytest.raises(ValueError, match="5 MB"):
        validate_upload_size(MAX_UPLOAD_BYTES + 1)


@pytest.mark.parametrize(
    ("logo_percent", "expected"),
    [(20, "ok"), (25, "ok"), (26, "warning"), (30, "warning"), (31, "strong_warning")],
)
def test_logo_risk_level(logo_percent, expected):
    assert logo_risk_level(logo_percent) == expected
