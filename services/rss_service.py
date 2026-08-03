import feedparser
from typing import List
from models.news_models import NewsArticle
from utils.logger import logger
from utils.exceptions import NewsFetchError
import hashlib
import re
import datetime as dt
import json
import threading
import os
from pathlib import Path
from time import mktime

# Persist the seen set so a process/container restart does not replay the same
# RSS items from the top of every feed.
SEEN_NEWS_FILE = Path(__file__).resolve().parent.parent / "data" / "seen_news.json"
SEEN_NEWS_LOCK = threading.Lock()
try:
    _seen_data = json.loads(SEEN_NEWS_FILE.read_text(encoding="utf-8"))
except (FileNotFoundError, json.JSONDecodeError, OSError):
    _seen_data = {"titles": [], "hashes": []}
SEEN_NEWS_HASHES = set(_seen_data.get("hashes", []))
SEEN_NEWS_TITLES = set(_seen_data.get("titles", []))

RSS_CACHE_TTL_SECONDS = int(os.getenv("RSS_CACHE_TTL_SECONDS", "300"))
RSS_CACHE = {}
RSS_CACHE_LOCK = threading.Lock()


def _save_seen_news():
    SEEN_NEWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = SEEN_NEWS_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps({
        "titles": sorted(SEEN_NEWS_TITLES),
        "hashes": sorted(SEEN_NEWS_HASHES),
    }, ensure_ascii=False), encoding="utf-8")
    tmp_file.replace(SEEN_NEWS_FILE)

# Multi-source RSS feeds covering trusted global & Indian news outlets
RSS_FEEDS = {
    "Top Stories": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "NDTV Top": "https://feeds.feedburner.com/ndtvnews-top-stories",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "India Today": "https://www.indiatoday.in/rss/1206578",
    "India": "https://news.google.com/rss/headlines/section/topic/NATION?hl=en-IN&gl=IN&ceid=IN:en",
    "World": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-IN&gl=IN&ceid=IN:en",
    "Business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-IN&gl=IN&ceid=IN:en",
    "Technology": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-IN&gl=IN&ceid=IN:en",
    "Sports": "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en-IN&gl=IN&ceid=IN:en",
    "Science": "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=en-IN&gl=IN&ceid=IN:en",
    "Entertainment": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-IN&gl=IN&ceid=IN:en",
    "Health": "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=en-IN&gl=IN&ceid=IN:en",
    "Google India Hindi": "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
    "BBC Hindi": "https://feeds.bbci.co.uk/hindi/rss.xml",
}


def mark_news_as_seen(title: str, unique_hash: str = ""):
    """Registers a news story as broadcasted so it will never be repeated."""
    with SEEN_NEWS_LOCK:
        if title:
            SEEN_NEWS_TITLES.add(title.strip().lower())
        if unique_hash:
            SEEN_NEWS_HASHES.add(unique_hash)
        _save_seen_news()


def is_news_seen(title: str, unique_hash: str = "") -> bool:
    """Checks if a story has already been broadcasted."""
    if unique_hash and unique_hash in SEEN_NEWS_HASHES:
        return True
    t_clean = title.strip().lower()
    if t_clean in SEEN_NEWS_TITLES:
        return True
    for seen_t in list(SEEN_NEWS_TITLES):
        if _is_similar_title(t_clean, seen_t):
            return True
    return False


def _is_within_freshness_window(entry, max_hours: float = 24.0) -> bool:
    """Checks if published date is within allowed freshness window (default 24h)."""
    parsed_time = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not parsed_time:
        return True  # If feed omits timestamp, allow article
    try:
        entry_dt = dt.datetime.fromtimestamp(mktime(parsed_time), tz=dt.timezone.utc)
        now_dt   = dt.datetime.now(dt.timezone.utc)
        age_hours = (now_dt - entry_dt).total_seconds() / 3600.0
        return age_hours <= max_hours
    except Exception:
        return True


def _is_similar_title(t1: str, t2: str) -> bool:
    """Check fuzzy word overlap between two titles for deduplication."""
    words1 = set(re.findall(r'\w+', t1.lower()))
    words2 = set(re.findall(r'\w+', t2.lower()))
    if not words1 or not words2:
        return False
    intersection = words1.intersection(words2)
    jaccard = len(intersection) / max(1, len(words1.union(words2)))
    return jaccard > 0.40


