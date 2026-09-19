"""Unit tests for Markdown to Telegram HTML conversion (spec FR-004, T006)."""

from pipeline.convert import to_telegram_html


def test_heading_becomes_bold():
    assert "<b>Title</b>" in to_telegram_html("# Title\n\nbody")


def test_bold_italic_preserved():
    html = to_telegram_html("**bold** and *italic*")
    assert "<b>bold</b>" in html
    assert "<i>italic</i>" in html


def test_strikethrough_preserved():
    assert "<s>gone</s>" in to_telegram_html("~~gone~~")


def test_inline_code_preserved():
    assert "<code>pip install</code>" in to_telegram_html("`pip install`")


def test_link_preserved():
    html = to_telegram_html("[Docs](https://example.com)")
    assert '<a href="https://example.com">Docs</a>' in html


def test_unsupported_constructs_degrade_to_plain_text():
    html = to_telegram_html("| a | b |\n| - | - |\n| 1 | 2 |")
    assert "<table>" not in html
    assert "a" in html


def test_raw_html_is_escaped():
    html = to_telegram_html("plain <script>alert(1)</script> text")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_images_degrade_to_text():
    html = to_telegram_html("![alt text](img.png)")
    assert "<img" not in html
    assert "alt text" in html
