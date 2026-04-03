"""Integration tests for rs-trafilatura Python bindings."""

import rs_trafilatura
import pytest


ARTICLE_HTML = """<html>
<head><title>Test Article</title></head>
<body>
    <nav>Home | About | Contact</nav>
    <article>
        <h1>Test Article Title</h1>
        <p>This is the main content of a test article about web extraction.
        It contains enough text for the extractor to identify as main content
        rather than boilerplate. The article discusses various topics.</p>
        <p>A second paragraph adds more substance to ensure reliable extraction
        across different extraction strategies and heuristics.</p>
    </article>
    <footer>Copyright 2026. All rights reserved.</footer>
</body>
</html>"""


class TestExtract:
    def test_basic_extraction(self):
        result = rs_trafilatura.extract(ARTICLE_HTML)
        assert result.main_content
        assert "main content" in result.main_content

    def test_extraction_with_url(self):
        result = rs_trafilatura.extract(ARTICLE_HTML, url="https://example.com/blog/test")
        assert result.page_type == "article"

    def test_extraction_quality_range(self):
        result = rs_trafilatura.extract(ARTICLE_HTML)
        assert 0.0 <= result.extraction_quality <= 1.0

    def test_markdown_output(self):
        result = rs_trafilatura.extract(ARTICLE_HTML, output_markdown=True)
        assert result.content_markdown is not None
        assert len(result.content_markdown) > 0

    def test_empty_html(self):
        result = rs_trafilatura.extract("")
        assert result.main_content == ""

    def test_repr(self):
        result = rs_trafilatura.extract(ARTICLE_HTML)
        r = repr(result)
        assert "ExtractResult" in r
        assert "quality=" in r

    def test_page_type_override(self):
        result = rs_trafilatura.extract(ARTICLE_HTML, page_type="forum")
        assert result.page_type == "forum"

    def test_invalid_page_type(self):
        with pytest.raises(ValueError):
            rs_trafilatura.extract(ARTICLE_HTML, page_type="nonexistent")

    def test_metadata_fields(self):
        result = rs_trafilatura.extract(ARTICLE_HTML, url="https://example.com/blog/test")
        assert hasattr(result, "language")
        assert hasattr(result, "sitename")
        assert hasattr(result, "description")

    def test_favor_precision(self):
        result = rs_trafilatura.extract(ARTICLE_HTML, favor_precision=True)
        assert isinstance(result.main_content, str)

    def test_favor_recall(self):
        result = rs_trafilatura.extract(ARTICLE_HTML, favor_recall=True)
        assert isinstance(result.main_content, str)

    def test_malformed_html(self):
        html = "<div>" * 500 + "<p>Content</p>" + "</div>" * 200
        result = rs_trafilatura.extract(html)
        assert isinstance(result.main_content, str)

    def test_large_html(self):
        html = "<html><body>" + "<p>Paragraph content. </p>" * 5000 + "</body></html>"
        result = rs_trafilatura.extract(html)
        assert len(result.main_content) > 0


class TestExtractBytes:
    def test_utf8_bytes(self):
        html = b"<html><body><article><p>Hello world from bytes.</p></article></body></html>"
        result = rs_trafilatura.extract_bytes(html)
        assert "Hello world" in result.main_content

    def test_latin1_bytes(self):
        html = b'<html><head><meta charset="ISO-8859-1"></head><body><article><p>Caf\xe9 content here.</p></article></body></html>'
        result = rs_trafilatura.extract_bytes(html)
        assert "Caf\u00e9" in result.main_content  # é decoded correctly

    def test_invalid_bytes(self):
        """Random binary data should not panic."""
        result = rs_trafilatura.extract_bytes(b"\xff\xfe\x00\x00garbage")
        assert isinstance(result.main_content, str)

    def test_null_bytes(self):
        result = rs_trafilatura.extract_bytes(b"\x00\x00\x00")
        assert isinstance(result.main_content, str)

    def test_with_url(self):
        html = b"<html><body><article><p>Some docs content.</p></article></body></html>"
        result = rs_trafilatura.extract_bytes(html, url="https://docs.example.com/api")
        assert result.page_type == "documentation"

    def test_full_kwargs(self):
        """extract_bytes accepts the same kwargs as extract."""
        html = b"<html><body><article><p>Content for bytes extraction test.</p></article></body></html>"
        result = rs_trafilatura.extract_bytes(
            html,
            url="https://example.com/products/test",
            page_type="product",
            favor_precision=True,
            output_markdown=True,
        )
        assert result.page_type == "product"
        # content_markdown should be populated when output_markdown=True
        assert result.content_markdown is not None or result.main_content == ""

    def test_page_type_override(self):
        html = b"<html><body><article><p>Test content.</p></article></body></html>"
        result = rs_trafilatura.extract_bytes(html, page_type="forum")
        assert result.page_type == "forum"


