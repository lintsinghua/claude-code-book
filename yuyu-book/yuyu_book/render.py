"""Markdown -> HTML rendering pipeline for one unit of the book.

Pipeline: synthesize H1 -> python-markdown (toc/codehilite/extra) ->
callout classify -> external-link footnotes -> table wrap -> mermaid
figures -> id prefix -> cross-ref autolink (inserted after prefix so the
global anchors stay unprefixed) -> plain-layer marks -> heading collect ->
section tier chips.
"""
from __future__ import annotations

import html
import re
import unicodedata

import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.codehilite import CodeHiliteExtension

from .core import BuildError, Unit
from .style import ink_mark, knot
from . import pages, plain

# ------------------------------------------------------------ callouts ----

CALLOUT_LABELS: dict[str, str] = {
    "最佳实践": "tip", "正确做法": "tip", "推荐做法": "tip",
    "反模式警告": "warning", "危险": "warning", "注意": "warning",
    "交叉引用": "info", "交叉引用提示": "info",
    "设计洞察": "concept", "原理": "concept",
    "best practice": "tip", "correct approach": "tip",
    "anti-pattern warning": "warning", "warning": "warning",
    "cross-reference": "info", "extended reflection": "info",
    "practical application scenarios": "info",
    "memories that should be saved": "tip",
    "memories that should not be saved": "warning",
    "design insight": "concept",
}
_LEAD_LABEL_RE = re.compile(
    r"<blockquote>\s*<p>\s*<strong>([^<]+?)\s*[：:]\s*</strong>")


def classify_callouts(doc: str, lang: str) -> str:
    def repl(m):
        raw = m.group(1).strip()
        key = re.sub(r"\s*[（(].*?[)）]\s*", "", raw).lower()
        ctype = CALLOUT_LABELS.get(key)
        if ctype is None:
            ctype = "note" if re.match(r"[A-Z]?[\w ]{2,40}$", raw) and \
                raw.lower() in {"learning objectives", "reference answer",
                                "reference answers", "reference answer hints"} \
                else None
            if ctype is None:
                return m.group(0)
        icon = ink_mark(ctype)
        colon = pages.COLON[lang]
        # balanced: the original paragraph's </p> closes callout-body
        return (f'<blockquote class="callout callout-{ctype}">'
                f'<p class="callout-tag">'
                f'<span class="callout-icon" aria-hidden="true">{icon}</span>'
                f'<strong>{html.escape(raw)}{colon}</strong></p>'
                f'<p class="callout-body">')
    return _LEAD_LABEL_RE.sub(repl, doc)


_HR_RE = re.compile(r"<hr\s*/>")


def ink_rules(doc: str) -> str:
    """A `---` in the manuscript is a scene change. Typeset as a drawn coupling
    between two hairlines instead of a diamond out of the font."""
    return _HR_RE.sub(f'<div class="hr-rule" aria-hidden="true">{knot()}</div>',
                      doc)


# --------------------------------------------------------------- links ----

_EXT_LINK_RE = re.compile(r'<a href="(https?://[^"]+)"(\s[^>]*)?>(.*?)</a>', re.S)


def process_links(doc: str, external: list[str]) -> str:
    """External links get a superscript footnote marker; every chapter ends
    with the full URL list so the printed book keeps all references."""
    counter: dict[str, int] = {}

    def repl(m):
        url, attrs, label = m.group(1), m.group(2) or "", m.group(3)
        if "class=" in attrs or 'rel="' in attrs or "<a " in label:
            return m.group(0)
        if url not in counter:
            external.append(url)
            counter[url] = len(external)
        num = counter[url]
        return (f'<a class="ext" href="{url}" rel="noopener"{attrs}>{label}</a>'
                f'<sup class="fnum"><a href="#fn-{num}" id="fnref-{num}">[{num}]</a></sup>')
    return _EXT_LINK_RE.sub(repl, doc)


