"""The book's stylesheet — tokens, typography, components, print & dark mode.

Design language「舆」: bronze fittings, ink-black lacquer, cinnabar accents on
warm paper, with a chariot-wheel (辐) motif as the recurring ornament. No web
fonts, no JS; everything must survive offline file:// viewing and A4 print.
"""
from __future__ import annotations

import math
import random

WHEEL_SVG = """<svg class="wheel" viewBox="0 0 200 200" role="img" aria-hidden="true">
<defs><line id="spoke" x1="100" y1="100" x2="100" y2="18"
 stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></defs>
<circle cx="100" cy="100" r="88" fill="none" stroke="currentColor" stroke-width="5"/>
<circle cx="100" cy="100" r="72" fill="none" stroke="currentColor" stroke-width="2" opacity=".55"/>
<circle cx="100" cy="100" r="16" fill="none" stroke="currentColor" stroke-width="7"/>
<circle cx="100" cy="100" r="4" fill="currentColor"/>
<g opacity=".9">
<use href="#spoke"/><use href="#spoke" transform="rotate(15 100 100)"/>
<use href="#spoke" transform="rotate(30 100 100)"/><use href="#spoke" transform="rotate(45 100 100)"/>
<use href="#spoke" transform="rotate(60 100 100)"/><use href="#spoke" transform="rotate(75 100 100)"/>
<use href="#spoke" transform="rotate(90 100 100)"/><use href="#spoke" transform="rotate(105 100 100)"/>
<use href="#spoke" transform="rotate(120 100 100)"/><use href="#spoke" transform="rotate(135 100 100)"/>
<use href="#spoke" transform="rotate(150 100 100)"/><use href="#spoke" transform="rotate(165 100 100)"/>
<use href="#spoke" transform="rotate(180 100 100)"/><use href="#spoke" transform="rotate(195 100 100)"/>
<use href="#spoke" transform="rotate(210 100 100)"/><use href="#spoke" transform="rotate(225 100 100)"/>
<use href="#spoke" transform="rotate(240 100 100)"/><use href="#spoke" transform="rotate(255 100 100)"/>
<use href="#spoke" transform="rotate(270 100 100)"/><use href="#spoke" transform="rotate(285 100 100)"/>
<use href="#spoke" transform="rotate(300 100 100)"/><use href="#spoke" transform="rotate(315 100 100)"/>
<use href="#spoke" transform="rotate(330 100 100)"/><use href="#spoke" transform="rotate(345 100 100)"/>
</g></svg>"""


_WHEEL_N = 0


def wheel(size: int = 44) -> str:
    """Each instance needs its own spoke id — the SVG is inlined repeatedly."""
    global _WHEEL_N
    _WHEEL_N += 1
    sid = f"spoke{_WHEEL_N}"
    return (WHEEL_SVG
            .replace('viewBox', f'width="{size}" height="{size}" viewBox', 1)
            .replace('id="spoke"', f'id="{sid}"')
            .replace('href="#spoke"', f'href="#{sid}"'))


# ------------------------------------------------------- hand-inked marks ----
# Callouts used to open with a font glyph (✦ ⚠ ↗ ◎ ※), which is the one place in
# the book where the typeface had to speak for the drawing. These are the same
# five marks inked by hand in the emblems' idiom: a ring left open where the
# brush lifted, a triangle whose corners do not meet at a perfect angle, pads
# and stubs that route like a trace. Inline, currentColor, no ids -- a callout
# mark is repeated some seventy times per edition.
INK_MARKS = {
    "tip": ('<path d="M13.3 5.2C12.3 2.9 10.1 1.6 7.5 2 4.3 2.4 2 5.2 2.1 8.4'
            'c.1 3.2 2.7 5.7 5.9 5.6 3.1-.1 5.6-2.6 5.7-5.6.1-1.2-.1-2.3-.4-3.2"/>'
            '<path d="M5.2 8.3l2.1 2.3 3.9-5"/>'),
    "warning": ('<path d="M7.3 2.5 13.7 12.8c.3.6-.1 1.2-.7 1.2H3.1c-.7 0-1.1-.6'
                '-.8-1.2L6.6 2.5c.2-.5.5-.5.7 0z"/>'
                '<path d="M8 6.3v3.2"/>'
                '<circle cx="8" cy="11.5" r=".8" fill="currentColor" stroke="none"/>'),
    "info": ('<path d="M3.2 12.7C5.6 10.8 7.9 8.1 10.4 5"/>'
             '<path d="M6.8 4.7 10.6 4.5l.3 3.9"/>'),
    "concept": ('<path d="M8 1.9c3.4 0 6.2 2.7 6.1 6.2C14 11.5 11.4 14.1 8 14.1'
                '4.6 14.1 2 11.4 2 7.9 2 4.5 4.5 1.9 8 1.9z"/>'
                '<circle cx="8.1" cy="7.9" r="2.7" opacity=".7"/>'
                '<circle cx="8" cy="8" r=".9" fill="currentColor" stroke="none"/>'),
    "note": ('<path d="M8 2.5C7.8 6.1 7.8 9.7 8 13.5"/>'
             '<path d="M3.6 4.6C6 7.2 8.5 9.8 12.4 12.4"/>'
             '<path d="M12.4 4.6C10 7.2 7.5 9.8 3.6 12.4"/>'
             '<path opacity=".5" d="M2.7 8c3.5-.2 7.1-.2 10.6 0"/>'),
}


def ink_mark(kind: str) -> str:
    """A callout's drawn mark, or '' for a kind the book has not inked yet."""
    body = INK_MARKS.get(kind)
    if not body:
        return ""
    return (f'<svg class="ink-mark" viewBox="0 0 16 16" aria-hidden="true"'
            f' fill="none" stroke="currentColor" stroke-width="1.4"'
            f' stroke-linecap="round" stroke-linejoin="round">{body}</svg>')


def trace(seed: str) -> str:
    """The wire a chapter head closes on: one hand-run line with pads, a couple
    of stubs and two bends that lift it off the baseline, like a trace routing
    around a via. Seeded by the unit id, so no two chapters draw the same line
    and every rebuild draws the same one."""
    rng = random.Random(seed)
    width, base = 240.0, 11.0
    nodes, x = [], 5.0
    while x < width - 5.0:
        nodes.append((x, base + rng.uniform(-1.4, 1.4)))
        x += rng.uniform(23.0, 41.0)
    nodes.append((width - 5.0, base + rng.uniform(-1.4, 1.4)))
    if len(nodes) > 4:
        for i in rng.sample(range(1, len(nodes) - 1), 2):
            px, _ = nodes[i]
            nodes[i] = (px, base - rng.uniform(3.4, 4.8))
    d = "M{:.1f} {:.1f}".format(*nodes[0])
    for (ax, ay), (bx, by) in zip(nodes, nodes[1:]):
        d += (f"Q{(ax + bx) / 2:.1f} {(ay + by) / 2 + rng.uniform(-.9, .9):.1f}"
              f" {bx:.1f} {by:.1f}")
    out = [f'<path stroke-width="1.3" d="{d}"/>']
    # the wire always lands on a pad at its far end; the rest are wherever the
    # seed put them
    pads = [len(nodes) - 1] + rng.sample(range(len(nodes) - 1),
                                         min(3, len(nodes) - 1))
    for i in pads:
        px, py = nodes[i]
        out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="1.9" '
                   f'stroke-width="1.1"/>')
        if rng.random() < .6:
            down = 1 if py <= base else -1
            out.append(f'<path stroke-width="1" opacity=".65" '
                       f'd="M{px + 2.8:.1f} {py + 2.4 * down:.1f}'
                       f'l{rng.choice((5, 6, 7))} {3.4 * down}"/>')
    ex, ey = nodes[-1]
    out.append(f'<path stroke-width="1.2" d="M{ex + 1.8:.1f} {ey - 3.3:.1f}v6.6"/>')
    return (f'<svg class="ch-trace" viewBox="0 0 250 22" aria-hidden="true"'
            f' fill="none" stroke="currentColor" stroke-linecap="round"'
            f' stroke-linejoin="round">{"".join(out)}</svg>')


def _mini_wheel(cx: float, cy: float, r: float, n: int = 8,
                phase: float = 0.0) -> str:
    """A spoked wheel worked out with arithmetic instead of <defs>/<use>, so it
    can be inlined a hundred times without ever owing the page an id."""
    out = [f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}"/>',
           f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r * .58:.2f}" opacity=".5"/>']
    for i in range(n):
        a = phase + i * 2 * math.pi / n
        out.append(
            f'<path d="M{cx + r * .26 * math.cos(a):.2f} {cy + r * .26 * math.sin(a):.2f}'
            f'L{cx + r * .9 * math.cos(a):.2f} {cy + r * .9 * math.sin(a):.2f}"/>')
    out.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="1" fill="currentColor"'
               ' stroke="none"/>')
    return "".join(out)


def route_map(seed: str, count: int) -> str:
    """The itinerary a part opens on: one road inked in a single run, a station
    ring for every chapter the part holds, a milepost between each pair, and the
    wheel the ride starts from. Seeded by the part id, so no two parts roll the
    same road and a rebuild rolls the same one."""
    count = max(int(count), 1)
    rng = random.Random(f"route:{seed}")
    base, first, last = 20.0, 46.0, 286.0
    if count == 1:
        stops = [(0.5 * (first + last), base)]
    else:
        step = (last - first) / (count - 1)
        stops = [(first + step * i, base + rng.uniform(-1.7, 1.7))
                 for i in range(count)]
    nodes = [(24.0, base)] + stops + [(314.0, base + rng.uniform(-1.2, 1.2))]
    d = "M{:.1f} {:.1f}".format(*nodes[0])
    for (ax, ay), (bx, by) in zip(nodes, nodes[1:]):
        d += (f"Q{(ax + bx) / 2:.1f} {(ay + by) / 2 + rng.uniform(-1.1, 1.1):.1f}"
              f" {bx:.1f} {by:.1f}")
    out = [f'<path stroke-width="1.3" d="{d}"/>',
           f'<g stroke-width="1.1">{_mini_wheel(13, base, 8.4)}</g>']
    for (ax, ay), (bx, by) in zip(stops, stops[1:]):
        # a stone set between the stations, at the height of the road itself
        mx, my = (ax + bx) / 2, (ay + by) / 2 + 4.4
        out.append(f'<path stroke-width="1" opacity=".45" '
                   f'd="M{mx:.1f} {my:.1f}v{rng.uniform(2.6, 3.8):.1f}"/>')
    for i, (sx, sy) in enumerate(stops):
        # the last stop of the part gets a second ring: the far end of the leg
        halo = f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="6" opacity=".35"/>' \
            if i == len(stops) - 1 and count > 1 else ""
        out.append(f'{halo}<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3.3"'
                   f' stroke-width="1.2"/>'
                   f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="1.1" fill="currentColor"'
                   f' stroke="none"/>')
    return (f'<svg class="pd-route" viewBox="0 0 320 40" aria-hidden="true"'
            f' fill="none" stroke="currentColor" stroke-linecap="round"'
            f' stroke-linejoin="round">{"".join(out)}</svg>')


