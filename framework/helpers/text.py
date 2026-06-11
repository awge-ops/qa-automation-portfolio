"""Text normalization utilities used across test assertions and data loading."""

import re


def normalize(value: str) -> str:
    """Collapse whitespace and non-breaking spaces to single spaces."""
    return re.sub(r"\s+", " ", (value or "").replace(" ", " ")).strip()


def canonical(value: str) -> str:
    """Uppercase, strip non-alphanumeric chars — used for fuzzy text matching."""
    text = normalize(value).upper()
    text = re.sub(r"[^A-Z0-9 ]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def snippet(value: str, word_count: int = 8) -> str:
    """First N words of normalized text — used for partial matching."""
    words = normalize(value).split()
    return " ".join(words[:word_count])
