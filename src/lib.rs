use std::str::FromStr;

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

// ---------------------------------------------------------------------------
// Result types exposed to Python
// ---------------------------------------------------------------------------

/// Extracted image metadata.
#[pyclass(frozen)]
#[derive(Clone)]
struct ImageData {
    #[pyo3(get)]
    src: String,
    #[pyo3(get)]
    alt: Option<String>,
    #[pyo3(get)]
    caption: Option<String>,
    #[pyo3(get)]
    filename: String,
    #[pyo3(get)]
    is_hero: bool,
}

/// Content extraction result.
#[pyclass(frozen)]
struct ExtractResult {
    #[pyo3(get)]
    title: Option<String>,
    #[pyo3(get)]
    author: Option<String>,
    #[pyo3(get)]
    date: Option<String>,
    #[pyo3(get)]
    main_content: String,
    #[pyo3(get)]
    content_markdown: Option<String>,
    #[pyo3(get)]
    content_html: Option<String>,
    #[pyo3(get)]
    page_type: Option<String>,
    #[pyo3(get)]
    extraction_quality: f64,
    #[pyo3(get)]
    classification_confidence: Option<f64>,
    #[pyo3(get)]
    language: Option<String>,
    #[pyo3(get)]
    sitename: Option<String>,
    #[pyo3(get)]
    description: Option<String>,
    #[pyo3(get)]
    images: Vec<ImageData>,
}

#[pymethods]
impl ExtractResult {
    fn __repr__(&self) -> String {
        format!(
            "ExtractResult(title={:?}, page_type={:?}, quality={:.2}, content_len={})",
            self.title, self.page_type, self.extraction_quality, self.main_content.len()
        )
    }
}

/// Convert a Rust ExtractResult into the Python ExtractResult.
fn build_result(result: rs_trafilatura::ExtractResult) -> ExtractResult {
    ExtractResult {
        title: result.metadata.title.clone(),
        author: result.metadata.author.clone(),
        date: result.metadata.date.map(|d| d.to_rfc3339()),
        main_content: result.content_text,
        content_markdown: result.content_markdown,
        content_html: result.content_html,
        page_type: result.metadata.page_type.clone(),
        extraction_quality: result.extraction_quality,
        classification_confidence: result.classification_confidence,
        language: result.metadata.language.clone(),
        sitename: result.metadata.sitename.clone(),
        description: result.metadata.description.clone(),
        images: result
            .images
            .iter()
            .map(|img| ImageData {
                src: img.src.clone(),
                alt: img.alt.clone(),
                caption: img.caption.clone(),
                filename: img.filename.clone(),
                is_hero: img.is_hero,
            })
            .collect(),
    }
}

/// Build Options from Python kwargs.
fn build_options(
    url: Option<String>,
    page_type: Option<&str>,
    favor_precision: bool,
    favor_recall: bool,
    include_tables: bool,
    include_images: bool,
    include_links: bool,
    include_comments: bool,
    output_markdown: bool,
) -> PyResult<rs_trafilatura::Options> {
    let pt = page_type
        .map(|s| rs_trafilatura::page_type::PageType::from_str(s))
        .transpose()
        .map_err(|e| PyValueError::new_err(format!("Invalid page_type: {e}")))?;

    Ok(rs_trafilatura::Options {
        url,
        page_type: pt,
        favor_precision,
        favor_recall,
        include_tables,
        include_images,
        include_links,
        include_comments,
        output_markdown,
        ..rs_trafilatura::Options::default()
    })
}

// ---------------------------------------------------------------------------
// Core extraction functions
// ---------------------------------------------------------------------------

/// Extract main content from an HTML document.
///
/// Args:
///     html: Raw HTML string.
///     url: Optional URL for page type classification hints.
///     page_type: Force a specific page type (article, forum, product,
///         collection, listing, documentation, service). Bypasses classifier.
///     favor_precision: Stricter filtering, less noise.
///     favor_recall: More inclusive, may include some noise.
///     include_tables: Include table content (default True).
///     include_images: Extract image metadata.
///     include_links: Preserve link information.
///     include_comments: Include comment sections.
///     output_markdown: Generate Markdown output in content_markdown field.
///
/// Returns:
///     ExtractResult with title, main_content, page_type, extraction_quality, etc.
#[pyfunction]
#[pyo3(signature = (html, *, url=None, page_type=None, favor_precision=false, favor_recall=false, include_tables=true, include_images=false, include_links=false, include_comments=false, output_markdown=false))]
fn extract(
    html: &str,
    url: Option<String>,
    page_type: Option<&str>,
    favor_precision: bool,
    favor_recall: bool,
    include_tables: bool,
    include_images: bool,
    include_links: bool,
    include_comments: bool,
    output_markdown: bool,
) -> PyResult<ExtractResult> {
    let options = build_options(
        url, page_type, favor_precision, favor_recall,
        include_tables, include_images, include_links, include_comments, output_markdown,
    )?;
    let result = rs_trafilatura::extract_with_options(html, &options)
        .map_err(|e| PyValueError::new_err(format!("Extraction failed: {e}")))?;
    Ok(build_result(result))
}

/// Extract main content from HTML bytes with automatic encoding detection.
///
/// Use this when you have raw bytes from an HTTP response and don't know
/// the encoding. Detects encoding from meta charset declarations and
/// converts to UTF-8 before extraction.
///
/// Accepts the same keyword arguments as extract().
#[pyfunction]
#[pyo3(signature = (html_bytes, *, url=None, page_type=None, favor_precision=false, favor_recall=false, include_tables=true, include_images=false, include_links=false, include_comments=false, output_markdown=false))]
fn extract_bytes(
    html_bytes: &[u8],
    url: Option<String>,
    page_type: Option<&str>,
    favor_precision: bool,
    favor_recall: bool,
    include_tables: bool,
    include_images: bool,
    include_links: bool,
    include_comments: bool,
    output_markdown: bool,
) -> PyResult<ExtractResult> {
    let options = build_options(
        url, page_type, favor_precision, favor_recall,
        include_tables, include_images, include_links, include_comments, output_markdown,
    )?;
    let result = rs_trafilatura::extract_bytes_with_options(html_bytes, &options)
        .map_err(|e| PyValueError::new_err(format!("Extraction failed: {e}")))?;
    Ok(build_result(result))
}

