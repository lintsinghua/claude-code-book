"""The plain-language layer (通俗层): term glosses, lead bands, reading tiers.

Nothing here touches the manuscript. glosses.json and reading-paths.json are
the only inputs, and both stay optional while they are being authored — an
absent file leaves the book exactly as it was.
"""
from __future__ import annotations

import html
import re

from .core import (BOOK_DIR, FENCE_RE, HAN_RE, REPO_ROOT, SOURCE_ID_RE,
                   BuildError, load_json, read_text)

TIER_ORDER = ("start", "core", "deep")
# the one line in the hover card whose job a reader cannot guess from its
# typography, so it says what it is
WHY_TAG = {"zh": "为什么", "en": "Why"}
ANALOGY_TAG = {"zh": "比方", "en": "Say it as"}
TIER_LABELS = {"start": {"zh": "起步", "en": "Start"},
               "core": {"zh": "主干", "en": "Core"},
               "deep": {"zh": "进阶", "en": "Advanced"}}
TIER_DESC = {
    "start": {"zh": "不懂背景也能读，先把全局看明白",
              "en": "Readable with no background; it builds the big picture"},
    "core": {"zh": "要理解这个子系统就必须读",
             "en": "Required to understand this subsystem"},
    "deep": {"zh": "源码级细节，动手实现时再回来",
             "en": "Source-level detail; come back when you build one"},
}

# the paper edition has no hover, so the chapter panel is the only carrier;
# past this many new terms in one chapter the panel stops being a help and
# becomes a wall of text, so the build asks for the registry to be trimmed.
MAX_PANEL = 22
# `why` is the longest of the three because it carries a causal chain (the
# constraint, then the choice), while `plain` names a thing and `analogy`
# pictures it. It stays under a sentence and a half on purpose: a hover card
# that needs its own scrollbar is a paragraph, not a help.
LIMITS = {"plain": {"zh": 40, "en": 130}, "analogy": {"zh": 44, "en": 130},
          "why": {"zh": 52, "en": 190}}
LEAD_LIMITS = {"plain": {"zh": 60, "en": 170}, "analogy": {"zh": 52, "en": 160}}

# annotating prose only: no links, code, headings, plates, sup/fn markers or
# already-built components (every component we emit lives in a <span>)
_SKIP_GLOSS = {"a", "code", "pre", "svg", "style", "sup", "sub", "figure",
               "h1", "h2", "h3", "h4", "span", "kbd", "samp", "var"}
# Inline <code> is the one exception: half the book's field names (an
# `isConcurrencySafe` in a sentence) never appear outside backticks, so the
# help has to be reachable where the reader first meets the term. `pre` stays
# skipped — a code plate is studied as a whole, and dashing shapes inside it
# would break the copy a reader pastes out of the page.
_SKIP_GLOSS_INLINE = _SKIP_GLOSS - {"code"}
_CODE_HUMP = re.compile(r"[_0-9]|[a-z][A-Z]")
_TAG_NAME_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)")
_ASCII_FORM = re.compile(r"[A-Za-z]")
_H2_RE = re.compile(r'<h2 id="([^"]+)">((?:(?!</?h2\b).)*)</h2>', re.S)


def load_plain():
    """(glosses, reading paths) — {} when the layer has not been authored yet."""
    out = []
    for name in ("glosses.json", "reading-paths.json"):
        p = BOOK_DIR / name
        out.append(load_json(p) if p.exists() else {})
    return out[0], out[1]


# ---------------------------------------------------------------- keeper ----
# The 按语 layer: one line of postman's marginalia per unit, at its wheel
# ruts. Commentary may not become a second manuscript, so it stays one
# sentence and must look back at a term that really stands in its own unit.
NOTE_LIMITS = {"zh": 36, "en": 130}


def load_notes() -> dict:
    p = BOOK_DIR / "notes.json"
    return load_json(p) if p.exists() else {}


def validate_notes(notes: dict, glosses: dict,
                   unit_texts: dict[str, dict[str, str]]) -> None:
    errors: list[str] = []
    missing = sorted(set(unit_texts) - set(notes))
    extra = sorted(set(notes) - set(unit_texts))
    if missing:
        errors.append(f"units without a note: {', '.join(missing)}")
    if extra:
        errors.append(f"notes without a unit: {', '.join(extra)}")
    forms = {lang: sorted({f for g in glosses.values()
                           for f in (g.get("forms") or {}).get(lang) or []},
                          key=len, reverse=True)
             for lang in ("zh", "en")}
    for uid, n in sorted(notes.items()):
        texts = unit_texts.get(uid) or {}
        for lang in ("zh", "en"):
            who = f"{uid}.{lang}"
            body = (n.get(lang) or "").strip()
            if not body:
                errors.append(f"{who}: empty note text")
                continue
            if len(body) > NOTE_LIMITS[lang]:
                errors.append(f"{who}: {len(body)} chars, over the "
                              f"上限 of {NOTE_LIMITS[lang]} — a note is one "
                              "sentence, or it is a paragraph")
            if lang == "en" and HAN_RE.search(body):
                errors.append(f"{who}: 汉字 in the English note — the edition "
                              "does not code-switch")
            unit = texts.get(lang) or ""
            if not any(f in body and f in unit for f in forms[lang]):
                errors.append(f"{who}: no registered term form of this unit "
                              "in it — 术语锁: the note must look back at a "
                              "word the chapter itself uses")
    if errors:
        raise BuildError("keeper layer invalid:\n  " + "\n  ".join(errors))


