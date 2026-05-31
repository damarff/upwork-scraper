"""HTML cleaning helpers."""

from bs4 import BeautifulSoup


def clean_html(raw: str | None) -> str:
    """Strip HTML tags and normalize whitespace."""
    if not raw:
        return ""
    return BeautifulSoup(raw, "html.parser").get_text(separator=" ", strip=True)
