"""Post discovery, parsing, and draft exclusion (FR-001, FR-002)."""

import os

import yaml

# Repository documents that sit next to the posts but are never published: the posts
# directory defaults to the repository root, so the landing README and its peers have to
# be excluded explicitly.
NON_POST_FILENAMES = (
    "README.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "LICENSE.md",
)


class MalformedPostError(Exception):
    """Raised when a post cannot be parsed or has an empty body (exit 20)."""


def discover_posts(posts_dir, ignore=None):
    """Return sorted paths of .md files directly under posts_dir (FR-001).

    Dotfiles and the repository documents listed in NON_POST_FILENAMES (or in the
    ``ignore`` override) are never treated as posts, so the repository root can hold the
    posts and the landing README side by side.
    """
    if not os.path.isdir(posts_dir):
        return []
    ignored = {name.lower() for name in (NON_POST_FILENAMES if ignore is None else ignore)}
    names = sorted(
        name for name in os.listdir(posts_dir)
        if name.lower().endswith(".md")
        and not name.startswith(".")
        and name.lower() not in ignored
        and os.path.isfile(os.path.join(posts_dir, name)))
    return [os.path.join(posts_dir, name) for name in names]


def parse_post(full_path):
    """Parse one post into (frontmatter dict, body text); raise on malformed input."""
    with open(full_path, "r", encoding="utf-8") as handle:
        text = handle.read()
    frontmatter, body = _split_frontmatter(text, full_path)
    meta = {}
    if frontmatter is not None:
        try:
            loaded = yaml.safe_load(frontmatter)
        except yaml.YAMLError as exc:
            raise MalformedPostError(
                f"{full_path}: invalid frontmatter: {exc}")
        if loaded is None:
            loaded = {}
        if not isinstance(loaded, dict):
            raise MalformedPostError(
                f"{full_path}: frontmatter must be a mapping")
        meta = loaded
    if not body.strip():
        raise MalformedPostError(f"{full_path}: empty body")
    return meta, body


def is_draft(meta):
    """True when the post opts out of publishing via frontmatter (FR-001)."""
    return meta.get("draft") is True


def _split_frontmatter(text, full_path):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1:])
    raise MalformedPostError(f"{full_path}: unterminated frontmatter")
