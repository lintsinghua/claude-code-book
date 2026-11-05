"""Front/back-matter page builders: cover, imprint, revisions, reading
guide, compass cards, part dividers, TOC, source registry, subject index."""
from __future__ import annotations

import html
import re

from .core import BuildError, INDEX_CN_LETTER  # noqa: E402
from .plain import ANALOGY_TAG, WHY_TAG  # noqa: E402

_LABELS = {
    "cover_kicker": {"zh": "Agent Harness Engineering",
                     "en": "Agent Harness Engineering"},
    "imprint": {"zh": "版本与许可", "en": "Imprint"},
    "revisions": {"zh": "版本与修订", "en": "Revision history"},
    "how": {"zh": "阅读路线", "en": "How to read"},
    "toc": {"zh": "目录", "en": "Contents"},
    "author": {"zh": "著", "en": "Author"},
    "edition": {"zh": "版本", "en": "Edition"},
    "date": {"zh": "日期", "en": "Date"},
    "license": {"zh": "许可", "en": "License"},
    "notice": {"zh": "声明", "en": "Notice"},
    "notice_body": {
        "zh": "Claude Code 为 Anthropic 产品；本书是独立的技术分析作品，并非官方出版物。"
              "阅读时请区分源码可确认的行为、架构推演与教学示例；功能标志与工具可用性取决于构建和运行时配置。",
        "en": "Claude Code is an Anthropic product; this book is an independent technical "
             "analysis, not an official publication. Distinguish observed implementation, "
             "architectural interpretation, and teaching examples; flags and tool "
             "availability depend on build and runtime configuration."},
    "sources_page": {"zh": "来源与许可", "en": "Sources & Licenses"},
    "sources_note": {
        "zh": "本书不转载来源正文；GitHub 参考钉住 tag/commit，社区材料标注访问日期且非规范。",
        "en": "The book does not republish source texts; GitHub references are pinned to "
             "tags/commits, community material carries access dates and is non-normative."},
    "index_page": {"zh": "主题索引", "en": "Subject Index"},
    "principles_page": {"zh": "原理札记", "en": "Why It Works This Way"},
    "notes_page": {"zh": "按语集", "en": "The Keeper's Notes"},
    "notes_note": {
        "zh": "每一章都收在它自己的车辙上；车辙上方另有一句按语，出自一位"
              "赶了三十年驿路的老驿卒。他不解释术语，只回头看看刚走完的"
              "这段路。这一页把二十条按语照原路再走一遍，每条链回章末。",
        "en": "Every unit closes on its own wheel ruts, and above them stands "
             "one line by an old postman who has ridden this road for thirty "
             "years. He explains nothing; he only looks back over the leg "
             "just travelled. This page walks all twenty lines in order, each "
             "linked back to the ruts it sat on."},
    "principles_note": {
        "zh": "书里的核心术语各有一句白话定义和一个比方；这一页补上中间那层——"
              "它非这样不可的理由。理由一律取自正文自己的论证，条目排在提出它的那一章下面。",
        "en": "Every core term carries a plain definition and an everyday "
             "comparison; this page supplies the layer in between, the reason it "
             "has to be that way. Each reason is the book's own argument, filed "
             "under the chapter that makes it."},
    "why_tag": WHY_TAG,
    "analogy_tag": ANALOGY_TAG,
    "index_cn": {"zh": "中文", "en": "Chinese"},
    "index_cn_note": {
        "zh": "按译名首字的部首笔画排列；一个英文术语有多个译名时，每个译名单独立条。",
        "en": "Filed by the radical and stroke count of the first character; a "
              "term with several translations is filed under each of them."},
    "compass_q": {"zh": "本章问题", "en": "The question"},
    "compass_d": {"zh": "读完交付", "en": "What you get"},
    "compass_b": {"zh": "本章边界", "en": "Out of scope"},
    "compass_src": {"zh": "来源锚点", "en": "Source anchors"},
    "front": {"zh": "前言", "en": "Foreword"},
    "appendix": {"zh": "附录", "en": "Appendix"},
    "diagrams": {"zh": "全书图版", "en": "Plates in this book"},
    "plate_fallback": {"zh": "架构示意", "en": "Architecture sketch"},
    "plate_wide": {"zh": "可横向拖动", "en": "drag sideways"},
    "lead_tag": {"zh": "一句话讲明白", "en": "In plain words"},
    "lead_analogy": {"zh": "打个比方：", "en": "Think of it as: "},
    "new_terms": {"zh": "本章新词", "en": "New terms in this chapter"},
    "new_terms_front": {"zh": "开篇新词", "en": "New terms in the foreword"},
    "new_terms_appendix": {"zh": "本附录新词",
                           "en": "New terms in this appendix"},
    "new_terms_note": {
        "zh": "正文里带虚线的词都收在这里；其余术语见附录 D 术语表。",
        "en": "Every dashed term in the text is listed here; Appendix D covers "
             "the rest."},
    "tier_legend": {"zh": "阅读层级", "en": "Reading tiers"},
    "tier_hint": {
        "zh": "每个二级小节右上角标了层级：起步可先读，主干要读，进阶可以跳。"
              "术语首次出现带虚线，鼠标悬停或点按出白话注释。",
        "en": "Every section carries a level at its right: read Start first, "
             "Core is required, Advanced can wait. Dashed terms reveal a "
             "plain-language note on hover or tap."},
    "route_map": {"zh": "全书线路图", "en": "The Book's Route"},
    "route_map_lead": {
        "zh": "把全书想成一条路：前言套车出发，十五章是路上依次排开的驿站，"
              "附录是停在路边的岔线，随时可以折过去取个东西再回来。",
        "en": "Think of the book as one road: the foreword harnesses the team, "
             "the fifteen chapters are the stations set out along it, and the "
             "appendices are a siding you can turn into whenever you need "
             "something and come back."},
    "rm_key_wheel": {"zh": "轮：前言发车", "en": "Wheel: the ride starts here"},
    "rm_key_ring": {"zh": "圈：一章一站", "en": "Ring: one chapter per stop"},
    "rm_key_siding": {"zh": "虚线：附录是岔线", "en": "Dashed: the appendices, a siding"},
    "rm_side": {"zh": "支线", "en": "Siding"},
    "rm_why_front": {"zh": "上车前先读：这本书在讲什么、怎么讲。",
                     "en": "Read before you set off: what this book covers and how."},
    "rm_why_apx": {"zh": "随时折回去查：源码地图、工具清单、功能标志、术语表。",
                   "en": "Turn back any time: the source map, the tool inventory, "
                        "the flag list, the glossary."},
}


