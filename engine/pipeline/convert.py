"""Markdown to Telegram HTML conversion and message splitting (FR-004, FR-010).

Allowed Telegram tags: b, i, u, s, code, pre, a[href]. Everything else degrades to
plain text (spec edge case: formatting alone never fails a delivery).
"""

import re

import markdown as md_lib

TELEGRAM_MESSAGE_LIMIT = 4096
_MARKER_RESERVE = 24  # room for the "Part N/M" marker appended to every part

_ALLOWED_TAG_PATTERN = re.compile(
    r'</?a\s+href="[^"]*"\s*>|</?a>|</?(?:b|i|u|s|code|pre)>')


def to_telegram_html(markdown_text):
    """Convert Markdown into the Telegram HTML subset."""
    text = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", markdown_text or "")
    html_text = md_lib.markdown(text)
    html_text = re.sub(r"<h([1-6])>(.*?)</h\1>", r"<b>\2</b>", html_text,
                       flags=re.DOTALL)
    html_text = html_text.replace("<strong>", "<b>").replace("</strong>", "</b>")
    html_text = html_text.replace("<em>", "<i>").replace("</em>", "</i>")
    html_text = html_text.replace("<del>", "<s>").replace("</del>", "</s>")
    html_text = html_text.replace("<li>", "\u2022 ").replace("</li>", "\n")
    html_text = re.sub(r"</?[uo]l[^>]*>", "", html_text)
    html_text = re.sub(r"<br\s*/?>", "\n", html_text)
    html_text = re.sub(r"<hr\s*/?>", "\u2014", html_text)
    html_text = html_text.replace("<blockquote>", "").replace("</blockquote>", "")
    html_text = re.sub(r'<img[^>]*alt="([^"]*)"[^>]*/?>', r"\1", html_text)
    html_text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*/?>', r"image: \1", html_text)
    html_text = html_text.replace("<p>", "").replace("</p>", "\n\n")
    return _escape_disallowed(html_text)


def build_message(title, body_html):
    """Prepend the bolded title to the converted body (FR-004)."""
    return f"<b>{title}</b>\n\n{body_html}".strip()


def split_message(text, limit=TELEGRAM_MESSAGE_LIMIT):
    """Split an over-limit message at block boundaries into marked parts (FR-010)."""
    if len(text) <= limit:
        return [text]
    effective = limit - _MARKER_RESERVE
    chunks = []
    remaining = text.strip()
    while len(remaining) > effective:
        window = remaining[:effective]
        cut = window.rfind("\n\n")
        if cut < effective // 2:
            cut = window.rfind("\n")
        if cut < effective // 2:
            cut = effective
        chunks.append(window[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        chunks.append(remaining)
    total = len(chunks)
    return [f"{chunk}\n\nPart {index}/{total}"
            for index, chunk in enumerate(chunks, start=1)]


def _escape_disallowed(html_text):
    """Escape angle brackets that are not part of the allowed Telegram tag set."""
    protected = []

    def _protect(match):
        protected.append(match.group(0))
        return f"\x00{len(protected) - 1}\x00"

    masked = _ALLOWED_TAG_PATTERN.sub(_protect, html_text)
    masked = masked.replace("<", "&lt;").replace(">", "&gt;")
    return re.sub("\x00([0-9]+)\x00",
                  lambda match: protected[int(match.group(1))], masked)