def footnotes_html(external: list[str], lang: str) -> str:
    if not external:
        return ""
    # the list closes whichever unit it sits under — the foreword and the
    # appendices cite too, and are not chapters
    title = "引用链接" if lang == "zh" else "Cited links"
    items = "".join(
        f'<li id="fn-{i}"><a class="fn-url" href="{html.escape(u, True)}" '
        f'rel="noopener">{html.escape(u)}</a> '
        f'<a class="backref" href="#fnref-{i}" aria-label="back">↩</a></li>'
        for i, u in enumerate(external, 1))
    return (f'<aside class="chapter-notes"><h4 class="notes-title">{title}</h4>'
            f'<ol class="notes-list">{items}</ol></aside>')


# --------------------------------------------------------------- tables ---

_TABLE_RE = re.compile(r"<table>.*?</table>", re.S)


def wrap_tables(doc: str) -> str:
    def repl(m):
        t = m.group(0)
        cols = t.count("<th") or t.count("<td") or 1
        return f'<div class="table-scroll" data-cols="{cols}" tabindex="0">{t}</div>'
    return _TABLE_RE.sub(repl, doc)


# ------------------------------------------------------------- name breaks --

_LONG_RUN = re.compile(r"\S{12,}")
_BREAK_AFTER = re.compile(r"[_/]+")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_NAME_BREAK_SKIP = {"svg", "style", "script", "textarea", "pre",
                    "h1", "h2", "h3", "h4", "h5", "h6"}


def _break_offsets(run: str) -> list[int]:
    """Character indices inside `run` where a line may break without damage."""
    cuts = {m.end() for m in _BREAK_AFTER.finditer(run)}
    cuts |= {m.start() for m in _CAMEL.finditer(run)}
    return sorted(c for c in cuts if 0 < c < len(run))


def soften_long_names(doc: str) -> str:
    """Give `FLAG_NAME_WITH_UNDERSCORES`, `skipDangerousMode…` and
    `~/.claude/settings.json` a place to break.

    Justified prose stretches badly when the next token cannot be cut: at
    desktop width 56 distinct inline tokens took more than 30% of a line on
    their own, and `getFeatureValue_CACHED_MAY_BE_STALE` filled 96% of a
    390px line. `overflow-wrap` does not create a *preferred* break and does
    not feed min-content width either, so it fixes neither the rivers on
    screen nor the table that ran past the A4 page box; an explicit `<wbr>`
    does, and is only used when the name genuinely cannot fit.

    Only runs of twelve characters or more are even examined, and a run is
    left alone if it holds no separator or case boundary, so ordinary English
    words are never cut. Entities are copied through untouched -- the offsets
    are computed against the source text, and `&amp;` is not an identifier.
    """
    def repl(m):
        run = m.group(0)
        if "&" in run:
            return run
        cuts = _break_offsets(run)
        if not cuts:
            return run
        out, prev = [], 0
        for c in cuts:
            out.append(run[prev:c])
            out.append("<wbr>")
            prev = c
        out.append(run[prev:])
        return "".join(out)

    out = []
    for kind, text, blocked in iter_doc(doc, _NAME_BREAK_SKIP):
        out.append(text if kind == "tag" or blocked else _LONG_RUN.sub(repl, text))
    return "".join(out)


# ------------------------------------------------------------- unit close --

_CLOSER_TAGS = {"p", "ul", "ol", "aside", "blockquote", "div"}
_CLOSER_HEAVY = ("<table", "<figure", "<svg")


def glue_closer(doc: str, ornament: str) -> str:
    """Wrap the block a unit ends on together with the ruts that close it.

    Chromium honours `break-inside: avoid` but not `break-before: avoid`, so a
    rut that no longer fitted on the last page landed alone at the top of a
    fresh sheet -- and since the next unit opens with a forced break, that sheet
    stayed empty: three of them in the Chinese PDF, two in the English. Glued to
    the block it closes, the pair moves together and the page ends short instead
    of vanishing.

    Only a light tail is wrapped: a plate or a wide table is its own
    keep-together unit already, and anything tall enough to be one of those
    cannot be moved at all, so gluing to it would only buy a hole.
    """
    stack: list[tuple[str, int]] = []
    last: tuple[str, int, int] | None = None
    for m in _TAG_RE.finditer(doc):
        name = m.group(2).lower()
        if name in _VOID_TAGS or m.group(3):
            continue
        if m.group(1):
            if not stack or name not in [n for n, _ in stack]:
                continue
            while stack[-1][0] != name:
                stack.pop()
            opened, start = stack.pop()
            if not stack:
                last = (opened, start, m.end())
        else:
            stack.append((name, m.start()))
    if last is None or doc[last[2]:].strip():
        return doc + ornament
    name, start, end = last
    block = doc[start:end]
    if name not in _CLOSER_TAGS or any(t in block for t in _CLOSER_HEAVY):
        return doc + ornament
    if len(re.sub(r"<[^>]+>", "", block)) > 900 or block.count("\n") > 30:
        return doc + ornament
    return doc[:start] + f'<div class="ch-close">{block}{ornament}</div>' + doc[end:]


