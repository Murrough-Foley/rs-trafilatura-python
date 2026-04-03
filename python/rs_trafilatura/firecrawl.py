"""Firecrawl integration for rs-trafilatura.

Usage:
    from firecrawl import FirecrawlApp
    from rs_trafilatura.firecrawl import extract_firecrawl_result

    app = FirecrawlApp(api_key="...")
    result = app.scrape_url("https://example.com", params={"formats": ["html"]})
    extracted = extract_firecrawl_result(result)
    print(extracted.title, extracted.main_content, extracted.page_type)
"""

from rs_trafilatura._core import extract, ExtractResult


def extract_firecrawl_result(
    result: dict,
    favor_precision: bool = False,
    favor_recall: bool = False,
    output_markdown: bool = False,
) -> ExtractResult:
    """Extract content from a Firecrawl scrape result.

    Args:
        result: The dict returned by FirecrawlApp.scrape_url().
            Must contain 'html' key (request formats=["html"]).
        favor_precision: Stricter filtering.
        favor_recall: More inclusive, may include some noise.
        output_markdown: Generate Markdown output.

    Returns:
        ExtractResult with title, main_content, page_type, etc.
    """
    html = result.get("html", "")
    url = result.get("metadata", {}).get("sourceURL", "")

    return extract(
        html,
        url=url,
        favor_precision=favor_precision,
        favor_recall=favor_recall,
        output_markdown=output_markdown,
    )
