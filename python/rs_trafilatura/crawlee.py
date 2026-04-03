"""Crawlee integration for rs-trafilatura.

Usage with BeautifulSoupCrawler:
    from crawlee.beautifulsoup_crawler import BeautifulSoupCrawler, BeautifulSoupCrawlingContext
    from rs_trafilatura.crawlee import extract_crawlee_context

    crawler = BeautifulSoupCrawler()

    @crawler.router.default_handler
    async def handler(context: BeautifulSoupCrawlingContext):
        extracted = extract_crawlee_context(context)
        print(extracted.title, extracted.main_content, extracted.page_type)

Usage with PlaywrightCrawler:
    from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
    from rs_trafilatura.crawlee import extract_playwright_context

    @crawler.router.default_handler
    async def handler(context: PlaywrightCrawlingContext):
        extracted = await extract_playwright_context(context)
"""

from rs_trafilatura._core import extract, ExtractResult


def extract_crawlee_context(
    context,
    favor_precision: bool = False,
    favor_recall: bool = False,
    output_markdown: bool = False,
) -> ExtractResult:
    """Extract content from a Crawlee BeautifulSoupCrawlingContext.

    Args:
        context: BeautifulSoupCrawlingContext from a request handler.
        favor_precision: Stricter filtering.
        favor_recall: More inclusive, may include some noise.
        output_markdown: Generate Markdown output.

    Returns:
        ExtractResult with title, main_content, page_type, etc.
    """
    html = str(context.soup) if hasattr(context, "soup") else ""
    url = str(context.request.url) if hasattr(context, "request") else ""

    return extract(
        html,
        url=url,
        favor_precision=favor_precision,
        favor_recall=favor_recall,
        output_markdown=output_markdown,
    )


async def extract_playwright_context(
    context,
    favor_precision: bool = False,
    favor_recall: bool = False,
    output_markdown: bool = False,
) -> ExtractResult:
    """Extract content from a Crawlee PlaywrightCrawlingContext.

    Args:
        context: PlaywrightCrawlingContext from a request handler.
        favor_precision: Stricter filtering.
        favor_recall: More inclusive, may include some noise.
        output_markdown: Generate Markdown output.

    Returns:
        ExtractResult with title, main_content, page_type, etc.
    """
    html = await context.page.content() if hasattr(context, "page") else ""
    url = str(context.request.url) if hasattr(context, "request") else ""

    import asyncio
    return await asyncio.to_thread(
        extract,
        html,
        url=url,
        favor_precision=favor_precision,
        favor_recall=favor_recall,
        output_markdown=output_markdown,
    )
