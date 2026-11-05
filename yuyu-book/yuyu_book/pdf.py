"""PDF pipeline: headless print of the styled HTML, then a PyMuPDF post-pass.

Chromium turns every in-document link into a named destination, so the
printed PDF already knows that #ch09 lives on page 81. The post-pass reads
those destinations instead of injecting marker text: it builds the bookmark
tree (meta["outline"]), the running heads (meta["heads"]), the footer folios
and the printed contents numbers (meta["toc_rows"] inside the contents
pages). Number glyphs use built-in Helvetica; CJK heads need a local system
font, subsetted before save, and degrade to a plain rule if none is there.

The subject index is the one thing that cannot be drawn on after the fact —
dozens of rows share an anchor and print near-identical lines — so it takes
two prints: `measure` learns which sheet each unit landed on, the folios are
written into the slots the rows already reserve, and the book is printed
again with them in place.
"""
from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from .core import BuildError

CJK_FONTS = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc",
             "C:/Windows/Fonts/simhei.ttf",
             # the running head is drawn with a real face; on a runner without
             # any of these the Chinese heads/folios would be dropped silently
             "/System/Library/Fonts/PingFang.ttc",
             "/System/Library/Fonts/Supplemental/Songti.ttc",
             "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"]
MARGIN = 48.0
INK = (0.42, 0.36, 0.26)
RULE = (0.82, 0.76, 0.62)
HEAD_BAND = 60.0      # anything painted above this is the running head
FOOT_BAND = 45.0      # ...and below the page bottom minus this is the folio


def empty_sheets(doc) -> list[int]:
    """1-based page numbers of sheets that carry nothing but furniture.

    A unit that ends a few lines above the text block used to leave a page
    behind with only a head and a folio on it — the reader turns a sheet and
    finds no prose at all. Text, vector drawing and image all count as body,
    so a plate that fills the block is never mistaken for a hole.
    """
    holes = []
    for i, page in enumerate(doc):
        lo, hi = HEAD_BAND, page.rect.height - FOOT_BAND
        boxes = [fitz.Rect(b[:4]) for b in page.get_text("blocks")]
        boxes += [d["rect"] for d in page.get_drawings()]
        for im in page.get_images(full=True):
            try:
                boxes.append(page.get_image_bbox(im))
            except Exception:                       # not painted on this page
                continue
        body = [b for b in boxes if b.is_valid and b.width > 1 and b.height > 1
                and b.y0 > lo and b.y1 < hi]
        if not body:
            holes.append(i + 1)
    return holes


def _launch(p, browser: str | None):
    if browser:
        try:
            return p.chromium.launch(executable_path=browser)
        except Exception:
            pass
    for kind in ("msedge", "chrome", None):
        try:
            return (p.chromium.launch(channel=kind) if kind
                    else p.chromium.launch())
        except Exception:
            continue
    raise BuildError("no Chromium/Edge available for PDF")


def _print_pdf(html_path: Path, raw: Path, browser: str | None) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise BuildError("playwright required for PDF") from e
    with sync_playwright() as p:
        launched = _launch(p, browser)
        page = launched.new_page(viewport={"width": 1280, "height": 900})
        page.goto(html_path.resolve().as_uri(), wait_until="load")
        try:
            page.evaluate("() => document.fonts.ready.then(() => true)")
        except Exception:
            pass
        page.emulate_media(media="print")
        page.pdf(path=str(raw), format="A4", print_background=True,
                 prefer_css_page_size=True, margin={"top": "0", "bottom": "0",
                                                    "left": "0", "right": "0"})
        launched.close()


def _destinations(doc, anchors: list[str]) -> dict[str, int]:
    """Zero-based page per anchor, read from the link annotations Chromium
    wrote for the in-book cross references (its target page is 0-based)."""
    want = set(anchors)
    found: dict[str, int] = {}
    for pno in range(doc.page_count):
        if want <= set(found):
            break
        for link in doc[pno].get_links():
            name, page = link.get("nameddest"), link.get("page")
            if name in want and isinstance(page, int) and 0 <= page < doc.page_count:
                found.setdefault(name, page)
    return found


