"""The shipped config must describe the book that is actually on disk.

Everything structural (book order, anchors, compass text, source anchors) is
derived from manifest.json; this module locks the manifest to the repository:
paths exist, nothing on disk is unregistered, ids stay in part order, and
validate_configs accepts the real files (and rejects the classic mistakes).
"""
import copy
import re
import sys
import unittest
from pathlib import Path

if not __package__:  # direct run: see tests/__init__.py for the real bootstrap
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yuyu_book.core import (GUIDE_FIELDS, REPO_ROOT, BuildError, expected_ids,
                            load_configs, load_unit, unit_stream,
                            validate_configs)

ZH_DIR_RX = re.compile(r"^(第[一二三四五六七八九十]+部分-.+|附录)$")
EN_DIR_RX = re.compile(r"^(Part-\d-.+|Appendices)$")


def disk_markdown(lang: str) -> set[str]:
    """Every book markdown file on disk for one language.

    The builder has no discovery of its own (the manifest is the registry), so
    this walks the part/appendix directories — plus the foreword — and returns
    repo-relative posix paths. A new part directory is picked up here, which is
    exactly how an unregistered chapter would slip into the book.
    """
    if lang == "zh":
        dirs = [p for p in REPO_ROOT.iterdir()
                if p.is_dir() and ZH_DIR_RX.match(p.name)]
        roots = [(p, p) for p in dirs]
        foreword = [p for p in REPO_ROOT.glob("00-*.md")]
    else:
        en = REPO_ROOT / "en"
        dirs = [p for p in en.iterdir() if p.is_dir() and EN_DIR_RX.match(p.name)]
        roots = [(en, p) for p in dirs]
        foreword = list(en.glob("00-*.md"))
    found = {p.relative_to(REPO_ROOT).as_posix() for _r, d in roots
             for p in d.glob("*.md")}
    found |= {p.relative_to(REPO_ROOT).as_posix() for p in foreword}
    return found