// ---------------------------------------------------------------------------
// Page type classification
// ---------------------------------------------------------------------------

/// Classify a web page type from its URL using heuristic pattern matching.
///
/// This is a fast heuristic check based on URL domain and path patterns.
/// When no pattern matches, it returns ("article", None) — use classify_page()
/// with ML features for a more accurate result in that case.
///
/// Returns:
///     Tuple of (page_type, confidence) where page_type is one of:
///     article, forum, product, collection, listing, documentation, service.
///     confidence is None when no URL pattern matched (article default),
///     or 0.9 when a specific pattern was recognised.
#[pyfunction]
fn classify_url(url: &str) -> (String, Option<f64>) {
    if url.is_empty() {
        return ("article".to_string(), None);
    }
    let page_type = web_page_classifier::classify_url(url);
    let confidence = if page_type == web_page_classifier::PageType::Article {
        None // No pattern matched — this is the fallback default
    } else {
        Some(0.9) // A specific URL pattern matched
    };
    (page_type.as_str().to_string(), confidence)
}

/// Classify a web page type using the ML model.
///
/// Args:
///     numeric_features: List of 89 numeric features extracted from the HTML DOM.
///     title_meta: Concatenated title + description text for TF-IDF features.
///
/// Returns:
///     Tuple of (page_type, confidence) where confidence is the softmax
///     probability from the XGBoost classifier (0.0 to 1.0).
#[pyfunction]
fn classify_page(numeric_features: Vec<f64>, title_meta: &str) -> PyResult<(String, f64)> {
    if numeric_features.len() != web_page_classifier::N_NUMERIC_FEATURES {
        return Err(PyValueError::new_err(format!(
            "Expected {} numeric features, got {}",
            web_page_classifier::N_NUMERIC_FEATURES,
            numeric_features.len()
        )));
    }
    let (page_type, confidence) = web_page_classifier::classify_ml(&numeric_features, title_meta);
    Ok((page_type.as_str().to_string(), confidence))
}

/// Predict extraction quality (estimated F1 score) from post-extraction features.
///
/// Args:
///     features: List of 27 quality features (content stats, page type indicators,
///         HTML-level signals).
///
/// Returns:
///     Quality score in [0.0, 1.0]. Scores below 0.80 suggest the extraction
///     may be poor and should be routed to an LLM fallback.
#[pyfunction]
fn predict_quality(features: Vec<f64>) -> PyResult<f64> {
    if features.len() != web_page_classifier::N_QUALITY_FEATURES {
        return Err(PyValueError::new_err(format!(
            "Expected {} quality features, got {}",
            web_page_classifier::N_QUALITY_FEATURES,
            features.len()
        )));
    }
    Ok(web_page_classifier::predict_quality(&features))
}

// ---------------------------------------------------------------------------
// HTML cleaning
// ---------------------------------------------------------------------------

/// Clean an HTML document by removing scripts, styles, comments, and other noise.
///
/// Removes: <script>, <style>, <noscript>, <svg>, <iframe> tags and HTML comments.
/// Normalises whitespace and prunes empty container elements.
///
/// Returns cleaned HTML as a string.
#[pyfunction]
fn clean_html(html: &str) -> String {
    let options = html_cleaning::CleaningOptions {
        tags_to_remove: vec![
            "script".into(), "style".into(), "noscript".into(),
            "svg".into(), "iframe".into(),
        ],
        remove_comments: true,
        normalize_whitespace: true,
        prune_empty: true,
        ..Default::default()
    };
    let doc = html_cleaning::Document::from(html);
    let cleaner = html_cleaning::HtmlCleaner::with_options(options);
    cleaner.clean(&doc);
    doc.html().to_string()
}

// ---------------------------------------------------------------------------
// HTML to Markdown
// ---------------------------------------------------------------------------

/// Convert an HTML string to GitHub Flavored Markdown.
///
/// Preserves headings, lists, tables, bold/italic, code blocks, and links.
#[pyfunction]
fn html_to_markdown(html: &str) -> String {
    quick_html2md::html_to_markdown(html)
}

// ---------------------------------------------------------------------------
// Module definition
// ---------------------------------------------------------------------------

/// rs-trafilatura: Fast web content extraction powered by Rust.
///
/// Functions:
///     extract(html, **kwargs) -> ExtractResult
///     extract_bytes(html_bytes, **kwargs) -> ExtractResult
///     classify_url(url) -> (page_type, confidence)
///     classify_page(features, title_meta) -> (page_type, confidence)
///     predict_quality(features) -> float
///     clean_html(html) -> str
///     html_to_markdown(html) -> str
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(extract, m)?)?;
    m.add_function(wrap_pyfunction!(extract_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(classify_url, m)?)?;
    m.add_function(wrap_pyfunction!(classify_page, m)?)?;
    m.add_function(wrap_pyfunction!(predict_quality, m)?)?;
    m.add_function(wrap_pyfunction!(clean_html, m)?)?;
    m.add_function(wrap_pyfunction!(html_to_markdown, m)?)?;
    m.add_class::<ExtractResult>()?;
    m.add_class::<ImageData>()?;
    Ok(())
}
