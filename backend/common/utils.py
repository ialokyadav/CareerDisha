import re


WHITESPACE_RE = re.compile(r"\s+")
NON_TEXT_RE = re.compile(r"[^a-zA-Z0-9+.#\s]")


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u00a0", " ")
    text = NON_TEXT_RE.sub(" ", text)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip().lower()
