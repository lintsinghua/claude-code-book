"""Every count the repository docs claim, recomputed from the files they describe.

These numbers move whenever the manuscript or a registry moves, and they rot
silently: one audit found the README describing a 100-entry glossary beside a
file holding 122 entries, a STRUCTURE row still saying "24 份图" after the
twenty-fifth drawing shipped, and a doc row promising that `extra` terms reach
the chapter panel when the panel has always been the marked set. Each claim is
one regex against one doc line, checked against a value computed from data, so
a reworded sentence fails as "claim missing" instead of passing vacuously.
"""
import re
import sys
import unittest
from pathlib import Path

if not __package__:  # direct run: see tests/__init__.py for the real bootstrap
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yuyu_book import plain
from yuyu_book.core import (BOOK_DIR, REPO_ROOT, extract_mermaid, load_json,
                            read_text, unit_stream)
from yuyu_book.plain import prose_lines

SEP_ROW = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+\s*:?\s*$")
ASCII = re.compile(r"[A-Za-z]")


class Data(unittest.TestCase):
    """Counts taken straight from the manuscript and the registries."""

    def setUp(self):
        self.manifest = load_json(BOOK_DIR / "manifest.json")
        self.units = [(u, k) for u, k, _p in unit_stream(self.manifest)]
        self.glosses = load_json(BOOK_DIR / "glosses.json")

    def unit_path(self, lang: str) -> list[str]:
        return [u[lang] for u, _k in self.units]

    def plates(self, lang: str) -> int:
        n = 0
        for rel in self.unit_path(lang):
            _body, blocks, _langs = extract_mermaid(read_text(REPO_ROOT / rel),
                                                    rel)
            n += len(blocks)
        return n

    def glossary_rows(self, lang: str) -> int:
        """Rows of the appendix D tables, headers excluded.

        Fence-aware: appendix D opens with a mermaid concept map whose
        `subgraph 核心架构["核心架构概念"]` lines look table-ish to a plain scan.
        """
        apxd = next(a for a in self.manifest["appendices"] if a["id"] == "apxd")
        lines = prose_lines(read_text(REPO_ROOT / apxd[lang]))
        order = sorted(lines)
        rows = 0
        for i, ln in enumerate(order):
            s = lines[ln].strip()
            if not s.startswith("|") or SEP_ROW.match(s):
                continue
            if i + 1 < len(order) and SEP_ROW.match(lines[order[i + 1]].strip()):
                continue          # this is a header row
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 5 or not ASCII.search(cells[0]):
                continue
            rows += 1
        return rows

    def drawings(self) -> int:
        return len(list((BOOK_DIR / "illustrations").glob("*.svg")))

    def index(self) -> list[dict]:
        return load_json(BOOK_DIR / "subject-index.json")

    def kinds(self) -> dict:
        out = {}
        for s in load_json(BOOK_DIR / "sources.json").values():
            out[s["kind"]] = out.get(s["kind"], 0) + 1
        return out

    def core_terms(self) -> int:
        return sum(1 for g in self.glosses.values()
                   if g.get("priority") == "core")

    def why_terms(self) -> int:
        return sum(1 for g in self.glosses.values()
                   if (g.get("why") or {}).get("zh"))

    def suite(self) -> int:
        loader = unittest.TestLoader()
        s = loader.discover(str(BOOK_DIR / "tests"))
        if loader.errors:
            raise AssertionError(f"discovery failed: {loader.errors[:2]}")
        return s.countTestCases()


