"""The fence-aware scanner behind all 314 diagram plates (157 per language).

Markdown is the read-only source of truth, so the only thing that may cut a
document into structure is a real (unfenced) line. extract_mermaid also has to
leave the document balanced: a closing fence re-emitted after the placeholder
unmatched every following fence and swallowed whole chapters into a <pre>, so
"no fence residue, one placeholder per block, placeholder alone on its line"
are pinned here together with the caption/cache/fallback contracts.
"""
import re
import sys
import unittest
from pathlib import Path

if not __package__:  # direct run: see tests/__init__.py for the real bootstrap
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yuyu_book import mermaid as mm
from yuyu_book import render
from yuyu_book.core import (REPO_ROOT, BuildError, Unit, expected_ids,
                            extract_mermaid, load_configs, load_unit,
                            normalize_h1, read_text, unit_stream)

PLACEHOLDER = re.compile(r"@@MM:[0-9a-f]{12}@@")
FENCE_LINE = re.compile(r"^\s*`{3,}")

CH11 = "第三部分-高级模式篇/11-技能系统与插件架构.md"
APXB = "附录/B-工具完整清单.md"


def pipeline(text, lang="zh", file="t.md"):
    """What load_unit does to one file, exposed for inline fixtures."""
    _no, _title, body = normalize_h1(text, lang, file)
    return extract_mermaid(body, file)