def measure(html_path: Path, anchors: list[str],
            browser: str | None = None) -> dict[str, int]:
    """Print the book once only to learn which sheet each anchor landed on.

    The index needs this before the real print: a headword's page cannot be
    stamped as ink after the fact the way a contents row can, because dozens of
    rows share one anchor and print identical lines. So the numbers are measured
    here, written into the slots the HTML already reserves, and the book is
    printed again with them in place.
    """
    probe = html_path.with_name(html_path.stem + ".probe.pdf")
    _print_pdf(html_path, probe, browser)
    doc = fitz.open(probe)
    try:
        found = _destinations(doc, anchors)
    finally:
        doc.close()
        probe.unlink(missing_ok=True)
    missing = sorted({a for a in anchors if a not in found})
    if missing:
        raise BuildError("pdf: measuring print has no destination for "
                         f"{missing[:8]}")
    return found


def folio_drift(dest: dict[str, int], folios: dict[str, int]) -> dict[str, tuple]:
    """Index anchors whose printed folio no longer matches where the unit lands.

    `dest` is 0-based from this print, `folios` the 1-based numbers written into
    the rows after the measuring print. Empty means the layout held: a row whose
    reserved slot turned out too narrow would repage the index *after* every
    number in it was measured.
    """
    return {a: (dest[a] + 1, got) for a, got in folios.items()
            if dest[a] + 1 != got}


def _fit(text: str, width: float, size: float, width_of) -> str:
    if width_of(text) <= width:
        return text
    trimmed = text
    while trimmed and width_of(trimmed + "…") > width:
        trimmed = trimmed[:-1]
    return (trimmed + "…") if trimmed else ""


class _Head:
    """Running-head/folio ink: Helvetica for digits, a local system font for
    CJK. Widths come from the real face, so nothing is silently clipped."""

    def __init__(self, fontfile: str | None):
        self.fontfile = fontfile
        self.face = None
        if fontfile:
            try:
                self.face = fitz.Font(fontfile=fontfile)
            except Exception:
                self.fontfile = None

    def width(self, text: str, size: float) -> float:
        if self.face:
            return self.face.text_length(text, fontsize=size)
        return fitz.get_text_length(text, fontname="helv", fontsize=size)

    def draw(self, page, x: float, y: float, text: str, size: float,
             color: tuple) -> None:
        if self.face:
            page.insert_text((x, y), text, fontsize=size, fontname="yuyu-head",
                             fontfile=self.fontfile, color=color)
        else:
            page.insert_text((x, y), text.encode("latin-1", "ignore").decode(),
                             fontsize=size, fontname="helv", color=color)


def _folio(head: _Head, page, n: int, total: int) -> None:
    """Centred footer folio: n / total, flanked by short hairlines."""
    text, size = f"{n} / {total}", 8.2
    rect = page.rect
    w = head.width(text, size)
    cx, y = rect.width / 2, rect.height - 26
    head.draw(page, cx - w / 2, y, text, size, INK)
    shape = page.new_shape()
    shape.draw_line((cx - w / 2 - 26, y - 3), (cx - w / 2 - 9, y - 3))
    shape.draw_line((cx + w / 2 + 9, y - 3), (cx + w / 2 + 26, y - 3))
    shape.finish(color=RULE, width=0.5)
    shape.commit()


def _running_head(head: _Head, page, text: str, side: str) -> None:
    size = 8.0
    rect = page.rect
    text = _fit(text, (rect.width - 2 * MARGIN) / 2, size,
                lambda t: head.width(t, size))
    if not text:
        return
    w = head.width(text, size)
    x = MARGIN if side == "left" else rect.width - MARGIN - w
    head.draw(page, x, 40, text, size, INK)
    shape = page.new_shape()
    shape.draw_line((MARGIN, 46), (rect.width - MARGIN, 46))
    shape.finish(color=RULE, width=0.5)
    shape.commit()