def ui(key: str, lang: str) -> str:
    return _LABELS[key][lang]


# the full-width colon is ours to choose, and the English book should not wear it
COLON = {"zh": "：", "en": ":"}

# the foreword is the one unit with no chapter number, so the book gives it the
# gutter number 00 -- the contents row and the route map's wheel both wear it
FRONT_NO = "00"


def esc(s: str) -> str:
    return html.escape(s, quote=False)


_NOTE_CODE = re.compile(r"`([^`]+)`")


def note(s: str) -> str:
    """A revision note, marked up: the notes quote the builder's own names, and
    a row of raw backticks around one reads as a typo in a typeset book."""
    out, prev = [], 0
    for m in _NOTE_CODE.finditer(s):
        out.append(esc(s[prev:m.start()]))
        out.append(f"<code>{esc(m.group(1))}</code>")
        prev = m.end()
    out.append(esc(s[prev:]))
    return "".join(out)


def cover(manifest: dict, lang: str) -> str:
    from .art import cover_plate
    from .style import wheel
    title = manifest["title"][lang]
    main, _, tail = title.partition("：")
    if main == title:
        main, _, tail = title.partition(":")
        tail = tail.strip()
    epigraph = manifest["epigraph"][lang]
    epi, _, epi_src = epigraph.rpartition("——")
    if not epi:
        epi, epi_src = epigraph, ""
    lic = manifest["license"]
    plate = cover_plate()
    # the plate carries a 30-spoke wheel of its own; a second one under the
    # title would be the same motif twice within a hand's width
    mark = "" if plate else wheel(26)
    src_line = (f'<span class="epi-src">——{esc(epi_src.strip())}</span>'
                if epi_src else "")
    seal = (f'<span class="cover-seal" aria-hidden="true">{esc(main.strip()[:2])}</span>'
            if lang == "zh" and main.strip() else "")
    return (f'<section class="front-page cover" id="cover">'
            f'<div class="cover-inner">{seal}'
            f'<p class="cover-kicker">{esc(ui("cover_kicker", lang))}</p>'
            f'<h1 class="book-title"><span class="bt-main">{esc(main.strip())}</span>'
            f'<span class="bt-tail">{esc(tail.strip())}</span></h1>'
            f'<div class="cover-rule"><i></i>{mark}<i></i></div>'
            f'{plate}'
            f'<p class="book-sub">{esc(manifest["subtitle"][lang])}</p>'
            f'<p class="book-epi">{esc(epi.strip())}{src_line}</p>'
            f'<div class="cover-foot">'
            f'<span class="book-author">{esc(manifest["author"])}</span>'
            f'<span class="cover-ver">v{esc(manifest["version"])} · '
            f'{esc(manifest["date"])} · <b>{esc(lic["name"])}</b></span>'
            f'</div></div></section>')