class ShippedConfigIsSelfConsistent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # load_configs() runs validate_configs() and raises on any drift, so
        # reaching the tests at all is the "real files are accepted" proof.
        cls.manifest, cls.sources = load_configs()

    def test_validate_configs_accepts_the_shipped_files(self):
        validate_configs(self.manifest, self.sources)
        self.assertEqual(self.manifest["front"]["id"], "front")
        self.assertGreaterEqual(len(self.sources), 30)

    def test_every_manifest_path_exists_on_disk_in_both_languages(self):
        for unit_def, _kind, _part in unit_stream(self.manifest):
            for lang in ("zh", "en"):
                rel = unit_def[lang]
                path = REPO_ROOT / rel
                self.assertTrue(path.is_file(), f"{unit_def['id']}.{lang}: {rel}")
                self.assertTrue(path.read_text(encoding="utf-8").lstrip(),
                                f"{unit_def['id']}.{lang}: empty file {rel}")

    def test_no_markdown_on_disk_is_unregistered(self):
        registered = {u[lang] for lang in ("zh", "en")
                      for u, _k, _p in unit_stream(self.manifest)}
        for lang in ("zh", "en"):
            on_disk = disk_markdown(lang)
            self.assertTrue(on_disk, f"no {lang} book markdown found")
            self.assertEqual(sorted(on_disk), sorted(registered & on_disk),
                             f"unregistered {lang} markdown")

    def test_expected_ids_follow_part_order(self):
        m = self.manifest
        manual = ([m["front"]["id"]]
                  + [u["id"] for p in m["parts"] for u in p["units"]]
                  + [a["id"] for a in m["appendices"]])
        self.assertEqual(expected_ids(m), manual)

    def test_book_order_is_foreword_then_15_chapters_then_four_appendices(self):
        ids = expected_ids(self.manifest)
        self.assertEqual(len(ids), 20)
        self.assertEqual(ids[0], "front")
        self.assertEqual(ids[1:16], [f"ch{n:02d}" for n in range(1, 16)])
        self.assertEqual(ids[16:], ["apxa", "apxb", "apxc", "apxd"])

    def test_unit_stream_matches_expected_ids_and_kinds(self):
        stream = [(u["id"], k) for u, k, _p in unit_stream(self.manifest)]
        self.assertEqual([i for i, _k in stream], expected_ids(self.manifest))
        kinds = {i: k for i, k in stream}
        self.assertEqual(kinds["front"], "front")
        self.assertEqual(kinds["ch07"], "chapter")
        self.assertEqual(kinds["apxd"], "appendix")

    def test_parts_cover_every_chapter_and_no_appendix(self):
        apx = {a["id"] for a in self.manifest["appendices"]}
        for part in self.manifest["parts"]:
            self.assertTrue(part["units"])
            for unit_def in part["units"]:
                self.assertNotIn(unit_def["id"], apx)
                self.assertRegex(unit_def["id"], r"^ch\d{2}$")

    def test_every_unit_has_a_non_empty_compass_in_both_languages(self):
        guides = self.manifest["guides"]
        self.assertEqual(sorted(guides), sorted(expected_ids(self.manifest)))
        for uid in expected_ids(self.manifest):
            for field in GUIDE_FIELDS:
                entry = guides[uid].get(field)
                self.assertIsInstance(entry, dict, f"{uid}.{field}")
                for lang in ("zh", "en"):
                    self.assertTrue((entry.get(lang) or "").strip(),
                                    f"{uid}.{field}.{lang} is empty")

    def test_compass_fields_are_single_sentences_not_paragraphs(self):
        # the compass card is a fixed-width sidebar; the real data tops out at
        # 163 chars (apxb.deliverable), so 200 is headroom without prose
        for uid, guide in self.manifest["guides"].items():
            for field in GUIDE_FIELDS:
                for lang in ("zh", "en"):
                    text = guide[field][lang]
                    self.assertNotIn("\n", text, f"{uid}.{field}.{lang}")
                    self.assertLessEqual(len(text), 200, f"{uid}.{field}.{lang}")

    def test_every_guide_source_id_resolves_in_sources_json(self):
        for uid, guide in self.manifest["guides"].items():
            self.assertTrue(guide.get("sources"), f"{uid} has no source anchors")
            for sid in guide["sources"]:
                self.assertIn(sid, self.sources, f"{uid} -> unknown source {sid}")

    def test_part_titles_mottos_and_goals_exist_in_both_languages(self):
        for part in self.manifest["parts"]:
            for field in ("no", "title", "motto", "goal"):
                for lang in ("zh", "en"):
                    self.assertTrue((part[field][lang] or "").strip(),
                                    f"{part['id']}.{field}.{lang} is empty")

    def test_top_level_book_metadata_is_present(self):
        for key in ("title", "subtitle", "epigraph"):
            for lang in ("zh", "en"):
                self.assertTrue(self.manifest[key][lang].strip(), key)
        self.assertTrue(self.manifest["license"]["url"].startswith("https://"))
        self.assertRegex(self.manifest["version"], r"^\d+\.\d+\.\d+$")
        self.assertRegex(self.manifest["date"], r"^\d{4}-\d{2}-\d{2}$")