# ------------------------------------------------------------- code langs -

_CODE_DIV_RE = re.compile(r'<div class="codehilite">')
_CODE_PRE_RE = re.compile(r'(<div class="codehilite"[^>]*>)<pre>')


def stamp_code_langs(doc: str, langs: list[str], file: str) -> str:
    """Label each highlighted block with the language it was fenced as, so
    the stylesheet can print a corner chip. Position-matched, so a drift
    between source fences and rendered blocks must fail loudly.

    The pass also gives each block's scroller a tab stop: a long line runs
    past the column and the block, unlike a link, is otherwise unreachable
    without a mouse."""
    left = list(langs)
    found = len(_CODE_DIV_RE.findall(doc))
    if found != len(left):
        raise BuildError(f"{file}: {found} rendered code blocks but "
                         f"{len(left)} source fences")

    def repl(m):
        lang = left.pop(0)
        if not lang:
            return m.group(0)
        return f'<div class="codehilite" data-lang="{html.escape(lang)}">'
    doc = _CODE_DIV_RE.sub(repl, doc)
    return _CODE_PRE_RE.sub(r'\1<pre tabindex="0">', doc)


# -------------------------------------------------------------- mermaid ---

_MM_PH_RE = re.compile(r"<p>@@MM:([0-9a-f]{12})@@</p>|@@MM:([0-9a-f]{12})@@")