def imprint(manifest: dict, lang: str) -> str:
    lic = manifest["license"]
    rows = [
        (ui("author", lang), esc(manifest["author"])),
        (ui("edition", lang), f'v{esc(manifest["version"])}'),
        (ui("date", lang), esc(manifest["date"])),
        (ui("license", lang),
         f'<a class="ext" href="{lic["url"]}" rel="noopener">{esc(lic["name"])}</a>'),
    ]
    dl = "".join(f'<div class="ip-row"><dt>{k}</dt><dd>{v}</dd></div>'
                 for k, v in rows)
    return (f'<section class="front-page" id="imprint">'
            f'<h1 class="page-title">{esc(ui("imprint", lang))}</h1>'
            f'<dl class="imprint-list">{dl}</dl>'
            f'<h2 class="ip-notice-t">{esc(ui("notice", lang))}</h2>'
            f'<p class="ip-notice">{esc(ui("notice_body", lang))}</p></section>')


def revisions_page(entries: list[dict], lang: str) -> str:
    items = []
    for e in entries:
        lis = "".join(f"<li>{note(x)}</li>" for x in e.get(lang, []))
        items.append(f'<h2 class="rev-v">v{esc(e["version"])}'
                     f'<span class="rev-d">{esc(e["date"])}</span></h2><ul>{lis}</ul>')
    return (f'<section class="front-page" id="revisions">'
            f'<h1 class="page-title">{esc(ui("revisions", lang))}</h1>'
            f'{"".join(items)}</section>')


def how_to_read(manifest: dict, lang: str, paths: dict | None = None) -> str:
    cards = "".join(
        f'<div class="route-card"><h3>{esc(r["label"][lang])}</h3>'
        f'<p>{esc(r["body"][lang])}</p></div>'
        for r in manifest["start_reading"])
    parts = "".join(
        f'<li><a class="xref" href="#{p["units"][0]["id"]}">'
        f'{esc(p["no"][lang])} · {esc(p["title"][lang])}</a>'
        f'<span class="route-goal">{esc(p["goal"][lang])}</span></li>'
        for p in manifest["parts"])
    return (f'<section class="front-page" id="how-to-read">'
            f'<h1 class="page-title">{esc(ui("how", lang))}</h1>'
            f'<div class="route-grid">{cards}</div>'
            f'<ul class="route-parts">{parts}</ul>{tier_legend(paths, lang)}</section>')


