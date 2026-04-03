"""Scrapy pipeline integration for rs-trafilatura.

Usage in settings.py:
    ITEM_PIPELINES = {
        'rs_trafilatura.scrapy.RsTrafilaturaPipeline': 300,
    }

The pipeline adds extraction results to each item under the 'extraction' key.
Items must have either a 'body' field (raw HTML bytes) or an 'html' field (str).
Set the 'url' field for page type classification.
"""

from rs_trafilatura._core import extract_bytes, extract


class RsTrafilaturaPipeline:
    """Scrapy pipeline that extracts content using rs-trafilatura.

    Looks for HTML in item['body'] (bytes) or item['html'] (str).
    Adds extraction results under item['extraction'].
    """

    def __init__(self, output_markdown: bool = False):
        self.output_markdown = output_markdown

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            output_markdown=crawler.settings.getbool(
                "RS_TRAFILATURA_MARKDOWN", False
            ),
        )

    def process_item(self, item, spider):
        url = item.get("url", "")

        if "body" in item and isinstance(item["body"], bytes):
            result = extract_bytes(
                item["body"], url=url, output_markdown=self.output_markdown
            )
        elif "html" in item and isinstance(item["html"], str):
            result = extract(
                item["html"], url=url, output_markdown=self.output_markdown
            )
        else:
            return item

        item["extraction"] = {
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
        return item