class FenceAwareExtraction(unittest.TestCase):
    def test_hash_inside_a_fence_is_never_document_structure(self):
        text = ("# 第 1 章　标题\n\n正文。\n\n"
                "```bash\n# 这是注释\n# 也是注释\nls\n```\n\n尾部。\n")
        no, title, _body = normalize_h1(text, "zh", "t.md")
        self.assertEqual((no, title), ("第 1 章", "标题"))
        body, blocks, langs = pipeline(text)
        self.assertEqual(blocks, [])
        self.assertEqual(langs, ["bash"])
        self.assertIn("# 这是注释", body)
        self.assertIsNone(PLACEHOLDER.search(body))

    def test_a_fence_never_opens_a_heading_for_the_scanner(self):
        # strip the real H1: the four `# ` lines in ch11 are all inside fenced
        # samples, so a fence-aware scanner must find NO heading at all
        text = read_text(REPO_ROOT / CH11)
        body = "\n".join(text.split("\n")[1:])
        with self.assertRaises(BuildError) as ctx:
            normalize_h1(body, "zh", CH11)
        self.assertIn("no top-level H1", str(ctx.exception))

    def test_chapter_11_regression_keeps_its_four_fenced_comments(self):
        unit_def, kind = next((u, k) for u, k, _p in unit_stream(load_configs()[0])
                              if u["id"] == "ch11")
        u = load_unit(unit_def, kind, "zh", REPO_ROOT)
        self.assertEqual(u.no, "第 11 章")
        self.assertEqual(u.title, "技能系统与插件架构")
        self.assertEqual(len(u.blocks), 7)
        for comment in ("# 技能正文", "# API 端点生成器", "# SKILL.md", "# 技能内容"):
            self.assertIn(f"{comment}\n", u.md, comment)

    def test_longer_outer_fence_contains_a_shorter_inner_fence(self):
        text = ("# 第 1 章　标题\n\n示例：\n\n"
                "````markdown\n```mermaid\ngraph LR\nA-->B\n```\n````\n\n"
                "真图：\n\n```mermaid\nA-->B\n```\n")
        body, blocks, langs = pipeline(text)
        self.assertEqual(langs[0], "markdown")          # the example is code
        self.assertEqual(len(blocks), 1)                # only the real diagram
        self.assertEqual(body.count("```mermaid"), 1)   # the example stays literal
        self.assertIn("graph LR", body)

    def test_tilde_fence_and_backtick_fence_do_not_cross_close(self):
        text = ("# 第 1 章　标题\n\n~~~\n```not-a-fence\n~~~\n\n"
                "```mermaid\nA-->B\n```\n")
        body, blocks, langs = pipeline(text)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(langs, [""])
        self.assertIn("```not-a-fence", body)

    def test_unclosed_fence_raises_and_names_the_file(self):
        with self.assertRaises(BuildError) as ctx:
            pipeline("# 第 1 章　标题\n\n```mermaid\nA-->B\n")
        self.assertIn("t.md: unclosed code fence at line", str(ctx.exception))

    def test_unclosed_plain_fence_names_the_line_it_opened_on(self):
        with self.assertRaises(BuildError) as ctx:
            pipeline("# 第 1 章　标题\n\n```python\nx = 1\n")
        self.assertIn("unclosed code fence at line 3", str(ctx.exception))

    def test_block_line_numbers_are_lines_of_the_markdown_file(self):
        _body, blocks, _langs = pipeline("# 第 1 章　标题\n\n```mermaid\nA-->B\n```\n")
        self.assertEqual(blocks[0].line, 3)

    def test_two_blocks_get_distinct_stable_uids(self):
        text = ("# 第 1 章　标题\n\n```mermaid\nA-->B\n```\n\n"
                "```mermaid\nA-->B\n```\n")
        _body, first, _l = pipeline(text)
        body2, second, _l = pipeline(text)
        self.assertEqual([b.uid for b in first], [b.uid for b in second])
        self.assertEqual(len({b.uid for b in first}), 2)   # same src, two places
        self.assertEqual(len({b.src for b in first}), 1)
        self.assertEqual(first[0].file, "t.md")
        self.assertEqual([b.line for b in first], [3, 7])

    def test_uid_moves_with_the_diagram_but_the_svg_cache_does_not(self):
        same_src = mm.MermaidBlock("x", "graph LR\nA-->B", "ch01.md", 10)
        moved = mm.MermaidBlock("y", "graph LR\nA-->B", "ch02.md", 99)
        self.assertNotEqual(same_src.uid, moved.uid)
        self.assertEqual(mm._cache_key(same_src.src, "11.17.2", "edge"),
                         mm._cache_key(moved.src, "11.17.2", "edge"))

    def test_placeholder_always_stands_alone_on_its_own_line(self):
        text = "# 第 1 章　标题\n\n段落紧贴图：\n```mermaid\nA-->B\n```\n紧跟的段落。\n"
        body, blocks, _langs = pipeline(text)
        uid = blocks[0].uid
        self.assertIn(f"\n\n@@MM:{uid}@@\n\n", body)
        for line in body.split("\n"):
            if "@@MM:" in line:
                self.assertEqual(line.strip(), f"@@MM:{uid}@@")

    def test_no_closing_fence_is_re_emitted_after_the_placeholder(self):
        # the catastrophic case: an extra ``` after the placeholder re-opened a
        # fence and swallowed every following paragraph into a <pre>
        text = ("# 第 1 章　标题\n\n```mermaid\nA-->B\n```\n\n"
                "之后的正文必须还是段落。\n\n## 下一节\n\n又一段。\n")
        body, blocks, _langs = pipeline(text)
        self.assertEqual(len(blocks), 1)
        self.assertNotIn("`", body)
        self.assertEqual(FENCE_LINE.findall(body), [])
        self.assertIn("之后的正文必须还是段落。", body)

    def test_code_langs_are_the_info_strings_in_document_order(self):
        text = ("# 第 1 章　标题\n\n```python\n1\n```\n\n"
                "```\nbare\n```\n\n```mermaid\nA-->B\n```\n\n"
                "```typescript title=x\n1\n```\n")
        _body, blocks, langs = pipeline(text)
        self.assertEqual(langs, ["python", "", "typescript"])
        self.assertEqual(len(blocks), 1)


