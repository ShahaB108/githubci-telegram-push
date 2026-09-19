"""Unit tests for post discovery, parsing, and exclusion (spec FR-001/FR-002, T008)."""

import pytest

from pipeline.detect import MalformedPostError, discover_posts, is_draft, parse_post


def test_discover_returns_only_markdown_files_sorted(env, write_post):
    write_post("b.md")
    (env / "posts" / "notes.txt").write_text("nope", encoding="utf-8")
    write_post("a.md")
    paths = discover_posts(str(env / "posts"))
    names = [path.replace("\\", "/").rsplit("/", 1)[-1] for path in paths]
    assert names == ["a.md", "b.md"]


def test_discover_missing_directory_is_empty_list():
    assert discover_posts("does-not-exist") == []


def test_parse_post_reads_frontmatter_and_body(env, write_post):
    write_post("meta.md", body="Body line.", frontmatter="title: Hi\ntags: [x]")
    meta, body = parse_post(str(env / "posts" / "meta.md"))
    assert meta == {"title": "Hi", "tags": ["x"]}
    assert body.strip() == "Body line."


def test_parse_post_without_frontmatter_is_allowed(env, write_post):
    write_post("plain.md")
    meta, body = parse_post(str(env / "posts" / "plain.md"))
    assert meta == {}
    assert "Hello" in body


def test_parse_post_empty_body_is_malformed(env, write_post):
    write_post("broken.md", body="", frontmatter="title: X")
    with pytest.raises(MalformedPostError) as excinfo:
        parse_post(str(env / "posts" / "broken.md"))
    assert "broken.md" in str(excinfo.value)


def test_parse_post_invalid_frontmatter_is_malformed(env, write_post):
    write_post("bad.md", body="body", frontmatter="title: [unclosed")
    with pytest.raises(MalformedPostError):
        parse_post(str(env / "posts" / "bad.md"))


def test_is_draft():
    assert is_draft({"draft": True}) is True
    assert is_draft({}) is False
    assert is_draft({"draft": False}) is False
