"""Structure pages: cover, imprint, compass, contents, registry, index, shell."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yuyu_book import pages, plain, render  # noqa: E402
from yuyu_book.core import (BOOK_DIR, REPO_ROOT, BuildError, expected_ids,
                            load_configs, load_json, load_unit,
                            unit_stream)  # noqa: E402
from yuyu_book.style import CSS, ink_mark, page, trace, wheel  # noqa: E402


class Config(unittest.TestCase):
    """Shared fixtures. It must be a TestCase itself: a plain mixin silently
    drops every subclass out of discovery, and the pages went untested."""
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.sources = load_configs()
        cls.units = {u["id"]: load_unit(u, k, "zh", REPO_ROOT)
                     for u, k, _p in unit_stream(cls.manifest)}


class Ornaments(Config):
    def test_each_wheel_gets_its_own_spoke_id(self):
        """The wheel is inlined 10+ times per book; shared ids would break
        every instance after the first."""
        a, b = wheel(24), wheel(24)
        ida = re.search(r'id="(spoke\d+)"', a).group(1)
        idb = re.search(r'id="(spoke\d+)"', b).group(1)
        self.assertNotEqual(ida, idb)
        self.assertIn(f'href="#{ida}"', a)
        self.assertNotIn('href="#spoke"', a + b)

    def test_wheel_is_self_coloured_and_accessible(self):
        self.assertIn('aria-hidden="true"', wheel())
        self.assertIn("currentColor", wheel())


class HandInked(unittest.TestCase):
    """The drawn marks and the chapter wire. Both are inlined dozens of times,
    so they answer to the same rules as a file in illustrations/."""

    KINDS = ("tip", "warning", "info", "concept", "note")

    def test_every_callout_kind_is_inked(self):
        from yuyu_book.render import CALLOUT_LABELS
        self.assertEqual(set(CALLOUT_LABELS.values()) - set(self.KINDS), set())
        for kind in self.KINDS:
            self.assertIn("currentColor", ink_mark(kind), kind)

    def test_nothing_the_builder_inlines_carries_an_id_or_a_reach_outside(self):
        marks = [ink_mark(k) for k in self.KINDS] + [trace("ch01"), trace("apxb")]
        for text in marks:
            for banned in ("id=", "href=", "url(", "<script", "<style"):
                self.assertNotIn(banned, text)

    def test_an_unknown_kind_draws_nothing(self):
        self.assertEqual(ink_mark("mood"), "")

    def test_a_unit_always_gets_the_same_wire_back(self):
        """The trace is seeded by the unit id: a rebuild must not redraw the
        chapter heads, or the SVG diff of two builds means nothing."""
        self.assertEqual(trace("ch07"), trace("ch07"))

    def test_no_two_units_share_a_wire(self):
        units = ["front", "ch01", "ch02", "ch03", "ch04", "ch05", "ch06",
                 "ch07", "ch08", "ch09", "ch10", "ch11", "ch12", "ch13",
                 "ch14", "ch15", "apxa", "apxb", "apxc", "apxd"]
        self.assertEqual(len({trace(u) for u in units}), len(units))

    def test_the_chapter_head_closes_on_the_wire(self):
        self.assertIn("ch-trace", CSS)
        self.assertIn('class="ch-trace"', trace("ch01"))

    def test_a_section_break_is_drawn_not_typed(self):
        from yuyu_book.render import ink_rules
        out = ink_rules("<p>a</p><hr /><p>b</p>")
        self.assertIn('class="hr-rule"', out)
        self.assertIn("currentColor", out)
        self.assertNotIn("<hr", out)
        self.assertNotIn("❖", CSS)

    def test_the_knot_follows_the_same_inline_rules_as_every_other_drawing(self):
        from yuyu_book.style import knot
        for banned in ("id=", "href=", "url(", "<script", "<style"):
            self.assertNotIn(banned, knot())


class RouteAndRut(unittest.TestCase):
    """The road a part opens on and the ruts a chapter closes on. Both are
    seeded, both are inlined for every unit, so they answer to the same rules."""

    def test_the_route_draws_one_station_per_chapter(self):
        from yuyu_book.style import route_map
        for count in (3, 4, 5):
            self.assertEqual(route_map("p1", count).count('r="3.3"'), count, count)

    def test_the_route_closes_the_leg_with_a_second_ring(self):
        from yuyu_book.style import route_map
        self.assertEqual(route_map("p2", 4).count('r="6"'), 1)

    def test_no_part_rolls_the_same_road(self):
        from yuyu_book.style import route_map
        roads = [route_map(f"p{i}", 4) for i in range(1, 6)]
        self.assertEqual(len(set(roads)), len(roads))

    def test_a_part_rolls_the_same_road_every_build(self):
        from yuyu_book.style import route_map
        self.assertEqual(route_map("p3", 4), route_map("p3", 4))

    def test_no_two_units_close_on_the_same_ruts(self):
        from yuyu_book.style import rut
        units = [f"ch{i:02d}" for i in range(1, 16)] + ["apxa", "apxb", "front"]
        self.assertEqual(len({rut(u) for u in units}), len(units))

    def test_both_new_drawings_are_inline_safe_and_self_coloured(self):
        from yuyu_book.style import route_map, rut
        for text in (route_map("p1", 4), rut("ch01"), rut("apxd")):
            for banned in ("id=", "href=", "url(", "<script", "<style"):
                self.assertNotIn(banned, text)
            self.assertIn("currentColor", text)
            self.assertIn('viewBox="', text)
            self.assertIn('aria-hidden="true"', text)

    def test_the_book_inks_them_and_re_inks_them_for_paper(self):
        from yuyu_book.style import CSS
        for selector, rule in ((".pd-route", "pd-route"), (".ch-rut", "ch-rut")):
            self.assertIn(selector, CSS)
        # the screen bronzes drop out on a laser printer, so both run full ink
        for name in ("pd-route", "ch-rut"):
            self.assertRegex(CSS, rf"\.{name}\{{[^}}]*var\(--bronze-3\)")
        self.assertRegex(CSS, r"\.ch-rut\{[^}]*break-before:avoid")


class RouteMap(Config):
    """The whole book on one road. The picture is the fun part, but the list
    under it is the part that has to be right: it is what a screen reader,
    a search box and a reader with a pen all get."""

    def setUp(self):
        self.nos = {i: (u.no_plain or pages.FRONT_NO)
                    for i, u in self.units.items()}
        self.html = pages.route_map_page(self.manifest, "zh", self.nos)
        self.svg = (self.html.split('<svg class="itinerary"', 1)[1]
                    .split("</svg>", 1)[0])

    def test_the_road_has_a_ring_for_every_chapter_and_a_dot_for_the_siding(self):
        chapters = sum(len(p["units"]) for p in self.manifest["parts"])
        self.assertEqual(self.svg.count('r="3.6"'), chapters, chapters)
        self.assertEqual(self.svg.count('r="2.7"'),
                         len(self.manifest["appendices"]))

    def test_the_wheel_at_the_head_carries_the_foreword_number(self):
        self.assertEqual(self.svg.count(f'>{pages.FRONT_NO}</text>'), 1)
        self.assertEqual(self.svg.count(f'>{self.nos["ch01"]}</text>'), 1)

    def test_the_map_is_the_same_map_every_build(self):
        again = pages.route_map_page(self.manifest, "zh", self.nos)
        self.assertEqual(again, self.html)

    def test_the_list_under_the_map_links_every_leg(self):
        want = [self.manifest["front"]["id"]] + \
               [p["id"] for p in self.manifest["parts"]] + \
               [self.manifest["appendices"][0]["id"]]
        got = re.findall(r'<li><p class="rm-head"><a class="xref" href="#([^"]+)"',
                         self.html)
        self.assertEqual(got, want)

    def test_the_list_names_the_number_written_on_every_station(self):
        for unit_id, no in self.nos.items():
            self.assertIn(no, self.html, unit_id)

    def test_the_key_teaches_the_three_marks_the_map_uses(self):
        keys = re.findall(r'<li><svg class="rmk rmk-(\w+)"', self.html)
        self.assertEqual(keys, ["wheel", "ring", "siding"])

    def test_the_new_drawings_are_inline_safe_and_self_coloured(self):
        from yuyu_book.style import key_mark
        for text in (self.svg, *(key_mark(k) for k in ("wheel", "ring", "siding"))):
            for banned in ("id=", "href=", "url(", "<script", "<style"):
                self.assertNotIn(banned, text)
            self.assertIn("currentColor", text)
            self.assertIn('aria-hidden="true"', text)

    def test_paper_re_inks_the_map_and_keeps_it_on_one_sheet(self):
        self.assertRegex(CSS, r"\.itinerary\{[^}]*break-inside:avoid")
        # the screen bronze drops out on a laser printer: paper runs full ink
        self.assertRegex(CSS, r"\.itinerary\{[^}]*var\(--bronze-3\)")
        print_block = CSS[CSS.index("@media print"):]
        self.assertIn(".rm-why{display:none}", print_block,
                      "the leg goals spill the route map over its own sheet")
        for name in ("rm-lead", "rm-key", "rm-legs", "rail-map"):
            self.assertIn(f".{name}", CSS)


class FrontMatter(Config):
    def test_cover_carries_title_epigraph_author_version_and_license(self):
        m = self.manifest
        html = pages.cover(m, "zh")
        self.assertIn('id="cover"', html)
        self.assertIn(m["title"]["zh"].split("：")[0], html)
        self.assertIn(m["author"], html)
        self.assertIn(m["version"], html)
        self.assertIn(m["license"]["name"], html)

    def test_cover_draws_the_carriage_inline_and_ships_no_bitmap(self):
        html = pages.cover(self.manifest, "zh")
        self.assertIn('class="cover-art"', html)
        self.assertNotIn("<img", html)
        self.assertIn("currentColor", html)

    def test_cover_splits_an_english_title_on_the_colon(self):
        html = pages.cover(self.manifest, "en")
        self.assertIn("bt-main", html)
        self.assertNotIn("：", html)

    def test_imprint_links_the_license_and_states_the_notice(self):
        html = pages.imprint(self.manifest, "zh")
        self.assertIn('id="imprint"', html)
        self.assertIn(self.manifest["license"]["url"], html)
        self.assertIn("front-page", html)

    def test_revision_history_is_rendered_per_language(self):
        entries = load_json(BOOK_DIR / "revisions.json")["entries"]
        for lang in ("zh", "en"):
            html = pages.revisions_page(entries, lang)
            self.assertIn('id="revisions"', html)
            self.assertIn(f'v{entries[0]["version"]}', html)
            self.assertTrue(re.search(r"<li>", html), "no bullet in revision list")

    def test_revision_notes_are_typeset_not_left_in_markdown(self):
        """The notes quote the builder's own names; a row of raw backticks
        around one reads as a typo in a book that sets code spans properly."""
        entries = load_json(BOOK_DIR / "revisions.json")["entries"]
        for lang in ("zh", "en"):
            html = pages.revisions_page(entries, lang)
            self.assertNotIn("`", html, "a backtick reached the page")
            self.assertIn("<code>pdf_meta()</code>", html)
            self.assertNotIn("<code></code>", html)

    def test_a_note_naming_a_long_flag_still_fits_a_narrow_screen(self):
        """Front matter never runs the unit pipeline, so the break points have
        to be put in over the assembled page: `getFeatureValue_CACHED_MAY_BE_STALE`
        in a revision note pushed the document 37px past a 390px screen."""
        entries = load_json(BOOK_DIR / "revisions.json")["entries"]
        for lang in ("zh", "en"):
            out = render.soften_long_names(pages.revisions_page(entries, lang))
            self.assertIn("<wbr>", out, "no break point in a long name")
            self.assertNotIn("<wbr><wbr>", out)
            self.assertIn("get<wbr>Feature<wbr>Value_<wbr>CACHED_<wbr>MAY_"
                          "<wbr>BE_<wbr>STALE", out)

    def test_reading_routes_link_to_the_first_chapter_of_each_part(self):
        html = pages.how_to_read(self.manifest, "zh")
        self.assertIn('id="how-to-read"', html)
        for part in self.manifest["parts"]:
            self.assertIn(f'href="#{part["units"][0]["id"]}"', html)
        self.assertEqual(html.count("route-card"), len(self.manifest["start_reading"]))

    def test_part_divider_lists_its_own_chapters(self):
        part = self.manifest["parts"][1]
        rows = [(u["id"], u["id"][-2:], u["id"].upper()) for u in part["units"]]
        html = pages.part_divider(part, "zh", 2, rows)
        self.assertEqual(f'id="{part["id"]}"', re.search(r'id="(p\d)"', html).group(0))
        for anchor, no, label in rows:
            self.assertIn(f'href="#{anchor}"', html)
            self.assertIn(f'data-no="{no}">{label}</a>', html)
        self.assertIn("Ⅱ", pages._ROMAN[2])

    def test_part_divider_draws_the_road_before_its_stops(self):
        """The strip above the list is the part's itinerary: one ring for every
        chapter the divider then names, so the count is not decoration."""
        part = self.manifest["parts"][1]
        rows = [(u["id"], u["id"][-2:], u["id"].upper()) for u in part["units"]]
        html = pages.part_divider(part, "zh", 2, rows)
        self.assertEqual(html.count('r="3.3"'), len(rows))
        self.assertLess(html.index("pd-route"), html.index("pd-list"))


class Compass(Config):
    def test_three_cards_and_cited_source_chips(self):
        guide = self.manifest["guides"]["ch07"]
        html = pages.compass(self.units["ch07"], guide, self.sources, "zh")
        for key in ("question", "deliverable", "boundary"):
            self.assertIn(f'compass-card {key}', html)
            self.assertIn(guide[key]["zh"], html)
        self.assertEqual(html.count("source-chip"), len(guide["sources"]))
        for sid in guide["sources"]:
            self.assertIn(f'href="#source-{sid}"', html)

    def test_english_compass_uses_english_copy(self):
        guide = self.manifest["guides"]["ch01"]
        html = pages.compass(self.units["ch01"], guide, self.sources, "en")
        self.assertIn(guide["question"]["en"], html)
        self.assertNotIn(guide["question"]["zh"], html)

    def test_chips_point_at_real_registry_entries(self):
        registry = pages.source_registry(self.sources, "zh")
        for uid, guide in self.manifest["guides"].items():
            for sid in guide.get("sources", []):
                self.assertIn(f'id="source-{sid}"', registry, uid)


class Contents(Config):
    def _entries(self):
        entries = [{"kind": "row", "anchor": "front", "no": "00", "title": "前言"}]
        for i, part in enumerate(self.manifest["parts"], 1):
            entries.append({"kind": "part", "anchor": part["id"],
                            "no": pages._ROMAN[i], "title": part["title"]["zh"]})
            for u in part["units"]:
                unit = self.units[u["id"]]
                entries.append({"kind": "row", "anchor": u["id"],
                                "no": unit.no_plain, "title": unit.title})
        entries.append({"kind": "hr"})
        for apx in self.manifest["appendices"]:
            unit = self.units[apx["id"]]
            entries.append({"kind": "row", "anchor": apx["id"],
                            "no": unit.no_plain, "title": unit.title})
        return entries

    def test_every_entry_gets_a_page_ref_placeholder(self):
        html = pages.toc_html(self._entries(), "zh")
        for e in self._entries():
            if e["kind"] == "hr":
                continue
            self.assertIn(f'data-ref="{e["anchor"]}"', html, e["anchor"])
        self.assertIn('class="page-ref', html)

    def test_parts_and_their_rows_group_so_a_page_break_cannot_strand_a_heading(self):
        html = pages.toc_html(self._entries(), "zh")
        groups = re.findall(r'<div class="toc-group">(.*?)</div>\s*(?=<div class="toc-group">|</section>)',
                            html, re.S)
        self.assertGreaterEqual(len(groups), 5)
        for group in groups:
            parts = re.findall(r'class="toc-part"', group)
            self.assertLessEqual(len(parts), 1, "one heading per group")

    def test_appendix_gutter_labels_are_letters_in_both_languages(self):
        for apx in self.manifest["appendices"]:
            for lang in ("zh", "en"):
                u = load_unit(apx, "appendix", lang, REPO_ROOT)
                self.assertEqual(u.no_plain, apx["id"][-1].upper(),
                                 f"{apx['id']} {lang}: {u.no_plain}")

    def test_chapter_gutter_labels_are_zero_padded_numbers(self):
        for part in self.manifest["parts"]:
            for u in part["units"]:
                unit = self.units[u["id"]]
                self.assertRegex(unit.no_plain, r"^\d{2}$", u["id"])


class BackMatter(Config):
    def test_registry_groups_by_kind_and_counts_every_source(self):
        html = pages.source_registry(self.sources, "zh")
        self.assertIn('id="sources"', html)
        for sid in self.sources:
            self.assertIn(f'id="source-{sid}"', html)
        self.assertEqual(html.count('class="reg-list"'),
                         len({s["kind"] for s in self.sources.values()}))

    def test_registry_urls_are_https_and_rel_noopener(self):
        html = pages.source_registry(self.sources, "en")
        for href in re.findall(r'<a class="ext" href="([^"]+)"', html):
            self.assertTrue(href.startswith("https://"), href)
        self.assertIn("rel=\"noopener\"", html)

    def test_registry_pins_are_shown_for_pinned_sources(self):
        html = pages.source_registry(self.sources, "zh")
        self.assertIn("v2.1.310", html)
        self.assertIn("b70dc411", html)

    def test_the_english_registry_holds_no_untranslated_annotation(self):
        """A row falls back to the Chinese field when its mirror is missing, so
        this is where a half-translated registry would surface: an English reader
        gets the date, the licence and the usage note in English or not at all."""
        en = pages.source_registry(self.sources, "en")
        leaks = sorted(set(re.findall(r"[一-鿿]", en)))
        self.assertEqual(leaks, [], f"English registry prints {leaks}")
        guide = self.manifest["guides"]["ch01"]
        chips = pages.compass(self.units["ch01"], guide, self.sources, "en")
        self.assertNotIn("：", chips, "English compass wears a full-width colon")
        self.assertEqual(re.findall(r"[一-鿿]", chips), [],
                         "English compass carries Chinese source text")
        zh = pages.source_registry(self.sources, "zh")
        self.assertTrue(re.search(r"[一-鿿]", zh),
                        "the Chinese registry lost its own text")

    def test_subject_index_links_only_to_units_that_exist(self):
        entries = load_json(BOOK_DIR / "subject-index.json")
        ids = set(expected_ids(self.manifest))
        html = pages.subject_index_page(entries, "zh")
        self.assertIn('id="subject-index"', html)
        for href in re.findall(r'<a class="xref" href="#([^"]+)"', html):
            self.assertIn(href, ids, "index points outside the book")
        self.assertGreater(len(entries), 50)

    def test_a_long_flag_name_breaks_on_the_underscore(self):
        """COWORKER_TYPE_TELEMETRY has no space in it; without a break point the
        row eats its dotted leader to fit, or runs over the column rule."""
        entries = load_json(BOOK_DIR / "subject-index.json")
        html = pages.subject_index_page(entries, "zh")
        row = re.search(r'<span class="idx-term">([^<]*(?:<wbr>[^<]*)*)</span>',
                        html)
        self.assertIsNotNone(row, "no underscore term reached the index")
        self.assertIn("_<wbr>", html)
        self.assertNotIn("<wbr><wbr>", html)
        self.assertNotIn("&lt;wbr&gt;", html, "the break tag got escaped away")

    def test_index_entries_are_sorted_and_lettered(self):
        entries = load_json(BOOK_DIR / "subject-index.json")
        letters = [e["letter"] for e in entries]
        self.assertEqual(letters, sorted(letters))
        for e in entries[:20]:
            self.assertTrue(e["zh"]["refs"] or e["en"]["refs"])
            self.assertTrue(e["key"].strip())

    def test_a_chinese_reader_can_search_in_chinese(self):
        """Appendix D files each term under its English name, which is the
        right heading for the English book and the wrong one for this: nobody
        who has just read 自动压缩 in ch 7 thinks to look under A. The
        translation column is a headword too, so it gets its own block."""
        entries = load_json(BOOK_DIR / "subject-index.json")
        html_zh = pages.subject_index_page(entries, "zh")
        terms = re.findall(r'<span class="idx-term">([^<]*)</span>', html_zh)
        cn = [t for t in terms if re.search(r"[\u4e00-\u9fff]", t)]
        self.assertGreater(len(cn), 60,
                           "the Chinese headwords never reached the index")
        self.assertIn("自动压缩", cn)
        heads = re.findall(r'<h2 class="idx-letter">([^<]*)</h2>', html_zh)
        self.assertEqual([h for h in heads if not re.fullmatch(r"[A-Z]", h)],
                         ["中文"], "the Chinese block needs its own heading")
        # nothing else in the book is filed by radical, so the block has to say
        # how it is ordered or it reads as a pile
        note = re.search(r'<p class="idx-note">([^<]*)</p>', html_zh)
        self.assertIsNotNone(note, "the Chinese block shipped without its rule")
        self.assertIn("部首", note.group(1))

    def test_the_english_index_does_not_inherit_chinese_rows(self):
        entries = load_json(BOOK_DIR / "subject-index.json")
        html_en = pages.subject_index_page(entries, "en")
        for t in re.findall(r'<span class="idx-term">([^<]*)</span>', html_en):
            self.assertNotRegex(t, r"[\u4e00-\u9fff]",
                                "a Chinese-only row leaked into the English index")
        self.assertNotIn("中文", html_en)

    def test_paper_reserves_the_folio_slot_the_pdf_fills(self):
        """A screen has no pages, so an index row shows only its locator chip and
        the row's folio placeholder stays hidden. Paper is the other case: the
        placeholder exists in the markup, but the print block inherited the
        screen's `display:none` and the PDF pass had no row list to stamp, so the
        slot was neither reserved nor filled."""
        entries = load_json(BOOK_DIR / "subject-index.json")
        printed = [e for e in entries if e["zh"]["refs"]]
        html = pages.subject_index_page(entries, "zh")
        rows = re.findall(r'<li class="idx-row">.*?</li>', html, re.S)
        self.assertEqual(len(rows), len(printed),
                         "a row this edition lists never reached the page")
        for row, e in zip(rows, printed):
            self.assertEqual(row.count('class="page-ref idx-ref"'), 1, e["key"])
            self.assertIn(f'data-ref="{e["zh"]["refs"][0]["anchor"]}"', row,
                          e["key"])
        print_block = CSS[CSS.index("@media print{"):]
        self.assertRegex(print_block, r"\.idx-row \.page-ref\{display:block")

    def test_the_meta_row_list_is_the_index_in_printed_order(self):
        """The folio pass is handed terms, not positions: page one of the PDF
        tells it which sheet each anchor landed on, the numbers are written into
        the slots the rows already reserve, and page two prints the book. If
        `pdf_meta` and the rendered page disagree, every number lands on somebody
        else's headword."""
        import build
        from html import unescape
        entries = load_json(BOOK_DIR / "subject-index.json")
        for lang in ("zh", "en"):
            printed = [e for e in entries if e[lang]["refs"]]
            html = pages.subject_index_page(entries, lang)
            rendered = [unescape(t).replace("_<wbr>", "_") for t in
                        re.findall(r'<span class="idx-term">(.*?)</span>', html, re.S)]
            rows = build.pdf_meta(self.manifest, [], [], lang, entries)["index_rows"]
            self.assertEqual([r["term"] for r in rows], rendered, lang)
            self.assertEqual([r["anchor"] for r in rows],
                             [e[lang]["refs"][0]["anchor"] for e in printed], lang)

    def test_folios_land_in_the_slot_of_their_own_row(self):
        """A row's slot is keyed by the anchor it links to, so `SessionStart`
        cannot borrow `Session`'s number however similar the two lines print."""
        html = ('<li class="idx-row"><span class="idx-term">Session</span>'
                '<span class="page-ref idx-ref" data-ref="ch07"></span></li>'
                '<li class="idx-row"><span class="idx-term">SessionStart</span>'
                '<span class="page-ref idx-ref" data-ref="ch08"></span></li>')
        filled = pages.fill_index_folios(html, {"ch07": 91, "ch08": 121})
        self.assertIn('data-ref="ch07">91</span>', filled)
        self.assertIn('data-ref="ch08">121</span>', filled)
        self.assertEqual(filled.count('class="page-ref idx-ref"'), 2)

    def test_an_unfilled_or_double_slot_fails_the_build(self):
        """The slot is the only place a folio may go: a row left blank prints an
        index that stops mid-column, and a number written twice would mean two
        rows claim one anchor."""
        html = ('<li class="idx-row"><span class="page-ref idx-ref" '
                'data-ref="ch07"></span></li>'
                '<li class="idx-row"><span class="page-ref idx-ref" '
                'data-ref="ch09"></span></li>')
        from yuyu_book.core import BuildError
        with self.assertRaises(BuildError):
            pages.fill_index_folios(html, {"ch07": 91})
        with self.assertRaises(BuildError):
            pages.fill_index_folios(html, {"ch07": 91, "ch09": 99, "ch11": 5})
        # the empty slot survives untouched in the source, so a screen reader
        # never gets a page number that only a printed sheet can know
        self.assertNotIn(">91<", html)


