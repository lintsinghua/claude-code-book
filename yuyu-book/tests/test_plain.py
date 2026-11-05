"""The plain-language layer: term marks, chapter panels, reading tiers.

Fixtures are synthetic so the contracts hold while the registry is still
being authored; the shipped glosses.json/reading-paths.json are asserted in
the RealRegistry tests once they exist.
"""
import copy
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yuyu_book import pages, plain, render  # noqa: E402
from yuyu_book.core import (BOOK_DIR, REPO_ROOT, BuildError, load_json,
                            read_text, unit_stream)  # noqa: E402

ZH_CH02 = "第一部分-基础篇/02-对话循环-Agent的心跳.md"
EN_CH02 = "en/Part-1-Foundations/02-The-Dialog-Loop-Heartbeat-of-an-Agent.md"


def _real_h2(manifest: dict, uid: str) -> int:
    """Headings the renderer actually turns into <h2>: `## ` lines that sit
    outside every code fence (four such lines in ch11/ch14 are sample text)."""
    path = next(u["zh"] for u, _k, _p in unit_stream(manifest) if u["id"] == uid)
    return sum(1 for line in plain.prose_lines(read_text(REPO_ROOT / path)).values()
               if re.match(r"^##\s+\S", line))


def gloss(gid, zh, en, forms_zh, forms_en, priority="core", mark=None,
          analogy=None, evidence=None, why=None, why_evidence=None,
          no_why=False):
    entry = {
        "term": {"zh": zh, "en": en},
        "forms": {"zh": forms_zh, "en": forms_en},
        "plain": {"zh": "能暂停再继续交结果的函数",
                  "en": "a function that pauses and hands out one result"},
        "analogy": dict({"zh": "像收银机，打一张撕一张"}, **(analogy or {})),
        "why": dict({"zh": "一趟要交很多次，等它返一次就全卡住",
                     "en": "a run hands out many results, so waiting for one "
                           "return would stall the rest"}, **(why or {})),
        "why_evidence": list(why_evidence if why_evidence is not None
                             else [f"{ZH_CH02}:18", f"{EN_CH02}:18"]),
        "priority": priority,
        "evidence": evidence if evidence is not None
        else [f"{ZH_CH02}:18", f"{EN_CH02}:18"]}
    if mark is not None:
        entry["mark"] = mark
    if no_why:
        entry.pop("why")
        entry.pop("why_evidence")
    return {gid: entry}


def _band_evidence(zh: str, en: str) -> list[str]:
    """The first prose line of each language's file — enough to prove the
    fixture points at real text rather than at a sample block."""
    out = []
    for rel in (zh, en):
        lines = plain.prose_lines(read_text(REPO_ROOT / rel))
        out.append(f"{rel}:{min(lines)}")
    return out


def mini_manifest(chapters=("ch02",), with_plain=True):
    ids = ["front"] + list(chapters)
    files = {"front": ("00-前言.md", "en/00-Foreword.md")}
    guides = {}
    for i in ids:
        guides[i] = {"question": {"zh": "问", "en": "q"},
                     "deliverable": {"zh": "交付", "en": "d"},
                     "boundary": {"zh": "边界", "en": "b"}}
        if with_plain:
            guides[i]["plain"] = {"zh": "循环怎么转", "en": "how the loop turns"}
            guides[i]["analogy"] = {"zh": "像流水线", "en": "an assembly line"}
            zh, en = files.get(i) or (ZH_CH02, EN_CH02)
            guides[i]["plain_evidence"] = _band_evidence(zh, en)
    return {"front": {"id": "front", "zh": "00-前言.md", "en": "en/00-Foreword.md"},
            "parts": [{"id": "p1", "units": [
                {"id": c, "zh": ZH_CH02, "en": EN_CH02} for c in chapters]}],
            "appendices": [], "guides": guides}


def mark(doc, glosses, lang="zh", tiers=None):
    layer = plain.Layer(glosses, lang)
    return layer.apply(doc, tiers) + (layer.used,)