class DerivedUnitLabels(unittest.TestCase):
    """The ids/labels the TOC, PDF bookmarks and folios are built from."""

    @classmethod
    def setUpClass(cls):
        cls.manifest, _ = load_configs()
        cls.by_id = {u["id"]: u for u, _k, _p in unit_stream(cls.manifest)}

    def unit(self, uid, lang):
        kind = ("front" if uid == "front"
                else "appendix" if uid.startswith("apx") else "chapter")
        return load_unit(self.by_id[uid], kind, lang, REPO_ROOT)

    def test_zh_display_uses_the_ideographic_space(self):
        u = self.unit("ch02", "zh")
        self.assertEqual(u.no, "第 2 章")
        self.assertEqual(u.display, f"第 2 章　{u.title}")
        self.assertEqual(u.eyebrow, "第 2 章")

    def test_en_display_uses_a_colon(self):
        u = self.unit("ch02", "en")
        self.assertEqual(u.no, "Chapter 2")
        self.assertEqual(u.display, f"Chapter 2: {u.title}")

    def test_no_plain_is_a_two_digit_gutter_label(self):
        self.assertEqual(self.unit("ch01", "zh").no_plain, "01")
        self.assertEqual(self.unit("ch15", "zh").no_plain, "15")
        self.assertEqual(self.unit("ch09", "en").no_plain, "09")

    def test_no_plain_for_appendices_is_the_letter(self):
        self.assertEqual(self.unit("apxa", "zh").no_plain, "A")
        self.assertEqual(self.unit("apxd", "en").no_plain, "D")

    def test_foreword_has_no_number_and_a_localised_eyebrow(self):
        zh = self.unit("front", "zh")
        en = self.unit("front", "en")
        self.assertEqual(zh.no, "")
        self.assertEqual(zh.display, zh.title)
        self.assertEqual(zh.eyebrow, "前言")
        self.assertEqual(en.eyebrow, "Foreword")

    def test_anchor_is_the_unit_id_for_every_unit(self):
        for uid in ("front", "ch07", "apxc"):
            for lang in ("zh", "en"):
                self.assertEqual(self.unit(uid, lang).anchor, uid)

    def test_unit_id_is_unique_across_the_book(self):
        ids = expected_ids(self.manifest)
        self.assertEqual(len(ids), len(set(ids)))


class ConfigValidationRejects(unittest.TestCase):
    """Negative cases over an in-memory copy of the real config."""

    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.sources = load_configs()

    def check(self, manifest, sources=None, message=""):
        with self.assertRaises(BuildError) as ctx:
            validate_configs(manifest, sources or self.sources)
        self.assertIn(message, str(ctx.exception))

    def test_missing_guide_for_a_unit(self):
        m = copy.deepcopy(self.manifest)
        del m["guides"]["ch07"]
        self.check(m, message="guides missing for: ch07")

    def test_guide_for_a_unit_that_does_not_exist(self):
        m = copy.deepcopy(self.manifest)
        m["guides"]["ch99"] = copy.deepcopy(m["guides"]["ch07"])
        self.check(m, message="guides for unknown units: ch99")

    def test_guide_pointing_at_an_unknown_source_id(self):
        m = copy.deepcopy(self.manifest)
        m["guides"]["ch07"]["sources"] = ["does-not-exist"]
        self.check(m, message="unknown source id 'does-not-exist'")

    def test_unit_file_missing_from_disk(self):
        m = copy.deepcopy(self.manifest)
        m["parts"][1]["units"][2]["en"] = "en/Part-2-Core-Systems/99-Ghost.md"
        self.check(m, message="unit ch07: missing en file")

    def test_empty_compass_field_in_one_language(self):
        m = copy.deepcopy(self.manifest)
        m["guides"]["ch07"]["deliverable"]["en"] = "   "
        self.check(m, message="guide ch07.deliverable.en is empty")

    def test_duplicate_unit_ids(self):
        m = copy.deepcopy(self.manifest)
        m["parts"][0]["units"].append(copy.deepcopy(m["appendices"][0]))
        self.check(m, message="duplicate unit ids")

    def test_source_missing_a_required_field(self):
        s = copy.deepcopy(self.sources)
        del s["cc-changelog"]["license"]
        self.check(self.manifest, sources=s,
                   message="source cc-changelog: field license missing/empty")

    def test_source_url_that_is_not_https(self):
        s = copy.deepcopy(self.sources)
        s["cc-changelog"]["url"] = "http://github.com/anthropics/claude-code"
        self.check(self.manifest, sources=s, message="source cc-changelog: url must be https")

    def test_github_source_without_a_pin(self):
        s = copy.deepcopy(self.sources)
        s["gh-book-repo"]["pinned"] = {}
        self.check(self.manifest, sources=s,
                   message="source gh-book-repo: github refs must pin tag or commit")

    def test_community_source_claiming_normative_status(self):
        s = copy.deepcopy(self.sources)
        s["ld-topic-1870593"]["normative"] = True
        self.check(self.manifest, sources=s,
                   message="source ld-topic-1870593: community refs need")

    def test_the_unmutated_copy_still_passes(self):
        validate_configs(copy.deepcopy(self.manifest),
                         copy.deepcopy(self.sources))


if __name__ == "__main__":
    unittest.main()
