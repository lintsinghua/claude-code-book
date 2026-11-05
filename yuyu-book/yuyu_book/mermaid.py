"""Mermaid pre-rendering: each diagram source is rendered to SVG once by a
headless Edge/Chromium page that imports mermaid ESM from node_modules, and
cached under .cache/mermaid keyed by (mermaid version, browser version, src).

Render-id prefixing (uid) is what keeps ~160 inline SVGs from colliding on
internal ids: mermaid prefixes every generated id/selector with the render id.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

from .core import (BOOK_DIR, CACHE_DIR, REPO_ROOT, BuildError, FENCE_RE,
                   MermaidBlock, read_text)

MERMAID_PKG = REPO_ROOT / "node_modules" / "mermaid" / "package.json"
MERMAID_ESM = REPO_ROOT / "node_modules" / "mermaid" / "dist" / "mermaid.esm.min.mjs"
MM_DIR = CACHE_DIR / "mermaid"

# Book palette (shared with style.py tokens) — diagrams must look like the
# book's own plates, not like library defaults.
THEME = {
    "themeVariables": {
        "fontFamily": "'PingFang SC','Microsoft YaHei','Segoe UI',sans-serif",
        "fontSize": "13px",
        "primaryColor": "#F3EAD8",
        "primaryTextColor": "#26221B",
        "primaryBorderColor": "#8A6B3F",
        "secondaryColor": "#E7D9BC",
        "tertiaryColor": "#FBF6EC",
        "lineColor": "#6E5B3A",
        "textColor": "#26221B",
        "mainBkg": "#FBF6EC",
        "nodeBorder": "#8A6B3F",
        "clusterBkg": "#F6F0E2",
        "clusterBorder": "#C8B691",
        "edgeLabelBackground": "#FBF6EC",
        "titleColor": "#26221B",
        "actorBkg": "#F3EAD8",
        "actorBorder": "#8A6B3F",
        "actorTextColor": "#26221B",
        "signalColor": "#6E5B3A",
        "signalTextColor": "#26221B",
        "labelColor": "#26221B",
        "stateBkg": "#F3EAD8",
        "stateBorder": "#8A6B3F",
        "classBkg": "#FBF6EC",
        "ganttTitleColor": "#26221B",
        "taskBkgColor": "#C8A45C",
        "taskBorderColor": "#8A6B3F",
        "doneTaskBkgColor": "#9A8C6F",
        "critBkgColor": "#B4472F",
        "activeTaskBkgColor": "#E7D9BC",
    },
    "flowchart": {"htmlLabels": True, "curve": "basis"},
    "themeCSS": ".node rect,.node circle,.node ellipse{filter:none}"
                " .node .label text{fill:#26221B}",
}

# ------- re-inking the author's own colours ------------------------------
# The theme above only reaches nodes the manuscript left alone. It does not
# reach the ~900 ``classDef``/``style`` directives that carry Material and
# Tailwind hexes, and those read as a different product than the book. The
# manuscript stays the source of truth, so the build re-inks them: the author's
# colour chooses a node's *role*, the book chooses how that role looks. Every
# mapped fill is a light tint, which is why ``color:`` is replaced rather than
# translated -- the authors' ``color:#fff`` would vanish on a tint.
BOOK_FAMILIES = {
    #            fill      stroke    text
    "neutral": ("#F3EAD8", "#8A6B3F", "#26221B"),
    "card":    ("#FFFDF8", "#D2C4A6", "#26221B"),
    "info":    ("#E4EBF2", "#4C7093", "#26435B"),
    "good":    ("#E5EEE6", "#4E6E5D", "#2C4638"),
    "warn":    ("#F8EBCF", "#A9752A", "#6A4715"),
    "danger":  ("#F6E3DD", "#B4472F", "#7C2E1B"),
    "plum":    ("#EFE7E9", "#7D5A6B", "#4A3441"),
}

_DIRECTIVE_RE = re.compile(r"^([ \t]*(?:classDef|style)[ \t]+\S+[ \t]+)(.*)$",
                           re.MULTILINE)
_HEX_PROP_RE = re.compile(r"\b(fill|stroke|color)[ \t]*:[ \t]*(#[0-9a-fA-F]{3,8})")


def _hsl(hexc: str) -> tuple[float, float, float]:
    """Parse #rgb / #rrggbb (extra alpha digits are ignored) into 0-1 HSL."""
    d = hexc[1:]
    if len(d) in (3, 4):
        d = "".join(c * 2 for c in d[:3])
    else:
        d = d[:6]
    r, g, b = (int(d[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hi, lo, delta = max(r, g, b), min(r, g, b), max(r, g, b) - min(r, g, b)
    l = (hi + lo) / 2
    if delta == 0:
        return 0.0, 0.0, l
    s = delta / (2 - hi - lo) if l > 0.5 else delta / (hi + lo)
    if hi == r:
        h = ((g - b) / delta + (6 if g < b else 0)) / 6
    elif hi == g:
        h = ((b - r) / delta + 2) / 6
    else:
        h = ((r - g) / delta + 4) / 6
    return h * 360, s, l


def _family(hexc: str) -> str:
    """Which book family an author colour stands for.

    Lightness only picks between the two near-white neutrals; no shipped
    directive fills a node dark, so a dark hex is read for its hue like any
    other and comes back as that hue's tint.
    """
    h, s, l = _hsl(hexc)
    if s < 0.14:
        return "card" if l > 0.88 else "neutral"
    if h < 15 or h >= 345:
        return "danger"
    if h < 75:
        return "warn"
    if h < 175:
        return "good"
    if h < 250:
        return "info"
    if h < 300:
        return "plum"
    return "danger"                       # pinks and magentas group with red


def _style_fingerprint() -> str:
    payload = json.dumps({"theme": THEME, "families": BOOK_FAMILIES},
                         sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]


def reink_colors(src: str) -> str:
    """Rewrite fill/stroke/color hexes on classDef and style directives."""
    def one(m: re.Match) -> str:
        head, decls = m.group(1), m.group(2)
        props = _HEX_PROP_RE.findall(decls)
        if not props:
            return m.group(0)
        anchor = dict(props).get("fill") or dict(props).get("stroke") \
            or dict(props).get("color")
        fill, stroke, text = BOOK_FAMILIES[_family(anchor)]
        repl = {"fill": fill, "stroke": stroke, "color": text}
        return head + _HEX_PROP_RE.sub(
            lambda p: f"{p.group(1)}:{repl[p.group(1)]}", decls)

    return _DIRECTIVE_RE.sub(one, src)


_STYLE_VER = _style_fingerprint()

_H_RE = re.compile(r"^(#{2,3})\s+(.*)$")


def captions_for(text: str, blocks: list[MermaidBlock],
                 fallback: str = "架构示意") -> dict[str, str]:
    """Nearest preceding H2 per block, fence-aware.

    ``block.line`` is a line of ``text``, so a heading sitting directly
    above the opening fence still counts; ``fallback`` applies only to a
    diagram with no heading above it at all.
    """
    by_line = {b.line: b.uid for b in blocks}
    caps: dict[str, str] = {}
    last, fence = "", None
    for line, raw in enumerate(text.split("\n"), 1):
        uid = by_line.get(line)
        if uid is not None and last:
            caps[uid] = last
        m = FENCE_RE.match(raw)
        if m:
            token, info = m.group(1), m.group(2).strip()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not info:
                fence = None
            continue
        if fence is not None:
            continue
        hm = _H_RE.match(raw)
        if hm and len(hm.group(1)) == 2:
            last = hm.group(2).strip()
    for b in blocks:
        caps.setdefault(b.uid, fallback)
    return caps


def _cache_key(src: str, mm_ver: str, browser_ver: str) -> Path:
    """The palette fingerprint belongs in the key: without it, editing a token
    above would keep serving the SVGs rendered under the old one."""
    h = hashlib.sha1(
        f"{_STYLE_VER}|{mm_ver}|{browser_ver}|{src}".encode("utf-8"))
    return MM_DIR / f"{h.hexdigest()[:24]}.svg"


def source_fallback(blocks: list[MermaidBlock], caps: dict[str, str]):
    return {b.uid: (caps.get(b.uid, ""),
                    f'<pre class="mermaid-source">{html.escape(b.src)}</pre>')
            for b in blocks}


_HARNESS = """<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>mm</title>
</head><body><div id="stage" style="position:absolute;left:-99999px;top:0"></div>
<script type="module">
let mermaid;
try {{
  mermaid = (await import("{esm_url}")).default;
  mermaid.initialize({{
    startOnLoad: false, securityLevel: 'strict',
    theme: 'base', themeVariables: {theme_json},
    flowchart: {flow_json},
  }});
  window.__harnessError = null;
}} catch (e) {{
  window.__harnessError = String(e && e.stack || e);
}}
window.__render = async (id, src) => {{
  if (!mermaid) throw new Error('harness not loaded: ' + window.__harnessError);
  const off = document.getElementById('stage');
  off.innerHTML = '';
  const {{ svg }} = await mermaid.render(id, src);
  return svg;
}};
window.__ready = true;
</script>"""


def render_all(blocks: list[MermaidBlock], caps: dict[str, str],
               browser_path: str | None = None) -> dict[str, tuple[str, str]]:
    """Render every unique block (cache-first). Returns uid -> (caption, svg)."""
    mm_ver = json.loads(read_text(MERMAID_PKG))["version"] if MERMAID_PKG.exists() else "?"
    if not MERMAID_ESM.exists():
        raise BuildError("node_modules/mermaid missing — run npm ci first")
    MM_DIR.mkdir(parents=True, exist_ok=True)

    out: dict[str, tuple[str, str]] = {}
    todo: dict[str, MermaidBlock] = {}
    browser_ver = "edge-static"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = None
            launched = []
            if browser_path:
                launched = [("executable", browser_path)]
            else:
                launched = [("msedge", None), ("chrome", None), ("chromium", None)]
            last_err = None
            for kind, path in launched:
                try:
                    browser = (p.chromium.launch(executable_path=path)
                               if path else p.chromium.launch(
                                   channel=kind,
                                   args=["--allow-file-access-from-files"])
                               if kind in ("msedge", "chrome")
                               else p.chromium.launch(
                                   args=["--allow-file-access-from-files"]))
                    break
                except Exception as e:  # noqa: BLE001
                    last_err = e
            if browser is None:
                raise BuildError(f"no browser for mermaid render: {last_err}")
            browser_ver = browser.version
            page = browser.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console",
                    lambda m: errors.append(m.text) if m.type == "error" else None)
            esm = MERMAID_ESM.resolve().as_uri()
            harness = MM_DIR / "_harness.html"
            harness.write_text(_HARNESS.format(
                esm_url=esm,
                theme_json=json.dumps(THEME["themeVariables"]),
                flow_json=json.dumps(THEME["flowchart"])), encoding="utf-8")
            page.goto(harness.resolve().as_uri(), wait_until="load")
            try:
                page.wait_for_function("() => window.__ready === true", timeout=30000)
            except Exception as e:  # noqa: BLE001
                why = page.evaluate("() => window.__harnessError") or \
                    (errors[-3:] if errors else str(e))
                raise BuildError(f"mermaid harness failed to load ({esm}): {why}") from e
            page.evaluate("() => window.__render('warmup','flowchart LR\\nA-->B')")
            for b in blocks:
                if b.uid in out:
                    continue
                src = reink_colors(b.src)
                key = _cache_key(src, mm_ver, browser_ver)
                if key.exists():
                    svg = read_text(key)
                else:
                    rid = f"mm-{b.uid}"
                    try:
                        svg = page.evaluate(
                            "([id, src]) => window.__render(id, src)",
                            [rid, src])
                    except Exception as e:  # noqa: BLE001
                        raise BuildError(
                            f"mermaid render failed {b.file}:{b.line} "
                            f"({b.uid}): {e}; page: {errors[-2:]}") from e
                    if "<svg" not in svg:
                        raise BuildError(f"mermaid produced no svg {b.file}:{b.line}")
                    # strip mermaid's injected width hacks for fluid layout
                    svg = re.sub(r'<svg([^>]*?)style="max-width: [\d.]+px;"',
                                 r'<svg\1style="max-width: 100%;"', svg, count=1)
                    key.write_text(svg, encoding="utf-8")
                out[b.uid] = (caps[b.uid], svg)
            browser.close()
    except ImportError as e:
        raise BuildError("playwright not installed — pip install -r requirements.txt") from e
    return out
