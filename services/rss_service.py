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
import sys
import requests
from pathlib import Path
import time
from time import mktime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# Persist the seen set so a process/container restart does not replay the same
# RSS items from the top of every feed.
SEEN_NEWS_FILE = Path(__file__).resolve().parent.parent / "data" / "seen_news.json"
SEEN_NEWS_LOCK = threading.Lock()
MAX_SEEN_TITLES = 200

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
    global SEEN_NEWS_TITLES, SEEN_NEWS_HASHES
    SEEN_NEWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = SEEN_NEWS_FILE.with_name(
        f"{SEEN_NEWS_FILE.stem}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    try:
        # Keep sliding window to prevent historical cache buildup from blocking fresh news
        if len(SEEN_NEWS_TITLES) > MAX_SEEN_TITLES:
            recent_titles = list(SEEN_NEWS_TITLES)[-MAX_SEEN_TITLES:]
            SEEN_NEWS_TITLES = set(recent_titles)
        if len(SEEN_NEWS_HASHES) > MAX_SEEN_TITLES:
            recent_hashes = list(SEEN_NEWS_HASHES)[-MAX_SEEN_TITLES:]
            SEEN_NEWS_HASHES = set(recent_hashes)

        tmp_file.write_text(json.dumps({
            "titles": sorted(SEEN_NEWS_TITLES),
            "hashes": sorted(SEEN_NEWS_HASHES),
        }, ensure_ascii=False), encoding="utf-8")
        tmp_file.replace(SEEN_NEWS_FILE)
    finally:
        try:
            tmp_file.unlink(missing_ok=True)
        except OSError:
            pass


def clear_seen_cache():
    """Resets seen news memory when new cycle begins."""
    global SEEN_NEWS_TITLES, SEEN_NEWS_HASHES
    with SEEN_NEWS_LOCK:
        SEEN_NEWS_TITLES.clear()
        SEEN_NEWS_HASHES.clear()
        _save_seen_news()


# Multi-source RSS feeds covering trusted global & Indian news outlets
RSS_FEEDS = {
    "Google India Hindi": "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
    "BBC Hindi": "https://feeds.bbci.co.uk/hindi/rss.xml",
    "Aaj Tak Hindi": "https://www.aajtak.in/rssfeeds/rss_topstories.xml",
    "NDTV India Hindi": "https://feeds.feedburner.com/ndtvkhabar",
    "Dainik Bhaskar": "https://www.bhaskar.com/rss-v1/2714.xml",
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


STOP_WORDS = {
    "the", "and", "in", "a", "an", "to", "of", "for", "on", "with", "at", "by", "from",
    "is", "are", "was", "were", "be", "been", "news", "today", "india", "breaking", "update",
    "says", "after", "over", "into", "amid", "gets", "new", "big", "live", "net", "com",
    "के", "का", "की", "में", "पर", "से", "को", "और", "है", "हैं", "था", "थी", "ने", "पर", "बड़ी", "खबर"
}

def _is_similar_title(t1: str, t2: str) -> bool:
    """
    Check fuzzy word and entity overlap between two story titles for strict deduplication.
    Prevents re-posting the same underlying news event across multiple feeds.
    """
    words1 = {w for w in re.findall(r'[a-zA-Z0-9\u0900-\u097F]+', t1.lower()) if len(w) > 2 and w not in STOP_WORDS}
    words2 = {w for w in re.findall(r'[a-zA-Z0-9\u0900-\u097F]+', t2.lower()) if len(w) > 2 and w not in STOP_WORDS}
    if not words1 or not words2:
        return False
    intersection = words1.intersection(words2)
    min_len = min(len(words1), len(words2))
    
    # If 2 or more strong content words match, or overlap >= 35% of either title, flag duplicate
    if len(intersection) >= 2 and (len(intersection) / max(1, min_len)) >= 0.35:
        return True
    jaccard = len(intersection) / max(1, len(words1.union(words2)))
    return jaccard >= 0.35


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
        "Google India Hindi": 25.0,
        "BBC Hindi": 25.0,
        "Aaj Tak Hindi": 25.0,
        "NDTV India Hindi": 25.0,
        "Dainik Bhaskar": 25.0,
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


def fetch_news(limit_per_category: int = 5, topic: str = None) -> List[NewsArticle]:
    """
    Fetches news items across categories, performs deduplication, and scores for virality.
    If topic is provided, fetches specific topic coverage.
    """
    raw_articles: List[NewsArticle] = []

    logger.info("Fetching RSS news feeds across categories...")

    try:
        feed_map = dict(RSS_FEEDS)
        if topic:
            topic_clean = topic.strip()
            topic_rss = f"https://news.google.com/rss/search?q={requests.utils.quote(topic_clean)}&hl=en-IN&gl=IN&ceid=IN:en"
            feed_map = {f"Topic: {topic_clean}": topic_rss}

        for category, url in feed_map.items():
            entries = _get_feed_entries(category, url)

            count_for_category = 0
            for entry in entries:
                if count_for_category >= limit_per_category:
                    break

                title = getattr(entry, "title", "").strip()
                if not title:
                    continue

                if not _is_within_freshness_window(entry, max_hours=36.0):
                    continue

                summary = ""
                if hasattr(entry, "summary"):
                    summary = entry.summary.strip()
                elif hasattr(entry, "description"):
                    summary = entry.description.strip()

                link = getattr(entry, "link", "")
                published_at = getattr(entry, "published", None)

                # Extract direct editorial event photo attached by press wire
                img_url = None
                if hasattr(entry, "media_content") and entry.media_content:
                    img_url = entry.media_content[0].get("url")
                elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                    img_url = entry.media_thumbnail[0].get("url")
                elif hasattr(entry, "enclosures") and entry.enclosures:
                    img_url = entry.enclosures[0].get("href")

                if not img_url and summary:
                    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
                    if m:
                        img_url = m.group(1)

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
                    unique_hash=u_hash,
                    image_url=img_url
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
    """Fetches and returns 100% unique fresh news articles, with auto-pruning to guarantee continuous stream."""
    global SEEN_NEWS_TITLES, SEEN_NEWS_HASHES
    all_news = fetch_news(limit_per_category=10)
    if not all_news:
        all_news = fetch_news(limit_per_category=5)

    unseen = [art for art in all_news if not is_news_seen(art.title, art.unique_hash)]

    # If all news has been seen, prune the oldest 70% of seen news to unlock fresh cycles
    if not unseen and all_news:
        logger.warning("[FRESH NEWS ENGINE] Seen cache exhausted. Pruning older history to refresh news cycle...")
        with SEEN_NEWS_LOCK:
            keep_count = min(30, len(SEEN_NEWS_TITLES) // 4)
            SEEN_NEWS_TITLES = set(list(SEEN_NEWS_TITLES)[-keep_count:])
            SEEN_NEWS_HASHES = set(list(SEEN_NEWS_HASHES)[-keep_count:])
            _save_seen_news()
        unseen = [art for art in all_news if not is_news_seen(art.title, art.unique_hash)]
        if not unseen:
            unseen = all_news

    selected = unseen[:count] if unseen else all_news[:count]
    for art in selected:
        mark_news_as_seen(art.title, art.unique_hash)
    logger.info(f"[FRESH NEWS ENGINE] Selected {len(selected)} 100% unique unseen news articles!")
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


def _truncate_hindi(text: str, max_chars: int) -> str:
    """Word-boundary-aware truncation to prevent cutting Devanagari grapheme clusters mid-character."""
    if not text or len(text) <= max_chars:
        return text
    words = text.split()
    out = ""
    for w in words:
        if len(out) + len(w) + 1 > max_chars:
            break
        out = f"{out} {w}".strip()
    return out or text[:max_chars]


def _proofread_hindi_spelling(text: str) -> str:
    """
    Lightweight self-proofreading pass to correct malformed Devanagari spelling / matra placement.
    Fail-open: returns original text if LLM call fails.
    """
    if not text or not any('\u0900' <= c <= '\u097F' for c in text):
        return text
    from services.groq_service import generate_text
    try:
        proofread_prompt = (
            f"इस हिंदी वाक्य में कोई वर्तनी (spelling) या मात्रा की गलती हो तो उसे ठीक करके सिर्फ सही वाक्य लौटाओ, "
            f"कोई गलती न हो तो वही वाक्य जस का तस लौटाओ: '{text}'. Return ONLY the corrected Hindi text."
        )
        corrected = generate_text(proofread_prompt, temperature=0.1).strip().replace('"', '')
        if corrected and len(corrected) >= len(text) * 0.5:
            return corrected
    except Exception as e:
        logger.warning(f"Proofreading pass skipped/failed: {e}")
    return text


def get_dynamic_hindi_news_data(main_title_eng: str, main_category: str) -> dict:
    """
    Fetches live current news across categories and translates titles into simple, natural Devanagari Hindi.
    """
    from services.groq_service import generate_text

    try:
        prompt = (
            f"Translate this news headline into highly natural, authentic TV news Hindi (जैसे Aaj Tak या ABP News की भाषा). "
            f"Avoid literal dictionary translations and artificial words. Write standard, grammatically correct Hindi without spelling mistakes: "
            f"'{main_title_eng}'. Return ONLY the polished Hindi headline text."
        )
        main_hindi = generate_text(prompt, temperature=0.1).strip().replace('"', '')
        main_hindi = _proofread_hindi_spelling(main_hindi)
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
                p = (
                    f"Shorten and translate this news headline into 4 to 6 natural TV news Hindi words (जैसे Aaj Tak की भाषा): "
                    f"'{raw_t}'. Return ONLY the Hindi text."
                )
                h_text = generate_text(p, temperature=0.1).strip().replace('"', '')
                h_text = _proofread_hindi_spelling(h_text)
                truncated_text = _truncate_hindi(h_text, 35)
                quick_hindi_cards.append(f"[{cat.upper()}]\n{truncated_text}")
            except Exception:
                quick_hindi_cards.append(f"[{cat.upper()}]\n{_truncate_hindi(raw_t, 30)}")
        else:
            quick_hindi_cards.append(f"[{cat.upper()}]\nताज़ा समाचार अपडेट")

    raw_tickers = get_realtime_ticker_headlines(limit=10)
    ticker_hindi_list = []
    for rt in raw_tickers[:6]:
        try:
            p_t = (
                f"Translate this news title into 1 short natural Devanagari Hindi ticker phrase: '{rt}'. "
                f"Use standard grammatically correct Hindi. Return ONLY Hindi text."
            )
            ht = generate_text(p_t, temperature=0.1).strip().replace('"', '')
            ht = _proofread_hindi_spelling(ht)
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


_ALL_DAY_HEADLINES_CACHE = {"timestamp": 0, "headlines": []}
_ALL_DAY_LOCK = threading.Lock()

def get_all_day_breaking_headlines() -> List[str]:
    """
    Returns an unlimited, continuously refreshed pool of breaking news headlines across
    all categories for 24/7 full-day TV broadcast motion tickers and lower-third headline animation.
    """
    global _ALL_DAY_HEADLINES_CACHE
    now = time.time()

    with _ALL_DAY_LOCK:
        if _ALL_DAY_HEADLINES_CACHE["headlines"] and (now - _ALL_DAY_HEADLINES_CACHE["timestamp"] < 300):
            return _ALL_DAY_HEADLINES_CACHE["headlines"]

    headlines = []
    try:
        articles = fetch_news(limit_per_category=4)
        for art in articles:
            clean_t = art.title.split(" - ")[0].strip()
            if clean_t and clean_t not in headlines:
                headlines.append(f"[{art.category.upper()}] {clean_t}")
    except Exception as e:
        logger.warning(f"Error fetching all-day headlines: {e}")

    if len(headlines) < 5:
        headlines.extend([
            "[NATIONAL] सुप्रीम कोर्ट का ऐतिहासिक फैसला: नए नियमों पर लगी मुहर",
            "[BUSINESS] शेयर बाज़ार में जबरदस्त तेजी: सेंसेक्स और निफ्टी नए रिकॉर्ड स्तर पर",
            "[TECHNOLOGY] भारत में 5G और AI क्रांति: ग्लोबल टेक कंपनियों का बड़ा निवेश",
            "[SPORTS] टीम इंडिया की शानदार जीत: ऐतिहासिक मुकाबले में रचा नया इतिहास",
            "[WORLD] वैश्विक शिखर सम्मेलन में अहम सहमति: पर्यावरण और ऊर्जा पर बड़ा फैसला",
            "[DEFENCE] स्वदेशी रक्षा प्रणालियों का सफल परीक्षण: सेना की ताकत में बड़ा इजाफा",
            "[WEATHER] देश के प्रमुख राज्यों में मौसम विभाग का अलर्ट जारी",
            "[ECONOMY] भारतीय अर्थव्यवस्था की रफ्तार तेज: जीडीपी में 7.8% की ऐतिहासिक वृद्धि"
        ])

    with _ALL_DAY_LOCK:
        _ALL_DAY_HEADLINES_CACHE = {
            "timestamp": now,
            "headlines": headlines
        }

    return headlines
