"""Minimal Markdown to HTML for rickykhamis.com posts.

Deliberately covers only the subset the posts use, and has no third-party
dependency, so the scheduled publish job can never fail on a package install.

Supported: ATX headings, paragraphs, unordered and ordered lists, GFM pipe
tables, blockquotes, horizontal rules, and the inline run of **bold**,
*italic*, `code` and [links](url).
"""

from __future__ import annotations

import html
import re

_HEADING = re.compile(r"(#{1,6})\s+(.*)")
_RULE = re.compile(r"(-{3,}|\*{3,}|_{3,})")
_BULLET = re.compile(r"[-*+]\s+")
_ORDERED = re.compile(r"\d+\.\s+")
_TABLE_DIVIDER = re.compile(r"\|?[\s:|-]+\|[\s:|-]*")

_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")

_SENTINEL = "\x00{}\x00"


def _inline(text: str) -> str:
    """Render the inline run. Code spans are stashed so their contents are
    never re-processed as markup."""
    out = html.escape(text, quote=False)

    stash: list[str] = []

    def keep(match: re.Match[str]) -> str:
        stash.append(match.group(1))
        return _SENTINEL.format(len(stash) - 1)

    out = _CODE.sub(keep, out)
    out = _LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', out)
    out = _BOLD.sub(r"<strong>\1</strong>", out)
    out = _ITALIC.sub(r"<em>\1</em>", out)
    out = re.sub(
        r"\x00(\d+)\x00", lambda m: f"<code>{stash[int(m.group(1))]}</code>", out
    )
    return out


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _starts_block(line: str) -> bool:
    return bool(
        _HEADING.fullmatch(line)
        or _RULE.fullmatch(line)
        or _BULLET.match(line)
        or _ORDERED.match(line)
        or line.startswith(">")
        or line.startswith("|")
    )


def convert(text: str) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        heading = _HEADING.fullmatch(line)
        if heading:
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2).strip())}</h{level}>")
            i += 1
            continue

        if _RULE.fullmatch(line):
            out.append("<hr>")
            i += 1
            continue

        # GFM table: a header row followed by a divider row.
        if (
            "|" in line
            and i + 1 < len(lines)
            and _TABLE_DIVIDER.fullmatch(lines[i + 1].strip())
        ):
            header = _cells(line)
            i += 2
            body: list[list[str]] = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                body.append(_cells(lines[i]))
                i += 1
            head_html = "".join(f"<th>{_inline(c)}</th>" for c in header)
            rows_html = "".join(
                "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>"
                for row in body
            )
            out.append(
                f"<table><thead><tr>{head_html}</tr></thead>"
                f"<tbody>{rows_html}</tbody></table>"
            )
            continue

        if line.startswith(">"):
            quoted: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quoted.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f"<blockquote><p>{_inline(' '.join(quoted))}</p></blockquote>")
            continue

        if _BULLET.match(line):
            items: list[str] = []
            while i < len(lines) and _BULLET.match(lines[i].strip()):
                items.append(_BULLET.sub("", lines[i].strip(), count=1))
                i += 1
            out.append(
                "<ul>" + "".join(f"<li>{_inline(t)}</li>" for t in items) + "</ul>"
            )
            continue

        if _ORDERED.match(line):
            items = []
            while i < len(lines) and _ORDERED.match(lines[i].strip()):
                items.append(_ORDERED.sub("", lines[i].strip(), count=1))
                i += 1
            out.append(
                "<ol>" + "".join(f"<li>{_inline(t)}</li>" for t in items) + "</ol>"
            )
            continue

        paragraph: list[str] = []
        while i < len(lines) and lines[i].strip() and not _starts_block(lines[i].strip()):
            paragraph.append(lines[i].strip())
            i += 1
        out.append(f"<p>{_inline(' '.join(paragraph))}</p>")

    return "\n".join(out)
