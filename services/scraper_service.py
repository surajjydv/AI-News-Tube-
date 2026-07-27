import trafilatura
from utils.logger import logger


def get_article_context(url: str, fallback_summary: str = "", max_chars: int = 3000) -> str:
    """
    Tries to scrape full article text for better RAG context.
    Falls back gracefully to the RSS summary if scraping fails.
    """
    if not url:
        return fallback_summary[:max_chars] if fallback_summary else ""

    try:
        logger.info(f"Scraping article context from: {url}")
        downloaded = trafilatura.fetch_url(url, no_ssl=True)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text and len(text.strip()) > 50:
                logger.info("Successfully extracted article body text.")
                return text.strip()[:max_chars]
    except Exception as e:
        logger.warning(f"Scraping failed for {url} ({e}). Falling back to summary.")

    return fallback_summary[:max_chars] if fallback_summary else ""