def route_map_page(manifest: dict, lang: str, nos: dict[str, str]) -> str:
    """The whole book as one road, for the reader who wants to know how far it
    goes before opening it. The drawing is the ornament; the list under it is
    the thing itself, because the numbers written inside an `aria-hidden`
    picture are unreachable to a screen reader and carry no link."""
    from .style import itinerary, key_mark

    front = manifest["front"]["id"]
    front_stop = (front, nos.get(front, ""))
    side = [(a["id"], nos.get(a["id"], "")) for a in manifest["appendices"]]
    siding = f'{ui("appendix", lang)} · {ui("rm_side", lang)}'
    legs = [(f'{p["no"][lang]} · {p["title"][lang]}',
             [(u["id"], nos.get(u["id"], "")) for u in p["units"]])
            for p in manifest["parts"]]
    # the foreword is the wheel at the head of the road rather than a ring on
    # it: it is where the team harnesses up, not a station you travel to
    rows = [(front, ui("front", lang), [front_stop], ui("rm_why_front", lang))]
    rows += [(p["id"], head, stops, p["goal"][lang])
             for p, (head, stops) in zip(manifest["parts"], legs)]
    rows.append((side[0][0], siding, side, ui("rm_why_apx", lang)))

    def li(anchor: str, head: str, stops: list[tuple[str, str]], why: str) -> str:
        numbers = " ".join(n for _a, n in stops if n)
        return (f'<li><p class="rm-head"><a class="xref" href="#{anchor}">'
                f'{esc(head)}</a><span class="rm-nos">{esc(numbers)}</span></p>'
                f'<p class="rm-why">{esc(why)}</p></li>')

    keys = "".join(f'<li>{key_mark(kind)}{esc(ui(label, lang))}</li>'
                   for kind, label in (("wheel", "rm_key_wheel"),
                                       ("ring", "rm_key_ring"),
                                       ("siding", "rm_key_siding")))
    map_svg = itinerary("route",
                        [(esc(head), stops) for head, stops in legs]
                        + [(esc(siding), side)],
                        start_label=esc(nos.get(front, "")))
    return (f'<section class="front-page route-map" id="route-map">'
            f'<h1 class="page-title">{esc(ui("route_map", lang))}</h1>'
            f'<p class="rm-lead">{esc(ui("route_map_lead", lang))}</p>'
            f'{map_svg}'
            f'<ul class="rm-key">{keys}</ul>'
            f'<ul class="rm-legs">{"".join(li(*r) for r in rows)}</ul></section>')


def tier_legend(paths: dict | None, lang: str) -> str:
    """How many sections sit at each level, so a reader can size the shortcut."""
    if not paths:
        return ""
    from .plain import TIER_DESC, TIER_LABELS, TIER_ORDER

    counts = {t: sum(1 for tiers in paths.values()
                     for x in tiers if x == t) for t in TIER_ORDER}
    rows = "".join(
        f'<li class="tl-row"><span class="tier-chip t-{t}">'
        f'{esc(TIER_LABELS[t][lang])}</span>'
        f'<span class="tl-desc">{esc(TIER_DESC[t][lang])}</span>'
        f'<span class="tl-n tl-n-{t}">{counts[t]}</span></li>'
        for t in TIER_ORDER)
    return (f'<div class="tier-legend"><h2 class="page-sub">'
            f'{esc(ui("tier_legend", lang))}</h2>'
            f'<p class="tl-hint">{esc(ui("tier_hint", lang))}</p>'
            f'<ul class="tl-list">{rows}</ul></div>')


def lead_band(guide: dict, lang: str) -> str:
    """The one plain-language device that reads the same on paper and screen."""
    plain = (guide.get("plain") or {}).get(lang) or ""
    if not plain:
        return ""
    analogy = (guide.get("analogy") or {}).get(lang) or ""
    a = (f'<p class="lb-analogy"><span class="lb-a-tag">'
         f'{esc(ui("lead_analogy", lang))}</span>{esc(analogy)}</p>'
         if analogy else "")
    return (f'<div class="lead-band"><p class="lb-tag">'
            f'{esc(ui("lead_tag", lang))}</p>'
            f'<p class="lb-plain">{esc(plain)}</p>{a}</div>')


def new_terms_panel(hits: list[dict], lang: str, kind: str = "") -> str:
    """Paper has no hover, so the dashed terms a reader meets in this unit are
    restated here in document order — the marks and this list are the same
    set, which the build asserts."""
    if not hits:
        return ""
    title = ui("new_terms" if kind in ("", "chapter") else f"new_terms_{kind}",
               lang)
    rows = "".join(
        f'<li class="nt-row"><span class="nt-term">{esc(h["term"])}</span>'
        f'<span class="nt-plain">{esc(h["plain"])}</span></li>'
        for h in hits)
    return (f'<aside class="new-terms"><h4 class="nt-title">'
            f'{esc(title)}'
            f'<span class="nt-n">{len(hits)}</span></h4>'
            f'<p class="nt-note">{esc(ui("new_terms_note", lang))}</p>'
            f'<ul class="nt-list">{rows}</ul></aside>')