class TermMarks(unittest.TestCase):
    def test_first_prose_mention_gets_a_dashed_mark(self):
        out, hits, _used = mark("<p>异步生成器是循环的骨骼。</p>",
                                    gloss("async-generator", "异步生成器",
                                          "async generator", ["异步生成器"],
                                          ["async generator"]))
        self.assertIn('<span class="gloss" tabindex="0" data-g="async-generator">'
                      '异步生成器', out)
        self.assertEqual([h["id"] for h in hits], ["async-generator"])

    def test_only_the_first_mention_of_a_term_is_marked(self):
        doc = "<p>异步生成器很好。异步生成器确实好。</p>"
        out, hits, _u = mark(doc, gloss("ag", "异步生成器", "async generator",
                                            ["异步生成器"], ["async generator"]))
        self.assertEqual(out.count('class="gloss"'), 1)
        self.assertEqual(len(hits), 1)

    def test_the_popover_carries_the_definition_the_reason_and_the_picture(self):
        out, _h, _u = mark("<p>异步生成器</p>",
                              gloss("ag", "异步生成器", "async generator",
                                    ["异步生成器"], ["async generator"]))
        self.assertIn('<span class="gloss-pop" role="tooltip">'
                      '<b>异步生成器</b>'
                      '<span class="gp-plain">能暂停再继续交结果的函数</span>'
                      '<span class="gp-why"><i class="gw-t">为什么</i>'
                      '一趟要交很多次，等它返一次就全卡住</span>'
                      '<span class="gp-analogy">像收银机，打一张撕一张</span>', out)

    def test_a_gloss_without_a_reason_drops_the_reason_line(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], no_why=True)
        out, _h, _u = mark("<p>异步生成器</p>", g)
        self.assertNotIn("gp-why", out)
        self.assertIn("gp-analogy", out)

    def test_analogy_is_optional(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], analogy={"zh": ""})
        out, _h, _u = mark("<p>异步生成器</p>", g)
        self.assertNotIn("gp-analogy", out)

    def test_code_links_headings_and_plates_are_never_marked(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"])
        cases = [
            ("<p><code>异步生成器</code>，正文里也提到了异步生成器。</p>", 1),
            ('<p><a class="xref" href="#ch03">异步生成器</a>'
             '，正文里也提到了异步生成器。</p>', 1),
            ('<p><span class="fig-no">异步生成器</span>'
             '正文里的异步生成器也要标。</p>', 1),
            ("<h2>异步生成器</h2>", 0),
            ("<figure><figcaption>异步生成器</figcaption></figure>", 0),
            ('<p><sup class="fn">异步生成器</sup>脚注不算。</p>', 0),
            ("<p><svg><text>异步生成器</text></svg></p>", 0),
        ]
        for frag, want in cases:
            out, hits, _u = mark(frag, g)
            self.assertEqual(len(hits), want, frag)
            self.assertEqual(out.count('class="gloss"'), want, frag)
        out, _h, _u = mark(cases[0][0], g)
        self.assertIn("<code>异步生成器</code>", out)

    def test_an_identifier_is_marked_where_a_reader_meets_it(self):
        """Half the book's vocabulary only ever appears as code: a term written
        `isConcurrencySafe` in a sentence is that reader's first and only
        meeting with it, so the help has to be reachable there."""
        g = gloss("concurrency-safe", "并发安全", "concurrency safe",
                  ["isConcurrencySafe"], ["isConcurrencySafe"],
                  evidence=[f"{ZH_CH02}:18", f"{EN_CH02}:18"])
        out, hits, _u = mark("<p><code>isConcurrencySafe</code> 决定两个工具"
                             "能不能同时跑。</p>", g)
        self.assertEqual([h["id"] for h in hits], ["concurrency-safe"])
        self.assertRegex(out, r"<code><span class=\"gloss\"[^>]*>"
                             r"isConcurrencySafe<span class=\"gloss-pop\"")

    def test_an_ordinary_word_inside_code_stays_plain(self):
        """Only shapes a reader cannot parse as a word earn a mark inside
        code; `Streaming` in backticks is English already, and dashing every
        backtapped word would turn prose into a field of dashes."""
        g = gloss("streaming", "流式", "Streaming", ["Streaming"],
                  ["Streaming"])
        out, hits, _u = mark("<p>先看 <code>Streaming</code> 的两种收尾，"
                             "正文里的 Streaming 才算。</p>", g)
        self.assertEqual(len(hits), 1)
        self.assertIn("<code>Streaming</code>", out)

    def test_a_code_plate_never_gets_a_mark_even_for_an_identifier(self):
        g = gloss("concurrency-safe", "并发安全", "concurrency safe",
                  ["isConcurrencySafe"], ["isConcurrencySafe"])
        out, hits, _u = mark(
            "<pre><code>const t = buildTool({ isConcurrencySafe: true });"
            "</code></pre>", g)
        self.assertEqual(len(hits), 0)
        self.assertNotIn('class="gloss"', out)

    def test_the_longer_form_wins_when_two_terms_overlap(self):
        g = {}
        g.update(gloss("async-generator", "异步生成器", "async generator",
                       ["异步生成器"], ["async generator"]))
        g.update(gloss("generator", "生成器", "generator", ["生成器"],
                       ["generator"],
                       evidence=[f"{ZH_CH02}:18"]))
        out, hits, _u = mark("<p>异步生成器与生成器</p>", g)
        self.assertEqual([h["id"] for h in hits],
                         ["async-generator", "generator"])
        self.assertNotIn('data-g="generator">异步', out)

    def test_ascii_forms_do_not_bite_into_longer_words(self):
        g = gloss("token", "Token", "token", ["Token"], ["token", "Token"])
        out, hits, _u = mark("<p>Tokens 与 tokenized 不该命中，Token 才命中。</p>", g)
        self.assertEqual([h["form"] for h in hits], ["Token"])
        self.assertNotIn("Tokens<span", out)

    def test_markup_between_two_words_of_a_form_does_not_split_the_match(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"])
        _out, hits, _u = mark("<p>an async generator loop</p>", g, lang="en")
        self.assertEqual([h["form"] for h in hits], ["async generator"])

    def test_popover_text_is_escaped(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"])
        g["ag"]["plain"]["zh"] = '若 x < y 则 "暂停"'
        out, _h, _u = mark("<p>异步生成器</p>", g)
        self.assertIn("&lt;", out)
        self.assertNotIn("<span class=\"gp-plain\">若 x < y", out)

    def test_mark_false_terms_stay_out_of_the_book(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], mark=False)
        out, hits, used = mark("<p>异步生成器</p>", g)
        self.assertNotIn('class="gloss"', out)
        self.assertEqual((hits, used), ([], set()))

    def test_extra_terms_are_registered_but_not_dashed(self):
        """Only core terms clutter the prose; `mark: true` opts one back in."""
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], priority="extra")
        out, hits, _u = mark("<p>异步生成器</p>", g)
        self.assertEqual((out, hits), ("<p>异步生成器</p>", []))
        g["ag"]["mark"] = True
        _out, hits, _u = mark("<p>异步生成器</p>", g)
        self.assertEqual([h["id"] for h in hits], ["ag"])

    def test_a_unit_with_too_many_new_terms_fails_loudly(self):
        g = {}
        for i in range(plain.MAX_PANEL + 1):
            g.update(gloss(f"t{i}", f"词{i}", f"term{i}", [f"词{i}"],
                           [f"term{i}"], priority="extra", mark=True))
        doc = "<p>" + "".join(f"词{i}" for i in range(plain.MAX_PANEL + 1)) + "</p>"
        with self.assertRaises(BuildError) as ctx:
            mark(doc, g)
        self.assertIn("new terms in one unit", str(ctx.exception))
        self.assertIn("priority", str(ctx.exception))


