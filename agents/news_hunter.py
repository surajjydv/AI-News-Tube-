from typing import List, Optional
from services.rss_service import fetch_news
from models.news_models import NewsArticle
from utils.logger import logger


def news_hunter(topic: Optional[str] = None) -> List[NewsArticle]:
    """
    Smart News Hunter Agent: Fetches, deduplicates, and ranks news stories by virality & trending score.
    If topic is provided, fetches news filtered specifically for that topic.
    """
    logger.info("=" * 50)
    logger.info("📰 SMART NEWS HUNTER AGENT (Virality Ranking & Deduplication)")
    if topic:
        logger.info(f"🎯 Target Topic: {topic}")
    logger.info("=" * 50)

    news = fetch_news(topic=topic)

    for i, item in enumerate(news[:10], start=1):
        brk_tag = "🚨 [BREAKING] " if item.is_breaking else ""
        logger.info(f"{i:2d}. {brk_tag}[Score: {item.trending_score:.0f}] [{item.category}] {item.title}")

    categories_count = len(set(n.category for n in news))
    logger.info(f"✅ Smart News Hunter Ready — Top {len(news)} ranked unique news items across {categories_count} categories.")

    return news
