import trafilatura


def get_article_context(url, fallback_summary="", max_chars=3000):
    """
    Tries to scrape the full article text for better RAG context.
    Falls back to the RSS summary if scraping fails (paywalls, timeouts, etc).
    """
    try:
        downloaded = trafilatura.fetch_url(url, no_ssl=True)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text and len(text.strip()) > 50:
                return text.strip()[:max_chars]
    except Exception:
        pass

    return fallback_summary[:max_chars] if fallback_summary else ""
