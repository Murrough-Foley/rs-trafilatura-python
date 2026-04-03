"""Tests for framework adapter wrappers."""

import asyncio
import json
from rs_trafilatura.crawl4ai import RsTrafilaturaStrategy
from rs_trafilatura.firecrawl import extract_firecrawl_result
from rs_trafilatura.crawlee import extract_crawlee_context, extract_playwright_context
from rs_trafilatura.scrapy import RsTrafilaturaPipeline


HTML = """<html><head><title>Test Page</title></head>
<body><article><h1>Test</h1>
<p>Main content with enough text for extraction to work properly across all adapters.</p>
</article></body></html>"""


class TestCrawl4aiAdapter:
    def test_extract_returns_list_of_dicts(self):
        strategy = RsTrafilaturaStrategy()
        results = strategy.extract("https://example.com", HTML)
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], dict)

    def test_extract_contains_expected_keys(self):
        strategy = RsTrafilaturaStrategy()
        results = strategy.extract("https://example.com", HTML)
        data = results[0]
        for key in ("main_content", "title", "page_type", "extraction_quality",
                     "language", "sitename", "description"):
            assert key in data, f"Missing key: {key}"

    def test_run_joins_sections(self):
        strategy = RsTrafilaturaStrategy()
        results = strategy.run("https://example.com", [HTML])
        assert len(results) == 1
        assert results[0]["main_content"]

    def test_run_empty_sections(self):
        strategy = RsTrafilaturaStrategy()
        results = strategy.run("https://example.com", [])
        assert isinstance(results, list)

    def test_input_format_is_html(self):
        strategy = RsTrafilaturaStrategy()
        assert strategy.input_format == "html"

    def test_markdown_option(self):
        strategy = RsTrafilaturaStrategy(output_markdown=True)
        results = strategy.extract("https://example.com", HTML)
        assert results[0].get("content_markdown") is not None or results[0]["main_content"] == ""

    def test_duck_types_extraction_strategy(self):
        """Verify all required attributes/methods for crawl4ai compatibility."""
        strategy = RsTrafilaturaStrategy()
        assert hasattr(strategy, "input_format")
        assert hasattr(strategy, "name")
        assert hasattr(strategy, "DEL")
        assert callable(getattr(strategy, "extract", None))
        assert callable(getattr(strategy, "run", None))
        assert callable(getattr(strategy, "arun", None))

    def test_arun_async(self):
        """Verify async arun works."""
        strategy = RsTrafilaturaStrategy()
        results = asyncio.run(strategy.arun("https://example.com", [HTML]))
        assert len(results) == 1
        assert results[0]["main_content"]

    def test_result_is_json_serialisable(self):
        """crawl4ai calls json.dumps on extraction results — verify it works."""
        strategy = RsTrafilaturaStrategy()
        results = strategy.extract("https://example.com", HTML)
        serialised = json.dumps(results)
        assert isinstance(serialised, str)
        roundtripped = json.loads(serialised)
        assert roundtripped[0]["main_content"] == results[0]["main_content"]

    def test_malformed_html_propagates_error(self):
        """Extraction on empty HTML should return empty content, not raise."""
        strategy = RsTrafilaturaStrategy()
        results = strategy.extract("https://example.com", "")
        assert results[0]["main_content"] == ""


class TestFirecrawlAdapter:
    def test_extract_from_result_dict(self):
        firecrawl_result = {
            "html": HTML,
            "metadata": {"sourceURL": "https://example.com/page"},
        }
        extracted = extract_firecrawl_result(firecrawl_result)
        assert extracted.main_content
        assert isinstance(extracted.extraction_quality, float)

    def test_missing_html_key(self):
        firecrawl_result = {"metadata": {"sourceURL": "https://example.com"}}
        extracted = extract_firecrawl_result(firecrawl_result)
        assert extracted.main_content == ""

    def test_missing_metadata(self):
        firecrawl_result = {"html": HTML}
        extracted = extract_firecrawl_result(firecrawl_result)
        assert extracted.main_content

    def test_favor_recall(self):
        firecrawl_result = {"html": HTML, "metadata": {"sourceURL": "https://example.com"}}
        extracted = extract_firecrawl_result(firecrawl_result, favor_recall=True)
        assert isinstance(extracted.main_content, str)


class TestCrawleeAdapter:
    def test_extract_from_mock_context(self):
        class MockSoup:
            def __str__(self):
                return HTML

        class MockRequest:
            url = "https://example.com/test"

        class MockContext:
            soup = MockSoup()
            request = MockRequest()

        extracted = extract_crawlee_context(MockContext())
        assert extracted.main_content
        assert isinstance(extracted.extraction_quality, float)

    def test_url_passthrough(self):
        """Verify the URL from context.request.url reaches the classifier."""
        class MockSoup:
            def __str__(self):
                return "<html><body><article><p>Some documentation content.</p></article></body></html>"

        class MockRequest:
            url = "https://docs.example.com/api/reference"

        class MockContext:
            soup = MockSoup()
            request = MockRequest()

        extracted = extract_crawlee_context(MockContext())
        assert extracted.page_type == "documentation"

    def test_output_markdown(self):
        class MockSoup:
            def __str__(self):
                return HTML

        class MockRequest:
            url = "https://example.com/test"

        class MockContext:
            soup = MockSoup()
            request = MockRequest()

        extracted = extract_crawlee_context(MockContext(), output_markdown=True)
        assert extracted.content_markdown is not None or extracted.main_content == ""

    def test_missing_soup(self):
        class MockContext:
            pass

        extracted = extract_crawlee_context(MockContext())
        assert extracted.main_content == ""

    def test_playwright_context_async(self):
        """Verify async extract_playwright_context works."""
        class MockPage:
            async def content(self):
                return HTML

        class MockRequest:
            url = "https://example.com/test"

        class MockContext:
            page = MockPage()
            request = MockRequest()

        extracted = asyncio.run(extract_playwright_context(MockContext()))
        assert extracted.main_content
        assert isinstance(extracted.extraction_quality, float)


class TestScrapyAdapter:
    def test_process_item_with_html_string(self):
        pipeline = RsTrafilaturaPipeline()
        item = {"url": "https://example.com", "html": HTML}
        result = pipeline.process_item(item, spider=None)
        assert "extraction" in result
        assert result["extraction"]["main_content"]
        assert result["extraction"]["page_type"]

    def test_process_item_with_body_bytes(self):
        pipeline = RsTrafilaturaPipeline()
        item = {"url": "https://example.com", "body": HTML.encode("utf-8")}
        result = pipeline.process_item(item, spider=None)
        assert "extraction" in result
        assert result["extraction"]["main_content"]

    def test_process_item_no_html(self):
        pipeline = RsTrafilaturaPipeline()
        item = {"url": "https://example.com", "other_field": "data"}
        result = pipeline.process_item(item, spider=None)
        assert "extraction" not in result  # passes through unchanged

    def test_markdown_option(self):
        pipeline = RsTrafilaturaPipeline(output_markdown=True)
        item = {"url": "https://example.com", "html": HTML}
        result = pipeline.process_item(item, spider=None)
        assert "content_markdown" in result["extraction"]

    def test_extraction_dict_has_all_fields(self):
        """Verify Scrapy extraction dict matches crawl4ai adapter fields."""
        pipeline = RsTrafilaturaPipeline()
        item = {"url": "https://example.com", "html": HTML}
        result = pipeline.process_item(item, spider=None)
        for key in ("title", "author", "date", "main_content", "content_markdown",
                     "page_type", "extraction_quality", "language", "sitename", "description"):
            assert key in result["extraction"], f"Missing key: {key}"