class CoverageGate(unittest.TestCase):
    def test_a_core_term_nobody_marked_means_its_forms_are_wrong(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"])
        layer = plain.Layer(g, "zh")
        with self.assertRaises(BuildError) as ctx:
            layer.check_coverage()
        self.assertIn("never marked", str(ctx.exception))
        layer.apply("<p>异步生成器</p>", None)
        layer.check_coverage()

    def test_an_extra_term_that_never_appears_is_allowed(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], priority="extra")
        plain.Layer(g, "zh").check_coverage()


class SectionTiers(unittest.TestCase):
    def test_each_h2_gets_its_level_chip_in_order(self):
        doc = '<h2 id="a">甲</h2><h2 id="b">乙</h2><h2 id="c">丙</h2>'
        out = plain.stamp_tiers(doc, ["start", "core", "deep"], "zh")
        self.assertEqual(out,
                         '<h2 id="a">甲<span class="sec-tier t-start">起步</span></h2>'
                         '<h2 id="b">乙<span class="sec-tier t-core">主干</span></h2>'
                         '<h2 id="c">丙<span class="sec-tier t-deep">进阶</span></h2>')

    def test_english_uses_the_english_labels(self):
        out = plain.stamp_tiers('<h2 id="a">One</h2>', ["core"], "en")
        self.assertIn('t-core">Core<', out)

    def test_a_tier_list_that_does_not_line_up_fails_the_build(self):
        """Positional chips must not drift onto the wrong sections."""
        doc = '<h2 id="a">甲</h2><h2 id="b">乙</h2>'
        for tiers in (["start"], ["start", "core", "deep"]):
            with self.assertRaises(BuildError) as cm:
                plain.stamp_tiers(doc, tiers, "zh", who="ch02")
            self.assertIn("2", str(cm.exception))
            self.assertIn("ch02", str(cm.exception))

    def test_no_tiers_means_no_chips(self):
        doc = '<h2 id="a">甲</h2>'
        self.assertEqual(plain.stamp_tiers(doc, [], "zh"), doc)
        self.assertEqual(plain.stamp_tiers(doc, None, "zh"), doc)

    def test_a_heading_containing_markup_still_gets_one_chip(self):
        out = plain.stamp_tiers('<h2 id="a">用 <code>yield</code> 的循环</h2>',
                                ["core"], "zh")
        self.assertEqual(out.count("sec-tier"), 1)
        self.assertTrue(out.endswith("</h2>"))