class Captions(unittest.TestCase):
    def captions(self, text, file="t.md"):
        _no, _t, body = normalize_h1(text, "zh", file)
        _body, blocks, _langs = extract_mermaid(body, file)
        # build.py passes the file as shipped; block.line is a line of it
        return mm.captions_for(text, blocks), blocks

    def test_caption_is_the_nearest_preceding_h2(self):
        caps, blocks = self.captions(
            "# 第 1 章　标题\n\n## 第一节\n\n```mermaid\nA-->B\n```\n\n"
            "## 第二节\n")
        self.assertEqual(caps[blocks[0].uid], "第一节")

    def test_h3_is_not_a_caption_source(self):
        caps, blocks = self.captions(
            "# 第 1 章　标题\n\n## 大节\n\n### 小节\n\n```mermaid\nA-->B\n```\n")
        self.assertEqual(caps[blocks[0].uid], "大节")

    def test_heading_inside_a_fence_does_not_become_a_caption(self):
        caps, blocks = self.captions(
            "# 第 1 章　标题\n\n## 真标题\n\n```bash\n## 假标题\n```\n\n"
            "```mermaid\nA-->B\n```\n")
        self.assertEqual(caps[blocks[0].uid], "真标题")

    def test_each_block_in_a_unit_gets_its_own_section_caption(self):
        caps, blocks = self.captions(
            "# 第 1 章　标题\n\n## A 节\n\n```mermaid\nA-->B\n```\n\n"
            "## B 节\n\n```mermaid\nC-->D\n```\n")
        self.assertEqual([caps[b.uid] for b in blocks], ["A 节", "B 节"])

    def test_heading_directly_above_the_fence_is_the_caption(self):
        caps, blocks = self.captions(
            "# 第 1 章　标题\n\n## 上一节\n\n正文。\n## 应有的标题\n"
            "```mermaid\nA-->B\n```\n")
        self.assertEqual(caps[blocks[0].uid], "应有的标题")

    def test_diagram_with_no_preceding_heading_uses_the_neutral_fallback(self):
        caps, blocks = self.captions(
            "# 附录 B：清单\n\n前言一段。\n\n```mermaid\nA-->B\n```\n\n"
            "## 最后一节\n")
        self.assertEqual(caps[blocks[0].uid], "架构示意")

    def test_shipped_appendix_b_first_plate_uses_the_neutral_fallback(self):
        # observed in the real book (zh + en 附录 B): the first plate sits
        # above every H2, so it must not inherit the document's last heading
        unit_def, kind = next((u, k) for u, k, _p in unit_stream(load_configs()[0])
                              if u["id"] == "apxb")
        u = load_unit(unit_def, "appendix", "zh", REPO_ROOT)
        caps = mm.captions_for(read_text(REPO_ROOT / APXB), u.blocks)
        first = min(u.blocks, key=lambda b: b.line)
        self.assertEqual(caps[first.uid], "架构示意")
        self.assertEqual(first.line, 14)


class CacheKeyAndFallback(unittest.TestCase):
    def setUp(self):
        self.src = "graph LR\nA-->B"
        self.base = mm._cache_key(self.src, "11.17.2", "edge-140")

    def test_key_is_a_svg_path_inside_the_mermaid_cache_dir(self):
        self.assertEqual(self.base.parent, mm.MM_DIR)
        self.assertEqual(self.base.suffix, ".svg")
        self.assertRegex(self.base.stem, r"^[0-9a-f]{24}$")

    def test_key_changes_when_the_source_changes(self):
        self.assertNotEqual(self.base,
                            mm._cache_key("graph LR\nA-->C", "11.17.2", "edge-140"))

    def test_key_changes_when_the_mermaid_version_changes(self):
        self.assertNotEqual(self.base,
                            mm._cache_key(self.src, "11.18.0", "edge-140"))

    def test_key_changes_when_the_browser_version_changes(self):
        self.assertNotEqual(self.base,
                            mm._cache_key(self.src, "11.17.2", "edge-141"))

    def test_key_is_stable(self):
        self.assertEqual(self.base, mm._cache_key(self.src, "11.17.2", "edge-140"))

    def test_key_changes_when_the_book_palette_changes(self):
        """A cached SVG is a picture of one palette. Editing a token must not
        keep serving the picture drawn under the old one."""
        original = mm._STYLE_VER
        try:
            mm._STYLE_VER = "deadbeef00"
            self.assertNotEqual(self.base,
                                mm._cache_key(self.src, "11.17.2", "edge-140"))
        finally:
            mm._STYLE_VER = original

    def test_style_version_fingerprints_both_theme_and_families(self):
        self.assertEqual(mm._style_fingerprint(), mm._STYLE_VER)
        saved = mm.BOOK_FAMILIES["info"]
        try:
            mm.BOOK_FAMILIES["info"] = ("#000001", "#000002", "#000003")
            self.assertNotEqual(mm._style_fingerprint(), mm._STYLE_VER)
        finally:
            mm.BOOK_FAMILIES["info"] = saved
        saved_theme = mm.THEME["themeVariables"]["primaryColor"]
        try:
            mm.THEME["themeVariables"]["primaryColor"] = "#000004"
            self.assertNotEqual(mm._style_fingerprint(), mm._STYLE_VER)
        finally:
            mm.THEME["themeVariables"]["primaryColor"] = saved_theme

    def test_source_fallback_escapes_the_original_source(self):
        block = mm.MermaidBlock("a" * 12, 'graph LR\nA -->|x<y & "q"| B', "ch01.md", 3)
        out = mm.source_fallback([block], {block.uid: "标题"})
        caption, html = out[block.uid]
        self.assertEqual(caption, "标题")
        self.assertTrue(html.startswith('<pre class="mermaid-source">'))
        self.assertTrue(html.endswith("</pre>"))
        self.assertIn("A --&gt;|x&lt;y &amp; &quot;q&quot;| B", html)
        self.assertNotIn("<svg", html)

    def test_source_fallback_covers_every_block(self):
        blocks = [mm.MermaidBlock(f"{i:012d}", "graph\nA-->B", "ch01.md", i)
                  for i in range(5)]
        out = mm.source_fallback(blocks, {})
        self.assertEqual(sorted(out), sorted(b.uid for b in blocks))
        self.assertEqual(out["000000000000"][0], "")   # caption-less is fine


