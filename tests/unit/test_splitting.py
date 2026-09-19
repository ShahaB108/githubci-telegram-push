"""Unit tests for 4096-character message splitting (spec FR-010, T007)."""

from pipeline.convert import TELEGRAM_MESSAGE_LIMIT, split_message


def test_short_message_unchanged_single_part():
    parts = split_message("hello")
    assert parts == ["hello"]
    assert all("Part" not in part for part in parts)


def test_long_message_splits_into_ordered_marked_parts():
    parts = split_message("word " * 1200)
    assert len(parts) >= 2
    for index, part in enumerate(parts, start=1):
        assert len(part) <= TELEGRAM_MESSAGE_LIMIT
        assert part.endswith(f"Part {index}/{len(parts)}")


def test_split_prefers_paragraph_boundaries():
    first = "first paragraph " + "x" * 2500
    second = "second paragraph " + "y" * 2500
    parts = split_message(first + "\n\n" + second)
    assert len(parts) == 2
    assert parts[0].startswith("first paragraph")
    assert parts[1].startswith("second paragraph")


def test_no_content_lost_when_splitting():
    text = "\n\n".join(
        "paragraph {} {}".format(index, "filler " * 100) for index in range(30))
    parts = split_message(text)
    cleaned = [part.split("\n\nPart")[0] for part in parts]
    assert " ".join(cleaned).split() == text.split()
