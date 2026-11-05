"""Licence / provenance gates over the shipped sources.json.

The book links sources instead of republishing them, so the registry is a
legal surface: every entry must be pinned, dated and licence-labelled, and
nothing that ships inside the book may rest on a copyleft-for-shipping
family (GPL/AGPL/LGPL). Length ceilings below are measured against the real
file (snapshot max 144 chars, scope max 143, license max 57) so a pasted body
paragraph cannot hide in a metadata field.
"""
import re
import sys
import unittest
from pathlib import Path

if not __package__:  # direct run: see tests/__init__.py for the real bootstrap
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yuyu_book.core import (BOOK_DIR, MIRRORED_FIELDS, SOURCE_REQUIRED,
                            SOURCE_ID_RE, expected_ids, load_json)
from yuyu_book.pages import KIND_GROUP

KINDS = {"github", "docs", "blog", "spec", "npm", "community"}
# measured ceilings: snapshot 144, scope 143, license 57 -> one paragraph is
# always hundreds of chars, so these also encode "metadata, not prose". The
# English mirrors say the same thing in Latin script, which costs about 2.5x
# the characters (scope 381, snapshot 276, license 124 measured), so they get
# their own wider ceiling — still a fraction of a pasted paragraph.
SNAPSHOT_MAX = 180
SCOPE_MAX = 180
LICENSE_MAX = 80
SNAPSHOT_MAX_LATIN = 300
SCOPE_MAX_LATIN = 400
LICENSE_MAX_LATIN = 140
TITLE_MAX_LATIN = 100
COPYLEFT_FOR_SHIPPING = re.compile(r"\b(?:AGPL|LGPL|GPL|GNU General Public)\b", re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HAN = re.compile(r"[一-鿿]")


def sources():
    return load_json(BOOK_DIR / "sources.json")


def manifest():
    return load_json(BOOK_DIR / "manifest.json")


class SourceEntryShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = sources()
        cls.manifest = manifest()

    def test_registry_is_not_empty_and_ids_are_slugs(self):
        self.assertGreaterEqual(len(self.sources), 30)
        for sid in self.sources:
            self.assertRegex(sid, SOURCE_ID_RE)
            # source-<sid> is used as an HTML id by the registry page
            self.assertNotIn(" ", sid)

    def test_every_entry_carries_every_required_field_non_empty(self):
        for sid, src in self.sources.items():
            for field in SOURCE_REQUIRED:
                self.assertIn(field, src, f"{sid} lacks {field}")
                self.assertTrue(str(src[field]).strip(), f"{sid}.{field} is empty")

    def test_kind_is_from_the_closed_set(self):
        self.assertEqual({s["kind"] for s in self.sources.values()}, KINDS)

    def test_every_url_is_https_and_absolute(self):
        for sid, src in self.sources.items():
            self.assertTrue(src["url"].startswith("https://"), sid)
            self.assertNotIn(" ", src["url"])
            self.assertRegex(src["url"], r"^https://[^./]+(\.[^./]+)+")

    def test_accessed_is_an_iso_date_not_after_the_book_date(self):
        for sid, src in self.sources.items():
            self.assertRegex(src["accessed"], DATE_RE, sid)
            self.assertLessEqual(src["accessed"], self.manifest["date"], sid)

    def test_snapshot_and_scope_are_metadata_not_paragraphs(self):
        ceilings = {"snapshot": (SNAPSHOT_MAX, SNAPSHOT_MAX_LATIN),
                    "scope": (SCOPE_MAX, SCOPE_MAX_LATIN),
                    "license": (LICENSE_MAX, LICENSE_MAX_LATIN)}
        for sid, src in self.sources.items():
            for field, (cjk_cap, latin_cap) in ceilings.items():
                for key in (field, f"{field}_en"):
                    if key not in src:
                        continue
                    text = str(src[key])
                    self.assertNotIn("\n", text, f"{sid}.{key} spans lines")
                    cap = latin_cap if key.endswith("_en") else cjk_cap
                    self.assertLessEqual(len(text), cap, f"{sid}.{key}")

    def test_snapshot_starts_with_the_access_date(self):
        for sid, src in self.sources.items():
            self.assertTrue(src["snapshot"].startswith(src["accessed"]), sid)
            self.assertTrue(src["snapshot_en"].startswith(src["accessed"]), sid)

    def test_title_and_authority_are_single_line(self):
        for sid, src in self.sources.items():
            for field in ("title", "authority"):
                self.assertNotIn("\n", src[field], sid)
                self.assertLessEqual(len(src[field]), 80, f"{sid}.{field}")
                mirror = src.get(f"{field}_en")
                if mirror:
                    self.assertNotIn("\n", mirror, sid)
                    self.assertLessEqual(len(mirror), TITLE_MAX_LATIN,
                                         f"{sid}.{field}_en")

    def test_every_annotation_we_wrote_has_an_english_mirror(self):
        """Snapshot, licence and scope are the book's own words about a source,
        so the English edition can print them without falling back to Chinese —
        including the two forum threads, whose Chinese title an English reader
        cannot otherwise read at all."""
        for sid, src in self.sources.items():
            for field in MIRRORED_FIELDS:
                base = str(src.get(field, ""))
                if not HAN.search(base):
                    continue
                mirror = str(src.get(f"{field}_en", ""))
                self.assertTrue(mirror.strip(), f"{sid} needs {field}_en")
                self.assertFalse(HAN.search(mirror), f"{sid}.{field}_en is "
                               "still Chinese")


class PinnedProvenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = sources()

    def github(self):
        return [(k, v) for k, v in self.sources.items() if v["kind"] == "github"]

    def test_github_entries_pin_a_tag_or_a_full_commit(self):
        self.assertTrue(self.github())
        for sid, src in self.github():
            pinned = src.get("pinned") or {}
            self.assertTrue(pinned.get("tag") or pinned.get("commit"), sid)
            if pinned.get("commit"):
                self.assertRegex(pinned["commit"], r"^[0-9a-f]{7,40}$", sid)

    def test_shipped_github_commits_are_full_shas(self):
        for sid, src in self.github():
            commit = (src.get("pinned") or {}).get("commit")
            if commit:
                self.assertEqual(len(commit), 40, f"{sid}: abbreviated sha is ambiguous")

    def test_npm_entries_pin_a_version(self):
        npm = [(k, v) for k, v in self.sources.items() if v["kind"] == "npm"]
        self.assertTrue(npm)
        for sid, src in npm:
            self.assertTrue((src.get("pinned") or {}).get("version"), sid)

    def test_community_entries_are_dated_and_marked_non_normative(self):
        community = [(k, v) for k, v in self.sources.items()
                     if v["kind"] == "community"]
        self.assertTrue(community)
        for sid, src in community:
            self.assertIs(src.get("normative"), False, sid)
            self.assertRegex(src["accessed"], DATE_RE, sid)

    def test_only_community_entries_may_be_non_normative(self):
        for sid, src in self.sources.items():
            if src["kind"] != "community":
                self.assertNotIsInstance(src.get("normative"), bool, sid)


class LicenceGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = sources()

    def test_no_entry_claims_a_copyleft_for_shipping_licence(self):
        for sid, src in self.sources.items():
            for field in ("license", "snapshot", "scope"):
                for key in (field, f"{field}_en"):
                    if key not in src:
                        continue
                    hit = COPYLEFT_FOR_SHIPPING.search(str(src[key]))
                    self.assertIsNone(hit, f"{sid}.{key}: "
                                  f"{hit.group(0) if hit else ''}")

    def test_book_license_is_the_declared_cc_nc_family(self):
        name = manifest()["license"]["name"]
        self.assertIn("CC BY-NC", name)
        self.assertFalse(COPYLEFT_FOR_SHIPPING.search(name), name)

    def test_every_entry_declares_how_it_may_be_used(self):
        # "不转载"/"linked, never republished" is the whole point of the registry
        for sid, src in self.sources.items():
            for key in ("license", "license_en"):
                text = str(src[key])
                self.assertTrue(any(word in text for word in
                                    ("转载", "引用", "SPDX", "license",
                                     "linked", "cited", "republished")),
                                f"{sid}.{key}: licence note says nothing about use")


class RegistryIsRenderable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = sources()
        cls.manifest = manifest()

    def test_every_kind_has_a_group_heading_in_both_languages(self):
        for sid, src in self.sources.items():
            for lang in ("zh", "en"):
                self.assertIn(src["kind"], KIND_GROUP[lang], sid)

    def test_every_source_is_cited_by_at_least_one_compass(self):
        cited = {sid for guide in self.manifest["guides"].values()
                 for sid in guide.get("sources", [])}
        self.assertEqual(set(self.sources) - cited, set(),
                         "uncited source shipped in the registry")

    def test_no_compass_cites_a_source_outside_the_book_order(self):
        ids = set(expected_ids(self.manifest))
        self.assertEqual(set(self.manifest["guides"]) - ids, set())


if __name__ == "__main__":
    unittest.main()
