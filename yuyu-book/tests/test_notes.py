"""The keeper layer (按语层): one line of marginalia per unit.

An old postman sits at the foot of every chapter, above its wheel ruts, and
looks back over the leg just travelled. Commentary is not a claim about the
manuscript, so its gate is lighter than the why layer's — but it is not
nothing: a note must contain a registered term form that really stands in
that unit's own text (术语锁), stay one sentence, exist in both languages,
and never mix Han characters into the English edition.

Synthetic rules first; the shipped notes.json is asserted against the real
book in ShippedNotes.
"""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yuyu_book import art, pages, plain  # noqa: E402
from yuyu_book.core import (BOOK_DIR, REPO_ROOT, BuildError, load_json,  # noqa
                            read_text, unit_stream)  # noqa: E402

GLOSSARY = {
    "main-loop": {
        "term": {"zh": "主循环", "en": "Main Loop"},
        "forms": {"zh": ["主循环", "Main Loop"],
                  "en": ["Main Loop", "main loop"]},
        "plain": {"zh": "一遍一遍转的那个圈", "en": "the circle that turns"},
        "priority": "core",
    },
    "faraway": {
        "term": {"zh": "远方概念", "en": "Faraway Concept"},
        "forms": {"zh": ["远方概念"], "en": ["faraway concept"]},
        "plain": {"zh": "别处的东西", "en": "a thing from elsewhere"},
        "priority": "extra",
    },
}
UNIT_TEXTS = {
    "ch02": {"zh": "主循环每转一圈，就少一段路。",
             "en": "Every turn of the main loop is a mile less."},
}


def note(zh="主循环走一圈，路就短一天。",
         en="Every turn of the main loop is a day less of road."):
    return {"ch02": {"zh": zh, "en": en}}


class NoteRules(unittest.TestCase):
    def test_a_note_holding_a_term_of_its_unit_passes(self):
        plain.validate_notes(note(), GLOSSARY, UNIT_TEXTS)

    def test_a_note_without_any_registered_form_fails(self):
        with self.assertRaisesRegex(BuildError, "术语锁"):
            plain.validate_notes(note(zh="天色不早了，该收车了。"),
                                 GLOSSARY, UNIT_TEXTS)

    def test_a_form_that_is_not_in_this_units_text_fails(self):
        """The lock is per unit: a form registered somewhere in the book but
        absent from this chapter's own text does not unlock its note."""
        with self.assertRaisesRegex(BuildError, "术语锁"):
            plain.validate_notes(note(zh="远方概念在这里并不出现。"),
                                 GLOSSARY, UNIT_TEXTS)

    def test_the_english_note_is_locked_by_the_english_forms(self):
        with self.assertRaisesRegex(BuildError, "术语锁"):
            plain.validate_notes(note(en="天色不早，收车。没有英文词形。"),
                                 GLOSSARY, UNIT_TEXTS)

    def test_a_too_long_note_fails(self):
        long = "主循环" + "绕" * plain.NOTE_LIMITS["zh"]
        with self.assertRaisesRegex(BuildError, "上限"):
            plain.validate_notes(note(zh=long), GLOSSARY, UNIT_TEXTS)

    def test_an_english_note_may_not_carry_han(self):
        with self.assertRaisesRegex(BuildError, "汉字"):
            plain.validate_notes(note(en="the main loop 绕了一圈"),
                                 GLOSSARY, UNIT_TEXTS)

    def test_every_unit_needs_its_note_and_no_unit_invents_one(self):
        with self.assertRaisesRegex(BuildError, "ch03"):
            plain.validate_notes(note(), GLOSSARY,
                                 {**UNIT_TEXTS, "ch03": {"zh": "", "en": ""}})
        with self.assertRaisesRegex(BuildError, "ch02"):
            plain.validate_notes({}, GLOSSARY, UNIT_TEXTS)

    def test_an_empty_language_fails(self):
        bad = {"ch02": {"zh": "主循环。", "en": "  "}}
        with self.assertRaisesRegex(BuildError, "en"):
            plain.validate_notes(bad, GLOSSARY, UNIT_TEXTS)


class NotesPage(unittest.TestCase):
    def test_the_page_prints_each_note_once_with_a_way_back(self):
        units = [SimpleNamespace(id="ch02", anchor="ch02", display="第 2 章")]
        html = pages.notes_page(note(), units, "zh")
        self.assertIn('id="keeper-notes"', html)
        self.assertIn("主循环走一圈，路就短一天。", html)
        self.assertIn('href="#ch02"', html)
        self.assertEqual(html.count('<li class="kn-row"'), 1)

    def test_the_head_is_the_gutter_label_not_the_whole_title(self):
        units = [SimpleNamespace(id="ch02", anchor="ch02", eyebrow="第 2 章",
                                 display="第 2 章　对话循环 — Agent 的心跳")]
        html = pages.notes_page(note(), units, "zh")
        self.assertIn(">第 2 章</a>", html)
        self.assertIn('title="第 2 章　对话循环 — Agent 的心跳"', html)


@unittest.skipUnless((art.ART_DIR / "keeper.svg").exists(),
                     "no keeper drawing yet")
class KeeperDrawing(unittest.TestCase):
    def test_the_keeper_passes_the_loader_and_reaches_the_page(self):
        block = art.keeper()
        self.assertTrue(block.startswith('<span class="kp-art"'))
        self.assertIn("<svg", block)

    def test_the_keeper_is_small_enough_to_inline_twenty_times(self):
        size = len((art.ART_DIR / "keeper.svg").read_text(
            encoding="utf-8").encode("utf-8"))
        # inlined once per unit: twice the emblem budget would grow the file
        # by ~120 KB a book does not owe a mascot
        self.assertLessEqual(size, 3000, f"keeper.svg is {size} bytes")


class ShippedNotes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.glosses = load_json(BOOK_DIR / "glosses.json")
        cls.manifest = load_json(BOOK_DIR / "manifest.json")
        cls.notes = plain.load_notes()
        cls.units = [SimpleNamespace(id=u["id"], path=u["zh"], en=u["en"])
                     for u, _k, _p in unit_stream(cls.manifest)]
        cls.unit_texts = {
            u.id: {"zh": read_text(REPO_ROOT / u.path),
                   "en": read_text(REPO_ROOT / u.en)}
            for u in cls.units}

    def test_the_shipped_notes_pass_their_own_gate(self):
        self.assertTrue(self.notes, "notes.json must ship before its gate runs")
        plain.validate_notes(self.notes, self.glosses, self.unit_texts)

    def test_the_notes_page_lists_the_units_in_reading_order(self):
        units = [SimpleNamespace(id=u.id, anchor=u.id, display=u.id)
                 for u in self.units]
        html = pages.notes_page(self.notes, units, "zh")
        self.assertEqual(html.count('<li class="kn-row"'), len(self.units))


if __name__ == "__main__":
    unittest.main()