class Principles(Config):
    """The reason layer on paper: a hover card never reaches the PDF, so every
    core term's `why` has to be printed somewhere, filed under the chapter that
    argues for it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import build
        cls.build = build
        cls.glosses, _paths = plain.load_plain()

    def _groups(self, lang="zh"):
        units = [load_unit(u, k, lang, REPO_ROOT)
                 for u, k, _p in unit_stream(self.manifest)]
        return self.build._principle_groups(self.glosses, units, lang)

    def test_every_reason_the_html_hovers_is_printed_once(self):
        groups = self._groups()
        printed = sum(len(g["terms"]) for g in groups)
        owed = sum(1 for g in self.glosses.values()
                   if (g.get("why") or {}).get("zh"))
        self.assertEqual(printed, owed)
        self.assertEqual(owed, sum(1 for g in self.glosses.values()
                                   if g.get("priority") == "core"),
                         "a core term is missing its reason line")

    def test_the_page_files_each_reason_under_a_real_unit(self):
        ids = set(expected_ids(self.manifest))
        html = pages.principles_page(self._groups(), "zh")
        self.assertIn('id="principles"', html)
        for href in re.findall(r'<a class="xref" href="#([^"]+)"', html):
            self.assertIn(href, ids, "a principle head points outside the book")

    def test_a_row_carries_the_reason_then_the_picture(self):
        html = pages.principles_page(self._groups(), "zh")
        row = re.search(r'<li class="pr-row">.*?</li>', html, re.S).group(0)
        self.assertIn('<span class="pr-why"><i class="pr-t">为什么</i>', row)
        self.assertIn('<span class="pr-ana"><i class="pr-t">比方</i>', row)
        self.assertLess(row.index("pr-why"), row.index("pr-ana"),
                        "the picture must follow the reason, not lead it")

    def test_the_english_page_leaks_no_chinese(self):
        html = pages.principles_page(self._groups("en"), "en")
        self.assertEqual(sorted(set(re.findall(r"[一-鿿]", html))), [],
                         "the English principles page printed Chinese text")

    def test_a_reason_pointer_outside_the_book_is_a_build_failure(self):
        glosses = {"ag": {"term": {"zh": "异步生成器", "en": "async generator"},
                          "why": {"zh": "一趟要交很多次", "en": "many results"},
                          "why_evidence": ["nowhere/missing.md:1",
                                           "en/nowhere/missing.md:1"]}}
        with self.assertRaises(BuildError):
            self.build._principle_groups(glosses, list(self.units.values()),
                                         "zh")


class Shell(unittest.TestCase):
    def test_page_shell_is_js_free_and_offline(self):
        html = page("zh", "御舆", CSS, "lang-zh", "<p>x</p>", "<nav></nav>", "")
        self.assertIn('<html lang="zh-CN">', html)
        self.assertIn("<style>", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("http-equiv", html)

    def test_no_external_asset_is_referenced_from_the_stylesheet(self):
        self.assertNotIn("@import", CSS)
        for url in re.findall(r"url\(([^)]*)\)", CSS):
            self.assertNotIn("http", url, f"remote asset in CSS: {url}")


if __name__ == "__main__":
    unittest.main()
