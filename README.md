# rs-trafilatura

Fast web content extraction, page classification, HTML cleaning, and Markdown conversion — powered by Rust.

## Install

```bash
pip install rs-trafilatura
```

## Usage

```python
import rs_trafilatura

# Extract main content from HTML
result = rs_trafilatura.extract(html, url="https://example.com")
print(result.title, result.main_content, result.page_type, result.extraction_quality)

# Classify page type from URL
page_type, confidence = rs_trafilatura.classify_url("https://docs.example.com/api")

# Clean HTML (remove scripts, styles, comments)
cleaned = rs_trafilatura.clean_html(raw_html)

# Convert HTML to Markdown
markdown = rs_trafilatura.html_to_markdown(html)
```

## License

MIT OR Apache-2.0