def build_pdf(html_path: Path, meta: dict, browser: str | None = None,
              folios: dict[str, int] | None = None) -> Path:
    raw = html_path.with_name(html_path.stem + ".raw.pdf")
    out = html_path.with_suffix(".pdf")
    _print_pdf(html_path, raw, browser)
    doc = fitz.open(raw)
    n = doc.page_count

    anchors = [a for (_lvl, _t, a) in meta["outline"]]
    anchors += list(meta["toc_rows"]) + ["front"]
    anchors += sorted({r["anchor"] for r in meta.get("index_rows", ())})
    dest = _destinations(doc, anchors)
    missing = sorted({a for a in anchors if a not in dest})
    if missing:
        doc.close()
        raise BuildError(f"pdf: no destination found for {missing[:8]}")

    # the index folios were measured on the previous print and written into the
    # rows; a number that has moved means the reserved slot changed the column
    # layout after all, and every folio in the book is now suspect
    if folios:
        moved = folio_drift(dest, folios)
        if moved:
            doc.close()
            raise BuildError(
                f"pdf: {len(moved)} index folio(s) moved between the measuring "
                f"print and this one ({list(moved.items())[:4]}) — a row must "
                "reserve the width its number needs")

    doc.set_toc([[lvl, label, dest[a] + 1]
                 for lvl, label, a in meta["outline"]])

    fontfile = next((f for f in CJK_FONTS if Path(f).exists()), None)
    if fontfile is None and meta.get("lang") == "zh":
        doc.close()
        raise BuildError(
            "pdf: no CJK face available, so the running heads and folios "
            f"would lose every Chinese glyph (searched: {', '.join(CJK_FONTS)})")
    head = _Head(fontfile)
    book = meta["title"]
    starts = sorted((dest[a], label) for a, label in meta["heads"])

    def head_for(pno: int) -> str:
        cur = ""
        for page_start, label in starts:
            if page_start <= pno:
                cur = label
            else:
                break
        return cur

    first_body = dest["front"]
    for pno in range(1, n):                     # the cover stays clean
        page = doc[pno]
        _folio(head, page, pno + 1, n)
        if pno < first_body:
            continue
        if pno % 2 == 0:                        # recto: chapter, outer edge
            _running_head(head, page, head_for(pno) or book, "right")
        else:                                   # verso: book title
            _running_head(head, page, book, "left")

    rows = set(meta["toc_rows"])
    # the contents is the last section before the body, so its first page is
    # the last match for the heading title; rows then run to that page's end
    hits = [pno for pno in range(dest["front"])
            if doc[pno].search_for(meta["toc_title"])]
    if not hits:
        doc.close()
        raise BuildError("pdf: contents pages not found")
    # every contents row is a full-width flex link, so a narrow rect with the
    # same destination (a compass chip) can never be mistaken for one
    min_row = doc[0].rect.width * 0.5
    best: dict[str, tuple[int, fitz.Rect]] = {}
    for pno in range(hits[-1], dest["front"]):
        for link in doc[pno].get_links():
            anchor = link.get("nameddest")
            if anchor not in rows:
                continue
            r = fitz.Rect(link["from"])
            if r.width < min_row:
                continue
            # a row pushed to the next page leaves a clipped sliver behind;
            # the row actually printed is the tallest fragment
            if anchor not in best or r.height > best[anchor][1].height:
                best[anchor] = (pno, r)
    for anchor, (pno, r) in best.items():
        label = str(dest[anchor] + 1)
        w = fitz.get_text_length(label, fontname="helv", fontsize=8.2)
        doc[pno].insert_text((r.x1 - w, r.y1 - 7), label, fontsize=8.2,
                             fontname="helv", color=(0.36, 0.32, 0.24))
    if len(best) < len(rows):
        missed = sorted(rows - set(best))
        doc.close()
        raise BuildError(f"pdf: stamped only {len(best)} of {len(rows)} "
                         f"contents rows (missing {missed[:8]})")

    holes = empty_sheets(doc)
    if holes:
        doc.close()
        raise BuildError(
            f"pdf: {len(holes)} sheet(s) carry nothing but a running head and a "
            f"folio (pages {holes[:8]}{'…' if len(holes) > 8 else ''}) — a unit "
            "must close on the page it ends on")

    doc.set_metadata({
        "title": meta["title"], "author": meta["author"],
        "subject": meta.get("subtitle", ""),
        "keywords": meta.get("keywords", ""),
        "creator": "yuyu-book", "producer": "yuyu-book"})
    doc.subset_fonts()                    # the running-head face ships once
    try:
        doc.save(out, garbage=3, deflate=True)
    except Exception as exc:
        # Windows refuses to replace a PDF that is open in a viewer or held by
        # another process; the raw print file stays behind for a re-run.
        doc.close()
        raise BuildError(
            f"pdf: cannot replace {out.name}: {exc}. Close it in any viewer "
            f"or checker, then re-run the build.") from exc
    doc.close()
    raw.unlink(missing_ok=True)
    return out
