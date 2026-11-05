#!/usr/bin/env python3
"""yuyu-book: assemble the offline single-file editions of《御舆》.

Usage (from the repo root):
    python yuyu-book/build.py --check
    python yuyu-book/build.py --lang zh
    python yuyu-book/build.py --lang en --pdf
    python yuyu-book/build.py --regen-index
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from yuyu_book import (art, audit, mermaid as mm, pages, plain,
                       render)  # noqa: E402
from yuyu_book.core import (BOOK_DIR, HAN_RE, INDEX_CN_LETTER, REPO_ROOT,
                            BuildError, dump_json, expected_ids, load_configs,
                            load_json, load_unit, read_text,
                            unit_stream)  # noqa: E402
from yuyu_book.style import CSS, key_mark, page, rut, trace, wheel  # noqa: E402


def glossary_to_index(manifest: dict) -> list[dict]:
    """Build the subject index from appendix D tables (both languages)."""
    apxd = next(a for a in manifest["appendices"] if a["id"] == "apxd")
    entries: dict[str, dict] = {}

    def add(term: str, lang: str, anchor: str, label: str):
        key = term.strip().lower()
        if not key or len(term) > 64:
            return
        e = entries.setdefault(key, {"key": key, "letter": "A", lang: {"term": term.strip(), "refs": []}})
        for lk in ("zh", "en"):
            e.setdefault(lk, {"term": term.strip(), "refs": []})
        first = re.search(r"[A-Za-z]", term)
        if first:
            e["letter"] = first.group(0).upper()
        refs = e[lang]["refs"]
        if not any(r["anchor"] == anchor for r in refs):
            refs.append({"anchor": anchor, "label": label})

    def add_alias(term: str, anchor: str, label: str):
        """A Chinese headword pointing at the same chapter. Appendix D files
        every term under its English name, which is the right heading for the
        English book and the wrong one for the Chinese: a reader who just met
        自动压缩 in ch 7 does not think to look under A."""
        key = term.strip().lower()
        if not key or len(term) > 64:
            return
        e = entries.setdefault(key, {"key": key, "letter": INDEX_CN_LETTER,
                                     "zh": {"term": term.strip(), "refs": []},
                                     "en": {"term": term.strip(), "refs": []}})
        if not any(r["anchor"] == anchor for r in e["zh"]["refs"]):
            e["zh"]["refs"].append({"anchor": anchor, "label": label})

    rx_zh = re.compile(r"第\s*(\d{1,2})\s*章")
    rx_en = re.compile(r"Chapter\s+(\d{1,2})", re.I)
    for lang in ("zh", "en"):
        text = read_text(REPO_ROOT / apxd[lang])
        fence = None
        for line in text.split("\n"):
            m = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
            if m:
                token, info = m.group(1), m.group(2).strip()
                if fence is None:
                    fence = token
                elif token[0] == fence[0] and not info:
                    fence = None
                continue
            if fence is not None or not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2 or set("".join(cells)) <= set("-: "):
                continue
            term = cells[0].strip("*` ")
            tail = " ".join(cells[2:])
            rx = rx_zh if lang == "zh" else rx_en
            nums = [int(n) for n in rx.findall(tail) if 1 <= int(n) <= 15]
            if not nums or len(term) < 2:
                continue
            for n in nums[:4]:
                add(term, lang, f"ch{n:02d}",
                    f"第 {n} 章" if lang == "zh" else f"Ch {n}")
            if lang == "zh" and len(cells) >= 5:
                # the 中文译名 column, split on the slash that lets one English
                # term carry several translations
                for part in re.split(r"\s*/\s*", cells[1].strip("*` ")):
                    if len(part) >= 2 and HAN_RE.search(part):
                        for n in nums[:4]:
                            add_alias(part, f"ch{n:02d}", f"第 {n} 章")
    out = sorted(entries.values(), key=lambda e: (e["letter"], e["key"]))
    return [e for e in out if e.get("zh", {}).get("refs")
            or e.get("en", {}).get("refs")]


def build_edition(lang: str, manifest: dict, sources: dict, *,
                  mode: str, browser: str | None, autolink: bool,
                  out_dir: Path, do_pdf: bool, edge: str | None,
                  glosses: dict | None = None,
                  paths: dict | None = None,
                  notes: dict | None = None,
                  plain_layer: bool = True) -> Path:
    ids = expected_ids(manifest)
    mapping = {i: i for i in ids}
    glosses = glosses or {}
    paths = paths or {}
    notes = notes or {}
    layer = plain.Layer(glosses, lang)

    units = []
    for unit_def, kind, part in unit_stream(manifest):
        u = load_unit(unit_def, kind, lang, REPO_ROOT)
        u.part = part  # type: ignore[attr-defined]
        units.append(u)

    all_blocks, caps = [], {}
    for u in units:
        caps.update(mm.captions_for(read_text(REPO_ROOT / u.path), u.blocks,
                                    fallback=pages.ui("plate_fallback", lang)))
        all_blocks.extend(u.blocks)
    if mode == "render":
        diagrams = mm.render_all(all_blocks, caps, browser)
        expect_svgs = len(diagrams)
    else:
        diagrams = mm.source_fallback(all_blocks, caps)
        expect_svgs = None

    payloads = []
    for u in units:
        payloads.append(render.render_unit(u, mapping, diagrams=diagrams,
                                           autolink=autolink, gloss=layer,
                                           tiers=paths.get(u.id)))
    by_id = {p["unit"].id: p for p in payloads}
    layer.check_coverage()

    # ---------------- assemble ----------------
    body: list[str] = []
    body.append(pages.cover(manifest, lang))
    body.append(pages.imprint(manifest, lang))
    rev = load_json(BOOK_DIR / "revisions.json")["entries"]
    body.append(pages.revisions_page(rev, lang))
    body.append(pages.how_to_read(manifest, lang, paths))

    front_id = manifest["front"]["id"]
    toc_entries: list[dict] = [
        {"kind": "row", "anchor": front_id, "no": pages.FRONT_NO,
         "title": by_id[front_id]["unit"].title}]
    outline: list[tuple[int, str, str]] = [
        (1, by_id[front_id]["unit"].display or pages.ui("front", lang),
         front_id)]
    rail = [f'<nav class="rail" aria-label="contents"><p class="rail-title">'
            f'<a href="#toc">{pages.ui("toc", lang)}</a></p>']
    rail.append(f'<a class="rail-map" href="#route-map">'
                f'{key_mark("wheel")}{pages.ui("route_map", lang)}</a>')
    rail.append(f'<a href="#{front_id}">{pages.ui("front", lang)}</a>')

    for p_idx, part in enumerate(manifest["parts"], 1):
        label = f'{part["no"][lang]} · {part["title"][lang]}'
        toc_entries.append({"kind": "part", "anchor": part["id"],
                            "no": pages._ROMAN[p_idx],
                            "title": part["title"][lang]})
        outline.append((1, label, part["id"]))
        rail.append(f'<p class="rail-part">{pages.esc(label)}</p>')
        for unit_def in part["units"]:
            u = by_id[unit_def["id"]]["unit"]
            toc_entries.append({"kind": "row", "anchor": unit_def["id"],
                                "no": u.no_plain, "title": u.title})
            outline.append((2, u.display, unit_def["id"]))
            rail.append(f'<a href="#{unit_def["id"]}">{pages.esc(u.no)} '
                        f'{pages.esc(u.title)}</a>')

    toc_entries.append({"kind": "hr"})
    rail.append(f'<p class="rail-part">{pages.ui("appendix", lang)}</p>')
    for apx in manifest["appendices"]:
        u = by_id[apx["id"]]["unit"]
        toc_entries.append({"kind": "row", "anchor": apx["id"],
                            "no": u.no_plain, "title": u.title})
        outline.append((1, u.display, apx["id"]))
        rail.append(f'<a href="#{apx["id"]}">{pages.esc(u.no)} '
                    f'{pages.esc(u.title)}</a>')

    index_path = BOOK_DIR / "subject-index.json"
    idx_entries = None
    if index_path.exists():
        idx_entries = load_json(index_path)

    why_groups = _principle_groups(glosses, units, lang)
    back = ([] if not why_groups
            else [("principles", pages.ui("principles_page", lang))])
    if notes:
        back += [("keeper-notes", pages.ui("notes_page", lang))]
    back += [("sources", pages.ui("sources_page", lang)),
             ("subject-index", pages.ui("index_page", lang))]
    for anchor, label in back:
        if anchor == "subject-index" and not idx_entries:
            continue
        toc_entries.append({"kind": "part", "anchor": anchor, "no": "",
                            "title": label})
        outline.append((1, label, anchor))
        rail.append(f'<a href="#{anchor}">{pages.esc(label)}</a>')

    body.append(pages.toc_html(toc_entries, lang))
    # the foreword has no chapter number of its own; the wheel at the head of
    # the road wears the same gutter number the contents row shows
    nos = {p["unit"].id: p["unit"].no_plain for p in payloads}
    nos[front_id] = nos[front_id] or pages.FRONT_NO
    body.append(pages.route_map_page(manifest, lang, nos))
    body.append(_article(by_id[front_id], manifest, sources, lang,
                         notes=notes, show_lead=plain_layer))
    for part in manifest["parts"]:
        rows = [(u["id"], by_id[u["id"]]["unit"].no_plain,
                 by_id[u["id"]]["unit"].title)
                for u in part["units"]]
        body.append(pages.part_divider(part, lang,
                                       manifest["parts"].index(part) + 1, rows))
        for unit_def in part["units"]:
            body.append(_article(by_id[unit_def["id"]], manifest, sources,
                                 lang, notes=notes, show_lead=plain_layer))
    for apx in manifest["appendices"]:
        body.append(_article(by_id[apx["id"]], manifest, sources, lang,
                             kind="appendix", notes=notes,
                             show_lead=plain_layer))

    if why_groups:
        body.append(pages.principles_page(why_groups, lang))
    if notes:
        body.append(pages.notes_page(notes, units, lang))
    body.append(pages.source_registry(sources, lang))
    if idx_entries:
        body.append(pages.subject_index_page(idx_entries, lang))

    n_diagrams = sum(p["n_diagrams"] for p in payloads)
    foot = pages.ui("diagrams", lang)
    body.append(f'<footer class="colophon">{wheel(34)}'
                f'{pages.esc(manifest["title"][lang])} · v'
                f'{pages.esc(manifest["version"])} · {n_diagrams} {foot}</footer>')

    # the break points go in here, over the whole assembled book rather than
    # unit by unit: the front and back matter never runs the unit pipeline, and
    # a revision note quoting getFeatureValue_CACHED_MAY_BE_STALE pushed the
    # document 37px past a 390px screen. This is also the last pass that reads
    # the text as words — term matching, the outline and the cross-references
    # have all already seen it uncut.
    body_html = render.soften_long_names("\n".join(body))
    html_text = page(lang, f'{manifest["title"][lang]} — {manifest["author"]}',
                     CSS, f"lang-{lang}", body_html,
                     "\n".join(rail) + "</nav>", "")
    audit.audit(html_text, n_units=len(units), expect_svgs=expect_svgs)

    # the dashed marks and the chapter panels come from the same hit list; if
    # they ever diverge, paper readers would chase underlines that are nowhere
    # explained (there is no hover in print)
    n_marks = html_text.count('<span class="gloss"')
    n_rows = html_text.count('<li class="nt-row">')
    n_chips = html_text.count('<span class="sec-tier')
    n_emblems = html_text.count('<span class="ch-emblem"')
    ids = [p["unit"].id for p in payloads]
    parts = [f'part-{p["id"]}' for p in manifest["parts"]]
    want_emblems = len(ids) - len(art.missing(ids))
    n_heads = html_text.count('<div class="pd-art"')
    want_heads = len(parts) - len(art.missing(parts))
    if n_emblems != want_emblems or n_heads != want_heads:
        raise BuildError(f"{n_emblems}/{want_emblems} emblems and "
                         f"{n_heads}/{want_heads} headpieces reached the book "
                         "— every drawing must reach its page")
    if n_marks != n_rows:
        raise BuildError(f"plain layer: {n_marks} dashed marks but {n_rows} "
                         f"panel rows — every mark must be restated on paper")
    n_keep = html_text.count('<div class="keeper">')
    n_kn = html_text.count('<li class="kn-row">')
    want_keep = sum(1 for u in units if (notes.get(u.id) or {}).get(lang))
    if notes and (n_keep != want_keep or n_kn != want_keep):
        raise BuildError(f"keeper layer: {n_keep} chapter notes and {n_kn} "
                         f"collection rows for {want_keep} authored — the "
                         "postman must sit at every rut and be listed once")
    n_lead = html_text.count('<div class="lead-band"')
    want_lead = len(units) if plain_layer else 0
    if n_lead != want_lead:
        raise BuildError(f"plain layer: {n_lead} lead bands for {want_lead} "
                         "units — the band belongs to the layer, so --no-plain "
                         "has to drop it with everything else")

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"yuyu-agent-harness-{lang}.html"
    out.write_text(html_text, encoding="utf-8")
    stats = (f"{out.name}: {out.stat().st_size / 1e6:.1f} MB, "
             f"{len(units)} units, {n_diagrams} plates, "
             f"{sum(len(p['external']) for p in payloads)} cited links, "
             f"{n_marks} glosses, {n_lead} lead bands, {n_chips} tier chips, "
             f"{n_emblems} emblems, {n_heads} headpieces, "
             f"{n_keep} keeper notes")
    print("  " + stats)
    if do_pdf:
        from yuyu_book import pdf
        pmeta = pdf_meta(manifest, outline, toc_entries, lang, idx_entries)
        # paper has no hover and no locator chip that means anything without a
        # sheet number, so the index rows get their folios from a measuring
        # print and the book is printed again with the numbers in place
        folios = {}
        if pmeta["index_rows"]:
            dest = pdf.measure(out,
                               sorted({r["anchor"] for r in pmeta["index_rows"]}),
                               edge or browser)
            folios = {a: dest[a] + 1 for a in dest}
            out.write_text(pages.fill_index_folios(html_text, folios),
                           encoding="utf-8")
        p = pdf.build_pdf(out, pmeta, edge or browser, folios=folios)
        print(f"  {p.name}: {p.stat().st_size / 1e6:.1f} MB, "
              f"{len(outline)} bookmarks, {len(folios)} index folios")
    return out


def pdf_meta(manifest, outline, toc_entries, lang, idx_entries=()):
    """Everything the PDF pass needs that the HTML cannot say for itself:
    bookmarks, running heads, the contents rows it must number, and the index
    rows it must number once the measuring print says where each unit lands."""
    return {"outline": outline,
            # every bookmark opens a section, parts included: leaving the part
            # dividers out made those pages wear the previous chapter's head
            "heads": [(a, label) for _lvl, label, a in outline],
            "toc_rows": [e["anchor"] for e in toc_entries
                         if e["kind"] in ("row", "part")],
            # a folio is written into the row it belongs to, keyed by the anchor
            # the row links to — the terms are here so a test can prove this list
            # is the index in the order the page puts it down: an entry this
            # edition has no chip for prints no row and gets no folio
            "index_rows": [{"term": e[lang]["term"],
                            "anchor": e[lang]["refs"][0]["anchor"]}
                           for e in idx_entries if e[lang]["refs"]],
            "toc_title": pages.ui("toc", lang),
            "title": manifest["title"][lang],
            "subtitle": manifest["subtitle"][lang],
            "author": manifest["author"],
            "keywords": f'v{manifest["version"]} {manifest["date"]}',
            "lang": lang}


def _principle_groups(glosses: dict, units, lang: str) -> list[dict]:
    """The why lines, filed under the chapter that argues for them.

    A term's own chapter is decided by its `why_evidence` pointer rather than by
    where the word first appears: the reason lives where the reason is given,
    which is not always the first mention.
    """
    by_path = {u.path: u for u in units}
    order = {u.id: n for n, u in enumerate(units)}
    groups: dict[str, dict] = {}
    for gid, g in sorted(glosses.items(), key=lambda kv: kv[1]["term"][lang]):
        why = (g.get("why") or {}).get(lang)
        if not why:
            continue
        unit = next((by_path[str(r).rsplit(":", 1)[0].replace("\\", "/")]
                     for r in g.get("why_evidence") or []
                     if str(r).rsplit(":", 1)[0].replace("\\", "/") in by_path),
                    None)
        if unit is None:
            raise BuildError(f"gloss {gid}: why_evidence points outside the book")
        groups.setdefault(unit.id, {"anchor": unit.anchor,
                                    "head": unit.display, "terms": []})
        groups[unit.id]["terms"].append(
            {"term": g["term"][lang], "why": why,
             "analogy": (g.get("analogy") or {}).get(lang, "")})
    return [groups[k] for k in sorted(groups, key=lambda k: order.get(k, 99))]


def _article(payload, manifest, sources, lang, kind=None, notes=None,
             show_lead=True):
    u = payload["unit"]
    kind = kind or u.kind
    guide = manifest["guides"].get(u.id, {})
    part = getattr(u, "part", None)
    eyebrow = []
    if part:
        eyebrow.append(f'{part["no"][lang]} {part["title"][lang]}')
    if kind != "front":
        eyebrow.append(u.eyebrow)
    label = u.display
    if kind == "chapter" and u.no:
        digits = "".join(c for c in u.no if c.isdigit())
        seal = f'<span class="ch-seal" aria-hidden="true">{digits.zfill(2)}</span>'
        label = u.title
    elif kind == "appendix":
        seal = f'<span class="ch-seal" aria-hidden="true">{u.id[-1].upper()}</span>'
        label = u.title
    else:
        seal = ""
    # the emblem rides at the end of the head row, so the top of every unit is
    # title + seal + drawing rather than a wide empty band over the sheet
    emblem = art.emblem(u.id)
    title_html = (f'{seal}<h1 class="ch-title">{pages.esc(label)}</h1>{emblem}')
    if seal or emblem:
        title_html = f'<div class="ch-head-row">{title_html}</div>'
    # the foreword is the one unit whose number-free title is the eyebrow text,
    # so it renders no eyebrow at all rather than "前言" twice above the H1
    eyebrow_html = (f'<p class="eyebrow">{pages.esc(" · ".join(eyebrow))}</p>'
                    if eyebrow else "")
    # the head closes on a drawn wire rather than a ruled line: same job, and it
    # carries the unit id so no two chapters run the same trace
    head = (f'<header class="chapter-head">{eyebrow_html}{title_html}'
            f'{trace(u.id)}</header>')
    cls = "chapter" if kind == "chapter" else ("unit" if kind == "front"
                                               else "unit appendix")
    # the band's text lives in the manifest, not in the glossary, so it is the
    # one device the empty layer cannot swallow by itself
    lead = pages.lead_band(guide, lang) if show_lead else ""
    compass = pages.compass(u, guide, sources, lang) if guide else ""
    panel = pages.new_terms_panel(payload.get("new_terms") or [], lang, kind)
    # keep rendered body but drop its own H1 (re-synthesised above)
    body_html = re.sub(r"<h1 [^>]*>.*?</h1>|<h1>.*?</h1>", "", payload["html"],
                       count=1)
    # the ruts go inside the body, glued to the block they close: left as a
    # trailing sibling they can fall alone onto a sheet the next unit's forced
    # page break then empties
    keeper = ((notes or {}).get(u.id) or {}).get(lang)
    closer = (f'<div class="keeper">{art.keeper()}'
              f'<p class="keeper-note">{pages.esc(keeper)}</p></div>'
              if keeper else "") + rut(u.id)
    body_html = render.glue_closer(body_html, closer)
    # the card of new terms trails the chapter rather than opening it: it is
    # the tallest block on the opener, and ahead of the prose it spent the
    # whole first sheet on furniture so that a chapter's first sentence landed
    # on page two. The ruts stay the last ink of the argument; the card is the
    # apparatus that closes it.
    return (f'<article class="{cls}" id="{u.id}">{head}'
            f'{lead}{compass}<div class="chapter-body">{body_html}{panel}</div>'
            f'</article>')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lang", default="both", choices=["zh", "en", "both"])
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="build into a temp dir and only validate")
    ap.add_argument("--out-dir", default=str(BOOK_DIR / "dist"))
    ap.add_argument("--browser", default=None,
                    help="explicit msedge/chrome executable for mermaid & PDF")
    ap.add_argument("--edge", default=None, help="PDF browser executable")
    ap.add_argument("--mermaid", default="render", choices=["render", "source"])
    ap.add_argument("--no-autolink", action="store_true")
    ap.add_argument("--no-plain", action="store_true",
                    help="skip the plain-language layer (marks, panels, lead "
                         "bands, tier chips, principle notes, keeper notes)")
    ap.add_argument("--regen-index", action="store_true")
    args = ap.parse_args(argv)

    try:
        manifest, sources = load_configs()
        glosses, paths = ({}, {}) if args.no_plain else plain.load_plain()
        notes = {} if args.no_plain else plain.load_notes()
        if not args.no_plain:
            plain.validate_plain(glosses, paths, manifest)
            if notes:
                unit_texts = {u["id"]: {"zh": read_text(REPO_ROOT / u["zh"]),
                                        "en": read_text(REPO_ROOT / u["en"])}
                              for u, _k, _p in unit_stream(manifest)}
                plain.validate_notes(notes, glosses, unit_texts)
        if args.regen_index:
            entries = glossary_to_index(manifest)
            dump_json(BOOK_DIR / "subject-index.json", entries)
            zh_n = sum(1 for e in entries if e["zh"]["refs"])
            en_n = sum(1 for e in entries if e["en"]["refs"])
            print(f"subject index: {len(entries)} terms ({zh_n} zh refs, "
                  f"{en_n} en refs)")
            if args.lang == "both" and not args.check:
                pass  # index-only run still produces files; build continues
        langs = ["zh", "en"] if args.lang == "both" else [args.lang]
        out_dir = Path(args.out_dir)
        if args.check:
            out_dir = Path(tempfile.mkdtemp(prefix="yuyu-check-"))
        for lang in langs:
            print(f"[{lang}]")
            build_edition(lang, manifest, sources, mode=args.mermaid,
                          browser=args.browser, autolink=not args.no_autolink,
                          out_dir=out_dir, do_pdf=args.pdf and not args.check,
                          edge=args.edge, glosses=glosses, paths=paths,
                          notes=notes, plain_layer=not args.no_plain)
        print("OK" if not args.check else "CHECK OK")
    except BuildError as e:
        print(f"BUILD FAILED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