# Mermaid lays a plate out in its own units and draws its labels at 13px,
# so a 1500-unit map inside the 635px reading column drops those labels to
# 5px — a texture, not a diagram. Hold the genuinely oversized plates above
# a readable scale and let .diagram-frame scroll sideways (2600px caps the
# drag at ~4 screens for the biggest dependency maps). @media print drops
# the floor again so the PDF keeps the whole plate on one A4 page.
_FLOOR_FROM = 1150.0
_FLOOR_RATIO = 0.85
_FLOOR_CAP = 2600.0
_VIEWBOX_RE = re.compile(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"')
_SVG_ROOT_RE = re.compile(r"<svg\b[^>]*>")


def floor_wide_svg(svg: str) -> tuple[str, str | None]:
    """Return (svg with a min-width floor, that floor in px or None).

    Only rendered plates are floored: --mermaid=source hands over a <pre>,
    which already wraps.
    """
    tag = _SVG_ROOT_RE.match(svg)
    if not tag:
        return svg, None
    head = tag.group(0)
    vb = _VIEWBOX_RE.search(head)
    if not vb:
        return svg, None
    vw = float(vb.group(1))
    if vw < _FLOOR_FROM:
        return svg, None
    floor = f"{round(min(vw * _FLOOR_RATIO, _FLOOR_CAP))}px"
    if " style=" in head:
        new = head.replace('style="', f'style="min-width:{floor};', 1)
    else:
        new = head[:4] + f' style="min-width:{floor};"' + head[4:]
    return svg[:tag.start()] + new + svg[tag.end():], floor


# A plate's own labels are what has to survive the page. An A4 text block here
# is 665x926 CSS px, and the 150mm default cap is a compromise for wide plates;
# a tall one — a stacked layer map, a long decision chain — is shrunk by it into
# a 4pt texture even though the column has room below it. So a plate that could
# reach a legible scale by standing taller is given the room it needs, up to a
# full column less its caption.
_PRINT_COL_PX = 665.0
_PRINT_CAP_PX = 567.0        # 150mm, style.py's default
_PRINT_MAX_PX = 926.0        # 245mm
_LAND_COL_PX = 993.0         # A4 landscape text block: 297mm - 2x17mm
_LAND_MAX_PX = 567.0         # 150mm — the sheet's own cap, see mermaid_figure:
                             # 170mm of landscape block minus the caption row
_MIN_PLATE_PT = 6.0          # what a plate must reach to stay portrait
_LAND_MIN_PLATE_PT = 5.0     # a turned sheet is held to a slightly lower bar:
                             # it costs a whole sheet, but reads at arm's length
_PX_PER_MM = 96 / 25.4


def _plate_metrics(svg: str) -> tuple[float, float, float] | None:
    tag = _SVG_ROOT_RE.match(svg)
    if not tag:
        return None
    vb = _VIEWBOX_RE.search(tag.group(0))
    if not vb:
        return None
    fonts = [float(x) for x in re.findall(r"font-size:\s*([0-9.]+)px", svg)]
    return (float(vb.group(1)), float(vb.group(2)),
            max(fonts) if fonts else 16.0)


def plate_cap(svg: str) -> str | None:
    """Print height cap in mm for this plate, or None for the default."""
    m = _plate_metrics(svg)
    if not m:
        return None
    w, h, base = m
    need = _MIN_PLATE_PT / (base * 0.75)      # 1px = 0.75pt
    if w * need <= _PRINT_COL_PX and _PRINT_CAP_PX < h * need <= _PRINT_MAX_PX:
        return f"{h * need / _PX_PER_MM:.0f}mm"
    return None


def plate_landscape(svg: str) -> bool:
    """True when turning the sheet is what makes the plate readable.

    A wide band is bound by the column, not by the cap, so standing taller
    cannot save it; a landscape sheet buys 50% more width. That buys a whole
    mostly-empty sheet, though, so it is spent only where it lands the plate
    above a readable size rather than merely moving the unreadability around."""
    m = _plate_metrics(svg)
    if not m:
        return False
    w, h, base = m
    here = base * min(_PRINT_COL_PX / w, _PRINT_CAP_PX / h) * 0.75
    turned = base * min(_LAND_COL_PX / w, _LAND_MAX_PX / h) * 0.75
    return here < _MIN_PLATE_PT and turned >= _LAND_MIN_PLATE_PT \
        and turned > here * 1.25


def mermaid_figure(uid: str, svg: str, fig_no: str, caption: str,
                   lang: str) -> str:
    cap_word = "图" if lang == "zh" else "Figure"
    svg, floor = floor_wide_svg(svg)
    classes = ["diagram"]
    if floor:
        classes.append("wide")
    land = plate_landscape(svg)
    if land:
        classes.append("landscape")
    hint = (f'<span class="fig-hint">{pages.ui("plate_wide", lang)}</span>'
            if floor else "")
    # A turned plate takes the sheet's default cap: the landscape block is
    # 170mm tall, so a cap of its own would push the caption onto a second sheet.
    cap = None if land else plate_cap(svg)
    style = f' style="--plate-cap:{cap}"' if cap else ""
    return (f'<figure class="{" ".join(classes)}" id="fig-{uid}"{style}>'
            f'<div class="diagram-frame">{svg}</div>'
            f'<figcaption><span class="fig-no">{cap_word} {fig_no}</span>'
            f'<span class="fig-cap">{caption}</span>{hint}</figcaption></figure>')


# ------------------------------------------------------------ autolink --

_SKIP_TAGS = {"a", "code", "pre", "h1", "svg", "style", "sup", "figure"}
_CURL_SKIP = {"code", "pre", "svg", "style", "kbd", "samp", "var", "textarea"}
_VOID_TAGS = ("br", "img", "hr", "meta", "input", "wbr")
_TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)[^>]*?(/)?>")


