"""HTML post-processing contracts: ids, slugs, stray angles, callouts, code chips."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yuyu_book import render  # noqa: E402
from yuyu_book.core import (BuildError, REPO_ROOT, expected_ids, load_configs,  # noqa: E402
                            load_unit, unit_stream)


class IdsAndSlugs(unittest.TestCase):
    def test_prefix_ids_namespaces_headings_and_local_links(self):
        doc = '<h2 id="sec-a">x</h2><a href="#sec-a">go</a>'
        out = render.prefix_ids(doc, "ch03")
        self.assertIn('id="ch03-sec-a"', out)
        self.assertIn('href="#ch03-sec-a"', out)

    def test_prefix_ids_leaves_diagram_and_figure_ids_alone(self):
        doc = '<svg id="mm-abc"></svg><figure id="fig-abc"></figure>'
        self.assertEqual(render.prefix_ids(doc, "ch03"), doc)

    def test_prefix_ids_is_idempotent(self):
        doc = '<h2 id="s">x</h2>'
        once = render.prefix_ids(doc, "ch03")
        self.assertEqual(render.prefix_ids(once, "ch03"), once)

    def test_book_slug_keeps_cjk_and_drops_punctuation(self):
        self.assertEqual(render.book_slug("工具系统 — Agent 的双手"),
                         "工具系统-agent-的双手")
        self.assertEqual(render.book_slug("`code` **bold**"), "code-bold")
        self.assertEqual(render.book_slug("!!!"), "section")

    def test_heading_ids_are_slugified_consistently_for_both_languages(self):
        for unit_def, kind, _part in unit_stream(load_configs()[0]):
            for lang in ("zh", "en"):
                u = load_unit(unit_def, kind, lang, REPO_ROOT)
                for rx in re.finditer(r"^###\s+(.+)$", u.md, re.M):
                    slug = render.book_slug(rx.group(1))
                    self.assertRegex(slug, r"^[a-z0-9\w\u4e00-\u9fff-]+$")


class StrayAnglesAndQuotes(unittest.TestCase):
    def test_type_parameters_in_prose_are_escaped(self):
        out = render.escape_stray_angles("协议是 Tool<I,O,P> 五要素")
        self.assertIn("&lt;I,O,P&gt;", out)
        self.assertIn("Tool", out)

    def test_code_spans_and_fences_are_left_untouched(self):
        text = "`Tool<I,O,P>` 与\n\n```ts\nconst x: Map<K,V> = new Map()\n```\n"
        self.assertEqual(render.escape_stray_angles(text), text)

    def test_curlify_pairs_quotes_only_outside_code(self):
        doc = '<p>他说"好"了</p><pre><code>print("hi")</code></pre>'
        out = render.curlify(doc)
        self.assertIn("“好”", out)
        self.assertIn('print("hi")', out)

    def test_curlify_balances_many_quotes_in_one_paragraph(self):
        out = render.curlify("<p>\"a\" \"b\" \"c\"</p>")
        self.assertEqual(out.count("“"), 3)
        self.assertEqual(out.count("”"), 3)


class Components(unittest.TestCase):
    def test_labelled_quotes_become_typed_callouts(self):
        doc = ('<blockquote><p><strong>最佳实践：</strong> 内容</p></blockquote>'
               '<blockquote><p><strong>反模式警告：</strong> 小心</p></blockquote>'
               '<blockquote><p><strong>Design Insight:</strong> note</p></blockquote>')
        out = render.classify_callouts(doc, "zh")
        self.assertIn('class="callout callout-tip"', out)
        self.assertIn('class="callout callout-warning"', out)
        self.assertIn('class="callout callout-concept"', out)
        self.assertIn("callout-tag", out)
        self.assertIn("callout-body", out)

    def test_callout_labels_wear_the_punctuation_of_their_own_language(self):
        # an English chapter closing on "Best practice：" is a typographic leak
        doc = "<blockquote><p><strong>Best Practice:</strong> content</p></blockquote>"
        self.assertIn("<strong>Best Practice：</strong>",
                      render.classify_callouts(doc, "zh"))
        en = render.classify_callouts(doc, "en")
        self.assertIn("<strong>Best Practice:</strong>", en)
        self.assertNotIn("：", en)

    def test_unlabelled_quotes_stay_plain_blockquotes(self):
        doc = "<blockquote><p>普通的引文</p></blockquote>"
        self.assertEqual(render.classify_callouts(doc, "zh"), doc)

    def test_unknown_labels_are_not_invented(self):
        doc = "<blockquote><p><strong>某个没登记的标签：</strong> x</p></blockquote>"
        self.assertEqual(render.classify_callouts(doc, "zh"), doc)

    def test_tables_are_wrapped_for_horizontal_scroll(self):
        out = render.wrap_tables("<table><tr><th>a</th><th>b</th></tr></table>")
        self.assertIn('class="table-scroll" data-cols="2"', out)
        # a phone paints no scrollbar until the reader drags, so the only other
        # way to the columns past the cut is keyboard -- which needs a stop here
        self.assertIn('tabindex="0"', out)

    def test_a_long_flag_name_gets_break_points_in_a_table(self):
        # Appendix B ships flag names like KAIROS_GITHUB_WEBHOOKS; without a
        # break point the cell's min-content width pushed the table off the page.
        out = render.soften_long_names(
            "<td><code>KAIROS_GITHUB_WEBHOOKS</code></td>")
        self.assertEqual(out, "<td><code>KAIROS_<wbr>GITHUB_<wbr>WEBHOOKS</code></td>")

    def test_softening_never_changes_a_tables_column_count(self):
        table = ("<table><tr><td><code>KAIROS_GITHUB_WEBHOOKS</code></td>"
                 "<td>c</td></tr></table>")
        out = render.soften_long_names(render.wrap_tables(table))
        self.assertIn('data-cols="2"', out)
        self.assertIn("KAIROS_<wbr>GITHUB_<wbr>WEBHOOKS", out)

    def test_a_flag_name_in_plain_table_text_is_softened(self):
        # Appendix B writes （条件启用：CLAUDE_CODE_VERIFY_PLAN） with no markup at
        # all, which is exactly the cell that ran 7pt past the printed page box.
        out = render.soften_long_names(
            "<td>计划执行验证（条件启用：CLAUDE_CODE_VERIFY_PLAN）</td>")
        self.assertIn("CLAUDE_<wbr>CODE_<wbr>VERIFY_<wbr>PLAN", out)
        self.assertTrue(out.endswith("）</td>"), out)

    def test_markup_and_attributes_are_never_broken_into(self):
        doc = '<td class="KAIROS_GITHUB_WEBHOOKS"><a href="#p_q_2025">说明</a></td>'
        self.assertEqual(render.soften_long_names(doc), doc)

    def test_camel_case_names_break_at_each_word(self):
        # ch05's skipDangerousModePermissionPrompt is one 34-character word
        # that no CJK line will ever hold, and it has no underscore to lean on.
        out = render.soften_long_names(
            "<p><code>skipDangerousModePermissionPrompt</code> 控制</p>")
        self.assertEqual(
            out,
            "<p><code>skip<wbr>Dangerous<wbr>Mode<wbr>Permission"
            "<wbr>Prompt</code> 控制</p>")

    def test_a_camel_boundary_next_to_an_underscore_is_not_doubled(self):
        out = render.soften_long_names("<code>getFeatureValue_CACHED_MAY_BE_STALE</code>")
        self.assertEqual(
            out,
            "<code>get<wbr>Feature<wbr>Value_<wbr>CACHED_<wbr>MAY_<wbr>BE_<wbr>STALE</code>")
        self.assertNotIn("<wbr><wbr>", out)

    def test_a_path_breaks_after_its_slashes_but_not_inside_a_scheme(self):
        out = render.soften_long_names("<p><code>~/.claude/settings.json</code></p>")
        self.assertEqual(out, "<p><code>~/<wbr>.claude/<wbr>settings.json</code></p>")

    def test_names_too_short_to_run_off_a_line_are_left_alone(self):
        doc = "<td><code>FileWrite</code> 和 <code>read_only</code> 的说明</td>"
        self.assertEqual(render.soften_long_names(doc), doc)

    def test_entities_are_copied_through(self):
        # the offsets are counted against the source text; cutting inside
        # `&amp;` would print a literal ampersand.
        doc = "<p>ANTHROPIC_API_&amp;_KEY_HERE_NOW</p>"
        self.assertEqual(render.soften_long_names(doc), doc)

    def test_the_closing_ruts_are_glued_to_the_block_they_close(self):
        # left as a trailing sibling they fall onto a fresh sheet, and the next
        # unit's forced page break then leaves that sheet empty
        out = render.glue_closer("<p>最后一句。</p>", '<svg class="ch-rut"></svg>')
        self.assertEqual(out, '<div class="ch-close"><p>最后一句。</p>'
                              '<svg class="ch-rut"></svg></div>')

    def test_the_notes_list_can_carry_the_ruts(self):
        # ch06 ends on its cited links, which is where the blank sheet appeared
        doc = '<p>正文</p><aside class="chapter-notes"><ol><li>u</li></ol></aside>'
        out = render.glue_closer(doc, "<i>")
        self.assertIn('<div class="ch-close"><aside', out)
        self.assertTrue(out.endswith("<i></div>"), out)

    def test_a_unit_ending_on_a_plate_closes_with_loose_ruts(self):
        doc = '<p>短</p><figure class="plate"><svg></svg></figure>'
        self.assertEqual(render.glue_closer(doc, "<i>"), doc + "<i>")

    def test_a_short_code_plate_can_carry_the_ruts(self):
        # ch04 (en) ends on a fence, and its ruts stranded a whole sheet
        doc = '<p>正文</p><div class="codehilite"><pre><code>a = 1</code></pre></div>'
        out = render.glue_closer(doc, "<i>")
        self.assertIn('<div class="ch-close"><div class="codehilite">', out)
        self.assertTrue(out.endswith("<i></div>"), out)

    def test_a_plate_taller_than_a_page_is_not_moved(self):
        lines = "\n".join(f"<code>line {n}</code>" for n in range(40))
        doc = f'<div class="codehilite"><pre>{lines}</pre></div>'
        self.assertEqual(render.glue_closer(doc, "<i>"), doc + "<i>")

    def test_a_tail_too_tall_to_move_is_left_alone(self):
        doc = "<p>" + "很长" * 500 + "</p>"
        self.assertEqual(render.glue_closer(doc, "<i>"), doc + "<i>")

    def test_stray_text_after_the_last_block_is_not_swallowed(self):
        doc = "<p>正文</p>尾注"
        self.assertEqual(render.glue_closer(doc, "<i>"), doc + "<i>")

    def test_code_blocks_get_the_language_chip(self):
        doc = '<div class="codehilite"><pre>x</pre></div>'
        out = render.stamp_code_langs(doc, ["ts"], "f.md")
        self.assertIn('data-lang="ts"', out)
        # the block scrolls sideways, so it needs a stop of its own
        self.assertIn('<pre tabindex="0">x</pre>', out)

    def test_an_unlabelled_fence_still_gets_its_scroller_reachable(self):
        doc = '<div class="codehilite"><pre>x</pre></div>'
        out = render.stamp_code_langs(doc, [""], "f.md")
        self.assertNotIn("data-lang", out)
        self.assertIn('<pre tabindex="0">', out)

    def test_language_stamp_refuses_to_guess_when_counts_drift(self):
        doc = '<div class="codehilite"></div><div class="codehilite"></div>'
        with self.assertRaises(BuildError):
            render.stamp_code_langs(doc, ["py"], "f.md")

    def test_external_links_are_numbered_into_footnotes(self):
        external: list[str] = []
        doc = render.process_links(
            '<p>见 <a href="https://example.com/a">文档</a></p>', external)
        self.assertEqual(external, ["https://example.com/a"])
        self.assertIn('class="ext"', doc)
        self.assertIn("<sup", doc)
        notes = render.footnotes_html(external, "zh")
        self.assertIn("fn-", notes)
        self.assertIn("https://example.com/a", notes)


class RenderedUnit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.sources = load_configs()
        cls.mapping = {i: i for i in expected_ids(cls.manifest)}
        cls.payloads = {}
        for unit_def, kind, _part in unit_stream(cls.manifest):
            u = load_unit(unit_def, kind, "zh", REPO_ROOT)
            diagrams = {b.uid: ("标题", "<svg><g/></svg>") for b in u.blocks}
            cls.payloads[u.id] = render.render_unit(u, cls.mapping,
                                                    diagrams=diagrams)

    def test_no_mermaid_placeholder_survives_rendering(self):
        for pid, p in self.payloads.items():
            self.assertNotIn("@@MM:", p["html"], pid)

    def test_diagrams_are_figures_with_prefixed_ids_and_numbering(self):
        html = self.payloads["ch02"]["html"]
        self.assertIn('<figure class="diagram"', html)
        self.assertIn("图 2-1", html)
        self.assertIn("图 2-2", html)

    def test_front_matter_plates_are_plainly_numbered(self):
        html = self.payloads["front"]["html"]
        self.assertIn("图 1", html)
        self.assertNotIn("图 T", html)      # 前言 has no chapter digit to wear
        self.assertIn("图 A1", self.payloads["apxa"]["html"])

    def test_missing_diagram_is_visible_instead_of_silent(self):
        unit_def = next(u for u, k, _p in unit_stream(self.manifest)
                        if u["id"] == "ch02")
        u = load_unit(unit_def, "chapter", "zh", REPO_ROOT)
        p = render.render_unit(u, self.mapping, diagrams={})
        self.assertIn('class="mermaid-missing"', p["html"])

    def test_heading_ids_are_prefixed_and_discoverable(self):
        for pid in ("ch01", "apxd"):
            p = self.payloads[pid]
            self.assertTrue(p["headings"], pid)
            for h in p["headings"]:
                self.assertTrue(h["id"].startswith(f"{pid}-"), h["id"])
                self.assertIn(f'id="{h["id"]}"', p["html"])

    def test_unit_ids_never_collide_across_the_book(self):
        ids = re.findall(r'id="([^"]+)"',
                         "".join(p["html"] for p in self.payloads.values()))
        self.assertEqual(len(ids), len(set(ids)))

    def test_heading_levels_are_monotonic_enough_for_a_contents_page(self):
        for pid, p in self.payloads.items():
            for h in p["headings"]:
                self.assertIn(h["level"], (2, 3, 4), pid)
                self.assertTrue(h["text"].strip(), pid)


class PlatePrintGeometry(unittest.TestCase):
    """A plate must print at a scale its own labels survive."""

    @staticmethod
    def _svg(w, h, font=18.0):
        return (f'<svg id="mm-abc123def456" width="100%" '
                f'viewBox="0 0 {w} {h}" style="max-width:100%">'
                f'<text style="font-size:{font}px">节点</text></svg>')

    def test_a_tall_plate_buys_the_height_it_needs(self):
        # 328x1756 is Appendix A's layer map: the 150mm cap left it at 4pt.
        cap = render.plate_cap(self._svg(328, 1756))
        self.assertIsNotNone(cap)
        mm = float(cap[:-2])
        self.assertGreater(mm, 150.0, cap)
        self.assertLessEqual(mm, 245.0, cap)

    def test_a_legible_plate_keeps_the_default_cap(self):
        for w, h in ((700, 400), (1200, 900), (400, 300)):
            self.assertIsNone(render.plate_cap(self._svg(w, h)), (w, h))

    def test_a_width_bound_plate_is_not_helped_by_height(self):
        # 2609x274 is a band: the column, not the cap, is what shrinks it.
        self.assertIsNone(render.plate_cap(self._svg(2609, 274)))

    def test_a_wide_band_turns_the_sheet(self):
        self.assertTrue(render.plate_landscape(self._svg(2609, 274)))
        out = render.mermaid_figure("abc123def456", self._svg(2609, 274),
                                    "C6", "标志依赖", "zh")
        self.assertIn('class="diagram wide landscape"', out)
        # No cap of its own: the landscape sheet is 170mm tall and an inline
        # 165mm pushed the caption onto a second sheet.
        self.assertNotIn("--plate-cap", out)

    def test_a_tall_or_small_plate_keeps_the_portrait_sheet(self):
        for w, h in ((328, 1756), (700, 400), (300, 4000)):
            self.assertFalse(render.plate_landscape(self._svg(w, h)), (w, h))

    def test_a_plate_that_stays_illegible_either_way_keeps_its_sheet(self):
        # 3592x1330 reads at 2.5pt here and 3.7pt turned: no whole empty
        # landscape sheet buys anything real for it.
        self.assertFalse(render.plate_landscape(self._svg(3592, 1330)))

    def test_a_plate_too_big_for_one_column_gets_no_exception(self):
        self.assertIsNone(render.plate_cap(self._svg(300, 4000)))

    def test_the_figure_carries_its_cap_as_a_css_variable(self):
        out = render.mermaid_figure("abc123def456", self._svg(328, 1756),
                                    "A2", "模块依赖关系", "zh")
        self.assertRegex(out, r'<figure class="diagram" id="[^"]*" '
                             r'style="--plate-cap:\d+mm">')

    def test_an_ordinary_figure_carries_no_style_at_all(self):
        out = render.mermaid_figure("abc123def456", self._svg(700, 400),
                                    "2-3", "循环", "zh")
        self.assertNotIn("--plate-cap", out)
        self.assertIn("图 2-3", out)


if __name__ == "__main__":
    unittest.main()
