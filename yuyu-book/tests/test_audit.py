"""The build gate itself: what audit_html refuses to ship."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yuyu_book import audit  # noqa: E402
from yuyu_book.core import BuildError  # noqa: E402


def page(n_units=1, svgs=0, extra=""):
    """The smallest document that satisfies every structural contract."""
    articles = "".join(
        f'<article class="chapter" id="ch{i:02d}">'
        f'<div class="compass"><h4 class="cc-tag">问题</h4></div>'
        f'<h2 id="ch{i:02d}-s">节</h2><p>正文</p></article>'
        for i in range(1, n_units + 1))
    figures = "".join(f'<figure id="fig-{i}"><svg id="mm-{i}"></svg></figure>'
                      for i in range(svgs))
    return (f'<html><body>{articles}{figures}{extra}</body></html>')


def check(html, n_units=1, expect_svgs=None):
    audit.audit(html, n_units=n_units, expect_svgs=expect_svgs)


class Accepts(unittest.TestCase):
    def test_a_clean_document_passes(self):
        check(page(n_units=3, svgs=2))

    def test_expected_svg_count_is_honoured(self):
        check(page(n_units=1, svgs=4), expect_svgs=4)

    def test_source_mode_does_not_demand_svg(self):
        check("<html><body>" + '<article class="unit" id="front">'
              '<div class="compass"></div></article>'
              '</body></html>',
              n_units=1, expect_svgs=None)


class Rejects(unittest.TestCase):
    def assertRejects(self, html, needle, **kw):
        with self.assertRaises(BuildError) as cm:
            check(html, **kw)
        self.assertIn(needle, str(cm.exception))

    def test_duplicate_ids(self):
        self.assertRejects(page() + page(), "duplicate ids", n_units=2)

    def test_duplicate_id_inside_a_diagram_counts_too(self):
        html = page(svgs=1).replace('<svg id="mm-0">',
                                    '<svg id="mm-0"><g id="node0"></g>'
                                    '<g id="node0"></g>')
        self.assertIn('id="node0"', html)
        self.assertRejects(html, "duplicate ids")

    def test_broken_anchor(self):
        self.assertRejects(page(extra='<a href="#nope">x</a>'), "broken anchors")

    def test_javascript_is_not_shipped(self):
        self.assertRejects(page(extra='<script>alert(1)</script>'), "JS-free")

    def test_external_images_break_the_offline_promise(self):
        self.assertRejects(page(extra='<img src="https://x.test/a.png">'),
                           "offline guarantee")

    def test_data_uri_images_are_allowed(self):
        check(page(extra='<img src="data:image/png;base64,AAAA">'))

    def test_unresolved_mermaid_placeholder(self):
        self.assertRejects(page(extra='<p>@@MM:0123456789ab@@</p>'),
                           "unresolved mermaid")

    def test_missing_diagram_is_an_error_not_a_gap(self):
        self.assertRejects(page(extra='<div class="mermaid-missing">缺失图</div>'),
                           "missing diagrams")

    def test_svg_shortfall(self):
        self.assertRejects(page(svgs=1), "svg count", expect_svgs=2)

    def test_unclosed_fence_swallowing_the_rest_of_the_book(self):
        self.assertRejects(page(extra="<pre><code><table><tr><td>x</td></tr></table>"),
                           "nested inside <pre>")

    def test_stray_markdown_fence(self):
        self.assertRejects(page(extra="\n```python\nx\n```"),
                           "stray markdown fences")

    def test_residual_md_link(self):
        self.assertRejects(page(extra='<a href="../附录/D-术语表.md">t</a>'),
                           "residual .md links")

    def test_a_unit_without_a_compass_is_incomplete(self):
        html = page(n_units=2).replace('<div class="compass"><h4 class="cc-tag">问题</h4></div>',
                                        "", 1)
        self.assertRejects(html, "compass cards", n_units=2)

    def test_unbalanced_close_tag(self):
        self.assertRejects(page(extra="</section>"), "unbalanced closing tags")


if __name__ == "__main__":
    unittest.main()