def prose_lines(text: str) -> dict[int, str]:
    """1-based line numbers that sit outside every code fence."""
    keep, fence = {}, None
    for n, line in enumerate(text.split("\n"), 1):
        m = FENCE_RE.match(line)
        if m:
            token, info = m.group(1), m.group(2).strip()
            if fence is None:
                fence = token
            elif (token[0] == fence[0] and len(token) >= len(fence)
                    and not info):
                fence = None
            continue
        if fence is None:
            keep[n] = line
    return keep


def validate_plain(glosses: dict, paths: dict, manifest: dict) -> None:
    """Every gloss must be provably present in the prose it claims to explain.

    An evidence pointer is checked against the real file: the line has to sit
    outside a code fence and contain one of the registered surface forms, so a
    invented term or a form that never occurs cannot enter the registry.
    """
    from .core import unit_stream

    errors: list[str] = []
    guides = manifest.get("guides", {})
    if not glosses and not paths and \
            not any((g.get("plain") for g in guides.values())):
        return          # layer not authored yet: build the book as it stands
    cache: dict[str, dict[int, str]] = {}
    unit_ids = {u["id"] for u, _k, _p in unit_stream(manifest)}

    def prose(ref: str, who: str,
              forms_by_lang: dict[str, list[str]] | None = None) -> str | None:
        """The language a verified `file:line` points at, or None if it is not
        real prose. A pointer into a code fence proves nothing about the book's
        claims, so every plain-language sentence needs prose behind it."""
        m = re.match(r"^(.+):(\d+)$", str(ref))
        if not m:
            errors.append(f"{who}: evidence {ref!r} is not file:line")
            return None
        rel, lineno = m.group(1), int(m.group(2))
        lang = "en" if rel.replace("\\", "/").startswith("en/") else "zh"
        if rel not in cache:
            path = REPO_ROOT / rel
            if not path.exists():
                errors.append(f"{who}: evidence file {rel} missing")
                return None
            cache[rel] = prose_lines(read_text(path))
        line = cache[rel].get(lineno)
        if line is None or not line.strip():
            errors.append(f"{who}: evidence {ref} is inside a code fence, "
                          "blank, or past the end of the file")
            return None
        if forms_by_lang is not None:
            want = forms_by_lang.get(lang) or []
            if not any(f in line for f in want):
                errors.append(f"{who}: evidence {ref} does not contain any "
                              f"registered form")
                return None
        return lang

    for gid, g in glosses.items():
        if not SOURCE_ID_RE.match(gid):
            errors.append(f"gloss {gid!r} id not [a-z0-9-]+")
        for field in ("term", "forms", "plain"):
            entry = g.get(field) or {}
            for lang in ("zh", "en"):
                val = entry.get(lang)
                if field == "forms":
                    if not val:
                        errors.append(f"gloss {gid}: forms.{lang} empty")
                elif not (val or "").strip():
                    errors.append(f"gloss {gid}: {field}.{lang} empty")
        for field, lim in LIMITS.items():
            if field == "plain":
                continue
            for lang in ("zh", "en"):
                val = (g.get(field) or {}).get(lang)
                if val and len(val) > lim[lang]:
                    errors.append(f"gloss {gid}: {field}.{lang} is "
                                  f"{len(val)} chars (max {lim[lang]})")
        for lang in ("zh", "en"):
            limit = LIMITS["plain"][lang]
            val = (g.get("plain") or {}).get(lang) or ""
            if len(val) > limit:
                errors.append(f"gloss {gid}: plain.{lang} is {len(val)} "
                              f"chars (max {limit})")
        pr = g.get("priority")
        if pr not in ("core", "extra"):
            errors.append(f"gloss {gid}: priority must be core|extra")
        forms = g.get("forms") or {}
        ev = g.get("evidence") or []
        if not ev:
            errors.append(f"gloss {gid}: no evidence (file:line)")
        langs_seen = set()
        for ref in ev:
            lang = prose(ref, f"gloss {gid}", forms)
            if lang:
                langs_seen.add(lang)
        if not langs_seen:
            errors.append(f"gloss {gid}: no usable evidence")
        elif pr == "core" and langs_seen != {"zh", "en"}:
            errors.append(f"gloss {gid}: core glosses need evidence in both "
                          f"languages (found {sorted(langs_seen)})")
        # `why` is the layer's answer to "why is it built this way", so it may
        # not rest on the term's first mention: it needs its own prose line, in
        # each language, and that line has to name the term.
        why = g.get("why") or {}
        if pr == "core" and not (why.get("zh") or "").strip():
            errors.append(f"gloss {gid}: a core term owes the reader a why "
                          "line, not just a definition")
        if why:
            for lang in ("zh", "en"):
                val = (why.get(lang) or "").strip()
                if not val:
                    errors.append(f"gloss {gid}: why.{lang} is empty")
                elif lang == "en" and HAN_RE.search(val):
                    errors.append(f"gloss {gid}: why.en still carries Chinese")
            seen = {p for p in (prose(r, f"gloss {gid} why", forms)
                                for r in g.get("why_evidence") or [])
                    if p}
            if seen != {"zh", "en"}:
                errors.append(f"gloss {gid}: why needs one prose line in each "
                              f"language (found {sorted(seen)})")

    chapters = {u["id"] for u, k, _p in unit_stream(manifest) if k == "chapter"}
    for uid, tiers in paths.items():
        if uid not in unit_ids:
            errors.append(f"reading-paths: unknown unit {uid}")
        if not isinstance(tiers, list) or not tiers:
            errors.append(f"reading-paths {uid}: must be a non-empty list")
            continue
        bad = [t for t in tiers if t not in TIER_ORDER]
        if bad:
            errors.append(f"reading-paths {uid}: unknown tier(s) {bad}")
    for uid in chapters - set(paths):
        errors.append(f"reading-paths: chapter {uid} has no tiers")

    # the lead band is the one plain-language device that works identically on
    # screen and on paper, so every unit has to carry it once the layer exists
    guides = manifest.get("guides", {})
    for uid in sorted(unit_ids):
        guide = guides.get(uid) or {}
        for field, lim in LEAD_LIMITS.items():
            entry = guide.get(field)
            if entry is None:
                if field == "plain":
                    errors.append(f"guide {uid}: plain is missing")
                continue
            for lang in ("zh", "en"):
                val = (entry.get(lang) or "").strip()
                if not val:
                    errors.append(f"guide {uid}.{field}.{lang} is empty")
                elif len(val) > lim[lang]:
                    errors.append(f"guide {uid}.{field}.{lang} is "
                                  f"{len(val)} chars (max {lim[lang]})")
        # a summary sentence is a claim about the chapter, so it needs the same
        # proof as a gloss: real prose lines, in both languages, since both
        # editions print the band
        ev = guide.get("plain_evidence") or []
        if not ev:
            errors.append(f"guide {uid}: plain_evidence is missing")
            continue
        seen = {lang for lang in (prose(ref, f"guide {uid}") for ref in ev)
                if lang}
        if seen != {"zh", "en"}:
            errors.append(f"guide {uid}: plain_evidence must point at prose in "
                          f"both languages (found {sorted(seen)})")
    if errors:
        raise BuildError("plain layer invalid:\n  " + "\n  ".join(errors))


