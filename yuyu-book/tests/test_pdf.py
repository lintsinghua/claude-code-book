"""The printed-sheet audit: which pages count as carrying content, and whether
an index folio measured on one print is still true on the next.

`empty_sheets()` is the gate that keeps the book from shipping a reader-facing
hole — a sheet with nothing on it but the running head and the folio. These
cases build the pages in memory; no browser, no print pass.
"""
import sys
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yuyu_book.pdf import empty_sheets, folio_drift  # noqa: E402


def _doc(*pages):
    doc = fitz.open()
    for build in pages:
        page = doc.new_page()
        build(page)
    return doc


def _furniture_only(page):
    page.insert_text((60, 30), "Chapter 9: Sub-Agents", fontsize=8)
    page.insert_text((270, 812), "215 / 488", fontsize=8)


def _with_body(page):
    page.insert_text((60, 30), "Chapter 9", fontsize=8)
    page.insert_text((270, 812), "215 / 488", fontsize=8)
    page.insert_text((60, 200), "the prose a reader came for", fontsize=10)


def _plate_only(page):
    page.insert_text((270, 812), "215 / 488", fontsize=8)
    page.draw_line((60, 300), (530, 640), width=2)


class Sheets(unittest.TestCase):
    def test_a_sheet_with_only_head_and_folio_is_a_hole(self):
        with _doc(_furniture_only) as doc:
            self.assertEqual(empty_sheets(doc), [1])

    def test_a_sheet_with_running_prose_is_not_a_hole(self):
        with _doc(_with_body) as doc:
            self.assertEqual(empty_sheets(doc), [])

    def test_a_drawing_counts_as_content_so_a_plate_is_not_a_hole(self):
        with _doc(_plate_only) as doc:
            self.assertEqual(empty_sheets(doc), [])

    def test_a_landscape_sheet_is_measured_against_its_own_height(self):
        """Fold-out plates are 842x595; a band hard-coded to portrait would
        call the bottom of every landscape sheet furniture."""
        def build(page):
            page.insert_text((60, 300), "a plate that reaches low", fontsize=10)
        with fitz.open() as doc:
            doc.new_page(width=842, height=595)
            build(doc[0])
            self.assertEqual(empty_sheets(doc), [])

    def test_only_the_holes_are_listed_and_page_numbers_are_one_based(self):
        with _doc(_with_body, _furniture_only, _plate_only,
                  _furniture_only) as doc:
            self.assertEqual(empty_sheets(doc), [2, 4])


class Folios(unittest.TestCase):
    """The index's second print: numbers measured on one sheet must still be
    right on the sheet the book was actually printed to."""

    def test_a_number_that_stands_where_it_was_measured_is_no_drift(self):
        self.assertEqual(folio_drift({"ch07": 90, "ch08": 120},
                                     {"ch07": 91, "ch08": 121}), {})

    def test_rows_sharing_a_unit_agree_by_construction(self):
        """Two headwords filed under one chapter print two folios, and both are
        that chapter's page: the map is keyed by anchor, so it cannot disagree
        with itself."""
        self.assertEqual(folio_drift({"ch07": 90}, {"ch07": 91}), {})

    def test_a_sheet_that_moved_when_the_numbers_landed_is_named(self):
        """A row whose reserved slot turned out too narrow repages the index —
        and every folio in the book was measured before that happened."""
        self.assertEqual(folio_drift({"ch07": 90, "ch08": 122},
                                     {"ch07": 91, "ch08": 121}),
                         {"ch08": (123, 121)})


if __name__ == "__main__":
    unittest.main()
