"""Contract suite for the whole-book builder (`yuyu-book/`).

Single path bootstrap for the whole suite: discovery is started with the repo
root as ``-t``, which puts the repo root on sys.path but not ``yuyu-book/``
itself, so add it here exactly like build.py does for the CLI. Every module
can then ``import yuyu_book.*``; the two-line guard at the top of each module
only repeats this when a file is run directly.

Run from the repo root:

    python -m unittest discover -s yuyu-book/tests -t . -v

Scope: pure Python contracts over the shipped config and the markdown source.
No network, no browser, no PDF — render_all, pdf.build_pdf, cover_art.build
and build_edition are never called.
"""
import sys
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parents[1]
if str(BOOK_DIR) not in sys.path:
    sys.path.insert(0, str(BOOK_DIR))