class TestClassifyUrl:
    def test_documentation(self):
        pt, conf = rs_trafilatura.classify_url("https://docs.example.com/api/reference")
        assert pt == "documentation"
        assert conf == 0.9

    def test_forum(self):
        pt, conf = rs_trafilatura.classify_url("https://forum.example.com/thread/123")
        assert pt == "forum"
        assert conf == 0.9

    def test_product(self):
        pt, conf = rs_trafilatura.classify_url("https://example.com/products/widget")
        assert pt == "product"
        assert conf == 0.9

    def test_article_default_returns_none_confidence(self):
        pt, conf = rs_trafilatura.classify_url("https://example.com/some-page")
        assert pt == "article"
        assert conf is None  # No pattern matched

    def test_empty_url_returns_none_confidence(self):
        pt, conf = rs_trafilatura.classify_url("")
        assert pt == "article"
        assert conf is None


class TestCleanHtml:
    def test_removes_script_tags(self):
        cleaned = rs_trafilatura.clean_html("<html><script>alert(1)</script><p>Hello</p></html>")
        assert "<script" not in cleaned
        assert "alert(1)" not in cleaned
        assert "Hello" in cleaned

    def test_removes_style_tags(self):
        cleaned = rs_trafilatura.clean_html("<html><style>.x{color:red}</style><p>Text</p></html>")
        assert "<style" not in cleaned
        assert "color:red" not in cleaned
        assert "Text" in cleaned

    def test_removes_comments(self):
        cleaned = rs_trafilatura.clean_html("<html><p>Text</p><!-- secret comment --></html>")
        assert "secret" not in cleaned
        assert "Text" in cleaned

    def test_preserves_content(self):
        cleaned = rs_trafilatura.clean_html("<html><body><h1>Title</h1><p>Body text</p></body></html>")
        assert "Title" in cleaned
        assert "Body text" in cleaned

    def test_content_with_word_style(self):
        """The word 'style' in content should be preserved even though <style> tags are removed."""
        cleaned = rs_trafilatura.clean_html("<html><style>.x{}</style><p>My coding style is clean</p></html>")
        assert "My coding style is clean" in cleaned
        assert "<style" not in cleaned


class TestHtmlToMarkdown:
    def test_heading(self):
        md = rs_trafilatura.html_to_markdown("<h1>Title</h1>")
        assert "Title" in md

    def test_paragraph(self):
        md = rs_trafilatura.html_to_markdown("<p>Hello world</p>")
        assert "Hello world" in md

    def test_list(self):
        md = rs_trafilatura.html_to_markdown("<ul><li>Item 1</li><li>Item 2</li></ul>")
        assert "Item 1" in md
        assert "Item 2" in md

    def test_link(self):
        md = rs_trafilatura.html_to_markdown('<a href="https://example.com">Click</a>')
        assert "Click" in md
        assert "example.com" in md


class TestPredictQuality:
    def test_returns_float(self):
        features = [0.0] * 27
        quality = rs_trafilatura.predict_quality(features)
        assert isinstance(quality, float)
        assert 0.0 <= quality <= 1.0

    def test_wrong_feature_count(self):
        with pytest.raises(ValueError):
            rs_trafilatura.predict_quality([0.0] * 10)


class TestClassifyPage:
    def test_returns_tuple(self):
        features = [0.0] * 89
        pt, conf = rs_trafilatura.classify_page(features, "example blog post")
        assert isinstance(pt, str)
        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0

    def test_wrong_feature_count(self):
        with pytest.raises(ValueError):
            rs_trafilatura.classify_page([0.0] * 10, "test")


class TestThreadSafety:
    def test_concurrent_extraction(self):
        """Verify extraction works from multiple threads simultaneously."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        htmls = [
            f"<html><body><article><p>Content for thread {i}. Enough text to extract.</p></article></body></html>"
            for i in range(10)
        ]

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(rs_trafilatura.extract, h): i for i, h in enumerate(htmls)}
            results = {}
            for future in as_completed(futures):
                idx = futures[future]
                results[idx] = future.result()

        assert len(results) == 10
        for i, result in results.items():
            assert isinstance(result.main_content, str)
            assert f"thread {i}" in result.main_content, (
                f"Thread {i} got wrong content: {result.main_content[:80]}"
            )