class PanelAndLead(unittest.TestCase):
    def test_the_panel_repeats_every_marked_term_in_order(self):
        hits = [{"id": "a", "form": "甲", "term": "甲词", "plain": "说明甲",
                 "analogy": "", "priority": "core"},
                {"id": "b", "form": "乙", "term": "乙词", "plain": "说明乙",
                 "analogy": "", "priority": "extra"}]
        out = pages.new_terms_panel(hits, "zh")
        self.assertEqual(out.index("甲词") < out.index("乙词"), True)
        self.assertEqual(out.count('<li class="nt-row">'), 2)
        self.assertIn('<span class="nt-n">2</span>', out)

    def test_no_hits_means_no_panel(self):
        self.assertEqual(pages.new_terms_panel([], "zh"), "")

    def test_lead_band_needs_the_plain_line(self):
        self.assertEqual(pages.lead_band({}, "zh"), "")
        out = pages.lead_band({"plain": {"zh": "循环怎么转"}}, "zh")
        self.assertIn("一句话讲明白", out)
        self.assertIn("循环怎么转", out)
        self.assertNotIn("lb-analogy", out)

    def test_lead_band_adds_the_analogy_only_when_present(self):
        out = pages.lead_band({"plain": {"zh": "循环怎么转"},
                               "analogy": {"zh": "像流水线"}}, "zh")
        self.assertIn("打个比方", out)
        self.assertIn("像流水线", out)

    def test_tier_legend_counts_sections_per_level(self):
        out = pages.tier_legend({"ch01": ["start", "core"],
                                 "ch02": ["core", "deep"]}, "zh")
        self.assertIn('tl-n-start">1<', out)
        self.assertIn('tl-n-core">2<', out)
        self.assertIn('tl-n-deep">1<', out)

    def test_tier_legend_absent_without_paths(self):
        self.assertEqual(pages.tier_legend({}, "zh"), "")
        self.assertEqual(pages.tier_legend(None, "en"), "")