def iter_doc(doc: str, skip_tags: set[str]):
    """Walk rendered HTML and yield (kind, text, blocked) chunks, 'tag' being
    markup copied through verbatim. `blocked` says an element in skip_tags
    still owns this run, so prose annotators never reach into code, links,
    plates or headings. Closing tags whose partner never opened (the mermaid
    SVGs are full of them) pop back to the matching level instead of
    corrupting the stack."""
    stack: list[str] = []
    pos = 0
    while True:
        m = _TAG_RE.search(doc, pos)
        seg_end = m.start() if m else len(doc)
        blocked = any(name in skip_tags for name in stack)
        if seg_end > pos:
            yield "text", doc[pos:seg_end], blocked
        if not m:
            return
        closing, name, selfclose = m.group(1), m.group(2).lower(), m.group(3)
        if name in _VOID_TAGS or selfclose:
            pass
        elif closing:
            if name in stack:
                while stack and stack[-1] != name:
                    stack.pop()
                stack.pop()
        else:
            stack.append(name)
        yield "tag", m.group(0), blocked
        pos = m.end()


class RefLinker:
    """Wrap bare 第N章/Chapter N/附录X/Appendix X mentions in <a class=xref>.
    Skips subtrees of block/inline anchors; one link per target per text run."""

    def __init__(self, mapping: dict[str, str], current: str, lang: str):
        if lang == "zh":
            self.rx = re.compile(r"第\s*([1-9]|1[0-5])\s*章|附录\s*([A-D])")
        else:
            self.rx = re.compile(
                r"\bChapter\s+(\d{1,2})\b|\bAppendix\s+([A-D])\b")
        self.map = mapping
        self.current = current

    def transform(self, doc: str) -> str:
        out = []
        for kind, text, blocked in iter_doc(doc, _SKIP_TAGS):
            out.append(text if kind == "tag" or blocked
                       else self._link_text(text))
        return "".join(out)

    def _link_text(self, text: str) -> str:
        used: set[str] = set()
        out, last = [], 0
        for m in self.rx.finditer(text):
            g1, g2 = m.group(1), m.group(2)
            aid = f"ch{int(g1):02d}" if g1 else f"apx{g2.lower()}"
            anchor = self.map.get(aid)
            if not anchor or aid == self.current or aid in used:
                continue
            used.add(aid)
            out.append(text[last:m.start()])
            out.append(f'<a class="xref" href="#{anchor}">{m.group(0)}</a>')
            last = m.end()
        out.append(text[last:])
        return "".join(out)


# ---------------------------------------------------------------- ids -----

_STRAY_ANGLE = re.compile(r"<[A-Za-z][A-Za-z0-9_]*"
                          r"(?:[,\s]+[A-Za-z0-9_=?<>.'’]+)+>")


def escape_stray_angles(md_text: str) -> str:
    """Type-parameter notation like Tool<I,O,P> in prose is invalid HTML and
    would be swallowed by browsers; fence/code spans are left untouched."""
    lines, fence = [], None
    for line in md_text.split("\n"):
        m = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if m:
            token, info = m.group(1), m.group(2).strip()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not info:
                fence = None
            lines.append(line)
            continue
        if fence is not None:
            lines.append(line)
            continue
        parts = re.split(r"(`+[^`]*`+)", line)
        for i, seg in enumerate(parts):
            if i % 2 == 0 and "<" in seg:
                parts[i] = _STRAY_ANGLE.sub(
                    lambda mm: mm.group(0).replace("<", "&lt;").replace(
                        ">", "&gt;"), seg)
        lines.append("".join(parts))
    return "\n".join(lines)

def prefix_ids(doc: str, pfx: str) -> str:
    doc = re.sub(rf'\bid="(?!mm-|fig-)((?!{pfx}-)[^"]+)"',
                 rf'id="{pfx}-\1"', doc)
    doc = re.sub(r'href="#(?!fn-)((?!{0}-)[^"]+)"'.format(pfx),
                 rf'href="#{pfx}-\1"', doc)
    doc = doc.replace('href="#fn-', f'href="#{pfx}-fn-')
    return doc


# ------------------------------------------------------------ slugify ----