class ShippedCounts(Data):
    """The docs quote these; the data is the only authority."""

    def setUp(self):
        super().setUp()
        plates_zh, plates_en = self.plates("zh"), self.plates("en")
        src = str(len(load_json(BOOK_DIR / "sources.json")))
        g = str(len(self.glosses))
        d = str(self.drawings())
        self.claims = [
            ("README.md", r"\*\*术语表\*\* — (\d+) 条中英对照术语",
             [str(self.glossary_rows("zh"))]),
            ("en/README.md", r"\*\*Glossary\*\* — (\d+) bilingual term",
             [str(self.glossary_rows("en"))]),
            ("STRUCTURE.md", r"术语白话注，当前 (\d+) 条（(\d+) 个 core",
             [g, str(self.core_terms())]),
            # the reason layer is quoted in all three docs, and its size is a
            # fact about glosses.json rather than about the core count
            ("STRUCTURE.md", r"`why` \+ `why_evidence`（原理句与它的出处，"
                             r"(\d+) 个 core 各配一对",
             [str(self.core_terms())]),
            ("README.md", r"(\d+) 个主干术语的原理", [str(self.why_terms())]),
            ("en/README.md", r"the (\d+) core terms' reasons",
             [str(self.why_terms())]),
            ("STRUCTURE.md", r"主题索引（生成物，当前 (\d+) 个词条 = "
                             r"(\d+) 条英文原名 \+ (\d+) 条中文译名）",
             [str(len(self.index())), str(len([e for e in self.index()
                                               if e["letter"] != "中"])),
              str(len([e for e in self.index() if e["letter"] == "中"]))]),
            ("README.md", r"全书另有 (\d+) 份手写线描图——扉页一幅四马古车、"
                         r"(\d+) 枚章徽配在章名右侧、(\d+) 幅题刻",
             [d, str(len(self.units)), str(len(self.manifest["parts"]))]),
            ("STRUCTURE.md", r"\| `illustrations/` \| (\d+) 份手写 SVG",
             [d]),
            ("CREDITS.md", r"扉页一幅车图（共 (\d+) 份", [d]),
            ("STRUCTURE.md", r"以来源 id 为键的 (\d+) 条登记", [src]),
            ("CREDITS.md", r"sources\.json\)（(\d+) 条）", [src]),
            # the registry is also quoted by family, in a sentence and in four
            # section headings; both drift the moment one entry is added
            ("STRUCTURE.md", r"kind 分布：`docs` (\d+)、`github` (\d+)、"
                             r"`blog` (\d+)、`spec` (\d+)、`npm` (\d+)、"
                             r"`community` (\d+)；(\d+) 条全部被",
             [str(self.kinds()["docs"]), str(self.kinds()["github"]),
              str(self.kinds()["blog"]), str(self.kinds()["spec"]),
              str(self.kinds()["npm"]), str(self.kinds()["community"]), src]),
            ("CREDITS.md", r"## 二、官方文档（(\d+) 条）",
             [str(self.kinds()["docs"])]),
            ("CREDITS.md", r"## 三、GitHub 仓库与钉版（(\d+) 条）",
             [str(self.kinds()["github"])]),
            ("CREDITS.md", r"## 四、协议规范与工程博客（(\d+) 条）",
             [str(self.kinds()["spec"] + self.kinds()["blog"])]),
            ("CREDITS.md", r"## 五、npm（(\d+) 条）",
             [str(self.kinds()["npm"])]),
            ("README.md", r"每版 (\d+) 张（中英合计 (\d+)）",
             [str(plates_zh), str(plates_zh + plates_en)]),
            ("STRUCTURE.md", r"中英文各有 (\d+) 个 Mermaid 围栏（合计 (\d+)）",
             [str(plates_zh), str(plates_zh + plates_en)]),
            ("CREDITS.md", r"全书 (\d+) 张图（中英各 (\d+)）",
             [str(plates_zh + plates_en), str(plates_en)]),
            ("en/README.md", r"All (\d+) diagrams per edition \((\d+) across "
                            r"both\)", [str(plates_en),
                                        str(plates_zh + plates_en)]),
            ("README.md", r"`yuyu-book/` 把 (\d+) 个单元装配成",
             [str(len(self.units))]),
        ]

    def test_doc_counts_match_the_data(self):
        bad = []
        for doc, rx, want in self.claims:
            m = re.compile(rx, re.M).search(read_text(REPO_ROOT / doc))
            if not m:
                bad.append(f"{doc}: nothing matches {rx!r} — the sentence was "
                           "reworded; re-pin the claim if its numbers are "
                           "still facts")
                continue
            got = list(m.groups())
            if got != want:
                bad.append(f"{doc}: claims {got}, the data says {want}")
        self.assertEqual(bad, [], "\n  " + "\n  ".join(bad))

    def test_the_revision_note_closes_with_the_suite_it_shipped(self):
        """The newest note quotes the builder's own test count; the note is
        read as the version's summary, so the figure has to be current."""
        # the ledger is newest-first: the top entry is the version shipping
        entry = load_json(BOOK_DIR / "revisions.json")["entries"][0]
        want = str(self.suite())
        for lang, rx in (("zh", r"构建器测试 (\d+) 项全绿"),
                         ("en", r"(\d+) builder tests green")):
            m = re.search(rx, entry[lang][-1])
            self.assertIsNotNone(
                m, f"revisions.{lang}: the last note no longer states the "
                   "suite size — re-pin it")
            self.assertEqual(m.group(1), want,
                             f"revisions.{lang}: the note says {m.group(1)}, "
                             f"discovery says {want}")

    def test_extra_terms_stay_off_the_prose_and_the_panel(self):
        """STRUCTURE promises `extra` reaches neither the dashes nor the chapter
        panel; the panel is built from the marks, so one flag covers both."""
        leaked = [gid for gid, g in self.glosses.items()
                  if g.get("priority") == "extra" and plain.marks(g)]
        self.assertEqual(leaked, [],
                         f"marked but registered as extra: {leaked}")
        for lang in ("zh", "en"):
            self.assertTrue(plain.Matcher(self.glosses, lang).rx,
                            f"no markable form in {lang}")


CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
          "八": 8, "九": 9, "十": 10}
EN_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
          "seven": 7, "eight": 8, "nine": 9, "ten": 10}
TOOL_ROW = re.compile(r"^\|\s*([A-Za-z][A-Za-z0-9]*Tool)\s*\|")
CAT_HEADING = re.compile(r"^## \d+\. \S")


class TextTotalsMatchTheirOwnTables(Data):
    """A stated total is a promise the table underneath has to keep.

    Three figures in this book disagreed with the rows they summarised — a
    chapter about 26 lifecycle events whose own table lists 22, a section headed
    三个维度 that then describes five, and a tool count quoted as 45+, 六十多个 and
    55 in three places. A reader who counts rows catches all of them, so this
    test counts them too: the diagram and the table are the authority, and every
    sentence quoting their total is checked against them.
    """

    def path(self, needle: str, lang: str) -> str:
        """`needle` matches the Chinese path, which names the same unit in both
        editions (附录/B… and B-Complete… are one unit)."""
        return next(u[lang] for u, _k in self.units if needle in u["zh"])

    def table_after(self, rel: str, marker: str) -> list[str]:
        """Data rows of the table introduced by `marker`, header excluded."""
        lines = prose_lines(read_text(REPO_ROOT / rel))
        rows, seen = [], False
        for ln in sorted(lines):
            s = lines[ln].strip()
            if not seen:
                seen = s.startswith(marker)
                continue
            if s.startswith("|"):
                if not SEP_ROW.match(s):
                    rows.append(s)
            elif rows:
                break
        return rows[1:]

    def tools(self, lang: str) -> list[str]:
        lines = prose_lines(read_text(REPO_ROOT / self.path("附录/B", lang)))
        out, inside = [], False
        for ln in sorted(lines):
            s = lines[ln].strip()
            if CAT_HEADING.match(s):
                inside = True
                continue
            if inside and s.startswith("## "):
                break
            if inside and (m := TOOL_ROW.match(s)):
                out.append(m.group(1))
        return out

    def dimensions(self, rel: str) -> int:
        """How many cache-key dimensions the plate actually draws."""
        _body, blocks, _langs = extract_mermaid(read_text(REPO_ROOT / rel), rel)
        plate = next(b.src for b in blocks if "CacheSafeParams" in b.src)
        return len({m.group(1) for m in re.finditer(r"\bD(\d)\s*\[", plate)})

    def test_the_hook_table_lists_what_the_chapter_claims(self):
        quotes = {
            "zh": [r"掌握 (\d+) 个生命周期事件的触发时机",
                   r"本章按功能分组介绍其中 (\d+) 个生命周期事件",
                   r"下表总结了上述 (\d+) 个事件的分类",
                   r"\*\*(\d+) 个生命周期事件\*\*"],
            "en": [r"semantics of (\d+) lifecycle events",
                   r"this chapter introduces (\d+) of its lifecycle events",
                   r"typical uses of these (\d+) events",
                   r"\*\*(\d+) lifecycle events\*\*"],
        }
        docs = ("README.md", r"(\d+) 个生命周期事件；JSON 响应协议", "zh"), \
               ("en/README.md", r"(\d+) lifecycle events; JSON", "en"), \
               ("yuyu-book/manifest.json", r'"zh": "(\d+) 个生命周期事件上', "zh"), \
               ("yuyu-book/manifest.json",
                r'"en": "Across (\d+) lifecycle events', "en")
        bad = []
        for lang in ("zh", "en"):
            rel = self.path("08-钩子", lang)
            rows = len(self.table_after(rel, "下表总结了" if lang == "zh"
                                        else "The table below summarizes"))
            self.assertGreater(rows, 0, f"{rel}: no event table found")
            text = read_text(REPO_ROOT / rel)
            for rx in quotes[lang]:
                m = re.search(rx, text)
                self.assertIsNotNone(m, f"{rel}: nothing matches {rx!r}")
                if m.group(1) != str(rows):
                    bad.append(f"{rel}: {rx!r} says {m.group(1)}, the table "
                               f"lists {rows} events")
        for doc, rx, lang in docs:
            m = re.search(rx, read_text(REPO_ROOT / doc))
            self.assertIsNotNone(m, f"{doc}: nothing matches {rx!r}")
            rows = len(self.table_after(self.path("08-钩子", lang),
                                        "下表总结了" if lang == "zh"
                                        else "The table below summarizes"))
            if m.group(1) != str(rows):
                bad.append(f"{doc}: {rx!r} says {m.group(1)}, the table lists "
                           f"{rows} events")
        self.assertEqual(bad, [], "\n  " + "\n  ".join(bad))

    def test_the_tool_inventory_is_the_number_the_book_quotes(self):
        intro = {"zh": r"按 (\d+) 个功能类别列出 Claude Code 架构中注册的全部"
                       r" (\d+) 个工具",
                 "en": r"lists all (\d+) tools registered in the Claude Code "
                       r"architecture, indexed across (\d+) functional"}
        for lang in ("zh", "en"):
            apxb = self.path("附录/B", lang)
            rows = self.tools(lang)
            self.assertEqual(len(rows), len(set(rows)),
                             f"{lang}: a tool is listed twice in appendix B")
            text = read_text(REPO_ROOT / apxb)
            m = re.search(intro[lang], text)
            self.assertIsNotNone(m, f"{apxb}: its own intro states no total")
            want = ["12", str(len(rows))] if lang == "zh" \
                else [str(len(rows)), "12"]
            self.assertEqual(want, list(m.groups()),
                             f"{apxb}: rows and categories vs its own intro")
            bad = []
            for rel, rxs in self._tool_quotes(lang):
                body = read_text(REPO_ROOT / rel)
                for rx in rxs:
                    got = re.search(rx, body)
                    if not got:
                        bad.append(f"{rel}: nothing matches {rx!r}")
                    elif got.groups() and got.group(1) != str(len(rows)):
                        bad.append(f"{rel}: {rx!r} says {got.group(1)}, the "
                                   f"inventory lists {len(rows)}")
            self.assertEqual(bad, [], f"[{lang}] " + "\n  " + "\n  ".join(bad))

    def _tool_quotes(self, lang):
        """Every sentence outside the appendix that quotes the tool total."""
        if lang == "zh":
            return [
                (self.path("01-智能体编程", lang), [r"(\d+) 个工具 · 编排引擎"]),
                (self.path("03-工具系统", lang),
                 [r"掌握 Claude Code (\d+) 个已注册工具",
                  r"注册了 (\d+) 个专门化工具"]),
                (self.path("13-流式架构", lang),
                 [r"如果 Claude Code 的 (\d+) 个工具都在启动时构建 schema"]),
                (self.path("15-构建你自己的", lang),
                 [r"在拥有 (\d+) 个工具和数百个模块"]),
                ("README.md", [r"(\d+) 工具 × 12 类"]),
                ("yuyu-book/manifest.json",
                 [r'"zh": "(\d+) 个工具如何靠同一份类型契约']),
            ]
        return [
            (self.path("01-智能体编程", lang), [r"(\d+) Tools · Orchestration"]),
            (self.path("03-工具系统", lang),
             [r"Claude Code's (\d+) registered tools",
              r"registers (\d+) specialized tools"]),
            (self.path("13-流式架构", lang),
             [r"Claude Code's (\d+) tools all build schemas at startup"]),
            (self.path("15-构建你自己的", lang),
             [r"In a codebase with (\d+) tools and hundreds of modules"]),
            ("en/README.md", [r"(\d+) tools × 12 categories"]),
            ("yuyu-book/manifest.json",
             [r'"en": "How do (\d+) tools share one type contract']),
        ]

    def test_the_schema_arithmetic_follows_the_tool_count(self):
        """The startup-cost sentence is 0.1-0.3ms per tool; it moves with the
        inventory or it stops being arithmetic the reader can check."""
        for rel, rx in (
            (self.path("13-流式架构", "zh"),
             r"(\d+) 个工具都在启动时构建 schema，总开销为 ([\d.]+)-([\d.]+)ms"),
            (self.path("13-流式架构", "en"),
             r"(\d+) tools all build schemas at startup, total overhead is "
             r"([\d.]+)-([\d.]+)ms"),
        ):
            m = re.search(rx, read_text(REPO_ROOT / rel))
            self.assertIsNotNone(m, f"{rel}: the schema-cost sentence moved")
            n, low, high = int(m.group(1)), float(m.group(2)), float(m.group(3))
            self.assertAlmostEqual(n * 0.1, low, places=4, msg=rel)
            self.assertAlmostEqual(n * 0.3, high, places=4, msg=rel)

    def test_the_cache_dimensions_are_one_number_across_the_section(self):
        for label, rel, head, body, four, table in (
            ("zh", self.path("13-流式架构", "zh"),
             r"### 13\.5\.1 提示缓存共享的([一二三四五六七八九十])个维度",
             r"缓存键由([一二三四五六七八九十])个维度构成",
             r"`CacheSafeParams` 精确地封装了前([一二三四五六七八九十])个维度",
             CN_NUM),
            ("en", self.path("13-流式架构", "en"),
             r"### 13\.5\.1 ([A-Za-z]+) Dimensions of Prompt Cache",
             r"cache key consists of ([a-z]+) dimensions",
             r"encapsulates the first ([a-z]+) dimensions",
             EN_NUM),
        ):
            plate = self.dimensions(rel)
            text = read_text(REPO_ROOT / rel)
            nums = []
            for rx in (head, body, four):
                m = re.search(rx, text)
                self.assertIsNotNone(m, f"{label}: nothing matches {rx!r}")
                nums.append(m.group(1))
            # lower() is a no-op on the Chinese numerals and undoes the
            # title-case the English headings are written in
            self.assertEqual(table[nums[0].lower()], plate,
                             f"{label}: the heading counts {nums[0]}, the plate "
                             f"draws {plate} dimensions")
            self.assertEqual(nums[0].lower(), nums[1].lower(),
                             f"{label}: heading says {nums[0]}, the text says "
                             f"{nums[1]}")
            self.assertEqual(table[nums[2].lower()], plate - 1,
                             f"{label}: {nums[2]} dimensions wrapped, but the "
                             f"plate has {plate} and one is described apart")
            wrapped = text.split(re.search(four, text).group(0), 1)[1][:260]
            self.assertIn("model", wrapped,
                          f"{label}: the wrapped dimensions never name model — "
                          f"that is how the list lost a dimension once")

    KEEPER_TOTALS = {("apxb", "zh"): r"(\d+) 枚腰牌",
                     ("apxb", "en"): r"(\d+) tallies"}

    def test_the_postman_only_states_numbers_the_book_can_recount(self):
        """A keeper note is prose, but the numbers in it are the repository's.

        Spelled out, 五十五 is invisible to every gate in this file — that is
        precisely how 六十多个工具 lived beside an appendix listing 55. So a note
        either carries no digits at all or carries one a test recomputes; adding
        a second entry to KEEPER_TOTALS is the way to say where a new number
        comes from.
        """
        notes = load_json(BOOK_DIR / "notes.json")
        want = {lang: str(len(self.tools(lang))) for lang in ("zh", "en")}
        bad = []
        for lang in ("zh", "en"):
            for uid, body in notes.items():
                rx = self.KEEPER_TOTALS.get((uid, lang))
                if rx is None:
                    bad += [f"{uid}/{lang}: {d.group()!r} is a number no test "
                            f"can recount"
                            for d in re.finditer(r"\d+", body[lang])]
                    continue
                m = re.search(rx, body[lang])
                if m is None:
                    bad.append(f"{uid}/{lang}: its total is spelled out where no "
                               f"test can read it (looking for {rx!r})")
                    continue
                if m.group(1) != want[lang]:
                    bad.append(f"{uid}/{lang}: says {m.group(1)}, appendix B "
                               f"lists {want[lang]}")
                bad += [f"{uid}/{lang}: {d.group()!r} is a number no test can "
                        f"recount"
                        for d in re.finditer(r"\d+", body[lang])
                        if not (m.start(1) <= d.start() and d.end() <= m.end(1))]
        self.assertEqual(bad, [], "\n  " + "\n  ".join(bad))

    def test_the_superseded_figures_are_gone(self):
        """The wording these corrections replaced, nowhere in the book or its docs.

        A stale figure is worse than a rough one: 六十多个工具 next to an appendix
        listing 55 tells a reader the two were written by different hands.
        """
        stale = ("26 个生命周期事件", "26 lifecycle events", "all 26 events",
                 "45+ 工具", "45+ tools", "45-plus tools", "45 个以上工具",
                 "六十多个工具", "sixty-plus tools", "over sixty tools",
                 "提示缓存共享的三个维度", "Three Dimensions of Prompt Cache")
        docs = ("README.md", "en/README.md", "STRUCTURE.md", "CREDITS.md",
                "CONTRIBUTING.md", "yuyu-book/manifest.json")
        hits = []
        for needle in stale:
            for u, _k in self.units:
                for lang in ("zh", "en"):
                    if needle in read_text(REPO_ROOT / u[lang]):
                        hits.append(f"{u[lang]}: still says {needle!r}")
            for doc in docs:
                if needle in read_text(REPO_ROOT / doc):
                    hits.append(f"{doc}: still says {needle!r}")
        self.assertEqual(hits, [], "\n  " + "\n  ".join(hits))


if __name__ == "__main__":
    unittest.main()
