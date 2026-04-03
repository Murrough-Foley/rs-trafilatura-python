"""crawl4ai integration for rs-trafilatura.

Usage:
    import json
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from rs_trafilatura.crawl4ai import RsTrafilaturaStrategy

    config = CrawlerRunConfig(extraction_strategy=RsTrafilaturaStrategy())
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        data = json.loads(result.extracted_content)
"""

from typing import Any, Dict, List

from rs_trafilatura._core import extract as _extract

# Inherit from crawl4ai's ExtractionStrategy when available so that
# isinstance() checks in CrawlerRunConfig pass. When crawl4ai is not
# installed, fall back to a standalone base class.
try:
    from crawl4ai.extraction_strategy import ExtractionStrategy as _Base
except ImportError:
    class _Base:
        """Fallback base when crawl4ai is not installed."""
        def __init__(self, input_format="html", **kwargs):
            self.input_format = input_format
            self.DEL = "<|DEL|>"
            self.name = self.__class__.__name__
            self.verbose = kwargs.get("verbose", False)


class RsTrafilaturaStrategy(_Base):
    """crawl4ai ExtractionStrategy that uses rs-trafilatura for content extraction.

    Set as extraction_strategy in CrawlerRunConfig. Receives raw HTML
    (input_format="html") and returns structured extraction results.

    Inherits from crawl4ai's ExtractionStrategy when crawl4ai is installed,
    so that isinstance() checks pass. Falls back to a standalone class otherwise.
    """

    def __init__(
        self,
        favor_precision: bool = False,
        favor_recall: bool = False,
        output_markdown: bool = False,
        **kwargs,
    ):
        super().__init__(input_format="html", **kwargs)
        self.name = "RsTrafilaturaStrategy"
        self._favor_precision = favor_precision
        self._favor_recall = favor_recall
        self._output_markdown = output_markdown

    def extract(self, url: str, html: str, *q, **kwargs) -> List[Dict[str, Any]]:
        """Extract content from a single HTML section."""
        result = _extract(
            html,
            url=url,
            favor_precision=self._favor_precision,
            favor_recall=self._favor_recall,
            output_markdown=self._output_markdown,
        )
        return [
            {
                "title": result.title,
                "author": result.author,
                "date": result.date,
                "main_content": result.main_content,
                "content_markdown": result.content_markdown,
                "page_type": result.page_type,
                "extraction_quality": result.extraction_quality,
                "language": result.language,
                "sitename": result.sitename,
                "description": result.description,
            }
        ]

    def run(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        """Process HTML — rs-trafilatura needs the full document, not chunks."""
        full_html = sections[0] if sections else ""
        return self.extract(url, full_html, **kwargs)

    async def arun(self, url: str, sections: List[str], *q, **kwargs) -> List[Dict[str, Any]]:
        """Async version — runs sync extraction in a thread."""
        import asyncio
        return await asyncio.to_thread(self.run, url, sections, *q, **kwargs)
