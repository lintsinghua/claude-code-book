# Repository entry points for the offline book editions.
# The book Markdown is the source of truth; everything here only derives.
#
#   PYTHON     python launcher (make PYTHON=python3 on Linux CI)
#   BOOK_LANG  zh | en | both  -- deliberately NOT named LANG, which every
#              shell already exports as the locale (C.UTF-8, zh_CN.UTF-8, ...)

PYTHON     ?= python
BOOK_LANG  ?= both
BUILD      := yuyu-book/build.py
DIST       := yuyu-book/dist

.PHONY: help book book-pdf check index clean

help:
	@echo "make book       both HTML editions (BOOK_LANG=zh|en|both, into $(DIST)/)"
	@echo "make book-pdf   both HTML editions + A4 PDF post-pass"
	@echo "make check      build.py --check + both unittest suites + scripts/check_book.py + npm run check:diagrams"
	@echo "make index      rebuild subject-index.json from appendix D"
	@echo "make clean      remove $(DIST)/"
	@echo "variables in use: PYTHON=$(PYTHON) BOOK_LANG=$(BOOK_LANG)"

book:
	$(PYTHON) $(BUILD) --lang $(BOOK_LANG)

book-pdf:
	$(PYTHON) $(BUILD) --lang $(BOOK_LANG) --pdf

check:
	$(PYTHON) $(BUILD) --check
	$(PYTHON) -m unittest discover -s tests
	$(PYTHON) -m unittest discover -s yuyu-book/tests
	$(PYTHON) scripts/check_book.py
	npm run check:diagrams

# --regen-index rebuilds subject-index.json and then continues into a full
# assembly; build.py has no index-only invocation.
index:
	$(PYTHON) $(BUILD) --regen-index --lang $(BOOK_LANG)

clean:
	rm -rf $(DIST)
