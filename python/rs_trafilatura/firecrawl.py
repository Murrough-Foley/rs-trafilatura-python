"""Firecrawl integration for rs-trafilatura.

Usage:
    from firecrawl import FirecrawlApp
    from rs_trafilatura.firecrawl import extract_firecrawl_result

    app = FirecrawlApp(api_key="...")
    result = app.scrape("https://example.com", formats=["html"])
    extracted = extract_firecrawl_result(result)
    print(extracted.title, extracted.main_content, extracted.page_type)
"""

from rs_trafilatura._core import extract, ExtractResult


def extract_firecrawl_result(
    result,
    favor_precision: bool = False,
    favor_recall: bool = False,
    output_markdown: bool = False,
) -> ExtractResult:
    """Extract content from a Firecrawl scrape result.

    Args:
        result: The result from FirecrawlApp.scrape(). Accepts both
            v4 Document objects (with .html and .metadata attributes)
            and legacy v1 dicts (with 'html' and 'metadata' keys).
        favor_precision: Stricter filtering.
        favor_recall: More inclusive, may include some noise.
        output_markdown: Generate Markdown output.

    Returns:
        ExtractResult with title, main_content, page_type, etc.
    """
    # Support both v4 Document objects and legacy v1 dicts
    if isinstance(result, dict):
        html = result.get("html", "")
        url = result.get("metadata", {}).get("sourceURL", "")
    else:
        html = getattr(result, "html", "") or ""
        metadata = getattr(result, "metadata", None)
        url = getattr(metadata, "url", "") or getattr(metadata, "source_url", "") or "" if metadata else ""

    return extract(
        html,
        url=url,
        favor_precision=favor_precision,
        favor_recall=favor_recall,
        output_markdown=output_markdown,
    )