def book_slug(value: str, separator: str = "-") -> str:
    s = unicodedata.normalize("NFKC", value).strip().lower()
    s = re.sub(r"[`*_~\[\]()（）「」：:，,。.；;/\\]", "", s)
    s = re.sub(r"[^\w一-鿿-]", " ", s)
    s = re.sub(r"\s+", separator, s.strip())
    return s or "section"


# ------------------------------------------------------------- render ----

def build_md():
    return markdown.Markdown(extensions=[
        "extra", "sane_lists",
        TocExtension(slugify=book_slug, permalink=False),
        CodeHiliteExtension(language="text", guess_lang=False, linenums=False),
    ])


def curlify(doc: str) -> str:
    """Straight double quotes → typographic pairs in prose, never in code."""
    state = [0]

    def flip(_m):
        state[0] += 1
        return "“" if state[0] % 2 else "”"

    out, skip = [], None
    for piece in re.split(r"(<[^>]+>)", doc):
        if piece.startswith("<") and piece.endswith(">"):
            m = re.match(r"</?([a-zA-Z][\w-]*)", piece)
            name = m.group(1).lower() if m else ""
            if piece.startswith("</"):
                if name == skip:
                    skip = None
            elif skip is None and name in _CURL_SKIP:
                skip = name
            out.append(piece)
            continue
        out.append(re.sub(r'"', flip, piece) if not skip else piece)
    return "".join(out)


def render_unit(unit: Unit, mapping: dict[str, str], *,
                diagrams: dict[str, tuple[str, str]],
                autolink: bool = True, gloss=None,
                tiers: list[str] | None = None) -> dict:
    body = re.sub(r"\A[ \t]*>[ \t]*(English|中文)[^\n]*\n+", "", unit.md)
    if unit.kind == "front":
        h1 = f"# {unit.title}"
    elif unit.lang == "zh":
        h1 = f"# {unit.no}　{unit.title}"
    else:
        h1 = f"# {unit.no}: {unit.title}"

    md = build_md()
    doc = curlify(md.convert(escape_stray_angles(h1 + "\n\n" + body)))
    doc = stamp_code_langs(doc, unit.code_langs, unit.path)

    external: list[str] = []
    doc = classify_callouts(doc, unit.lang)
    doc = ink_rules(doc)
    doc = process_links(doc, external)
    doc += footnotes_html(external, unit.lang)
    doc = wrap_tables(doc)

    ch_num = re.sub(r"\D", "", unit.no) or ""
    apx_letter = unit.id[-1].upper()
    fig_seq = [0]

    def fig_no():
        fig_seq[0] += 1
        if unit.kind == "chapter":
            return f"{int(ch_num)}-{fig_seq[0]}"
        if unit.kind == "front":
            # front matter has no number to inherit; plain digits read better
            # than the "T" that unit.id[-1] would give 前言/front
            return f"{fig_seq[0]}"
        return f"{apx_letter}{fig_seq[0]}"

    def mm_repl(m):
        uid = m.group(1) or m.group(2)
        entry = diagrams.get(uid)
        if entry is None:
            return f'<div class="mermaid-missing">缺失图 {uid}</div>'
        caption, svg = entry
        return mermaid_figure(uid, svg, fig_no(), caption, unit.lang)
    doc = _MM_PH_RE.sub(mm_repl, doc)

    doc = prefix_ids(doc, unit.id)
    if autolink:
        doc = RefLinker(mapping, unit.id, unit.lang).transform(doc)

    new_terms: list[dict] = []
    if gloss is not None and gloss.active:
        doc, new_terms = gloss.apply(doc, tiers, who=unit.path)

    headings = [{"level": int(lvl), "id": hid,
                 "text": re.sub(r"<[^>]+>", "", txt)}
                for lvl, hid, txt in re.findall(
                    r'<h([234]) id="([^"]+)">(.*?)</h\1>', doc)]
    # stamped after the outline is collected: the chip belongs to the reader,
    # not to the section's name
    doc = plain.stamp_tiers(doc, tiers or [], unit.lang, who=unit.id)
    # the break points go in once the whole book is assembled, so the front and
    # back matter get them too — see build.py
    return {"unit": unit, "html": doc, "headings": headings,
            "external": external, "n_diagrams": fig_seq[0],
            "new_terms": new_terms}
