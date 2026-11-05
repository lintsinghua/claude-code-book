"""Cross-reference autolinking: 第N章 / Chapter N become clickable."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yuyu_book import render  # noqa: E402
from yuyu_book.core import (REPO_ROOT, expected_ids, load_configs, load_unit,  # noqa: E402
                            unit_stream)

MAP = {i: i for i in expected_ids(load_configs()[0])}


def link(text, current="ch01", lang="zh"):
    return render.RefLinker(MAP, current, lang).transform(text)


class ChineseReferences(unittest.TestCase):
    def test_plain_mention_becomes_a_link(self):
        out = link("<p>这一机制在第 3 章展开。</p>")
        self.assertIn('<a class="xref" href="#ch03">第 3 章</a>', out)

    def test_space_variants_all_match(self):
        for text in ("第3章", "第 3 章", "第  3 章"):
            self.assertIn('href="#ch03"', link(f"<p>{text}</p>"), text)

    def test_appendix_letters_match_too(self):
        self.assertIn('href="#apxd"', link("<p>详见附录 D。</p>"))

    def test_only_one_link_per_target_per_text_run(self):
        out = link("<p>第 4 章讲过，第 4 章还讲过。</p>")
        self.assertEqual(out.count('href="#ch04"'), 1)

    def test_a_mention_of_the_current_chapter_is_not_linked(self):
        out = link("<p>本章与第 1 章不同。</p>", current="ch01")
        self.assertNotIn("xref", out)

    def test_chapters_outside_the_book_are_left_alone(self):
        for text in ("第 16 章", "第 0 章"):
            self.assertNotIn("xref", link(f"<p>{text}</p>"))

    def test_code_and_pre_subtrees_are_never_rewritten(self):
        doc = ('<pre>第 3 章</pre><p>读 <code>第 3 章</code> 与'
               '<code data-x="1">第 4 章</code>。</p>')
        out = link(doc)
        self.assertIn("<pre>第 3 章</pre>", out)
        self.assertIn("<code>第 3 章</code>", out)
        self.assertIn("<code data-x=\"1\">第 4 章</code>", out)

    def test_existing_anchors_and_svg_are_skipped(self):
        doc = ('<a href="#ch03">第 3 章</a><p>第 5 章</p>'
               '<svg><text>第 6 章</text></svg>')
        out = link(doc)
        self.assertIn('<a href="#ch03">第 3 章</a>', out)
        self.assertIn("<svg><text>第 6 章</text></svg>", out)
        self.assertIn('href="#ch05"', out)

    def test_nesting_recovers_from_a_closed_skip_tag(self):
        doc = "<p><code>x</code>第 3 章</p>"
        self.assertIn('href="#ch03"', link(doc))


class EnglishReferences(unittest.TestCase):
    def test_chapter_and_appendix_mentions(self):
        self.assertIn('href="#ch12"', link("<p>see Chapter 12</p>", lang="en"))
        self.assertIn('href="#apxa"', link("<p>Appendix A lists it</p>", lang="en"))

    def test_plurals_and_prose_without_a_number_stay_plain(self):
        for text in ("Chapters 3 and 4", "the chapter explains"):
            self.assertNotIn("xref", link(f"<p>{text}</p>", lang="en"), text)

    def test_word_boundaries_prevent_midword_matches(self):
        self.assertNotIn("xref", link("<p>NonChapter 3 material</p>", lang="en"))


class WholeBookCrossReferences(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest, _sources = load_configs()
        cls.html = {}
        for lang in ("zh", "en"):
            # render every unit the way the book does, so the assertion is
            # about real prose rather than a fixture
            parts = []
            for unit_def, kind, _part in unit_stream(manifest):
                u = load_unit(unit_def, kind, lang, REPO_ROOT)
                diagrams = {b.uid: ("图", "<svg/>") for b in u.blocks}
                parts.append(render.render_unit(u, MAP, diagrams=diagrams)["html"])
            cls.html[lang] = "\n".join(parts)
        cls.manifest = manifest

    def test_every_generated_href_resolves_to_a_real_unit(self):
        for lang, doc in self.html.items():
            for href in re.findall(r'<a class="xref" href="#([^"]+)"', doc):
                self.assertIn(href, MAP, f"{lang}: xref to unknown unit {href}")

    def test_autolinking_actually_fires_in_prose(self):
        for lang in ("zh", "en"):
            self.assertGreater(
                self.html[lang].count('class="xref"'), 40,
                f"{lang}: cross-references went missing")

    def test_autolink_can_be_switched_off(self):
        unit_def, kind = next(
            (u, k) for u, k, _p in unit_stream(self.manifest)
            if u["id"] == "ch04")
        u = load_unit(unit_def, kind, "zh", REPO_ROOT)
        diagrams = {b.uid: ("图", "<svg/>") for b in u.blocks}
        off = render.render_unit(u, MAP, diagrams=diagrams, autolink=False)["html"]
        on = render.render_unit(u, MAP, diagrams=diagrams)["html"]
        self.assertLess(off.count('class="xref"'), on.count('class="xref"'))


if __name__ == "__main__":
    unittest.main()