class AuthorColoursReInked(unittest.TestCase):
    """The ~900 classDef/style hexes the manuscript brings to the 314 plates.

    Mermaid's ``theme: base`` only reaches nodes the author left alone, so an
    untreated Material-blue box sits in the middle of a bronze-and-parchment
    book and reads as a screenshot from another product. These tests pin the
    build-time re-inking: role preserved, palette replaced, and nothing outside
    a directive line touched.
    """

    def reink(self, decls: str) -> str:
        return mm.reink_colors(f"graph LR\nclassDef x {decls}").splitlines()[1]

    def test_hue_decides_the_family_not_the_exact_hex(self):
        cases = {
            "fill:#eff6ff,stroke:#3b82f6,color:#1e3a8a": mm.BOOK_FAMILIES["info"],
            "fill:#e8f4f8,stroke:#2196F3,color:#1565C0": mm.BOOK_FAMILIES["info"],
            "fill:#d4edda,stroke:#27ae60,color:#1b5e20": mm.BOOK_FAMILIES["good"],
            "fill:#fff3cd,stroke:#f39c12,color:#664d03": mm.BOOK_FAMILIES["warn"],
            "fill:#f8d7da,stroke:#c0392b,color:#842029": mm.BOOK_FAMILIES["danger"],
            "fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c": mm.BOOK_FAMILIES["plum"],
        }
        for decls, (fill, stroke, text) in cases.items():
            with self.subTest(decls=decls):
                out = self.reink(decls)
                self.assertIn(f"fill:{fill}", out)
                self.assertIn(f"stroke:{stroke}", out)
                self.assertIn(f"color:{text}", out)

    def test_the_fill_decides_the_family_when_the_stroke_disagrees(self):
        """A pale-blue box with a purple border is a blue box; the border is
        the weaker signal and both halves still have to come from one family."""
        out = self.reink("fill:#e3f2fd,stroke:#7b1fa2,color:#4a148c")
        fill, stroke, text = mm.BOOK_FAMILIES["info"]
        self.assertEqual(out, f"classDef x fill:{fill},stroke:{stroke},"
                              f"color:{text}")

    def test_a_diagram_that_distinguishes_two_groups_still_does(self):
        block = ("classDef core fill:#4a90d9,stroke:#2c5f8a,color:#fff\n"
                 "classDef tool fill:#8fbc8f,stroke:#5a8a5a,color:#fff")
        out = mm.reink_colors(block)
        self.assertIn(mm.BOOK_FAMILIES["info"][0], out)
        self.assertIn(mm.BOOK_FAMILIES["good"][0], out)

    def test_a_mid_tone_fill_becomes_its_hue_tint_not_a_dark_box(self):
        """The manuscript's darkest fills are #1abc9c / #27ae60; they read as
        teal and green here, and the white labels they carried stay legible."""
        for hexc, family in (("#27ae60", "good"), ("#1abc9c", "good"),
                             ("#0d47a1", "info")):
            with self.subTest(hexc=hexc):
                fill, _, text = mm.BOOK_FAMILIES[family]
                out = self.reink(f"fill:{hexc},stroke:#333,color:#fff")
                self.assertIn(f"fill:{fill}", out)
                self.assertIn(f"color:{text}", out)

    def test_properties_without_a_colour_are_left_alone(self):
        out = self.reink("fill:#2196F3,stroke:#333,stroke-width:2px,"
                         "font-weight:bold")
        self.assertIn("stroke-width:2px", out)
        self.assertIn("font-weight:bold", out)

    def test_only_directive_lines_are_rewritten(self):
        src = ("sequenceDiagram\n"
               "  Keychain-->>Server: hit #1 (32ms) fill:#000\n"
               '  A["style: keep this fill:#e8f4f8 text"]\n'
               "  style A fill:#2196F3,stroke:#333")
        out = mm.reink_colors(src)
        self.assertIn("hit #1 (32ms) fill:#000", out)
        self.assertIn('A["style: keep this fill:#e8f4f8 text"]', out)
        self.assertIn(f"style A fill:{mm.BOOK_FAMILIES['info'][0]}", out)

    def test_reinking_is_idempotent(self):
        src = ("classDef a fill:#27ae60,stroke:#1b5e20,color:#fff\n"
               "style B fill:#ffcdd2,stroke:#d32f2f")
        once = mm.reink_colors(src)
        self.assertEqual(once, mm.reink_colors(once))

    def test_no_shipped_directive_keeps_an_off_book_hex(self):
        allowed = {c.lower() for fam in mm.BOOK_FAMILIES.values() for c in fam}
        checked = 0
        for path in sorted(REPO_ROOT.glob("**/*.md")):
            if "node_modules" in path.parts:
                continue
            for block in re.findall(r"```mermaid\n(.*?)```",
                                    read_text(path), re.S):
                for line in mm.reink_colors(block).splitlines():
                    if not re.match(r"\s*(classDef|style)\s", line):
                        continue
                    for prop, hexc in re.findall(
                            r"\b(fill|stroke|color)\s*:\s*(#[0-9a-fA-F]{3,8})",
                            line):
                        with self.subTest(path=path.name, prop=prop):
                            self.assertIn(hexc.lower(), allowed)
                        checked += 1
        self.assertGreater(checked, 2000)