def rut(seed: str) -> str:
    """The mark a chapter closes on: the two ruts the wheels left in the road,
    running out and fraying into dashes, with the grit the ride kicked up. It
    sits where a chapter end used to leave a bare band of paper, and like the
    head wire it is seeded by the unit id."""
    rng = random.Random(f"rut:{seed}")
    top, low = 8.4, 13.6

    def line(y0: float) -> str:
        nodes, x = [], 26.0
        while x < 190.0:
            nodes.append((x, y0 + rng.uniform(-.75, .75)))
            x += rng.uniform(24.0, 44.0)
        nodes.append((198.0, y0 + rng.uniform(-.4, .4)))
        d = "M{:.1f} {:.1f}".format(*nodes[0])
        for (ax, ay), (bx, by) in zip(nodes, nodes[1:]):
            d += (f"Q{(ax + bx) / 2:.1f} {(ay + by) / 2 + rng.uniform(-.6, .6):.1f}"
                  f" {bx:.1f} {by:.1f}")
        return d

    out = [f'<g stroke-width="1.25">{_mini_wheel(13, 11, 8.8)}</g>',
           f'<path stroke-width="1.35" d="{line(top)}"/>',
           f'<path stroke-width="1.25" opacity=".85" d="{line(low)}"/>']
    for i, (x, w) in enumerate(((204, 13.0), (221, 9.0), (233, 5.0))):
        y = (top, low)[i % 2] + rng.uniform(-.9, .9)
        out.append(f'<path stroke-width="1.15" opacity="{.62 - .12 * i:.2f}"'
                   f' d="M{x} {y:.1f}h{w}"/>')
    for _ in range(rng.randint(2, 3)):
        sx, sy = rng.uniform(40, 186), rng.uniform(top + 3.4, low + 3.2)
        out.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{rng.uniform(.6, 1.1):.1f}"'
                   f' opacity=".45" fill="currentColor" stroke="none"/>')
    return (f'<svg class="ch-rut" viewBox="0 0 250 22" aria-hidden="true"'
            f' fill="none" stroke="currentColor" stroke-linecap="round"'
            f' stroke-linejoin="round">{"".join(out)}</svg>')


def itinerary(seed: str, legs: list[tuple[str, list[tuple[str, str]]]],
              dashed_last: bool = True, start_label: str = "") -> str:
    """The whole book as one road, for the page that tells readers where to
    start: a leg per part, a ring per unit of that leg, and the appendices
    running dashed at the end because they are a siding, not a stop on the
    ride. Serpentine so the line never lifts off the sheet, seeded so the map
    is the same map every build. The drawing is decorative -- the list under it
    carries the same route as text, and links."""
    rng = random.Random(f"map:{seed}")
    width, x_lo, x_hi = 760.0, 58.0, 702.0
    y0, dy, pad = 54.0, 76.0, 96.0
    height = y0 + dy * (len(legs) - 1) + 38
    out: list[str] = []

    def run(nodes: list[tuple[float, float]]) -> str:
        d = "M{:.1f} {:.1f}".format(*nodes[0])
        for (ax, ay), (bx, by) in zip(nodes, nodes[1:]):
            d += (f"Q{(ax + bx) / 2:.1f} {(ay + by) / 2 + rng.uniform(-1.4, 1.4):.1f}"
                  f" {bx:.1f} {by:.1f}")
        return d

    for i, (label, stops) in enumerate(legs):
        y = y0 + i * dy
        right = i % 2 == 0
        d = 1 if right else -1
        sx, ex = (x_lo, x_hi) if right else (x_hi, x_lo)
        first = sx + d * pad
        n = max(len(stops), 1)
        xs = [first] if n == 1 else [first + (ex - d * 14 - first) * k / (n - 1)
                                     for k in range(n)]
        ys = [y + rng.uniform(-2.2, 2.2) for _ in range(n)]
        dashed = dashed_last and i == len(legs) - 1
        road = f'<path stroke-width="1.3" d="{run([(sx, y)] + list(zip(xs, ys)) + [(ex, y)])}"'
        if dashed:
            road = road[:-1] + ' stroke-dasharray="6 5" opacity=".8"/>'
        else:
            road += "/>"
        out.append(road)
        if i + 1 < len(legs):
            ny = y + dy
            out.append(f'<path stroke-width="1.3" d="M{ex:.1f} {y:.1f}'
                       f'C{ex + d * 34:.1f} {y + dy * .18:.1f}'
                       f' {ex + d * 34:.1f} {ny - dy * .18:.1f} {ex:.1f} {ny:.1f}"/>')
        out.append(f'<text x="{sx + d * 4:.1f}" y="{y - 21:.1f}" '
                   f'text-anchor="{"start" if right else "end"}">{label}</text>')
        for (ax, ay), (bx, by) in zip(list(zip(xs, ys)), list(zip(xs, ys))[1:]):
            out.append(f'<path stroke-width="1" opacity=".4" '
                       f'd="M{(ax + bx) / 2:.1f} {(ay + by) / 2 + 4.2:.1f}v3.4"/>')
        for (anchor, ring), px, py in zip(stops, xs, ys):
            r = 2.7 if dashed else 3.6
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}"'
                       f' stroke-width="1.2"/>'
                       f'<circle cx="{px:.1f}" cy="{py:.1f}" r="1.1" '
                       f'fill="currentColor" stroke="none"/>'
                       f'<text x="{px:.1f}" y="{py + 17:.1f}" '
                       f'text-anchor="middle">{ring}</text>')
        if i == 0:
            wx = sx - d * 22
            out.append(f'<g stroke-width="1.2">{_mini_wheel(wx, y, 9.2)}</g>')
            if start_label:
                out.append(f'<text x="{wx:.1f}" y="{y + 23:.1f}" '
                           f'text-anchor="middle">{start_label}</text>')
        if i == len(legs) - 1:
            out.append(f'<circle cx="{ex + d * 16:.1f}" cy="{y:.1f}" r="5.4" '
                       f'stroke-width="1.1" opacity=".75"/>'
                       f'<circle cx="{ex + d * 16:.1f}" cy="{y:.1f}" r="2.2"/>')
    return (f'<svg class="itinerary" viewBox="0 0 {width:.0f} {height:.0f}"'
            f' aria-hidden="true" fill="none" stroke="currentColor"'
            f' stroke-linecap="round" stroke-linejoin="round">{"".join(out)}</svg>')


def key_mark(kind: str) -> str:
    """The legend for the route map: the wheel that starts the ride, one ring
    per stop, and the dashed siding the appendices run down. Worked out at the
    same radii as the map itself, so the key shows what the sheet actually
    draws rather than a plumper stand-in."""
    body = {
        "wheel": _mini_wheel(11, 11, 8.6),
        "ring": ('<circle cx="11" cy="11" r="3.6" stroke-width="1.2"/>'
                 '<circle cx="11" cy="11" r="1.1" fill="currentColor" stroke="none"/>'),
        "siding": ('<path stroke-width="1.3" stroke-dasharray="6 5" opacity=".8"'
                   ' d="M2 11h13.5"/>'
                   '<circle cx="18.6" cy="11" r="2.6" stroke-width="1.1"/>'),
    }[kind]
    return (f'<svg class="rmk rmk-{kind}" viewBox="0 0 22 22" aria-hidden="true"'
            f' fill="none" stroke="currentColor" stroke-width="1.2"'
            f' stroke-linecap="round" stroke-linejoin="round">{body}</svg>')


def knot() -> str:
    """The mark a section break carries: two pads joined by a coupling, drawn
    once and repeated ~110 times per edition, where a typed ❖ used to sit."""
    return ('<svg class="hr-knot" viewBox="0 0 56 14" aria-hidden="true"'
            ' fill="none" stroke="currentColor" stroke-width="1.2"'
            ' stroke-linecap="round">'
            '<path d="M2.4 7.2c3.6-.3 7.6-.3 11.6-.1"/>'
            '<circle cx="17.2" cy="7" r="2.7"/>'
            '<path d="M19.9 7c2.8-3.4 5.3-3.4 8.1 0s5.3 3.4 8.1 0"/>'
            '<circle cx="38.8" cy="7" r="2.7"/>'
            '<path d="M41.5 6.9c4-.2 8-.2 12.1.1"/></svg>')