def marks(g: dict) -> bool:
    """Whether a term gets dashed in the prose. `extra` terms stay in the
    registry — searchable in appendix D, hoverable where they do occur — but
    are not marked, because a chapter whose every noun is annotated turns help
    into noise. `"mark": true` opts one back in deliberately."""
    return g.get("mark", g.get("priority") == "core")


class Matcher:
    """Longest-form-first alternation over every markable surface form.

    Two matchers: prose sees every form; inline code sees only shapes a
    reader cannot parse as an English word (camel humps, underscores,
    digits), because dashing every backtapped word turns prose into a
    field of dashes."""

    def __init__(self, glosses: dict, lang: str):
        pairs: list[tuple[str, str]] = []
        for gid, g in glosses.items():
            if not marks(g):
                continue
            for form in (g.get("forms") or {}).get(lang) or []:
                pairs.append((form, gid))
        pairs.sort(key=lambda p: (-len(p[0]), p[0]))
        self.pairs = pairs
        self.rx, self.gid_of = self._compile(pairs)
        code_pairs = [p for p in pairs if _CODE_HUMP.search(p[0])]
        self.rx_code, self.gid_of_code = self._compile(code_pairs)

    @staticmethod
    def _compile(pairs: list[tuple[str, str]]):
        alts = []
        for form, _gid in pairs:
            esc = re.escape(form)
            if _ASCII_FORM.match(form):
                esc = rf"(?<![A-Za-z0-9_]){esc}(?![A-Za-z0-9_])"
            alts.append(f"({esc})")
        rx = re.compile("|".join(alts)) if alts else None
        gid_of = [gid for _f, gid in pairs]
        return rx, gid_of

    def mark(self, doc: str, glosses: dict, lang: str,
             used: set[str]) -> tuple[str, list[dict]]:
        """Wrap the first occurrence of each term in this unit and return the
        hits in document order, so the chapter panel lists exactly the terms
        the prose actually marked."""
        if self.rx is None:
            return doc, []
        from . import render

        seen: set[str] = set()
        hits: list[dict] = []
        out: list[str] = []
        code_depth = pre_depth = 0
        for kind, text, blocked in render.iter_doc(doc, _SKIP_GLOSS_INLINE):
            if kind == "tag":
                m = _TAG_NAME_RE.match(text)
                if m:
                    closing, name = m.group(1), m.group(2).lower()
                    delta = -1 if closing else 1
                    if name == "code":
                        code_depth = max(0, code_depth + delta)
                    elif name == "pre":
                        pre_depth = max(0, pre_depth + delta)
                out.append(text)
                continue
            if blocked:
                out.append(text)
                continue

            if code_depth and not pre_depth:
                rx, gid_of = self.rx_code, self.gid_of_code
            else:
                rx, gid_of = self.rx, self.gid_of
            if rx is None:
                out.append(text)
                continue

            def repl(m, gid_of=gid_of):
                gid = gid_of[m.lastindex - 1]
                if gid in seen:
                    return m.group(0)
                seen.add(gid)
                used.add(gid)
                g = glosses[gid]
                hits.append({"id": gid, "form": m.group(0),
                             "term": g["term"][lang],
                             "plain": g["plain"][lang],
                             "analogy": (g.get("analogy") or {}).get(lang, ""),
                             "priority": g.get("priority", "extra")})
                return f'<span class="gloss" tabindex="0" data-g="{gid}">' \
                    f'{m.group(0)}{_pop(g, lang)}</span>'

            out.append(rx.sub(repl, text))
        return "".join(out), hits


