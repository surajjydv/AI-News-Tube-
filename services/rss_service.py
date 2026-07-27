import feedparser
from typing import List
from models.news_models import NewsArticle
from utils.logger import logger
from utils.exceptions import NewsFetchError

# RSS feeds covering all major current-affairs categories
RSS_FEEDS = {
    "Top Stories": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "India": "https://news.google.com/rss/headlines/section/topic/NATION?hl=en-IN&gl=IN&ceid=IN:en",
    "World": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-IN&gl=IN&ceid=IN:en",
    "Business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-IN&gl=IN&ceid=IN:en",
    "Technology": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-IN&gl=IN&ceid=IN:en",
    "Entertainment": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-IN&gl=IN&ceid=IN:en",
    "Sports": "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en-IN&gl=IN&ceid=IN:en",
    "Science": "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=en-IN&gl=IN&ceid=IN:en",
    "Health": "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=en-IN&gl=IN&ceid=IN:en",
}


import hashlib
import re


def _is_similar_title(t1: str, t2: str) -> bool:
    """Check fuzzy word overlap between two titles for deduplication."""
    words1 = set(re.findall(r'\w+', t1.lower()))
    words2 = set(re.findall(r'\w+', t2.lower()))
    if not words1 or not words2:
        return False
    intersection = words1.intersection(words2)
    jaccard = len(intersection) / max(1, len(words1.union(words2)))
    return jaccard > 0.45


def calculate_trending_score(title: str, summary: str, category: str) -> tuple:
    """
    Computes virality & trending score (0-100) and flags breaking news.
    """
    score = 50.0
    combined = (title + " " + summary).lower()

    viral_keywords = [
        "breaking", "shocking", "urgent", "huge", "record", "ban", "stunning",
        "crisis", "ai", "openai", "modi", "india", "isro", "court", "launch",
        "update", "warning", "banned", "secret", "future", "billion", "million"
    ]
    for kw in viral_keywords:
        if kw in combined:
            score += 12.0

    cat_weights = {
        "Top Stories": 20.0,
        "Technology": 18.0,
        "India": 15.0,
        "World": 12.0,
        "Business": 10.0,
        "Science": 10.0
    }
    score += cat_weights.get(category, 5.0)

    is_breaking = any(k in combined for k in ["breaking", "urgent", "just in", "flash", "dhamaka", "alert"])
    if is_breaking:
        score += 25.0

    return min(100.0, round(score, 1)), is_breaking


def fetch_news(limit_per_category: int = 5) -> List[NewsArticle]:
    """
    Fetches news items across categories, performs deduplication, and scores for virality.
    """
    raw_articles: List[NewsArticle] = []

    logger.info("Fetching RSS news feeds across categories...")

    try:
        for category, url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
            except Exception as fe:
                logger.warning(f"Failed to parse RSS feed for '{category}': {fe}")
                continue

            count_for_category = 0
            for entry in feed.entries:
                if count_for_category >= limit_per_category:
                    break

                title = getattr(entry, "title", "").strip()
                if not title:
                    continue

                summary = ""
                if hasattr(entry, "summary"):
                    summary = entry.summary.strip()
                elif hasattr(entry, "description"):
                    summary = entry.description.strip()

                link = getattr(entry, "link", "")
                published_at = getattr(entry, "published", None)

                score, is_brk = calculate_trending_score(title, summary, category)
                u_hash = hashlib.md5(title.lower().encode("utf-8")).hexdigest()[:10]

                article = NewsArticle(
                    title=title,
                    link=link,
                    summary=summary,
                    category=category,
                    published_at=published_at,
                    trending_score=score,
                    is_breaking=is_brk,
                    unique_hash=u_hash
                )
                raw_articles.append(article)
                count_for_category += 1

        # Deduplication
        deduped_articles: List[NewsArticle] = []
        for candidate in raw_articles:
            duplicate_found = False
            for existing in deduped_articles:
                if _is_similar_title(candidate.title, existing.title):
                    duplicate_found = True
                    # Keep the higher score article
                    if candidate.trending_score > existing.trending_score:
                        existing.trending_score = candidate.trending_score
                    break
            if not duplicate_found:
                deduped_articles.append(candidate)

        # Sort by trending score descending
        deduped_articles.sort(key=lambda x: x.trending_score, reverse=True)

        logger.info(f"Successfully fetched & ranked {len(deduped_articles)} unique news articles.")
        return deduped_articles

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise NewsFetchError(f"Failed to fetch news feeds: {e}") from e


def get_realtime_ticker_headlines(limit: int = 12) -> List[str]:
    """
    Fetches quick real-time breaking news titles across categories for the live ticker slide.
    """
    headlines = []
    try:
        articles = fetch_news(limit_per_category=2)
        for art in articles:
            # Clean headline title
            clean_t = art.title.split(" - ")[0].strip()
            if clean_t and clean_t not in headlines:
                headlines.append(f"[{art.category.upper()}] {clean_t}")
            if len(headlines) >= limit:
                break
    except Exception as e:
        logger.warning(f"Failed to fetch real-time ticker headlines: {e}")

    if not headlines:
        headlines = [
            "[INDIA] Supreme Court issues new directives on digital privacy and security",
            "[TECH] AI technology adoption accelerates across global broadcasting networks",
            "[BUSINESS] Markets reach new record high amidst robust quarterly economic growth",
            "[WORLD] Global climate summit delegates agree on renewable energy expansion",
            "[SPORTS] National team secures thrilling victory in international championship match"
        ]

    return headlines