def compass(unit, guide: dict, sources: dict, lang: str) -> str:
    # the labels say 本章, which is true of a chapter only: the foreword opens
    # the whole book and the appendices are not chapters
    scope = {"front": "全书", "appendix": "本附录"}.get(getattr(unit, "kind", ""), "")

    def tag(label: str) -> str:
        text = ui(label, lang)
        return scope + text[2:] if scope and text.startswith("本章") else text

    cards = "".join(
        f'<div class="compass-card {key}">'
        f'<h4 class="cc-tag">{esc(tag(label))}</h4>'
        f'<p>{esc(guide[key][lang])}</p></div>'
        for key, label in (("question", "compass_q"),
                           ("deliverable", "compass_d"),
                           ("boundary", "compass_b")))
    chips = ""
    if guide.get("sources"):
        names = {sid: src_field(sources.get(sid, {}), "title", lang) or sid
                 for sid in guide["sources"]}
        chips = ('<p class="cc-src"><span class="cc-src-t">'
                 f'{esc(ui("compass_src", lang))}{COLON[lang]}</span>' +
                 "".join(
                     f'<a class="source-chip" href="#source-{sid}" '
                     f'title="{html.escape(names[sid], True)}">'
                     f'{esc(names[sid])}</a>'
                     for sid in guide["sources"]) + "</p>")
    return (f'<div class="compass" role="complementary">{cards}{chips}</div>')


def src_field(src: dict, key: str, lang: str) -> str:
    """Registry text in the reader's language. Anything annotated by us carries
    a `_<key>_en` mirror when the base text is Chinese; third-party names are as
    published, so a Chinese forum thread keeps the title it was posted under."""
    return str(src.get(f"{key}_{lang}") or src.get(key, ""))


def part_divider(part: dict, lang: str, idx: int,
                 rows: list[tuple[str, str, str]]) -> str:
    from .style import route_map, wheel
    from . import art
    items = "".join(
        f'<li><a class="xref" href="#{anchor}" data-no="{esc(no)}">'
        f'{esc(label)}</a></li>'
        for anchor, no, label in rows)
    return (f'<section class="part-divider" id="{part["id"]}">'
            f'<span class="pd-ghost" aria-hidden="true">{wheel(360)}</span>'
            f'<div class="pd-inner">{art.headpiece(part["id"])}'
            f'<p class="pd-no">{esc(part["no"][lang])}</p>'
            f'<h1 class="pd-title">{esc(part["title"][lang])}</h1>'
            f'<div class="cover-rule"><i></i>{wheel(24)}<i></i></div>'
            f'<p class="pd-motto">{esc(part["motto"][lang])}</p>'
            f'<p class="pd-goal">{esc(part["goal"][lang])}</p>'
            f'{route_map(part["id"], len(rows))}'
            f'<ol class="pd-list">{items}</ol>'
            f'</div></section>')


_ROMAN = ["", "Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ", "Ⅷ"]


def toc_html(entries: list[dict], lang: str) -> str:
    """entries: {'kind': 'part'|'row'|'hr', 'anchor', 'no', 'title'}.
    Parts link to their divider page; rows carry a page-ref placeholder
    that the PDF pass stamps with the printed folio. Each part and its rows
    form one group, so a heading never strands itself on the previous page."""
    chunks: list[list[str]] = [[]]

    def close() -> None:
        if any(c.strip() for c in chunks[-1]):
            chunks.append([])

    for e in entries:
        kind = e["kind"]
        if kind in ("part", "hr"):
            close()
        if kind == "part":
            no = (f'<span class="tp-no">{esc(e["no"])}</span>'
                  if e["no"] else "")
            chunks[-1].append(
                f'<a class="toc-part" href="#{e["anchor"]}">{no}'
                f'<span class="tp-tx">{esc(e["title"])}</span>'
                f'<span class="page-ref" data-ref="{e["anchor"]}"></span></a>')
        elif kind == "hr":
            chunks[-1].append('<hr class="toc-hr">')
        else:
            chunks[-1].append(
                f'<a class="toc-row" href="#{e["anchor"]}">'
                f'<span class="toc-n">{esc(e["no"])}</span>'
                f'<span class="toc-t">{esc(e["title"])}</span>'
                f'<span class="leader"></span>'
                f'<span class="page-ref" data-ref="{e["anchor"]}"></span></a>')
    groups = "".join(f'<div class="toc-group">{"".join(c)}</div>'
                     for c in chunks if any(x.strip() for x in c))
    return (f'<section class="front-page toc" id="toc">'
            f'<h1 class="page-title">{esc(ui("toc", lang))}</h1>'
            f'{groups}</section>')


