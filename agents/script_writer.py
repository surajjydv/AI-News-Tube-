from services.scraper_service import get_article_context
from services.groq_service import generate_text
from config.settings import CHANNEL_NAME
from models.news_models import NewsArticle, GeneratedScript
from utils.logger import logger


def build_prompt(title: str, context: str, category: str = "General", is_breaking: bool = False) -> str:
    breaking_prefix = "🚨 BREAKING NEWS! " if is_breaking else ""
    return f"""Tum ek top-tier YouTube High-Retention News Scriptwriter ho aur {CHANNEL_NAME} channel ki lead news anchor ho.

Category: {category}
Topic: {breaking_prefix}{title}

Article Context:
\"\"\"
{context}
\"\"\"

YouTube Audience Retention ke liye 6-Stage High-Retention Spoken Hindi News Script likho.

SCRIPT STRUCTURE (MUST FOLLOW):
1. HOOK (First 5 seconds): High-intensity shocker ya curiosity statement se shuru karo.
2. PROBLEM / CONFLICT: Asli tension ya suspense spasht karo.
3. WHAT HAPPENED: Main news facts aur details batayein.
4. IMPACT: Yeh khabar audience aur duniya ke liye kyo mahtvapurna hai.
5. FUTURE PREDICTION: Aage kya expected hai ya kya badlav aayega.
6. CTA: {CHANNEL_NAME} ko subscribe aur video ko like karne ki urgent appeal.

RULES:
- Continuous spoken script text likho (no markdown headings, no bracket labels like [HOOK]).
- High-retention conversational Hindi tone (jaise TV broadcast presenter bolti ho).
- Word count: 180-240 words.
"""


def script_writer(news_item: NewsArticle) -> GeneratedScript:
    """
    Script Writer Agent: Takes a NewsArticle and generates a high-retention 6-part YouTube script.
    """
    logger.info("=" * 50)
    logger.info("✍️ HIGH-RETENTION SCRIPT WRITER AGENT (HOOK → Problem → Story → Impact → Future → CTA)")
    logger.info("=" * 50)

    title = news_item.title
    link = news_item.link
    summary = news_item.summary
    category = news_item.category
    is_brk = getattr(news_item, "is_breaking", False)

    logger.info(f"Writing retention script for: [{category}] {title} (Breaking: {is_brk})")

    context = get_article_context(link, fallback_summary=summary)
    if not context:
        context = title

    news_item.scraped_content = context

    prompt = build_prompt(title, context, category, is_breaking=is_brk)
    script_text = generate_text(prompt)

    word_count = len(script_text.split())

    logger.info(f"✅ High-Retention Script Generated ({word_count} words).")

    return GeneratedScript(
        topic_title=title,
        category=category,
        script_text=script_text,
        word_count=word_count
    )