class RegistryValidation(unittest.TestCase):
    def test_the_shipped_files_validate_when_present(self):
        glosses, paths = plain.load_plain()
        if not glosses:
            self.skipTest("registry not merged yet")
        plain.validate_plain(glosses, paths, mini_manifest(
            chapters=tuple(paths), with_plain=True))

    def test_evidence_must_point_at_prose_not_a_fence(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], evidence=[f"{ZH_CH02}:28",
                                                 f"{EN_CH02}:18"])
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {}, mini_manifest())
        self.assertIn("inside a code fence", str(ctx.exception))

    def test_evidence_line_must_actually_contain_the_form(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], evidence=[f"{ZH_CH02}:20",
                                                 f"{EN_CH02}:18"])
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {}, mini_manifest())
        self.assertIn("does not contain any registered form",
                      str(ctx.exception))

    def test_evidence_file_must_exist(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], evidence=["nope/missing.md:1"])
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {}, mini_manifest())
        self.assertIn("evidence file", str(ctx.exception))

    def test_core_glosses_need_both_languages(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], evidence=[f"{ZH_CH02}:18"])
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {}, mini_manifest())
        self.assertIn("both languages", str(ctx.exception))

    def test_an_extra_gloss_may_be_single_language(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], priority="extra",
                  evidence=[f"{ZH_CH02}:18"])
        plain.validate_plain(g, {"ch02": ["start", "core"]}, mini_manifest())

    def test_plain_lines_are_size_limited(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"])
        g["ag"]["plain"]["zh"] = "长" * (plain.LIMITS["plain"]["zh"] + 1)
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {}, mini_manifest())
        self.assertIn("plain.zh is", str(ctx.exception))

    def test_a_core_term_without_a_reason_is_rejected(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], no_why=True)
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {"ch02": ["start", "core"]},
                                 mini_manifest())
        self.assertIn("owes the reader a why", str(ctx.exception))

    def test_an_extra_term_may_stay_a_definition_only(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], priority="extra", no_why=True)
        plain.validate_plain(g, {"ch02": ["start", "core"]}, mini_manifest())

    def test_a_reason_needs_its_own_prose_line_in_each_language(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], why_evidence=[f"{ZH_CH02}:18"])
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {"ch02": ["start", "core"]},
                                 mini_manifest())
        self.assertIn("why needs one prose line in each language",
                      str(ctx.exception))

    def test_a_reason_may_not_be_backed_by_a_sample_block(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], why_evidence=[f"{ZH_CH02}:28",
                                                     f"{EN_CH02}:18"])
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {"ch02": ["start", "core"]},
                                 mini_manifest())
        self.assertIn("gloss ag why", str(ctx.exception))

    def test_reason_lines_are_size_limited(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"])
        g["ag"]["why"]["zh"] = "长" * (plain.LIMITS["why"]["zh"] + 1)
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {"ch02": ["start", "core"]},
                                 mini_manifest())
        self.assertIn("why.zh is", str(ctx.exception))

    def test_an_english_reason_may_not_carry_chinese(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"])
        g["ag"]["why"]["en"] = "a run hands out 很多次 results"
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {"ch02": ["start", "core"]},
                                 mini_manifest())
        self.assertIn("why.en still carries Chinese", str(ctx.exception))

    def test_a_gloss_without_evidence_is_rejected(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"], evidence=[])
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {}, mini_manifest())
        self.assertIn("no evidence", str(ctx.exception))

    def test_every_chapter_needs_tiers(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"])
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {}, mini_manifest())
        self.assertIn("chapter ch02 has no tiers", str(ctx.exception))
        plain.validate_plain(g, {"ch02": ["start", "core"]}, mini_manifest())

    def test_unknown_tier_names_are_rejected(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"])
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {"ch02": ["start", "optional"]},
                                 mini_manifest())
        self.assertIn("unknown tier", str(ctx.exception))

    def test_a_unit_without_a_lead_band_is_rejected(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"])
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain(g, {"ch02": ["start"]},
                                 mini_manifest(with_plain=False))
        self.assertIn("plain is missing", str(ctx.exception))

    def test_an_unauthored_layer_is_not_a_failure(self):
        plain.validate_plain({}, {}, mini_manifest(with_plain=False))

    def test_a_lead_band_without_evidence_is_rejected(self):
        m = mini_manifest()
        m["guides"]["ch02"]["plain_evidence"] = []
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain({}, {"ch02": ["start", "core"]}, m)
        self.assertIn("ch02: plain_evidence is missing", str(ctx.exception))

    def test_a_lead_band_needs_prose_on_both_sides_of_the_manuscript(self):
        m = mini_manifest()
        m["guides"]["ch02"]["plain_evidence"] = [f"{ZH_CH02}:18"]
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain({}, {"ch02": ["start", "core"]}, m)
        self.assertIn("both languages", str(ctx.exception))

    def test_band_evidence_pointing_into_a_sample_block_is_rejected(self):
        m = mini_manifest()
        m["guides"]["ch02"]["plain_evidence"] = [f"{ZH_CH02}:28",
                                                 f"{EN_CH02}:18"]
        with self.assertRaises(BuildError) as ctx:
            plain.validate_plain({}, {"ch02": ["start", "core"]}, m)
        self.assertIn("inside a code fence", str(ctx.exception))


class RenderIntegration(unittest.TestCase):
    """The layer must not corrupt the unit payload it annotates."""

    @classmethod
    def setUpClass(cls):
        from yuyu_book.core import (REPO_ROOT, expected_ids, load_configs,
                                    load_unit, unit_stream)
        cls.manifest = load_configs()[0]
        cls.mapping = {i: i for i in expected_ids(cls.manifest)}
        udef, kind, part = next(
            (u, k, p) for u, k, p in unit_stream(cls.manifest)
            if u["id"] == "ch02")
        cls.unit = load_unit(udef, kind, "zh", REPO_ROOT)
        cls.unit.part = part
        cls.diagrams = {b.uid: ("图说", '<svg viewBox="0 0 10 10"></svg>')
                        for b in cls.unit.blocks}

    def render(self, glosses, tiers=None):
        layer = plain.Layer(glosses, "zh") if glosses else None
        return render.render_unit(self.unit, self.mapping,
                                  diagrams=self.diagrams, gloss=layer,
                                  tiers=tiers)

    def test_headings_keep_their_names_without_chips(self):
        p = self.render({}, ["start"] * 6)
        self.assertTrue(p["headings"])
        for h in p["headings"]:
            self.assertNotIn("起步", h["text"])
            self.assertNotIn("sec-tier", h["text"])

    def test_marks_and_hits_agree(self):
        g = gloss("ag", "异步生成器", "async generator", ["异步生成器"],
                  ["async generator"])
        p = self.render(g)
        self.assertEqual(p["html"].count('class="gloss"'), len(p["new_terms"]))

    def test_the_plain_layer_leaves_structure_intact(self):
        bare = self.render({})
        doped = self.render(gloss("ag", "异步生成器", "async generator",
                                     ["异步生成器"], ["async generator"]),
                            ["start", "core", "deep", "core", "core", "deep"])
        for key in ("n_diagrams",):
            self.assertEqual(bare[key], doped[key])
        self.assertEqual(len(bare["headings"]), len(doped["headings"]))
        self.assertEqual(bare["external"], doped["external"])
        self.assertEqual(len(doped["html"]), len(doped["html"]))

    def test_ids_stay_prefixed_under_the_layer(self):
        p = self.render(gloss("ag", "异步生成器", "async generator",
                                 ["异步生成器"], ["async generator"]))
        self.assertNotIn('<span class="gloss" id=', p["html"])
        self.assertIn('data-g="ag"', p["html"])


@unittest.skipUnless((BOOK_DIR / "glosses.json").exists(),
                     "registry not merged yet")
class RealRegistry(unittest.TestCase):
    """What ships has to pass the same gates the fixtures are held to."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = load_json(BOOK_DIR / "manifest.json")
        cls.glosses, cls.paths = plain.load_plain()

    def test_the_shipped_registry_and_paths_validate(self):
        plain.validate_plain(self.glosses, self.paths, self.manifest)

    def test_the_registry_is_a_real_layer_not_a_token_one(self):
        core = sum(1 for g in self.glosses.values()
                   if g.get("priority") == "core")
        self.assertGreaterEqual(len(self.glosses), 70, "term coverage")
        self.assertGreaterEqual(core, 40, "core (dashed) coverage")
        self.assertEqual(sum(len(v) for v in self.paths.values()),
                         sum(_real_h2(self.manifest, uid) for uid in self.paths))

    def test_every_term_is_written_in_both_languages(self):
        for gid, g in self.glosses.items():
            for field in ("term", "forms", "plain"):
                for lang in ("zh", "en"):
                    val = g[field][lang]
                    self.assertTrue(val, f"{gid}.{field}.{lang} is empty")

    def test_no_analogy_reuses_the_term_it_explains(self):
        for gid, g in self.glosses.items():
            if not g.get("analogy"):
                continue
            for lang in ("zh", "en"):
                ana = g["analogy"].get(lang, "")
                if ana:
                    self.assertNotIn(g["term"][lang], ana,
                                     f"{gid} analogy.{lang} is circular")

    def test_every_core_term_tells_the_reader_why(self):
        bare = [gid for gid, g in self.glosses.items()
                if g.get("priority") == "core"
                and not all((g.get("why") or {}).get(lang)
                            for lang in ("zh", "en"))]
        self.assertEqual(bare, [], "core terms without a reason line")

    def test_a_reason_is_not_the_definition_repeated(self):
        for gid, g in self.glosses.items():
            for lang in ("zh", "en"):
                why = (g.get("why") or {}).get(lang)
                if why:
                    self.assertNotEqual(why, g["plain"][lang],
                                        f"{gid} why.{lang} repeats plain.{lang}")


@unittest.skipUnless((BOOK_DIR / "reading-paths.json").exists(),
                     "reading paths not merged yet")
class ShippedLayer(unittest.TestCase):
    """The lead bands and tier chips ship before the term registry does, so
    their own promises have to be checked against the real manuscript."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = load_json(BOOK_DIR / "manifest.json")
        _glosses, cls.paths = plain.load_plain()

    def test_the_shipped_paths_and_bands_validate(self):
        plain.validate_plain({}, self.paths, self.manifest)

    def test_every_unit_has_a_plain_band(self):
        ids = ({self.manifest["front"]["id"]}
               | {u["id"] for p in self.manifest["parts"] for u in p["units"]}
               | {a["id"] for a in self.manifest["appendices"]})
        self.assertEqual(ids, set(self.manifest["guides"]))
        for uid in ids:
            guide = self.manifest["guides"][uid]
            for field in ("plain", "plain_evidence"):
                self.assertIn(field, guide, f"{uid} has no {field}")

    def test_tier_lists_match_the_rendered_headings(self):
        """A heading that lives inside a code fence never becomes an <h2>, so
        counting `^## ` naively shifts every later chip onto the wrong
        section — the two counts have to agree per chapter, not just overall."""
        for uid, tiers in sorted(self.paths.items()):
            real = _real_h2(self.manifest, uid)
            self.assertEqual(len(tiers), real,
                             f"{uid}: {len(tiers)} tiers vs {real} headings")

    def test_every_level_of_the_route_is_used(self):
        """A route legend that only ever says 主干 teaches nothing."""
        counts = Counter(t for tiers in self.paths.values() for t in tiers)
        for tier in plain.TIER_ORDER:
            self.assertGreater(counts[tier], 5, tier)
