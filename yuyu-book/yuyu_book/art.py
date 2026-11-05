"""Chapter emblems — one small line drawing per unit, kept in the book's hand.

The rules below are what make a hand-drawn SVG safe to inline 20 times into a
single offline file: no ids (the audit fails on a duplicate), no scripts or
styles, no external references, and `currentColor` everywhere so one drawing
re-inks itself in dark mode and on paper without a second asset.
"""
from __future__ import annotations

import re
from pathlib import Path

from .core import BuildError

ART_DIR = Path(__file__).resolve().parent.parent / "illustrations"
MAX_BYTES = 6000
PLATE_BYTES = 20000

_BANNED = (
    (re.compile(r"<\s*script", re.I), "<script>"),
    (re.compile(r"<\s*style", re.I), "<style>"),
    (re.compile(r"<\s*iframe", re.I), "<iframe>"),
    (re.compile(r"\bid\s*=", re.I), "an id= attribute (20 inlined drawings would "
                                    "collide; the audit fails on a duplicate id)"),
    (re.compile(r"href\s*=", re.I), "an href= (external or #fragment reference)"),
    (re.compile(r"url\s*\(", re.I), "a url() (nothing may reach outside the file)"),
)


def _read(name: str, budget: int = MAX_BYTES) -> str | None:
    path = ART_DIR / f"{name}.svg"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if len(text.encode("utf-8")) > budget:
        raise BuildError(f"{path.name}: {len(text)} bytes, over the "
                         f"{budget} budget for an inlined drawing")
    if not text.startswith("<svg") or "viewBox" not in text.split(">", 1)[0]:
        raise BuildError(f"{path.name}: an emblem must be one <svg> with a viewBox")
    for rx, why in _BANNED:
        if rx.search(text):
            raise BuildError(f"{path.name}: contains {why}")
    if "currentColor" not in text:
        raise BuildError(f"{path.name}: nothing is drawn in currentColor, so the "
                         "emblem cannot re-ink itself in dark mode or on paper")
    return text


def emblem(unit_id: str) -> str:
    """The unit's emblem as inline markup, or '' when the unit has none."""
    text = _read(unit_id)
    if not text:
        return ""
    return f'<span class="ch-emblem" aria-hidden="true">{text}</span>'


def keeper() -> str:
    """The old postman at the foot of each chapter, inlined 20 times: small
    by contract, because a mascot the file cannot afford is not a mascot."""
    text = _read("keeper")
    if not text:
        return ""
    return f'<span class="kp-art" aria-hidden="true">{text}</span>'


def headpiece(part_id: str) -> str:
    """The drawing a part divider opens with, or '' when there is none."""
    text = _read(f"part-{part_id}")
    if not text:
        return ""
    return f'<div class="pd-art" aria-hidden="true">{text}</div>'


def cover_plate() -> str:
    """The cover's four-horse chariot, drafted in the same hand as the
    emblems: an inline plate costs the file 11 KB and needs no crop, no
    filter and no bitmap."""
    text = _read("cover", PLATE_BYTES)
    if not text:
        return ""
    return f'<div class="cover-art" aria-hidden="true">{text}</div>'


def missing(names: list[str]) -> list[str]:
    return [n for n in names if not (ART_DIR / f"{n}.svg").exists()]