class FigureMarkup(unittest.TestCase):
    def test_zh_and_en_caption_words_and_figure_id(self):
        zh = render.mermaid_figure("ab" * 6, "<svg/>", "7-1", "循环", "zh")
        en = render.mermaid_figure("ab" * 6, "<svg/>", "7-1", "loop", "en")
        self.assertIn('<figure class="diagram" id="fig-abababababab">', zh)
        self.assertIn('<span class="fig-no">图 7-1</span>', zh)
        self.assertIn('<span class="fig-no">Figure 7-1</span>', en)
        self.assertIn('<div class="diagram-frame"><svg/></div>', zh)

    def test_diagram_frame_holds_the_svg_and_no_block_element_is_nested(self):
        html = render.mermaid_figure("a" * 12, '<svg id="mm-a"><g/></svg>',
                                     "1-1", "x", "zh")
        self.assertEqual(html.count("<svg"), 1)
        self.assertNotIn("<pre>", html)

    WIDE = ('<svg id="mm-w" width="100%" style="max-width: 100%;" '
            'viewBox="0 0 3592 1200"></svg>')
    NARROW = ('<svg id="mm-n" width="100%" style="max-width: 100%;" '
              'viewBox="0 0 795 160"></svg>')

    def test_wide_plates_are_floored_and_advertise_the_scroll(self):
        zh = render.mermaid_figure("w" * 12, self.WIDE, "C-15", "依赖关系", "zh")
        self.assertIn("min-width:2600px;", zh)   # capped, so the drag stays sane
        self.assertIn('<figure class="diagram wide"', zh)
        self.assertIn('<span class="fig-hint">可横向拖动</span>', zh)
        en = render.mermaid_figure("w" * 12, self.WIDE, "C-15", "deps", "en")
        self.assertIn("drag sideways", en)
        self.assertNotIn("可横向", en)

    def test_plates_that_already_fit_the_column_are_untouched(self):
        for vw in ("795", "1100"):
            svg = self.NARROW.replace("0 0 795 160", f"0 0 {vw} 160")
            html = render.mermaid_figure("n" * 12, svg, "1-1", "x", "zh")
            self.assertNotIn("min-width", html)
            self.assertNotIn("fig-hint", html)
            self.assertIn('<figure class="diagram" id=', html)

    def test_the_floor_lands_on_the_root_tag_only(self):
        svg = ('<svg viewBox="0 0 2000 500"><style>.a{min-width:1px}</style>'
               '<g style="max-width:9px"/></svg>')
        out, floor = render.floor_wide_svg(svg)
        self.assertEqual(floor, "1700px")
        self.assertIn('<svg style="min-width:1700px;" viewBox="0 0 2000 500">', out)
        self.assertIn("<style>.a{min-width:1px}</style>", out)
        self.assertIn('<g style="max-width:9px"/>', out)