def _pop(g: dict, lang: str) -> str:
    ana = (g.get("analogy") or {}).get(lang)
    why = (g.get("why") or {}).get(lang)
    return ('<span class="gloss-pop" role="tooltip">'
            f'<b>{html.escape(g["term"][lang])}</b>'
            f'<span class="gp-plain">{html.escape(g["plain"][lang])}</span>'
            + (f'<span class="gp-why"><i class="gw-t">'
               f'{html.escape(WHY_TAG[lang])}</i>'
               f'{html.escape(why)}</span>' if why else "")
            + (f'<span class="gp-analogy">{html.escape(ana)}</span>' if ana
               else "") + "</span>")


def stamp_tiers(doc: str, tiers: list[str], lang: str, who: str = "") -> str:
    """Append a level chip to each H2, in document order. The list is
    positional, so it has to be exactly as long as the chapter's real heading
    count — a heading added, dropped or swallowed by a code fence shifts every
    chip after it onto the wrong section, which is worse than no chips."""
    if not tiers:
        return doc
    heads = _H2_RE.findall(doc)
    if len(heads) != len(tiers):
        raise BuildError(
            f"{who}: reading-paths lists {len(tiers)} sections but the unit "
            f"renders {len(heads)}")
    state = [0]

    def repl(m):
        i = state[0]
        state[0] += 1
        tier = tiers[i]
        return (f'<h2 id="{m.group(1)}">{m.group(2)}'
                f'<span class="sec-tier t-{tier}">'
                f'{html.escape(TIER_LABELS[tier][lang])}</span></h2>')

    return _H2_RE.sub(repl, doc)


class Layer:
    """One language's annotator; keeps the set of terms it ever marked."""

    def __init__(self, glosses: dict, lang: str):
        self.glosses = glosses
        self.lang = lang
        self.matcher = Matcher(glosses, lang)
        self.used: set[str] = set()

    @property
    def active(self) -> bool:
        return self.matcher.rx is not None

    def apply(self, doc: str, tiers: list[str] | None,
              who: str = "") -> tuple[str, list[dict]]:
        doc, hits = self.matcher.mark(doc, self.glosses, self.lang, self.used)
        if len(hits) > MAX_PANEL:
            raise BuildError(
                f"{who}: {len(hits)} new terms in one unit "
                f"(max {MAX_PANEL}): "
                + ", ".join(h["id"] for h in hits[:40])
                + "\n  demote the ones a reader can look up in appendix D to "
                  '"priority": "extra" (only core terms are marked)')
        return doc, hits

    def check_coverage(self) -> None:
        """A core term nobody ever marked means its forms list is wrong."""
        missing = sorted(gid for gid, g in self.glosses.items()
                         if marks(g) and g.get("priority") == "core"
                         and gid not in self.used)
        if missing:
            raise BuildError(
                f"glosses never marked in this edition: {', '.join(missing)}"
                "\n  the forms list does not match how the book spells them")