KIND_GROUP = {
    "zh": {"github": "GitHub 仓库与发布", "docs": "官方文档", "blog": "工程博客",
           "spec": "协议规范", "npm": "npm 包", "community": "社区材料（非规范）"},
    "en": {"github": "GitHub repositories & releases", "docs": "Official docs",
           "blog": "Engineering blog", "spec": "Protocol specs",
           "npm": "npm packages", "community": "Community (non-normative)"},
}


def source_registry(sources: dict, lang: str) -> str:
    order = ["github", "npm", "docs", "blog", "spec", "community"]
    groups: dict[str, list] = {k: [] for k in order}
    for sid, src in sources.items():
        groups.setdefault(src.get("kind", "docs"), []).append((sid, src))
    parts = [
        f'<section class="front-page sources" id="sources">'
        f'<h1 class="page-title">{esc(ui("sources_page", lang))}</h1>'
        f'<p class="reg-note">{esc(ui("sources_note", lang))}</p>']
    for kind in order:
        items = groups.get(kind) or []
        if not items:
            continue
        parts.append(f'<h2 class="reg-kind"><span class="rk-tx">{esc(KIND_GROUP[lang][kind])}</span>'
                     f'<span class="rk-n">{len(items)}</span></h2><ul class="reg-list">')
        for num, (sid, src) in enumerate(items, 1):
            pinned = src.get("pinned") or {}
            pin = ""
            if pinned.get("tag"):
                pin += f' · tag <code>{esc(pinned["tag"])}</code>'
            if pinned.get("commit"):
                pin += f' · commit <code>{esc(pinned["commit"][:10])}</code>'
            if pinned.get("version"):
                pin += f' · v<code>{esc(pinned["version"])}</code>'
            scope = src_field(src, "scope", lang)
            parts.append(
                f'<li id="source-{sid}"><div class="reg-head">'
                f'<span class="reg-no">{num:02d}</span>'
                f'<a class="ext" href="{esc(src["url"])}" rel="noopener">'
                f'{esc(src_field(src, "title", lang))}</a>'
                f'<span class="reg-auth">{esc(src_field(src, "authority", lang))}</span>'
                f'<span class="reg-pin">{pin}</span></div>'
                f'<div class="reg-meta">{esc(src_field(src, "snapshot", lang))} · '
                f'{esc(src_field(src, "license", lang))}</div>'
                f'<div class="reg-scope">{esc(scope)}</div></li>')
        parts.append("</ul>")
    parts.append("</section>")
    return "".join(parts)


def subject_index_page(entries: list[dict], lang: str) -> str:
    letters: dict[str, list] = {}
    for e in entries:
        if not e[lang]["refs"]:
            continue  # a headword this edition has no rows for
        letters.setdefault(e["letter"], []).append(e)
    parts = [f'<section class="front-page back-index" id="subject-index">'
             f'<h1 class="page-title">{esc(ui("index_page", lang))}</h1>'
             f'<div class="idx-cols">']
    for letter in sorted(letters):
        cn = letter == INDEX_CN_LETTER
        head = ui("index_cn", lang) if cn else esc(letter)
        parts.append(f'<div class="idx-block"><h2 class="idx-letter">{head}</h2>'
                     + (f'<p class="idx-note">{esc(ui("index_cn_note", lang))}</p>'
                        if cn else '')
                     + '<ul class="idx-list">')
        for e in letters[letter]:
            # a 23-character feature flag has no space to break at, and the row
            # would spend its dotted leader to fit it; `<wbr>` after each
            # underscore gives the name a place to end instead, and is used only
            # when the entry genuinely cannot fit on one line
            term = esc(e[lang]["term"]).replace("_", "_<wbr>")
            refs = "".join(
                f'<a class="xref" href="#{r["anchor"]}">{esc(r["label"])}</a>'
                for r in e[lang]["refs"])
            parts.append(f'<li class="idx-row"><span class="idx-term">{term}</span>'
                         f'<span class="leader"></span>'
                         f'<span class="idx-refs">{refs}</span>'
                         f'<span class="page-ref idx-ref" '
                         f'data-ref="{e[lang]["refs"][0]["anchor"] if e[lang]["refs"] else ""}"></span></li>')
        parts.append("</ul></div>")
    parts.append("</div></section>")
    return "".join(parts)