def _get_feed_entries(category: str, url: str):
    """Return RSS entries from a short-lived cache to avoid repeat downloads."""
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    with RSS_CACHE_LOCK:
        cached = RSS_CACHE.get(category)
        if cached and now - cached[0] < RSS_CACHE_TTL_SECONDS:
            return cached[1]

    try:
        feed = feedparser.parse(url)
        entries = list(feed.entries)
    except Exception as error:
        logger.warning(f"Failed to parse RSS feed for '{category}': {error}")
        return []

    with RSS_CACHE_LOCK:
        RSS_CACHE[category] = (now, entries)
    return entries


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
            entries = _get_feed_entries(category, url)

            count_for_category = 0
            for entry in entries:
                if count_for_category >= limit_per_category:
                    break

                title = getattr(entry, "title", "").strip()
                if not title:
                    continue

                if not _is_within_freshness_window(entry, max_hours=24.0):
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


def get_fresh_unseen_news(count: int = 5) -> List[NewsArticle]:
    """Fetches and returns 100% unseen, unique fresh news articles."""
    all_news = fetch_news(limit_per_category=10)
    unseen = [art for art in all_news if not is_news_seen(art.title, art.unique_hash)]

    if len(unseen) < count:
        logger.warning("Not enough unseen RSS stories available; keeping seen cache to prevent replay.")

    selected = unseen[:count]
    for art in selected:
        mark_news_as_seen(art.title, art.unique_hash)

    print(f"[FRESH NEWS ENGINE] 🆕 Selected {len(selected)} 100% unique unseen news articles!")
    return selected


def get_realtime_ticker_headlines(limit: int = 12) -> List[str]:
    """
    Fetches quick real-time breaking news titles across categories for the live ticker slide.
    """
    headlines = []
    try:
        articles = fetch_news(limit_per_category=2)
        for art in articles:
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


def get_dynamic_hindi_news_data(main_title_eng: str, main_category: str) -> dict:
    """
    Fetches live current news across categories and translates titles into simple, natural Devanagari Hindi.
    """
    from services.groq_service import generate_text

    try:
        prompt = f"Translate this news headline into 1 simple, natural Devanagari Hindi news headline suitable for reading: '{main_title_eng}'. Return ONLY the Hindi text."
        main_hindi = generate_text(prompt, temperature=0.2).strip().replace('"', '')
    except Exception:
        main_hindi = main_title_eng

    all_articles = fetch_news(limit_per_category=2)
    categories_needed = ["India", "Business", "Technology", "Sports"]
    quick_hindi_cards = []

    for cat in categories_needed:
        match = next((a for a in all_articles if a.category == cat), None)
        if match:
            raw_t = match.title.split(" - ")[0].strip()
            try:
                p = f"Shorten and translate this news headline into 4 to 6 simple Devanagari Hindi words: '{raw_t}'. Return ONLY the Hindi text."
                h_text = generate_text(p, temperature=0.2).strip().replace('"', '')
                quick_hindi_cards.append(f"[{cat.upper()}]\n{h_text[:35]}")
            except Exception:
                quick_hindi_cards.append(f"[{cat.upper()}]\n{raw_t[:30]}")
        else:
            quick_hindi_cards.append(f"[{cat.upper()}]\nताज़ा समाचार अपडेट")

    raw_tickers = get_realtime_ticker_headlines(limit=10)
    ticker_hindi_list = []
    for rt in raw_tickers[:6]:
        try:
            p_t = f"Translate this news title into 1 short simple Devanagari Hindi ticker phrase: '{rt}'. Return ONLY Hindi text."
            ht = generate_text(p_t, temperature=0.2).strip().replace('"', '')
            ticker_hindi_list.append(ht)
        except Exception:
            ticker_hindi_list.append(rt)

    return {
        "main_headline": main_hindi,
        "sub_takeaways": [
            "• प्रमुख बिंदु और मुख्य समाचार अपडेट्स",
            "• निष्पक्ष जांच और ताज़ा रिपोर्ट"
        ],
        "quick_cards": quick_hindi_cards[:4],
        "ticker_headlines": ticker_hindi_list if ticker_hindi_list else ["सरकार ने किसानों के लिए नई योजना का किया ऐलान", "भारत की अर्थव्यवस्था में रिकॉर्ड वृद्धि दर्ज"]
    }
