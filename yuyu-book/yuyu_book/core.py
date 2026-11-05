"""Core utilities: paths, config loading/validation, fence-aware scanning.

All file reads go through read_text(); the whole pipeline must stay
encoding-safe on Windows (the repo had a GBK crash before).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BOOK_DIR.parent
CACHE_DIR = BOOK_DIR / ".cache"

GUIDE_FIELDS = ("question", "deliverable", "boundary")
SOURCE_REQUIRED = ("title", "authority", "kind", "url", "snapshot",
                   "accessed", "license", "scope")
SOURCE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# registry text the book authored for itself, and therefore owes in both languages
MIRRORED_FIELDS = ("title", "authority", "snapshot", "license", "scope")
HAN_RE = re.compile(r"[\u4e00-\u9fff]")
# the subject index files translated terms here instead of under a Latin
# letter; "中" sorts after Z, so the block lands last without a special case
INDEX_CN_LETTER = "中"
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")

ZH_PATTERNS = [
    (re.compile(r"^#\s*前言\s*$"), "front", ("", "前言")),
    (re.compile(r"^#\s*第\s*(\d{1,2})\s*章\s*[：:]?\s*(.+)$"), "num", None),
    (re.compile(r"^#\s*附录\s*([A-D])\s*[：:]?\s*(.+)$"), "apx", None),
]
EN_PATTERNS = [
    (re.compile(r"^#\s*Foreword\s*$"), "front", ("", "Foreword")),
    (re.compile(r"^#\s*Chapter\s+(\d{1,2})[：:]?\s*(.+)$"), "num", None),
    (re.compile(r"^#\s*Appendix\s+([A-D])[：:]?\s*(.+)$"), "apx", None),
]


class BuildError(Exception):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path):
    return json.loads(read_text(path))


def dump_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


# ---------------------------------------------------------------- units ----

@dataclass
class MermaidBlock:
    uid: str
    src: str
    file: str
    line: int


@dataclass
class Unit:
    id: str
    kind: str                       # front | chapter | appendix
    lang: str
    no: str                         # "第 2 章" / "Chapter 2" / ""
    title: str                      # normalized display title
    md: str                         # body without H1, mermaid replaced
    blocks: list = field(default_factory=list)   # MermaidBlock
    code_langs: list = field(default_factory=list)  # fence info, document order
    path: str = ""                  # repo-relative posix path
    anchor: str = ""                # article id used across the book

    @property
    def display(self) -> str:
        if not self.no:
            return self.title
        return f"{self.no}　{self.title}" if self.lang == "zh" \
            else f"{self.no}: {self.title}"

    @property
    def eyebrow(self) -> str:
        return self.no or ("前言" if self.lang == "zh" else "Foreword")

    @property
    def no_plain(self) -> str:
        """Short gutter label: '01' for chapter 1, 'A' for 附录 A / Appendix A."""
        digits = "".join(c for c in self.no if c.isdigit())
        if digits:
            return digits.zfill(2)
        tail = self.no.split()[-1] if self.no else ""
        if tail.isascii() and tail.isalpha():
            return tail.upper()
        return re.sub(r"\s+", "", self.no)


def extract_mermaid(text: str, file: str):
    """Return (body_with_placeholders, blocks, code_langs). Fence-aware;
    other fences are tracked so their content is never mistaken for
    structure, and their info strings survive as a language label."""
    lines = text.split("\n")
    out, blocks, langs, fence, buf, start = [], [], [], None, None, 0
    for n, line in enumerate(lines, 1):
        m = FENCE_RE.match(line)
        if m:
            token, info = m.group(1), m.group(2).strip()
            if fence is None:
                start = n
                if info == "mermaid":
                    fence, buf = token, []
                else:
                    fence = token
                    langs.append(info.split()[0] if info else "")
                    out.append(line)
                continue
            if token[0] == fence[0] and len(token) >= len(fence) and not info:
                if buf is not None:
                    src = "\n".join(buf)
                    uid = hashlib.sha1(
                        f"{file}|{start}|{src}".encode("utf-8")).hexdigest()[:12]
                    blocks.append(MermaidBlock(uid, src, file, start))
                    if out and out[-1].strip():
                        out.append("")
                    out.append(f"@@MM:{uid}@@")
                    buf = None
                else:
                    out.append(line)
                fence = None
                continue
            if buf is not None:
                buf.append(line)
            else:
                out.append(line)
            continue
        if buf is not None:
            buf.append(line)
        else:
            out.append(line)
    if fence is not None:
        raise BuildError(f"{file}: unclosed code fence at line {start}")
    body = "\n".join(out)
    # a placeholder must stand alone, or markdown folds it into the
    # surrounding block (and renders the diagram inside a <pre>)
    body = re.sub(r"(@@MM:[0-9a-f]{12}@@\n)(?=\S)", r"\1\n", body)
    return body, blocks, langs


def normalize_h1(text: str, lang: str, file: str):
    """Fence-aware: first top-level H1 becomes (no, title); the line is
    blanked out (line numbers stay file-true) and the heading is
    re-synthesized at render time with a unified style."""
    lines = text.split("\n")
    fence = None
    for n, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if m:
            token, info = m.group(1), m.group(2).strip()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not info:
                fence = None
            continue
        if fence is not None or not line.startswith("# "):
            continue
        rest = line[2:].strip()
        patterns = ZH_PATTERNS if lang == "zh" else EN_PATTERNS
        for rx, kind, fixed in patterns:
            g = rx.match(line)
            if not g:
                continue
            if kind == "front":
                no, title = fixed
                # blank the line rather than drop it: MermaidBlock.line and
                # every "file:line" in build errors must stay true for the
                # author editing this very file
                body = "\n".join(lines[:n] + [""] + lines[n + 1:])
                return no, title, body
            num = g.group(1).upper() if kind == "apx" else g.group(1)
            raw = g.group(2).strip()
            raw = re.sub(r"\s+--\s+", " — ", raw)
            raw = re.sub(r"\s{2,}", " ", raw)
            if kind == "apx":
                no = f"附录 {num}" if lang == "zh" else f"Appendix {num}"
            else:
                no = (f"第 {int(num)} 章" if lang == "zh"
                      else f"Chapter {int(num)}")
            body = "\n".join(lines[:n] + [""] + lines[n + 1:])
            return no, raw, body
        raise BuildError(f"{file}:{n + 1}: unrecognised H1 {line!r}")
    raise BuildError(f"{file}: no top-level H1 found")


def load_unit(unit_def: dict, kind: str, lang: str, repo_root: Path) -> Unit:
    rel = unit_def[lang]
    path = repo_root / rel
    if not path.exists():
        raise BuildError(f"unit {unit_def['id']}: missing file {rel}")
    text = read_text(path)
    no, title, body = normalize_h1(text, lang, rel)
    body, blocks, langs = extract_mermaid(body, rel)
    anchor = (unit_def["id"] if kind == "front" else unit_def["id"])
    return Unit(id=unit_def["id"], kind=kind, lang=lang, no=no, title=title,
                md=body, blocks=blocks, code_langs=langs, path=rel,
                anchor=f"{unit_def['id']}" if kind == "front" else unit_def["id"])


# ------------------------------------------------------------- configs ----

def expected_ids(manifest: dict) -> list[str]:
    ids = [manifest["front"]["id"]]
    for part in manifest["parts"]:
        ids.extend(u["id"] for u in part["units"])
    ids.extend(a["id"] for a in manifest["appendices"])
    return ids


def unit_stream(manifest: dict):
    """Yield (unit_def, kind, part) in book order."""
    yield manifest["front"], "front", None
    for part in manifest["parts"]:
        for unit in part["units"]:
            yield unit, "chapter", part
    for apx in manifest["appendices"]:
        yield apx, "appendix", None


def validate_configs(manifest: dict, sources: dict) -> None:
    errors: list[str] = []
    ids = expected_ids(manifest)
    if len(ids) != len(set(ids)):
        errors.append("duplicate unit ids in manifest")

    for unit_def, kind, _part in unit_stream(manifest):
        for lang in ("zh", "en"):
            p = REPO_ROOT / unit_def[lang]
            if not p.exists():
                errors.append(f"unit {unit_def['id']}: missing {lang} file "
                              f"{unit_def[lang]}")

    guides = manifest.get("guides", {})
    if set(guides) != set(ids):
        missing = sorted(set(ids) - set(guides))
        extra = sorted(set(guides) - set(ids))
        if missing:
            errors.append(f"guides missing for: {', '.join(missing)}")
        if extra:
            errors.append(f"guides for unknown units: {', '.join(extra)}")
    for uid, guide in guides.items():
        for f in GUIDE_FIELDS:
            entry = guide.get(f) or {}
            for lang in ("zh", "en"):
                if not (entry.get(lang) or "").strip():
                    errors.append(f"guide {uid}.{f}.{lang} is empty")
        for sid in guide.get("sources", []):
            if sid not in sources:
                errors.append(f"guide {uid}: unknown source id {sid!r}")

    for sid, src in sources.items():
        if not SOURCE_ID_RE.match(sid):
            errors.append(f"source id {sid!r} not [a-z0-9-]+")
        for f in SOURCE_REQUIRED:
            if not str(src.get(f, "")).strip():
                errors.append(f"source {sid}: field {f} missing/empty")
        url = src.get("url", "")
        if not url.startswith("https://"):
            errors.append(f"source {sid}: url must be https")
        kind = src.get("kind")
        pinned = src.get("pinned") or {}
        if kind == "github" and not (pinned.get("tag") or pinned.get("commit")):
            errors.append(f"source {sid}: github refs must pin tag or commit")
        if kind == "npm" and not pinned.get("version"):
            errors.append(f"source {sid}: npm refs must pin version")
        if kind == "community" and (src.get("normative") is not False
                                    or not src.get("accessed")):
            errors.append(f"source {sid}: community refs need "
                          "normative:false + accessed date")
        if kind == "community" and pinned.get("commit"):
            if len(pinned["commit"]) < 40:
                errors.append(f"source {sid}: commit must be full sha")
        # Everything below is text *we* wrote about a source, not text from it,
        # so the English edition owns an English copy of it: a forum thread's
        # Chinese title is searchable by URL and post id, and an English reader
        # deserves to know what it says.
        for field in MIRRORED_FIELDS:
            value = str(src.get(field, ""))
            mirror = str(src.get(f"{field}_en", ""))
            if HAN_RE.search(value) and not mirror.strip():
                errors.append(f"source {sid}: {field} carries Chinese, so it "
                              f"needs {field}_en for the English edition")
            if mirror and HAN_RE.search(mirror):
                errors.append(f"source {sid}: {field}_en still carries Chinese")

    if errors:
        raise BuildError("config invalid:\n  " + "\n  ".join(errors))


def load_configs():
    manifest = load_json(BOOK_DIR / "manifest.json")
    sources = load_json(BOOK_DIR / "sources.json")
    validate_configs(manifest, sources)
    return manifest, sources