IDX_SLOT = re.compile(r'<span class="page-ref idx-ref" data-ref="([^"]*)"></span>')


def fill_index_folios(html_text: str, folios: dict[str, int]) -> str:
    """Write each index row's printed page number into the slot it reserves.

    The row is keyed by the anchor it links to, never by the headword: `Session`
    and `SessionStart` print almost the same line, so any pass that looked for
    the term in the printed sheet could hand `SessionStart` the other's number.
    A slot with no folio, or a folio whose anchor never reached the page, is a
    build failure rather than an index that quietly stops mid-column.
    """
    hit: list[str] = []

    def ink(m: re.Match) -> str:
        anchor = m.group(1)
        hit.append(anchor)
        if anchor not in folios:
            raise BuildError(
                f"index: no page number for {anchor!r} — the sheet would print "
                "an empty folio slot")
        return (f'<span class="page-ref idx-ref" data-ref="{anchor}">'
                f"{folios[anchor]}</span>")

    filled = IDX_SLOT.sub(ink, html_text)
    unknown = sorted(set(folios) - set(hit))
    if unknown:
        raise BuildError(
            f"index: {len(unknown)} folio(s) with no row to fill "
            f"({unknown[:8]}) — the index and the page disagree")
    return filled


def principles_page(groups: list[dict], lang: str) -> str:
    """The mechanism layer, on paper.

    A hover card cannot reach the printed book, so the reasons a term exists
    would otherwise live only in the HTML. Each row is one term: the reason,
    then the picture the book uses for it.
    """
    parts = [f'<section class="front-page back-why" id="principles">'
             f'<h1 class="page-title">{esc(ui("principles_page", lang))}</h1>'
             f'<p class="pr-note">{esc(ui("principles_note", lang))}</p>']
    why_tag, ana_tag = ui("why_tag", lang), ui("analogy_tag", lang)
    for g in groups:
        rows = []
        for t in g["terms"]:
            row = (f'<li class="pr-row"><b class="pr-term">{esc(t["term"])}</b>'
                   f'<span class="pr-why"><i class="pr-t">{esc(why_tag)}</i>'
                   f'{esc(t["why"])}</span>')
            if t["analogy"]:
                row += (f'<span class="pr-ana"><i class="pr-t">{esc(ana_tag)}</i>'
                        f'{esc(t["analogy"])}</span>')
            rows.append(row + "</li>")
        parts.append(
            f'<div class="pr-unit"><h2 class="pr-head">'
            f'<a class="xref" href="#{esc(g["anchor"])}">{esc(g["head"])}</a>'
            f'<span class="pr-n">{len(g["terms"])}</span></h2>'
            f'<ul class="pr-list">{"".join(rows)}</ul></div>')
    parts.append("</section>")
    return "".join(parts)


def notes_page(notes: dict, units, lang: str) -> str:
    """The twenty lines of the old postman, walked once more in order.

    One row per unit in reading order; the head links back to the chapter's
    own ruts, because a note taken out of its ending loses its timing."""
    parts = [f'<section class="front-page back-notes" id="keeper-notes">'
             f'<h1 class="page-title">{esc(ui("notes_page", lang))}</h1>'
             f'<p class="pr-note">{esc(ui("notes_note", lang))}</p>'
             f'<ul class="kn-list">']
    for u in units:
        body = (notes.get(u.id) or {}).get(lang)
        if not body:
            continue
        # the gutter label, not the full title: a row whose head wraps to three
        # lines stops being an index and becomes a table of contents
        label = getattr(u, "eyebrow", None) or u.display
        parts.append(
            f'<li class="kn-row"><b class="kn-head">'
            f'<a class="xref" href="#{esc(u.anchor)}" title="{esc(u.display)}">'
            f'{esc(label)}</a>'
            f'</b><span class="kn-note">{esc(body)}</span></li>')
    parts.append("</ul></section>")
    return "".join(parts)
