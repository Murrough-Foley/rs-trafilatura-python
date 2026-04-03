"""rs-trafilatura: Fast web content extraction powered by Rust.

Functions:
    extract(html, **kwargs) -> ExtractResult
    extract_bytes(html_bytes, **kwargs) -> ExtractResult
    classify_url(url) -> (page_type, confidence)
    classify_page(features, title_meta) -> (page_type, confidence)
    predict_quality(features) -> float
    clean_html(html) -> str
    html_to_markdown(html) -> str
"""

from rs_trafilatura._core import (
    ExtractResult,
    ImageData,
    classify_page,
    classify_url,
    clean_html,
    extract,
    extract_bytes,
    html_to_markdown,
    predict_quality,
)

__all__ = [
    "extract",
    "extract_bytes",
    "classify_url",
    "classify_page",
    "predict_quality",
    "clean_html",
    "html_to_markdown",
    "ExtractResult",
    "ImageData",
]

__version__ = "0.1.0"