CSS = r"""
:root{
  --paper:#FBF7EF; --paper-2:#F3EAD8; --paper-3:#EADFC7;
  --card:#FFFDF8; --ink:#26221B; --ink-2:#5C5448; --ink-3:#675F4F;
  --line:#E3D8C1; --line-2:#D2C4A6;
  --bronze:#8A6B3F; --bronze-2:#C8A45C; --bronze-3:#6E5B3A;
  --cinnabar:#B4472F; --jade:#4E6E5D; --sky:#4C7093;
  --code-bg:#211E19; --code-fg:#EDE6D6; --code-line:#3A352C;
  --serif:"Noto Serif SC","Source Han Serif SC","思源宋体","Songti SC",
          "SimSun",Georgia,"Times New Roman",serif;
  --kai:"Kaiti SC","STKaiti","KaiTi","楷体","AR PL KaitiM GB",var(--serif);
  --sans:"PingFang SC","Microsoft YaHei","Segoe UI",system-ui,-apple-system,sans-serif;
  --mono:"JetBrains Mono","Cascadia Code","SF Mono",Consolas,Menlo,monospace;
  --measure:46rem;   /* the prose column — ~43 CJK characters a line */
  --furniture:56rem; /* plates, tables, code and reference grids fill this */
  /* two corners and a circle: --r-1 turns a tag, --r-2 turns a box, and 999px
     is left to the things that really are pills (a scrollbar, a 3px rule).
     A fifth radius is a fifth book on the same sheet. */
  --r-1:4px; --r-2:10px;
}
/* Latin needs a shorter measure than CJK for the same comfort: 46rem of 17px
   Palatino is a 90-character line, which no one reads without losing the
   place. Both languages keep a small furniture/prose gap so the wide blocks
   are a step up, not a chasm. */
body.lang-en{--measure:37rem;--furniture:53rem}
@media (prefers-color-scheme:dark){
  body:not(.force-light){
    --paper:#181814; --paper-2:#22221C; --paper-3:#2B2A22;
    --card:#1E1D18; --ink:#E9E4D8; --ink-2:#BDB4A2; --ink-3:#A59C8A;
    --line:#37342A; --line-2:#4A4536;
    --bronze:#C8A45C; --bronze-2:#8A6B3F; --bronze-3:#DCC188;
    --cinnabar:#E07B5F; --jade:#9DBFA9; --sky:#8FB2D4;
    --code-bg:#12110D; --code-fg:#E4DDCC;
  }
  body:not(.force-light) .diagram-frame{background:#F5EFE2}
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);
  font:400 17px/1.8 var(--serif);
  font-feature-settings:"kern";text-rendering:optimizeLegibility;
  -webkit-font-smoothing:antialiased}
body.lang-en{font-family:"Iowan Old Style",Palatino,Georgia,var(--serif);
  line-height:1.75;font-size:17px}
/* book blocks: flush both edges; CJK breaks strictly, Latin hyphenates */
.chapter-body p,.chapter-body li{text-align:justify}
body.lang-zh .chapter-body p,body.lang-zh .chapter-body li,
body.lang-zh .chapter-body blockquote{line-break:strict}
body.lang-en .chapter-body p,body.lang-en .chapter-body li{hyphens:auto}
/* ragged-right beats a grid of gaps once the line is short enough that one
   unbreakable token costs the whole row its spacing -- see the contract test */
@media (max-width:30rem){body.lang-zh .chapter-body p,body.lang-zh .chapter-body li{text-align:left}}
::selection{background:rgba(200,164,92,.32)}
a{color:inherit}
a.ext::after{content:"↗";font-size:.72em;vertical-align:.15em;
  margin-inline:.12em .2em;color:var(--bronze);font-family:var(--sans)}
a.xref{color:var(--bronze-3);text-decoration:none;
  border-bottom:1px dotted var(--bronze-2)}
a.xref:hover{color:var(--cinnabar);border-bottom-color:var(--cinnabar)}
h1,h2,h3,h4{font-family:var(--sans);font-weight:700;line-height:1.35;
  color:var(--ink);letter-spacing:.01em}

/* ------- shell & rail ------- */
.sheet{max-width:calc(var(--measure) + 4rem);margin:0 auto;padding:0 2rem}
/* A wide screen splits the column in two widths — see the reading-column rule
   at the end of this sheet, which has to come last because every component
   below sets its own `margin` shorthand. */
nav.rail{display:none;position:fixed;inset:0 auto 0 0;width:17rem;
  overflow-y:auto;background:var(--paper-2);border-right:1px solid var(--line);
  padding:1.6rem 1.1rem 3rem;font-family:var(--sans);font-size:.82rem;
  scrollbar-width:thin}
/* the wide-screen block has to come after the base rule above: `nav.rail` and
   `nav.rail` are equally specific, so a media query written first simply loses
   and the reader gets the reserved gutter with no rail in it */
@media (min-width:1360px){
  body{padding-left:17.5rem}
  .sheet{max-width:var(--furniture)}
  nav.rail{display:block}
}
nav.rail .rail-title{font-size:.72rem;letter-spacing:.35em;color:var(--bronze);
  text-transform:uppercase;margin:0 0 1rem;display:flex;gap:.5rem;align-items:center}
nav.rail .rail-part{margin:.95rem 0 .25rem;font-weight:700;color:var(--bronze-3);
  font-size:.78rem;letter-spacing:.08em}
nav.rail a{display:block;color:var(--ink-2);text-decoration:none;
  padding:.16rem .5rem;border-left:2px solid transparent;line-height:1.5}
nav.rail a:hover{color:var(--cinnabar);border-left-color:var(--cinnabar);
  background:var(--paper)}
/* the rail's only non-chapter link, wearing the same wheel the route map
   starts with, so the sidebar and the page it jumps to share one sign */
nav.rail .rail-map{display:flex;align-items:center;gap:.45rem;
  color:var(--bronze-3);font-weight:600;margin-bottom:.5rem}
nav.rail .rail-map .rmk{flex:none;width:.8rem;height:.8rem;color:var(--bronze)}

/* ------- structure pages ------- */
.front-page{padding:2.3rem 0 1.8rem}
.page-title{font-size:1.9rem;margin:0 0 1.05rem;color:var(--bronze-3)}
.page-title::after{content:"";display:block;width:3.6rem;height:3px;
  background:linear-gradient(90deg,var(--bronze),var(--bronze-2));
  margin-top:.55rem;border-radius:999px}
section.front-page{break-before:page}
.cover{text-align:center;padding:0;position:relative}
.cover .wheel{width:26px;height:26px;color:var(--bronze-2);opacity:.9;flex:0 0 auto}
/* one frame, not two: the outline used to draw a second line 5px outside the
   border, which at book size reads as a plate that printed twice */
.cover-inner{position:relative;display:inline-block;text-align:center;
  padding:clamp(2.2rem,5vw,4rem) clamp(1.6rem,5vw,4.2rem) 2.6rem;margin:2.4rem 0;
  border:1px solid var(--line-2);
  background:linear-gradient(180deg,var(--card),var(--paper))}
.cover-kicker{font-family:var(--sans);font-size:.7rem;letter-spacing:.42em;
  color:var(--bronze);text-transform:uppercase;margin:0 0 1.6rem}
.book-title{margin:0;line-height:1.12}
.bt-main{display:block;font-size:clamp(3.1rem,9vw,4.9rem);letter-spacing:.14em;
  text-indent:.14em;color:var(--ink);font-weight:700;
  font-family:"STSong","Songti SC","Noto Serif SC",var(--serif)}
.bt-tail{display:block;font-family:var(--sans);font-weight:400;font-size:1.2rem;
  letter-spacing:.3em;text-indent:.3em;color:var(--ink-2);margin-top:.9rem}
.cover-seal{position:absolute;top:clamp(1.4rem,4vw,2.6rem);
  right:clamp(1.4rem,4vw,2.6rem);display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:.05rem;width:2.9rem;
  padding:.42rem 0;background:var(--cinnabar);color:#FBF7EF;
  font-family:var(--kai);font-size:1.05rem;line-height:1.15;letter-spacing:0;
  writing-mode:vertical-rl;border-radius:var(--r-1);
  box-shadow:inset 0 0 0 2px rgba(251,247,239,.55)}
.cover-rule{display:flex;align-items:center;justify-content:center;gap:.9rem;
  margin:1.7rem auto 1.2rem;max-width:26rem}
.cover-rule i{height:1px;flex:1;background:linear-gradient(90deg,transparent,
  var(--bronze-2),transparent)}
.cover-art{width:min(34rem,94%);display:block;margin:.5rem auto 1.6rem;
  color:var(--ink-2)}
.book-sub{font-family:var(--sans);font-size:.95rem;color:var(--ink-2);
  margin:0 0 1.8rem;letter-spacing:.1em}
.book-epi{font-family:var(--kai);font-size:1.02rem;color:var(--bronze-3);
  margin:0 auto 1.9rem;line-height:2}
.book-epi .epi-src{display:block;font-size:.86rem;color:var(--ink-3);margin-top:.2rem}
.cover-foot{display:flex;align-items:baseline;justify-content:center;gap:.9rem;
  border-top:1px solid var(--line);padding-top:1.1rem}
.book-author{font-family:var(--sans);letter-spacing:.28em;text-indent:.28em;
  color:var(--ink);font-size:.95rem;font-weight:700}
.cover-ver{font-family:var(--sans);font-size:.76rem;letter-spacing:.12em;
  color:var(--ink-3)}
.cover-ver b{color:var(--cinnabar);font-weight:700}
.cover-tag{font-family:var(--sans);font-size:.74rem;letter-spacing:.36em;
  color:var(--bronze);text-transform:uppercase;margin:0 0 2.2rem}
.imprint-list{margin:0 0 1.6rem}
.ip-row{display:grid;grid-template-columns:8.5rem 1fr;gap:1rem;padding:.5rem 0;
  border-bottom:1px solid var(--line)}
.ip-row dt{font-family:var(--sans);font-size:.8rem;letter-spacing:.2em;
  color:var(--bronze);margin:0}
.ip-row dd{margin:0}
.ip-notice-t{margin:1.4rem 0 .4rem;font-size:.95rem;color:var(--cinnabar)}
.ip-notice{color:var(--ink-2);font-size:.95rem;border-left:3px solid var(--line-2);
  padding-left:1rem}
.rev-v{display:flex;justify-content:space-between;align-items:baseline;
  font-size:1.05rem;margin:1.15rem 0 .3rem;color:var(--bronze-3)}
.rev-v .rev-d{font-size:.78rem;color:var(--ink-3);font-weight:400}
.revisions ul{margin:.2rem 0 0;padding-left:1.4rem;font-size:.96rem;color:var(--ink-2)}
.revisions li::marker{color:var(--bronze-2)}
/* four routes, one row: at 15rem the sheet broke 3+1 and the orphan card left
   two empty cells the reader scans as missing content */
.route-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(12.5rem,1fr));
  gap:.9rem;margin:1.1rem 0 1.6rem}
/* four routes never divide into a three-up row. Rather than leave the last
   row two-thirds empty, the fourth card takes the whole line and reads as the
   closing note it is */
.route-grid>:last-child:nth-child(4){grid-column:1/-1}
.route-card{background:var(--card);border:1px solid var(--line);border-radius:var(--r-2);
  padding:1rem 1.15rem;box-shadow:0 1px 4px rgba(38,34,27,.05)}
.route-card h3{margin:0 0 .35rem;font-size:.92rem;color:var(--cinnabar);
  letter-spacing:.05em}
.route-card p{margin:0;font-size:.95rem;color:var(--ink-2)}
/* the route map is its own leaf, not furniture on the reading-paths sheet:
   that page already carries the routes, the offline note, the parts list and
   the legend, and print has no room to spare for a second block that must not
   split. Here the map is the page, so it gets `break-inside:avoid` outright. */
.itinerary{display:block;width:min(46rem,100%);height:auto;break-inside:avoid;
  margin:.2rem auto 1.1rem;color:var(--bronze);opacity:.92}
.itinerary text{font-family:var(--sans);font-size:11px;fill:currentColor;
  stroke:none;letter-spacing:.02em}
.rm-lead{max-width:36rem;margin:.45rem auto 1.35rem;text-align:center;
  color:var(--ink-2);font-size:1.02rem}
/* the legend is read once and never looked at again, so it stays small, in the
   sans, and directly under the map it explains */
.rm-key{display:flex;flex-wrap:wrap;justify-content:center;gap:.35rem 1.5rem;
  list-style:none;margin:0 auto 1.6rem;padding:0;max-width:44rem;
  font-family:var(--sans);font-size:.76rem;letter-spacing:.02em;color:var(--ink-3)}
.rm-key li{display:flex;align-items:center;gap:.42rem}
.rmk{flex:none;width:1.05rem;height:1.05rem;color:var(--bronze)}
.rm-legs{list-style:none;margin:0 auto;padding:.85rem 0 0;max-width:34rem;
  border-top:1px solid var(--line)}
.rm-legs li{display:flex;flex-direction:column;gap:.15rem;padding:.42rem 0;
  border-bottom:1px solid var(--line);line-height:1.62}
.rm-legs li:last-child{border-bottom:0}
/* the two lines of a row are furniture text, not prose: the browser's own
   paragraph margins would otherwise spend more sheet than the sentences do */
.rm-legs p{margin:0}
.rm-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:.15rem .6rem}
.rm-head a{font-family:var(--sans);font-weight:700;color:var(--bronze-3)}
.rm-nos{font-family:var(--sans);font-size:.8rem;color:var(--cinnabar);
  letter-spacing:.08em}
.rm-why{color:var(--ink-2);font-size:.92rem}
.route-parts{list-style:none;margin:0;padding:0}
.route-parts li{padding:.55rem 0;border-bottom:1px solid var(--line);
  display:flex;flex-direction:column;gap:.15rem}
.route-parts a{font-family:var(--sans);font-weight:700;color:var(--bronze-3);
  text-decoration:none}
.route-goal{font-size:.9rem;color:var(--ink-3)}

/* ------- TOC ------- */
.toc-part{display:flex;align-items:baseline;gap:.85rem;margin:1.6rem 0 .5rem;
  font-family:var(--sans);font-weight:700;font-size:.85rem;letter-spacing:.2em;
  color:var(--bronze);text-decoration:none}
.toc-part:hover .tp-tx,.toc-part:hover .tp-no{color:var(--cinnabar)}
.toc-part::after{content:"";flex:1;height:1px;background:var(--line-2);
  transform:translateY(-.32em);order:2}
.toc-part .page-ref{order:3}
/* the numeral is inked, not outlined: a hollow 1.9rem Ⅰ is the loudest mark on
   the contents page and, being empty inside, reads as a plate that failed to
   take ink */
.tp-no{font-family:var(--serif);font-size:1.15rem;font-weight:700;
  line-height:1;color:var(--bronze);letter-spacing:.06em}
.tp-tx{color:var(--bronze-3)}
.toc-part-plain{color:var(--cinnabar);margin-top:2.4rem}
.toc-hr{border:none;border-top:1px solid var(--line);margin:1.2rem 0}
.toc-group{break-inside:avoid}
.toc-row{display:flex;align-items:baseline;text-decoration:none;color:var(--ink);
  padding:.32rem 0 .3rem;font-size:.99rem;border-radius:var(--r-1)}
.toc-row:hover{color:var(--cinnabar)}
.toc-row:hover .toc-n{color:var(--cinnabar);border-color:var(--cinnabar)}
.toc-n{flex:0 0 auto;min-width:2.1rem;margin-inline-end:.75rem;text-align:center;
  font-family:var(--sans);font-size:.7rem;font-weight:700;color:var(--bronze-3);
  border:1px solid var(--line-2);border-radius:var(--r-1);padding:.1rem .2rem;
  transform:translateY(-.12em)}
.toc-t{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
/* the leader carries the eye from a title to its folio, so it is drawn in the
   ornament gold rather than in the rule grey it kept getting lost in */
.leader{flex:1;border-bottom:1px dotted var(--bronze-2);margin:0 .5rem;
  transform:translateY(-.28em)}
.page-ref{font-family:var(--sans);font-size:.86rem;color:var(--bronze-3);
  font-variant-numeric:tabular-nums;min-width:1.6rem;
  text-align:right}

/* ------- part dividers ------- */
.part-divider{position:relative;overflow:hidden;text-align:center;
  padding:clamp(2.4rem,6vw,4rem) 1rem clamp(2rem,5vw,3.2rem);
  break-before:page;break-after:page;
  background:
    radial-gradient(120% 90% at 50% 0%,var(--paper-2) 0%,transparent 62%),
    linear-gradient(180deg,transparent,rgba(200,164,92,.06))}
.part-divider::before,.part-divider::after{content:"";position:absolute;
  left:50%;transform:translateX(-50%);width:min(70%,44rem);
  border-top:1px solid var(--line-2)}
.part-divider::before{top:1.4rem}
.part-divider::after{bottom:1.4rem}
/* the ghost wheel bleeds off one corner instead of sitting behind the plate:
   concentric wheels would double the rim, an off-centre arc gives the page a
   second, larger drawing to rest against */
.pd-ghost{position:absolute;right:-14%;top:-9%;width:min(360px,58vw);
  color:var(--bronze-2);opacity:.11;pointer-events:none;user-select:none}
.pd-ghost svg{width:100%;height:auto;display:block}
.pd-inner{position:relative;max-width:38rem;margin:0 auto;padding-top:clamp(3.4rem,8vw,5rem)}
/* the part's own drawing sits over the faint wheel: crisp line on ghosted
   line, the same depth the cover plate gets. Everything here is inked in
   currentColor, so dark mode and paper re-ink the drawing on their own. */
.pd-art{width:min(13.5rem,62%);margin:0 auto 1.1rem;color:var(--bronze);opacity:.9}
.pd-art svg{width:100%;height:auto;display:block}
.pd-no{font-family:var(--sans);letter-spacing:.5em;text-indent:.5em;
  color:var(--bronze);font-size:.85rem;margin:0 0 .5rem}
.pd-title{font-size:clamp(2rem,5.5vw,2.7rem);margin:0;letter-spacing:.08em}
.pd-motto{font-family:var(--kai);color:var(--cinnabar);margin:.2rem 0 1.3rem;
  letter-spacing:.14em;font-size:1.02rem}
.pd-goal{max-width:30rem;margin:0 auto;color:var(--ink-2);font-size:.98rem;
  line-height:1.9;text-wrap:balance}
/* the leg's road, drawn once above the stop list: the reader sees how many
   chapters the part is before reading a single one of their titles */
.pd-route{display:block;width:min(23rem,92%);height:auto;margin:1.55rem auto .1rem;
  color:var(--bronze);opacity:.85}
.pd-list{list-style:none;margin:1.1rem auto 0;padding:.9rem 0 0;max-width:26rem;
  text-align:start;border-top:1px solid var(--line-2)}
.pd-list li{padding:.42rem 0;border-bottom:1px solid var(--line)}
.pd-list a{text-decoration:none;color:var(--ink-2);font-size:.95rem;
  display:flex;gap:.7rem;align-items:baseline}
.pd-list a:hover{color:var(--cinnabar)}
.pd-list a::before{content:attr(data-no);
  font-family:var(--sans);font-size:.74rem;color:var(--bronze);
  font-variant-numeric:tabular-nums;flex:0 0 auto}

/* ------- chapters ------- */
article.chapter,article.unit{padding:1.7rem 0 2.2rem;break-before:page;
  overflow-wrap:break-word}
.chapter-head .eyebrow{font-family:var(--sans);font-size:.78rem;
  letter-spacing:.3em;color:var(--bronze);text-transform:uppercase;
  margin:0 0 .3rem;display:flex;align-items:center;gap:.7rem}
.chapter-head .eyebrow::after{content:"";flex:1;height:1px;
  background:linear-gradient(90deg,var(--line-2),transparent)}
article h1{font-size:1.85rem;margin:.15rem 0 1.05rem;line-height:1.4}
.ch-head-row{display:flex;align-items:flex-start;gap:1.05rem}
.ch-seal{flex:0 0 auto;display:grid;place-items:center;width:3.05rem;height:3.05rem;
  margin-top:.25rem;border:2px solid var(--bronze-2);border-radius:var(--r-1);
  color:var(--bronze-3);background:var(--card);
  font-family:Georgia,var(--sans);font-weight:700;font-size:1.32rem;
  letter-spacing:.02em;font-variant-numeric:tabular-nums;
  box-shadow:inset 0 0 0 1px var(--paper-2)}
.ch-head-row h1{margin-bottom:1.05rem}
.appendix .ch-seal{border-color:var(--cinnabar);color:var(--cinnabar)}
/* the unit emblem: drawn with currentColor so it re-inks itself in dark mode
   and on paper, and floats into the head row rather than eating a block of
   vertical space the way a full-width figure would */
.ch-emblem{flex:0 0 auto;align-self:center;margin-inline-start:auto;
  width:4.6rem;height:4.6rem;color:var(--bronze);opacity:.92}
.ch-emblem svg{width:100%;height:100%;display:block}
.appendix .ch-emblem{color:var(--cinnabar);opacity:.8}
@media (max-width:44rem){.ch-emblem{width:3.2rem;height:3.2rem}}
/* the wire the head closes on — a drawn line with pads, not a ruled one.
   Inline SVG, so it inherits currentColor like every other drawing here. */
.ch-trace{display:block;width:min(21rem,100%);height:auto;
  margin:-.15rem 0 .35rem;color:var(--bronze-2);opacity:.75}
.appendix .ch-trace{color:var(--cinnabar);opacity:.5}
/* and the ruts it ends on: a drawn full stop for the chapter, so the tail of
   the page closes on something the book inked rather than on blank paper */
.ch-rut{display:block;width:min(17rem,74%);height:auto;break-before:avoid;
  margin:2.1rem auto .15rem;color:var(--bronze);opacity:.8}
.appendix .ch-rut{color:var(--cinnabar);opacity:.62}
article h1 .h1-sub{display:block;font-weight:400;font-size:1.05rem;
  color:var(--ink-3);margin-top:.35rem;font-family:var(--serif)}
article h2{font-size:1.28rem;margin:1.9rem 0 .7rem;padding-left:.7rem;
  border-left:4px solid var(--bronze-2)}
article h3{font-size:1.06rem;margin:1.4rem 0 .45rem;color:var(--bronze-3)}
article h4{font-size:.95rem;margin:1.05rem 0 .35rem;color:var(--ink-2)}
article h2 .sec-no{color:var(--bronze);margin-right:.45rem;font-variant-numeric:tabular-nums}
article p{margin:0 0 1.05em}
article .chapter-body>p:first-of-type::first-letter{
  font-size:2.9em;line-height:.86;float:inline-start;padding:.08em .12em 0 0;
  color:var(--cinnabar);font-weight:700;font-family:var(--serif)}
ul,ol{padding-inline-start:1.6em;margin:0 0 1em}
li{margin:.24em 0}
li::marker{color:var(--bronze);font-family:var(--sans);font-size:.9em}
hr{border:none;text-align:center;margin:1.8rem 0}
/* the section break: hairline, drawn coupling, hairline. The coupling is an
   inline SVG rather than a typed glyph, so it re-inks in dark mode and on
   paper exactly like the emblems do. */
.hr-rule{display:flex;align-items:center;gap:.8rem;margin:1.7rem 0 1.8rem;
  color:var(--bronze-2)}
.hr-rule::before,.hr-rule::after{content:"";flex:1;height:1px;
  background:var(--line-2)}
/* plain 1px lines, not gradients: a gradient background is painted as a raster
   image by the print engine, and this rule appears 111 times per edition */
.hr-knot{flex:0 0 auto;width:3.4rem;height:auto}

/* ------- compass ------- */
.compass{display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;
  margin:0 0 1.1rem}
@media (max-width:860px){.compass{grid-template-columns:1fr}}
.compass-card{background:var(--card);border:1px solid var(--line);
  border-radius:var(--r-2);padding:.75rem .9rem .8rem;position:relative;overflow:hidden;
  box-shadow:0 1px 4px rgba(38,34,27,.05)}
.compass-card::before{content:"";position:absolute;inset:0 auto 0 0;width:4px;
  background:var(--bronze-2)}
.compass-card.question::before{background:var(--cinnabar)}
.compass-card.boundary::before{background:var(--ink-3)}
.cc-tag{margin:0 0 .3rem;font-size:.72rem;letter-spacing:.2em;
  color:var(--bronze);font-weight:700}
.compass-card.question .cc-tag{color:var(--cinnabar)}
.compass-card.boundary .cc-tag{color:var(--ink-3)}
.compass-card p{margin:0;font-size:.93rem;line-height:1.7;color:var(--ink-2)}
.cc-src{grid-column:1/-1;margin:0;font-family:var(--sans);font-size:.8rem;
  color:var(--ink-3);display:flex;flex-wrap:wrap;gap:.3rem;align-items:center}
.cc-src-t{letter-spacing:.14em;color:var(--bronze);margin-right:.4rem}
.source-chip{display:inline-block;background:var(--paper-2);color:var(--bronze-3);
  border:1px solid var(--line);border-radius:var(--r-1);padding:.08rem .68rem;
  text-decoration:none;font-size:.76rem;line-height:1.5;vertical-align:bottom}
.source-chip:hover{border-color:var(--cinnabar);color:var(--cinnabar)}

/* ------- callouts ------- */
.callout{margin:1.15rem 0;padding:.75rem 1.05rem .3rem;border-radius:var(--r-2);
  border:1px solid var(--line);border-left-width:4px;background:var(--card);
  font-size:.96rem}
.callout .callout-tag{margin:0 0 .2rem;font-family:var(--sans);font-weight:700}
.callout .callout-tag strong{font-size:.86rem;letter-spacing:.08em}
.callout .callout-body{margin:.15rem 0 .65rem;color:var(--ink-2)}
.callout-icon{margin-right:.45rem}
/* the mark is drawn, not typed: it has to sit on the tag's baseline and scale
   with the tag's own font-size rather than a fixed pixel size */
.callout-icon .ink-mark{width:1.06em;height:1.06em;vertical-align:-.15em}
.callout-tip{border-left-color:var(--jade);background:linear-gradient(90deg,
  rgba(78,110,93,.09),var(--card) 46%)}
.callout-tip .callout-tag{color:var(--jade)}
.callout-warning{border-left-color:var(--cinnabar);background:linear-gradient(90deg,
  rgba(180,71,47,.10),var(--card) 46%)}
.callout-warning .callout-tag{color:var(--cinnabar)}
.callout-info{border-left-color:var(--bronze);background:linear-gradient(90deg,
  rgba(138,107,63,.10),var(--card) 46%)}
.callout-info .callout-tag{color:var(--bronze)}
.callout-concept{border-left-color:var(--sky);background:linear-gradient(90deg,
  rgba(76,112,147,.09),var(--card) 46%)}
.callout-concept .callout-tag{color:var(--sky)}
.callout-note{border-left-color:var(--ink-3)}
.callout-note .callout-tag{color:var(--ink-2)}
blockquote{margin:1.15rem 0;padding:.8rem 1.1rem;border-left:3px solid var(--line-2);
  border-radius:0 var(--r-2) var(--r-2) 0;background:rgba(243,234,216,.5);color:var(--ink-2)}
blockquote p{margin:0 0 .5em}
/* A quotation follows its block's alignment, not the body's: justifying a
   Latin epigraph across the full measure stretches it into rivers, and it also
   defeated the right-aligned setting the first-quote rule asks for. */
.chapter-body blockquote p{text-align:inherit}
blockquote p:last-child{margin-bottom:0}
.chapter-body > blockquote:first-of-type{border-left:none;border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);border-radius:0;background:none;
  padding:.8rem 0;margin:0 auto 1.6rem;text-align:end;font-family:var(--kai);
  font-size:1.04rem;line-height:2;color:var(--bronze-3)}
@media (prefers-color-scheme:dark){
  body:not(.force-light) blockquote{background:rgba(34,34,28,.55)}}

/* ------- code ------- */
code{font-family:var(--mono);font-size:.86em;background:var(--paper-2);
  border:1px solid var(--line);border-radius:var(--r-1);padding:.06em .34em;
  color:var(--bronze-3)}
.codehilite{margin:1.1rem 0 1.25rem;border-radius:var(--r-2);position:relative;
  overflow:hidden;background:var(--code-bg);border:1px solid var(--code-line);
  box-shadow:0 6px 18px -12px rgba(38,34,27,.55)}
.mermaid-source-wrap{margin:1rem 0 1.25rem;border-radius:var(--r-2);
  overflow-x:auto;background:var(--code-bg);border:1px solid var(--code-line);
  box-shadow:0 2px 10px -4px rgba(0,0,0,.35)}
.codehilite::after{content:attr(data-lang);position:absolute;top:0;right:0;
  font-family:var(--sans);font-size:.6rem;font-weight:600;letter-spacing:.16em;
  text-transform:uppercase;line-height:1;padding:.34rem .55rem .3rem;
  color:#B9AC8E;background:rgba(200,164,92,.13);
  border-inline-start:1px solid var(--code-line);
  border-bottom:1px solid var(--code-line);border-start-end-radius:0;
  border-start-start-radius:8px}
.codehilite:not([data-lang])::after{content:none}
.codehilite pre,.mermaid-source pre{margin:0;padding:1.05rem 1.2rem;
  color:var(--code-fg);font-family:var(--mono);font-size:.83rem;line-height:1.68;
  background:transparent;overflow-x:auto;white-space:pre;
  scrollbar-width:thin;scrollbar-color:rgba(200,164,92,.4) transparent}
.codehilite pre::-webkit-scrollbar{height:7px}
.codehilite pre::-webkit-scrollbar-thumb{background:rgba(200,164,92,.35);
  border-radius:999px}
/* the ring is drawn inside because the frame clips what sticks out, and in
   bronze-2 because the code plate is dark ink in both colour schemes */
.codehilite pre:focus-visible{outline:2px solid var(--bronze-2);outline-offset:-2px}
.codehilite code{background:none;border:none;color:inherit;padding:0}
.codehilite .c,.codehilite .cm,.codehilite .c1,.codehilite .cs{color:#93886F;font-style:italic}
.codehilite .k,.codehilite .kd,.codehilite .kn,.codehilite .kt{color:#D8B26A;font-weight:600}
.codehilite .nf,.codehilite .nc,.codehilite .fm{color:#E2C08D}
.codehilite .s,.codehilite .s1,.codehilite .s2,.codehilite .sb,.codehilite .sd{color:#A9C46C}
.codehilite .m,.codehilite .mi,.codehilite .mf,.codehilite .mh{color:#DFA878}
.codehilite .nt,.codehilite .tag{color:#8FB2D4}
.codehilite .na,.codehilite .attr{color:#C8A45C}
.codehilite .o,.codehilite .ow{color:#BDB4A2}
.codehilite .p{color:#9A917E}
.codehilite .err{color:#E07B5F}

/* ------- tables ------- */
.table-scroll{overflow-x:auto;margin:1.1rem 0;border:1px solid var(--line);
  border-radius:var(--r-2);background:var(--card);
  scrollbar-width:thin;scrollbar-color:var(--line-2) var(--paper-2);
  box-shadow:0 1px 5px rgba(38,34,27,.05)}
/* a phone paints no bar until the reader drags, so a column sliced in half
   reads as the end of the table: measured on a 390px screen, one appendix sheet
   hid 493px of columns behind a straight cut. Naming the bar makes Chrome and
   Firefox keep a classic one in layout, which is the cue the plate frames
   below already give. `tabindex` on the wrapper (render.py) is what makes the
   hidden columns reachable without a mouse -- the focus ring below is the
   reason that attribute is there. */
.table-scroll::-webkit-scrollbar{height:9px}
.table-scroll::-webkit-scrollbar-track{background:var(--paper-2);
  border-radius:0 0 var(--r-2) var(--r-2)}
.table-scroll::-webkit-scrollbar-thumb{background:var(--line-2);border-radius:999px}
.table-scroll::-webkit-scrollbar-thumb:hover{background:var(--bronze-2)}
.table-scroll:focus-visible{outline:2px solid var(--bronze)}
table{border-collapse:collapse;width:100%;font-size:.9rem;line-height:1.6}
th{font-family:var(--sans);font-weight:700;color:var(--bronze-3);
  background:var(--paper-2);text-align:start;padding:.6rem .9rem;
  border-bottom:2px solid var(--line-2);white-space:nowrap}
td{padding:.55rem .9rem;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:nth-child(2n){background:rgba(243,234,216,.45)}
@media (prefers-color-scheme:dark){
  body:not(.force-light) tbody tr:nth-child(2n){background:rgba(34,34,28,.6)}}
tr{break-inside:avoid}
table td code{font-size:.8rem}

/* ------- figures & diagrams ------- */
figure.diagram{margin:1.5rem 0;text-align:center;break-inside:avoid}
.diagram-frame{position:relative;background:
    linear-gradient(180deg,var(--card),var(--paper-2)),
    radial-gradient(100% 60% at 50% 0%,rgba(200,164,92,.07),transparent);
  border:1px solid var(--line-2);border-radius:var(--r-2);padding:1.1rem 1rem;
  box-shadow:0 6px 22px -12px rgba(38,34,27,.30),
    inset 0 0 0 1px rgba(255,255,255,.55);overflow-x:auto}
.diagram-frame::before,.diagram-frame::after{content:"";position:absolute;
  width:11px;height:11px;border:1px solid var(--bronze-2);opacity:.75}
.diagram-frame::before{left:7px;top:7px;border-right:none;border-bottom:none}
.diagram-frame::after{right:7px;bottom:7px;border-left:none;border-top:none}
/* no filter: the print engine rasterises a filtered subtree, which would turn
   every plate's labels into outlines — unsearchable, and most of a 31MB PDF */
.diagram-frame svg{display:block;margin:0 auto;max-width:100%;height:auto}
.diagram-frame::-webkit-scrollbar{height:8px}
.diagram-frame::-webkit-scrollbar-track{background:var(--paper-2);
  border-radius:0 0 var(--r-2) var(--r-2)}
.diagram-frame::-webkit-scrollbar-thumb{background:var(--line-2);border-radius:999px}
.diagram-frame::-webkit-scrollbar-thumb:hover{background:var(--bronze-2)}
.diagram-frame .node rect,.diagram-frame .cluster rect{rx:8}
figcaption{margin:.7rem auto 0;max-width:var(--measure);font-family:var(--sans);
  font-size:.83rem;color:var(--ink-2);line-height:1.7;
  display:flex;gap:.7rem;justify-content:center;align-items:baseline}
figcaption::before,.figcaption::after{content:"";flex:0 0 2.2rem;height:1px;
  background:linear-gradient(90deg,transparent,var(--line-2));
  transform:translateY(-.35em)}
figcaption::after{background:linear-gradient(90deg,var(--line-2),transparent)}
.fig-no{color:var(--bronze);font-weight:700;letter-spacing:.06em;white-space:nowrap}
.fig-cap{color:var(--ink-3)}
.fig-hint{font-size:.7rem;line-height:1.5;color:var(--ink-3);white-space:nowrap;
  border:1px solid var(--line-2);border-radius:var(--r-1);padding:.02rem .5rem;
  transform:translateY(-.12em)}
/* the caption is a centered flex row, and a nowrap hint chip is the widest
   unbreakable item on it — on a phone the row overflows past the right edge,
   so let the chip drop to a second line instead */
@media (max-width:44rem){figcaption{flex-wrap:wrap;row-gap:.2rem}}
.mermaid-missing{color:var(--cinnabar);border:1px dashed var(--cinnabar);
  padding:1rem;text-align:center;border-radius:var(--r-2);font-family:var(--sans)}
.mermaid-source{text-align:start}
img{max-width:100%;height:auto}

/* ------- chapter notes ------- */
.chapter-notes{margin:1.9rem 0 0;padding:.85rem 1.05rem .9rem;border:1px solid var(--line);
  border-radius:var(--r-2);background:var(--card)}
.notes-title{font-family:var(--sans);font-size:.75rem;letter-spacing:.25em;
  color:var(--bronze);margin:0 0 .5rem}
.notes-list{list-style:none;margin:0;padding:0;counter-reset:fn;
  font-family:var(--mono);font-size:.74rem;color:var(--ink-3)}
.notes-list li{display:flex;gap:.6rem;align-items:baseline;padding:.32rem 0;
  border-bottom:1px dotted var(--line);word-break:break-all;flex-wrap:wrap}
.notes-list li:last-child{border-bottom:none}
.notes-list code,.notes-list a{min-width:0;max-width:100%;overflow-wrap:anywhere}
.notes-list li::before{counter-increment:fn;content:counter(fn);flex:0 0 1.3rem;
  text-align:right;font-family:var(--sans);font-weight:700;color:var(--bronze)}
.notes-list a.fn-url{color:inherit;text-decoration:none}
.notes-list a.fn-url:hover{color:var(--cinnabar)}
.notes-list .backref{text-decoration:none;color:var(--bronze)}
sup.fnum{font-family:var(--sans);font-size:.68em}
sup.fnum a{text-decoration:none;color:var(--cinnabar)}

/* ------- source registry ------- */
.reg-note{color:var(--ink-3);font-size:.95rem;margin:0 0 1.6rem}
.reg-kind{display:flex;align-items:baseline;gap:.7rem;font-family:var(--sans);
  font-size:.95rem;color:var(--bronze-3);letter-spacing:.12em;
  margin:2.6rem 0 .8rem}
.reg-kind::after{content:"";flex:1;height:1px;background:var(--line-2);
  transform:translateY(-.3em)}
.rk-n{font-family:var(--mono);font-size:.7rem;color:var(--bronze);
  border:1px solid var(--line-2);border-radius:var(--r-1);padding:.06rem .45rem;
  letter-spacing:0}
.reg-list{list-style:none;margin:0;padding:0}
/* a row is a bordered card: cut by a page break it reads as two broken boxes */
.reg-list li{padding:.85rem 1rem .95rem;margin-bottom:.55rem;
  border:1px solid var(--line);border-inline-start:3px solid var(--bronze-2);
  border-radius:0 var(--r-2) var(--r-2) 0;background:var(--card);
  break-inside:avoid;transition:border-inline-start-color .15s ease}
.reg-list li:hover{border-inline-start-color:var(--cinnabar)}
.reg-head{display:flex;flex-wrap:wrap;gap:.55rem;align-items:baseline}
.reg-no{font-family:var(--mono);font-size:.72rem;color:var(--bronze-3);
  letter-spacing:.04em}
.reg-head a{font-weight:700;text-decoration:none;color:var(--ink)}
.reg-head a:hover{color:var(--cinnabar)}
.reg-auth{font-family:var(--sans);font-size:.78rem;color:var(--bronze);
  background:var(--paper-2);border-radius:var(--r-1);padding:.05rem .7rem}
.reg-pin{font-family:var(--sans);font-size:.78rem;color:var(--ink-3)}
.reg-pin code{font-size:.72rem}
.reg-meta{font-family:var(--sans);font-size:.76rem;color:var(--ink-3);margin-top:.3rem}
.reg-scope{font-size:.9rem;color:var(--ink-2);margin-top:.35rem}

/* ------- subject index ------- */
.idx-cols{columns:2;column-gap:3rem;column-rule:1px solid var(--line)}
.idx-block{break-inside:avoid}
.idx-letter{font-family:var(--sans);color:var(--cinnabar);font-size:1.3rem;
  margin:1.6rem 0 .4rem;border-bottom:2px solid var(--bronze-2);
  padding-bottom:.15rem;display:inline-block;min-width:2.2rem}
.idx-list{list-style:none;margin:0;padding:0;font-size:.9rem}
/* the Chinese block needs one line of instruction: nothing else in the book
   is filed by radical, and a reader who is not told will assume it is random */
.idx-note{font-size:.82rem;color:var(--ink-2);margin:-.15rem 0 .3rem;
  line-height:1.55;max-width:26rem}
.idx-row{display:flex;align-items:baseline;gap:.35rem;padding:.26rem 0}
.idx-term{flex:0 1 auto;min-width:0;font-family:var(--sans);font-weight:600;
  overflow-wrap:anywhere}
.idx-refs{white-space:nowrap}
.idx-refs a{margin-right:.5rem}
/* a long identifier used to squeeze the leader down to a stub; the term may
   break anywhere rather than eat the dots, so the row always reads as an entry
   with a leader */
.idx-row .leader{margin:0 .35rem;flex:1 1 1.2rem;min-width:1.2rem}
.idx-row .page-ref{display:none}
@media (max-width:52rem){.idx-cols{columns:1}}

/* ------- principles (原理札记) ------- */
/* a hover card cannot reach the printed book, so the reason line gets a page;
   the term sits in a gutter so the reasons align into one readable column
   instead of staircasing down the measure */
.pr-note{font-size:.9rem;color:var(--ink-2);line-height:1.75;max-width:34rem;
  margin:-.35rem 0 1.4rem}
.pr-unit{margin:0 0 1.6rem}
.pr-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:.5rem;
  font-family:var(--sans);font-size:.95rem;font-weight:700;margin:0;
  padding:.2rem 0 .4rem;border-bottom:2px solid var(--bronze-2)}
.pr-head a{color:var(--bronze-3);text-decoration:none}
.pr-head a:hover{color:var(--cinnabar)}
.pr-n{margin-inline-start:auto;font-family:var(--mono);font-size:.66rem;
  color:var(--bronze-3);border:1px solid var(--line-2);border-radius:var(--r-1);
  padding:.05rem .45rem}
.pr-list{list-style:none;margin:.35rem 0 0;padding:0}
.pr-row{display:grid;grid-template-columns:7.5rem 1fr;column-gap:.9rem;
  padding:.45rem 0 .5rem;border-bottom:1px dotted var(--line-2);
  break-inside:avoid}
.pr-term{grid-column:1;grid-row:1;font-family:var(--sans);font-weight:700;
  font-size:.88rem;line-height:1.8;color:var(--bronze-3);overflow-wrap:anywhere}
.pr-why{grid-column:2;grid-row:1;padding-inline-start:.55rem;
  border-inline-start:2px solid var(--bronze-2);font-size:.95rem;line-height:1.8;
  color:var(--ink)}
.pr-ana{grid-column:2;grid-row:2;margin-top:.22rem;padding-inline-start:.55rem;
  font-family:var(--kai);font-size:.9rem;line-height:1.75;color:var(--cinnabar)}
.pr-t{font-style:normal;font-family:var(--sans);font-size:.62rem;
  letter-spacing:.14em;color:var(--bronze-3);margin-inline-end:.4rem}
/* the collapse has to release the row pin too: term and reason both sit on row
   1 by design at full width, and a shared cell is how they overlapped on a phone */
@media (max-width:44rem){
  .pr-row{grid-template-columns:1fr;row-gap:.15rem}
  .pr-term,.pr-why,.pr-ana{grid-column:1;grid-row:auto}
}

/* ------- keeper (按语) ------- */
/* the old postman at the foot of each unit: a narrow box floated to the far
   edge so the line reads as marginalia, not as a paragraph the manuscript
   grew; on paper the same box sits inline above the ruts it comments on */
.keeper{display:flex;align-items:flex-end;gap:.65rem;margin:1.4rem 0 .15rem;
  max-width:min(38ch,100%);margin-inline-start:auto}
.kp-art{flex:none;width:2.4rem;line-height:0;color:var(--ink-3)}
.kp-art svg{width:100%;height:auto;transition:transform .18s ease}
.keeper:hover .kp-art svg,.keeper:focus-within .kp-art svg{
  transform:translateY(-3px) rotate(-4deg)}
.keeper-note{margin:0;font-family:var(--kai);font-size:.92rem;line-height:1.75;
  color:var(--ink-2);border-inline-start:2px solid var(--bronze-2);
  padding-inline-start:.6rem}
.kn-list{list-style:none;margin:.35rem 0 0;padding:0}
.kn-row{display:grid;grid-template-columns:7.2rem 1fr;column-gap:.9rem;
  padding:.45rem 0 .5rem;border-bottom:1px dotted var(--line-2);
  break-inside:avoid;align-items:baseline}
.kn-head{font-family:var(--sans);font-weight:700;font-size:.88rem;
  line-height:1.8;overflow-wrap:anywhere}
.kn-head a{color:var(--bronze-3);text-decoration:none}
.kn-head a:hover{color:var(--cinnabar)}
.kn-note{padding-inline-start:.55rem;border-inline-start:2px solid
  var(--bronze-2);font-family:var(--kai);font-size:.92rem;line-height:1.75;
  color:var(--ink)}
@media (max-width:44rem){
  .kn-row{grid-template-columns:1fr;row-gap:.15rem}
  .kn-head,.kn-note{grid-column:1}
}

/* ------- footer ------- */
.colophon{margin:2.8rem 0 1.3rem;text-align:center;color:var(--ink-3);
  font-family:var(--sans);font-size:.78rem;letter-spacing:.1em}
.colophon .wheel{width:34px;height:34px;color:var(--bronze-2);opacity:.7;
  display:block;margin:0 auto .8rem}

/* ------- plain-language layer (通俗层) ------- */
/* the lead band is the one device that survives print unchanged, so it is
   deliberately the loudest block on a chapter opener */
.lead-band{position:relative;margin:0 0 1.1rem;padding:.9rem 1.2rem 1rem;
  border:1px solid var(--line);border-radius:var(--r-2);overflow:hidden;
  background:linear-gradient(135deg,var(--card),var(--paper-2) 82%);
  box-shadow:0 1px 4px rgba(38,34,27,.05)}
.lead-band::before{content:"";position:absolute;inset:0 auto 0 0;width:4px;
  background:linear-gradient(180deg,var(--cinnabar),var(--bronze-2))}
/* a faint wheel in the corner: the band is the loudest block on a chapter
   opener, and the ornament ties it to the rest of the book without adding a
   line of copy */
.lead-band::after{content:"";position:absolute;inset-block-end:-2.6rem;
  inset-inline-end:-2.4rem;width:8rem;height:8rem;border-radius:50%;
  border:1px solid var(--bronze-2);opacity:.16;pointer-events:none;
  box-shadow:0 0 0 .55rem var(--card),0 0 0 .6rem var(--bronze-2)}
.lb-tag{margin:0 0 .35rem;font-family:var(--sans);font-size:.7rem;font-weight:700;
  letter-spacing:.28em;color:var(--cinnabar)}
.lb-plain{margin:0;font-size:1.08rem;line-height:1.8;color:var(--ink);
  text-wrap:pretty}
/* the analogy tag is an inline chip, not a row: as a flex item the sentence
   after it became its own anonymous item and dropped to a second line, which
   cost the band a whole line of height on every chapter */
.lb-analogy{margin:.5rem 0 0;font-family:var(--kai);font-size:1rem;
  line-height:1.85;color:var(--bronze-3)}
.lb-a-tag{display:inline-block;font-family:var(--sans);font-size:.68rem;font-weight:700;
  letter-spacing:.14em;color:var(--bronze);background:var(--paper-2);
  border:1px solid var(--line);border-radius:var(--r-1);padding:.06rem .55rem;
  margin-inline-end:.45rem;vertical-align:.14em}
@media (max-width:860px){.lead-band{padding:.9rem 1rem 1rem}
  .lb-plain{font-size:1.02rem}}

/* dashed term + CSS-only popover: no JS, and focus works for tap and keyboard */
.gloss{position:relative;border-bottom:1px dashed var(--bronze-2);cursor:help}
.gloss:hover,.gloss:focus,.gloss:focus-within{border-bottom-color:var(--cinnabar);
  color:var(--cinnabar);outline:none}
.gloss-pop{position:absolute;left:50%;bottom:calc(100% + .55rem);
  transform:translate(-50%,.35rem);z-index:40;width:max-content;
  max-width:min(21rem,80vw);padding:.6rem .8rem .65rem;text-align:start;
  font-family:var(--sans);font-size:.8rem;line-height:1.65;font-weight:400;
  color:var(--ink);background:var(--card);border:1px solid var(--line-2);
  border-radius:var(--r-2);box-shadow:0 12px 28px -16px rgba(38,34,27,.6);
  opacity:0;visibility:hidden;pointer-events:none;
  transition:opacity .12s ease,transform .12s ease}
.gloss:hover .gloss-pop,.gloss:focus .gloss-pop,.gloss:focus-within .gloss-pop{
  opacity:1;visibility:visible;transform:translate(-50%,0)}
.gloss-pop::after{content:"";position:absolute;left:50%;top:100%;
  transform:translateX(-50%);border:6px solid transparent;
  border-top-color:var(--card)}
.gloss-pop b{display:block;margin-bottom:.15rem;font-size:.72rem;
  letter-spacing:.12em;color:var(--bronze-3)}
.gloss-pop .gp-plain{display:block;color:var(--ink)}
/* the reason line is the one a reader skims for, so it gets a rule rather than
   another font: the calligraphic analogy below must stay the softest of three */
.gloss-pop .gp-why{display:block;margin-top:.4rem;padding-inline-start:.5rem;
  border-inline-start:2px solid var(--bronze-2);color:var(--ink)}
.gloss-pop .gw-t{font-style:normal;font-size:.62rem;letter-spacing:.14em;
  color:var(--bronze-3);margin-inline-end:.35rem}
.gloss-pop .gp-analogy{display:block;margin-top:.35rem;font-family:var(--kai);
  color:var(--cinnabar)}
/* a centred popover next to the page edge would be cut off; below the width
   where one can fit it becomes a caption pinned to the bottom of the viewport
   instead. That width is arithmetic, not taste: a term may sit at the very end
   of the 46rem measure, and the bubble reaches 10.5rem past its centre, so the
   screen has to be measure + bubble = 67rem across before the bubble can be
   trusted. (720px screens used to hang 100px of it off the right edge, which
   the whole document then had to scroll sideways for.) */
@media (max-width:67rem){
  .gloss-pop{position:fixed;left:50%;bottom:.9rem;top:auto;
    width:min(22rem,92vw);max-width:92vw;transform:translate(-50%,.5rem)}
  .gloss-pop::after{display:none}
}
/* a sheet that scrolls sideways clips everything painted inside it, including a
   bubble whose term sits near its edge: measured at 1360px and above, 13 of the
   book's tables hid their bubbles entirely outside the visible cell area and
   one grew 78px of phantom scroll. Terms inside a table therefore take the
   caption at every width -- it is the one place the reader can always see it. */
.table-scroll .gloss-pop{position:fixed;left:50%;bottom:.9rem;top:auto;
  width:min(22rem,92vw);max-width:92vw;transform:translate(-50%,.5rem)}
.table-scroll .gloss-pop::after{display:none}
@media (prefers-color-scheme:dark){
  body:not(.force-light) .gloss-pop{box-shadow:0 12px 28px -14px rgba(0,0,0,.75)}}

/* the chapter's terms are a card you read across, not a box you look inside: a
   dashed frame round twenty-two dotted rows made a chapter open entirely on
   furniture, and the prose never reached the first page. It now trails the
   unit, so it needs the air a following block would have had */
.new-terms{margin:1.5rem 0 0;padding:.6rem 0 0;border-top:1px solid var(--line)}
.nt-title{display:flex;align-items:baseline;gap:.5rem;margin:0 0 .35rem;
  font-family:var(--sans);font-size:.72rem;letter-spacing:.25em;
  color:var(--bronze);font-weight:700}
.nt-n{font-family:var(--mono);font-size:.68rem;letter-spacing:0;color:var(--bronze-3)}
/* the panel is the one block that gets taller the more terms a chapter uses;
   at three columns a 20-term chapter is seven rows instead of twenty, which is
   the difference between a reference card and a wall of text */
.nt-list{list-style:none;margin:0;padding:0;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:0 1.6rem}
/* the air between rows sits above them, not below: a row's bottom padding is
   the last thing the card leaves on a sheet, and 1.6px that will not fit was
   enough for Chromium to strand a whole empty page after the chapter */
.nt-row{display:flex;flex-wrap:wrap;align-items:baseline;
  padding:.32rem 0 0;min-width:0;break-inside:avoid}
.nt-term{flex:0 1 auto;min-width:0;font-family:var(--sans);font-weight:700;
  font-size:.84rem;color:var(--bronze-3)}
/* the tie between a term and its plain wording is one gold dot: the drawn
   dash it replaces cost a row of its own colour in every one of 20 panels */
.nt-term::after{content:"·";color:var(--bronze-2);font-weight:700;
  margin-inline:.18rem .22rem}
.nt-plain{flex:1 1 6rem;min-width:0;font-size:.86rem;line-height:1.6;
  color:var(--ink-2)}
.nt-note{margin:0 0 .3rem;font-family:var(--sans);font-size:.74rem;
  color:var(--ink-3)}
@media (max-width:44rem){.nt-list{grid-template-columns:1fr}}

/* section level chips — flex puts the chip at the end of the heading line
   without a float, which would fight page breaks in print */
article h2{display:flex;flex-wrap:wrap;align-items:baseline;column-gap:.6rem}
.sec-tier,.tier-chip{flex:0 0 auto;align-self:center;margin-inline-start:auto;
  font-family:var(--sans);font-size:.62rem;font-weight:700;letter-spacing:.14em;
  color:var(--ink-3);border:1px solid var(--line-2);border-radius:var(--r-1);
  padding:.08rem .5rem;white-space:nowrap}
.t-start{color:var(--jade);border-color:var(--jade)}
.t-core{color:var(--bronze-3);border-color:var(--bronze-2)}
.t-deep{color:var(--sky);border-color:var(--sky)}
.tier-legend{margin:2.4rem 0 0;padding-top:1.4rem;border-top:1px solid var(--line)}
.tier-legend .page-sub{font-size:1.2rem;margin:0 0 .4rem;color:var(--bronze-3)}
.tl-hint{margin:0 0 1rem;color:var(--ink-2);font-size:.94rem;max-width:34rem}
.tl-list{list-style:none;margin:0;padding:0}
.tl-row{display:flex;align-items:baseline;gap:.75rem;padding:.4rem 0;
  border-bottom:1px solid var(--line)}
.tl-row .tier-chip{margin-inline-start:0}
.tl-desc{flex:1;color:var(--ink-2);font-size:.92rem}
.tl-n{font-family:var(--mono);font-size:.76rem;color:var(--ink-3)}

/* ------- the reading column -------
   Only the running prose steps in to the measure; the chapter furniture above
   the body, and the plates, tables and code inside it, keep the sheet width. An
   inset lead band over full-width compass cards reads as a mistake rather than
   a hierarchy, and the 157 plates need the room. This block is deliberately
   last: every component above sets its own `margin` shorthand, which would
   reset the centring. */
.chapter-body>p,.chapter-body>ul,.chapter-body>ol,.chapter-body>dl,
.chapter-body>blockquote,.chapter-body>h2,.chapter-body>h3,.chapter-body>h4,
.chapter-body .ch-close,.chapter-body .callout,.chapter-notes,.tier-legend,
.reg-note,.tl-hint,.ip-notice,.revisions ul{
  max-width:var(--measure);margin-inline:auto}

/* ------- print / PDF ------- */
@media print{
  /* #B4472F is mixed against the screen's warm paper; on a laser printer's
     pure white it burns straight through the earth palette, so paper re-inks
     the accent one step deeper before anything else is drawn */
  :root{--paper:#FFFFFF;--card:#FFFFFF;--paper-2:#F6F0E2;--code-bg:#F8F4EA;
    --code-fg:#26221B;--code-line:#E3D8C1;--cinnabar:#9C4630}
  body{background:#fff;font-size:10.2pt;line-height:1.74;padding:0!important}
  body.lang-en{font-size:10pt;line-height:1.6}
  /* the A4 text block is ~665px, narrower than either measure: on paper the
     column is the page, so the cap must stand down for both languages */
  body,body.lang-en{--measure:52rem;--furniture:60rem}
  nav.rail,.no-print{display:none!important}
  .sheet{max-width:none;padding:0}
  /* on screen the cover is a card in the page flow; on paper the frame should
     be the page, so it takes the whole text block (297mm - 2x17mm margins).
     The stack is then spent from edge to edge -- kicker against the top of the
     frame, the author line against the bottom -- because a centred stack left
     a third of the sheet below the foot, which is the one place a cover may
     not be empty. */
  .front-page.cover{min-height:250mm;display:flex;align-items:stretch}
  .cover-inner{margin:0;width:100%;border-color:var(--line-2);
    display:flex;flex-direction:column;justify-content:space-between}
  .diagram-frame,.codehilite,.table-scroll,.compass-card,.route-card{
    box-shadow:none}
  /* the reading-paths page carries the routes, the offline note, the parts list
     and the tier legend; the legend is the one block that must not be split.
     Rows lose a few points of air so the legend stays on the page it starts on,
     instead of opening a sheet of its own three lines deep. */
  .route-parts li{padding:.3rem 0}
  .ip-notice-t{margin:1rem 0 .3rem}
  .tier-legend{break-inside:avoid;margin-top:.8rem;padding-top:.7rem}
  .tl-hint{font-size:.84rem;line-height:1.5;margin:0 0 .5rem}
  .tl-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
    column-gap:1.5rem}
  .tl-row{border-bottom:none;padding:.1rem 0;gap:.5rem}
  /* the screen lets a wide table scroll; paper has no scrollbars, so headers
     wrap and long code tokens break to fit the page box. Both properties are
     chosen to keep whole words: `anywhere` also feeds min-content width, which
     let the layout squeeze a column narrower than "FileWriteTool" or "章节" and
     then split them mid-word — `break-word` breaks only what cannot fit.
     CJK breaks between any two characters by default, so headers get keep-all
     to stop "模块名称" setting as "模块名/称". */
  th{white-space:normal;word-break:keep-all;overflow-wrap:break-word}
  table{font-size:8.6pt}
  table td{overflow-wrap:break-word}
  /* the screen drops to one index column below 52rem, but the printed page box
     is 665px of a much taller sheet — two columns is the book convention and
     halves the index */
  .idx-cols{columns:2;column-gap:2.2rem}
  /* the folio slot: a screen has no pages, so the row hides its page reference;
     paper reserves the box here and the PDF pass writes the number into it —
     nothing in the HTML can know the page a row lands on */
  .idx-row .page-ref{display:block}
  /* the printed sheet is 665px of text box: a 7.5rem gutter for a two-character
     term would be a third of the line gone, so the gutter narrows with the page.
     6.4rem is where the longest single-word English term ("immutability") still
     sets on one line; past that only terms with a space in them wrap, which
     reads as a term rather than as a break. The 44rem collapse above is a screen
     rule the page box also matches — 665px is under 704px — so paper has to put
     the gutter and the row pins back. */
  .pr-row{grid-template-columns:6.4rem 1fr;column-gap:.7rem;padding:.28rem 0 .32rem}
  .pr-term{grid-column:1;grid-row:1}
  .pr-why{grid-column:2;grid-row:1}
  .pr-ana{grid-column:2;grid-row:2}
  .pr-unit{margin-bottom:1.25rem}
  /* there is no hover on paper: the mark stays as a quiet dotted underline,
     and the chapter panel — which the build keeps in step with the marks —
     carries the plain wording. Two columns halves its height. */
  .gloss{border-bottom:1px dotted var(--line-2);color:inherit;cursor:auto}
  .gloss-pop{display:none}
  .lead-band{break-inside:avoid;background:var(--card);
    box-shadow:none;border-color:var(--line-2)}
  /* the corner wheel is a screen flourish; on paper a clipped circle at the
     edge of a boxed band reads as a printing artefact */
  .lead-band::after{display:none}
  /* the compass is a three-column row on screen and collapses below 860px —
     which the printed text block (665px) always is, so without this every
     chapter opener spent three full-width boxes down the sheet for what is
     one line of text each. Three columns keeps the opener on one page. */
  .compass{grid-template-columns:repeat(3,minmax(0,1fr));gap:.5rem;
    margin-bottom:.95rem;break-inside:avoid}
  .compass-card{padding:.6rem .7rem .65rem}
  .cc-tag{font-size:.66rem;letter-spacing:.14em;margin-bottom:.24rem}
  .compass-card p{font-size:.84rem;line-height:1.62}
  .cc-src{gap:.26rem .3rem}
  .ch-emblem{width:2.4rem;height:2.4rem;opacity:1;color:var(--bronze-3)}
  /* the trace's screen colour is a light bronze at three-quarter opacity, which
     a laser printer drops out entirely; on paper it runs full ink */
  .ch-trace{width:min(15rem,100%);opacity:.9;color:var(--bronze-3)}
  /* the ruts must never fall onto a sheet of their own: glued to the block they
     close, the pair moves together and the page ends short instead of emptying.
     Chromium honours break-inside, not break-before:avoid. A chapter ends on
     the tail of its last page, so the mark has to be big enough to be the
     reason the page stops there rather than a stray that fell into the void. */
  .ch-close{break-inside:avoid}
  .ch-rut{width:min(19rem,82%);margin-top:1.6rem;opacity:.9;color:var(--bronze-3)}
  /* the keeper keeps the ink it has on paper; the hover lean simply stops */
  .keeper{break-inside:avoid;margin:.9rem 0 0}
  .kp-art svg{transition:none}
  .pd-route{width:min(20rem,100%);opacity:.95;color:var(--bronze-3)}
  /* the map is the one page a reader consults before choosing a route, so on
     paper it takes the full measure and its station numbers grow a point */
  .itinerary{width:100%;opacity:.95;color:var(--bronze-3)}
  .itinerary text{font-size:12px}
  .rmk{color:var(--bronze-3);opacity:1}
  /* the page has to stay on one sheet: the map is the point, and a list that
     spills to a second page would leave the road drawn but unread */
  .rm-lead{font-size:.95rem;margin:.3rem auto .8rem}
  .rm-key{font-size:.7rem;margin-bottom:1rem}
  .rm-legs{padding-top:.5rem;max-width:38rem}
  .rm-legs li{padding:.18rem 0;gap:.05rem;line-height:1.5}
  .rm-head a{font-size:.86rem}
  .rm-nos{font-size:.75rem}
  /* the one line that does not survive the sheet: with the goals kept, the page
     ran to 994px against a 926px block and the last leg fell onto its own
     sheet. Every part repeats its goal in large type on its own divider page,
     so paper trades the reminder for the road fitting on one page */
  .rm-why{display:none}
  .hr-rule{color:var(--bronze-3);break-inside:avoid;margin:1.25rem 0 1.35rem}
  /* the opener owns a whole page on paper: lift the plate to the head of the
     sheet and let it draw bigger than it does beside the sticky rail */
  .pd-inner{padding-top:1.6rem}
  .pd-art{width:min(15rem,58%);margin-bottom:.7rem}
  /* the card is a plate, so it moves as one: allowed to break, its last row
     overflowed the text block by a point and Chromium handed the chapter an
     extra sheet carrying nothing at all — the one thing the empty-page gate
     exists to catch. Twenty-two terms are eleven rows at two columns, which
     is a third of a sheet and always fits on one. */
  .new-terms{break-inside:avoid}
  .nt-list{grid-template-columns:repeat(2,minmax(0,1fr))}
  .nt-term{font-size:.8rem}
  .nt-plain{font-size:.83rem;line-height:1.6}
  .sec-tier,.tier-chip{font-size:6.6pt;padding:0 .34rem}
  /* the plate's corner marks belong to the frame that no longer prints; the
     caption's flanking hairlines stay — with the box gone they are what holds
     each figure to the page. */
  .diagram-frame::before,.diagram-frame::after{display:none}
  .part-divider{background:none}
  .pd-ghost{opacity:.12}
  .cover-seal{print-color-adjust:exact;-webkit-print-color-adjust:exact}
  .codehilite pre{white-space:pre-wrap;word-break:break-word}
  .codehilite .c,.codehilite .c1{color:#7A6F58}
  .codehilite .k{color:#7A5B22}.codehilite .s{color:#4F6B3A}
  .codehilite .m{color:#8A5A2B}.codehilite .nt{color:#3A5F80}
  h1{bookmark-level:1;bookmark-label:content()}
  .page-title,.pd-title{bookmark-level:1;bookmark-label:content()}
  article h2,article h3,article h4,.rev-v,.reg-kind,.idx-letter{
    bookmark-level:none;bookmark-label:none}
  h1,h2,h3{break-after:avoid}
  /* the article's screen padding is air between chapters; on paper it is a
     trap. The last line of ch04 (en) ended 15pt above the box edge, the 2.2rem
     of bottom padding did not fit, and Chromium kept a sheet alive just to
     paint it -- an empty page, because the next unit opens with a forced break.
     The page box's own margin is the air here. */
  article.chapter,article.unit{padding-bottom:0}
  /* two, not three: the fold-out plates already start their own sheet, and a
     three-line tail cost four pages and produced one fully blank sheet */
  p{orphans:2;widows:2}
  /* one link of a chapter's citation list landing alone at the head of a fresh
     sheet reads as a printing slip; the block is short enough to move whole */
  .chapter-notes{break-inside:avoid}
  figure.diagram,figure{break-inside:avoid;max-height:none}
  /* An A4 text column here is 257mm tall. A plate capped at 200mm needs 78% of
     it, so almost no page can host one and the figure jumps to the next sheet,
     leaving the hole behind it. 150mm still shows a full architecture diagram
     legibly while fitting any page that has half its column left -- which is
     how most of the 314 plates get to stay where the prose put them. */
  .diagram-frame svg{max-height:var(--plate-cap,150mm);width:auto!important;
    min-width:0!important}
  /* a wide band is bound by the column, not by the cap, so standing taller
     cannot save it — the sheet turns instead. Chromium honours named pages: the
     plate gets a landscape sheet of its own and the prose returns to portrait
     on the next one. No break-after: the page name already ends the sheet, and
     asking for both cost an empty landscape page after every fold-out. The
     sheet is 170mm tall, so the plate keeps the 150mm default and the caption
     fits under it instead of spilling onto a second sheet. */
  @page plate-landscape{size:A4 landscape;margin:21mm 17mm 19mm}
  figure.landscape{page:plate-landscape;break-before:page;
    display:flex;flex-direction:column;justify-content:center;min-height:150mm}
  figure.landscape figcaption{margin-top:1.2rem}
  /* A capped plate is narrower than the column, so a bordered frame would print
     as a wide empty box around a small drawing. Paper has no surface to lift off
     and no scrollbar to hint at, so the box stands down entirely: the drawing
     sits on the page, centred, and the caption rule beneath it does the framing.
     (Shrinking the frame instead is not an option — every plate's root element
     is `width="100%"`, which a shrink-to-fit container resolves to nothing.) */
  .diagram-frame{background:none;border:0;border-radius:0;padding:0;overflow:visible}
  .fig-hint{display:none}
  .part-divider{padding:40mm 0 35mm}
  /* the plate has to hold its ground on one sheet: 40/35mm of air plus the big
     numeral pushed the last entry of a four-item list onto the next sheet as a
     line of its own. Same look, ~20mm shorter, and nothing escapes. */
  .part-divider{padding:26mm 0 24mm}
  .pd-num{-webkit-text-stroke:1.6px var(--bronze-2)}
  tbody tr:nth-child(2n){background:transparent}
  a.ext::after{content:""}
  @page{size:A4;margin:21mm 17mm 19mm}
}
"""


def page(lang: str, title: str, css: str, body_class: str, content: str,
         rail: str, colophon: str) -> str:
    return f"""<!doctype html>
<html lang="{'zh-CN' if lang == 'zh' else 'en'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="author" content="LinTsinghua">
<meta name="generator" content="yuyu-book">
<title>{title}</title>
<style>{css}</style>
</head>
<body class="{body_class}">
{rail}
<main class="sheet">
{content}
{colophon}
</main>
</body>
</html>"""
