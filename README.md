# rs-trafilatura

Fast web content extraction, page type classification, HTML cleaning, and Markdown conversion for Python — powered by Rust.

rs-trafilatura is a Python package built with [PyO3](https://pyo3.rs) that wraps four Rust crates into a single `pip install`. It extracts the main content from web pages, classifies page types, predicts extraction quality, cleans HTML, and converts HTML to Markdown — all at native Rust speed.

## Why rs-trafilatura?

- **Fast**: Rust-native extraction at ~44ms per page on commodity hardware — 36x faster than neural approaches
- **Accurate**: F1 0.859 across 7 page types on the [Web Content Extraction Benchmark](https://webcontentextraction.org), outperforming Trafilatura (0.791), MinerU-HTML (0.827), and ReaderLM-v2 (0.741)
- **Page-type aware**: XGBoost classifier detects articles, forums, products, collections, listings, documentation, and service pages — then applies type-specific extraction profiles
- **Quality scoring**: ML-based confidence predictor (0.0–1.0) tells you when extraction might be unreliable, enabling hybrid pipelines with LLM fallback
- **Framework adapters**: Drop-in integrations for crawl4ai, Scrapy, Firecrawl, and Crawlee

## Install

```bash
pip install rs-trafilatura
```

## Quick Start

```python
import rs_trafilatura

# Extract main content from HTML
result = rs_trafilatura.extract(html, url="https://example.com")
print(result.title)                # Page title
print(result.main_content)         # Clean extracted text
print(result.page_type)            # article, forum, product, etc.
print(result.extraction_quality)   # 0.0–1.0 confidence score
```

## API Reference

### Content Extraction

```python
# From a string
result = rs_trafilatura.extract(
    html,
    url="https://example.com",      # URL for page type classification
    page_type="product",             # Force a page type (bypasses classifier)
    favor_precision=True,            # Stricter filtering, less noise
    favor_recall=False,              # More inclusive extraction
    include_tables=True,             # Include table content
    include_images=True,             # Extract image metadata
    include_comments=False,          # Include comment sections
    output_markdown=True,            # Generate Markdown in content_markdown
)

# From raw bytes (auto-detects encoding)
result = rs_trafilatura.extract_bytes(
    response_bytes,
    url="https://example.com",
    output_markdown=True,
)
```

**`ExtractResult` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str \| None` | Page title |
| `author` | `str \| None` | Author name |
| `date` | `str \| None` | Publication date (ISO 8601) |
| `main_content` | `str` | Extracted main content as plain text |
| `content_markdown` | `str \| None` | Markdown output (when `output_markdown=True`) |
| `content_html` | `str \| None` | Extracted content as HTML |
| `page_type` | `str \| None` | Detected page type |
| `extraction_quality` | `float` | Confidence score (0.0–1.0) |
| `classification_confidence` | `float \| None` | Page type classifier confidence |
| `language` | `str \| None` | Detected language |
| `sitename` | `str \| None` | Site name |
| `description` | `str \| None` | Meta description |
| `images` | `list[ImageData]` | Extracted images with src, alt, caption |

### Page Type Classification

```python
# Fast URL-based heuristic (no HTML needed)
page_type, confidence = rs_trafilatura.classify_url("https://docs.example.com/api")
# ("documentation", 0.9) — or ("article", None) when no pattern matches

# ML classifier with DOM features (higher accuracy)
page_type, confidence = rs_trafilatura.classify_page(
    numeric_features,   # 89 numeric features from the HTML DOM
    "page title text",  # Title + description for TF-IDF
)
```

### Extraction Quality Prediction

```python
# Predict how reliable an extraction is (for hybrid pipeline routing)
quality = rs_trafilatura.predict_quality(features)  # 27 post-extraction features
# Returns 0.0–1.0. Below 0.80 suggests routing to an LLM fallback.
```

### HTML Cleaning

```python
# Remove scripts, styles, comments, SVGs, iframes — keep content
cleaned = rs_trafilatura.clean_html(raw_html)
```

### HTML to Markdown

```python
# Convert HTML to GitHub Flavored Markdown
markdown = rs_trafilatura.html_to_markdown(html)
```

## Framework Integrations

### crawl4ai

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from rs_trafilatura.crawl4ai import RsTrafilaturaStrategy

config = CrawlerRunConfig(extraction_strategy=RsTrafilaturaStrategy(output_markdown=True))
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com", config=config)
    data = json.loads(result.extracted_content)
    print(data[0]["main_content"])
```

### Scrapy

```python
# settings.py
ITEM_PIPELINES = {
    "rs_trafilatura.scrapy.RsTrafilaturaPipeline": 300,
}
RS_TRAFILATURA_MARKDOWN = True  # optional

# spider.py
def parse(self, response):
    yield {"url": response.url, "body": response.body}
    # Pipeline adds item["extraction"] with title, main_content, page_type, etc.
```

### Firecrawl

```python
from firecrawl import FirecrawlApp
from rs_trafilatura.firecrawl import extract_firecrawl_result

app = FirecrawlApp(api_key="...")
result = app.scrape("https://example.com", formats=["html"])
extracted = extract_firecrawl_result(result)
print(extracted.title, extracted.main_content, extracted.page_type)
```

### Crawlee

```python
from crawlee.beautifulsoup_crawler import BeautifulSoupCrawler
from rs_trafilatura.crawlee import extract_crawlee_context

crawler = BeautifulSoupCrawler()

@crawler.router.default_handler
async def handler(context):
    extracted = extract_crawlee_context(context)
    print(extracted.title, extracted.main_content, extracted.page_type)
```

## Benchmarks

Tested on the [Web Content Extraction Benchmark](https://webcontentextraction.org) (WCEB) — 1,497 pages across 7 page types:

| System | F1 | Speed |
|--------|---:|------:|
| **rs-trafilatura** | **0.859** | 44 ms/page |
| MinerU-HTML (0.6B) | 0.827 | 1,570 ms/page |
| Trafilatura (Python) | 0.791 | 94 ms/page |
| ReaderLM-v2 (1.5B) | 0.741 | 10,410 ms/page |

Per-page-type F1:

| Page Type | F1 |
|-----------|---:|
| Article | 0.932 |
| Documentation | 0.931 |
| Service | 0.843 |
| Forum | 0.792 |
| Collection | 0.713 |
| Listing | 0.704 |
| Product | 0.670 |

## What's Inside

This package bundles four Rust crates compiled into a single Python extension:

| Crate | What it does |
|-------|-------------|
| [rs-trafilatura](https://crates.io/crates/rs-trafilatura) | Content extraction with page-type-aware profiles |
| [web-page-classifier](https://crates.io/crates/web-page-classifier) | XGBoost page type classification + quality prediction |
| [html-cleaning](https://crates.io/crates/html-cleaning) | HTML sanitisation and tag removal |
| [quick_html2md](https://crates.io/crates/quick_html2md) | HTML to GFM Markdown conversion |

## Links

- **Website**: [webcontentextraction.org](https://webcontentextraction.org)
- **Benchmark**: [GitHub](https://github.com/Murrough-Foley/web-content-extraction-benchmark)
- **Rust crate**: [crates.io/crates/rs-trafilatura](https://crates.io/crates/rs-trafilatura)
- **Author**: [Murrough Foley](https://murroughfoley.com) · [LinkedIn](https://linkedin.com/in/m-foley-seo/) · [ORCID](https://orcid.org/0009-0008-3127-2101)

## License

MIT OR Apache-2.0