class DiagramsSurviveRendering(unittest.TestCase):
    """End-to-end for one synthetic unit: placeholder -> figure, no <pre>."""

    def render(self, text, lang="zh", uid="ch01", kind="chapter"):
        _no, _t, body = normalize_h1(text, lang, "t.md")
        body, blocks, langs = extract_mermaid(body, "t.md")
        caps = mm.captions_for(text, blocks)
        unit = Unit(id=uid, kind=kind, lang=lang, no=_no, title=_t,
                    md=body, blocks=blocks, code_langs=langs, path="t.md",
                    anchor=uid)
        mapping = {i: i for i in expected_ids(load_configs()[0])}
        return render.render_unit(unit, mapping,
                                  diagrams=mm.source_fallback(blocks, caps))

    def test_prose_after_a_diagram_is_not_swallowed_by_a_pre(self):
        payload = self.render(
            "# 第 1 章　标题\n\n```mermaid\ngraph LR\nA-->B\n```\n\n"
            "这段是普通段落，不该在 pre 里。\n")
        html = payload["html"]
        self.assertEqual(payload["n_diagrams"], 1)
        self.assertNotIn("@@MM:", html)
        self.assertNotIn("```", html)
        self.assertIn("<p>这段是普通段落，不该在 pre 里。</p>", html)
        pre = re.search(r"<pre[^>]*>(.*?)</pre>", html, re.S)
        self.assertIn("graph LR", pre.group(1))       # the mermaid source
        self.assertNotIn("普通段落", pre.group(1))

    def test_missing_diagram_is_marked_not_dropped(self):
        payload = self.render("# 第 1 章　标题\n\n```mermaid\nA-->B\n```\n")
        unit = payload["unit"]
        html = render.render_unit(unit, {}, diagrams={})["html"]
        self.assertIn('class="mermaid-missing"', html)
        self.assertNotIn("@@MM:", html)

    def test_figures_are_numbered_by_chapter_and_run(self):
        payload = self.render(
            "# 第 7 章　上下文\n\n```mermaid\nA-->B\n```\n\n```mermaid\nC-->D\n```\n")
        self.assertEqual(payload["n_diagrams"], 2)
        self.assertIn(">图 7-1<", payload["html"])
        self.assertIn(">图 7-2<", payload["html"])

    def test_appendix_figures_are_numbered_with_the_letter(self):
        payload = self.render("# 附录 A：地图\n\n```mermaid\nA-->B\n```\n",
                              uid="apxa", kind="appendix")
        self.assertIn(">图 A1<", payload["html"])

    def test_diagram_uids_do_not_collide_across_the_two_languages(self):
        manifest, _sources = load_configs()
        seen = {}
        for lang in ("zh", "en"):
            for unit_def, kind, _part in unit_stream(manifest):
                u = load_unit(unit_def, kind, lang, REPO_ROOT)
                for b in u.blocks:
                    seen.setdefault(b.uid, set()).add((lang, u.id))
        self.assertEqual(sum(1 for v in seen.values() if len(v) > 1), 0)


if __name__ == "__main__":
    unittest.main()
