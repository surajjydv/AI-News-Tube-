"""
services/viral_topic_service.py
===============================
Viral Topic Discovery Engine for AI-NewsTube.
Scrapes YouTube India's official Trending / Most Popular videos with >= 1,000,000 views
and combines with Google Trends India for maximum viral traction.
"""

import os
import sys
import re
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from models.news_models import NewsArticle
from utils.logger import logger
from services.youtube_upload_service import get_authenticated_service

MIN_VIRAL_VIEWS = 1_000_000

# High-interest news/documentary/viral categories on YouTube
PREFERRED_CATEGORIES = {
    "25": "News & Politics",
    "17": "Sports",
    "28": "Science & Technology",
    "24": "Entertainment",
    "27": "Education",
    "22": "People & Blogs"
}

def parse_views_count(view_val: Any) -> int:
    """Extracts integer view count from string or int."""
    if isinstance(view_val, int):
        return view_val
    if not view_val:
        return 0
    s = str(view_val).lower().replace(',', '').replace('views', '').replace('view', '').strip()
    try:
        if 'm' in s:
            return int(float(s.replace('m', '').strip()) * 1_000_000)
        elif 'k' in s:
            return int(float(s.replace('k', '').strip()) * 1_000)
        elif 'lakh' in s or 'lac' in s:
            return int(float(s.replace('lakh', '').replace('lac', '').strip()) * 100_000)
        elif 'crore' in s or 'cr' in s:
            return int(float(s.replace('crore', '').replace('cr', '').strip()) * 10_000_000)
        else:
            digits = re.sub(r'[^\d]', '', s)
            return int(digits) if digits else 0
    except Exception:
        return 0


def fetch_youtube_viral_videos(min_views: int = MIN_VIRAL_VIEWS, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Fetches trending videos directly from YouTube Data API (India region)
    filtering strictly for >= 1,000,000 views.
    """
    viral_videos = []
    try:
        srv = get_authenticated_service()
        # Query mostPopular videos for India
        res = srv.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode="IN",
            maxResults=max_results
        ).execute()

        items = res.get("items", [])
        logger.info(f"🔥 [Viral Service] Fetched {len(items)} popular videos from YouTube India API.")

        for item in items:
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            views = int(stats.get("viewCount", 0))
            if views < min_views:
                continue

            title = snippet.get("title", "").strip()
            cat_id = snippet.get("categoryId", "")
            channel = snippet.get("channelTitle", "").strip()
            desc = snippet.get("description", "").strip()
            tags = snippet.get("tags", [])
            vid_id = item.get("id", "")
            thumb_url = snippet.get("thumbnails", {}).get("high", {}).get("url", "")
            published_at = snippet.get("publishedAt", "")

            # Category mapping
            category_name = PREFERRED_CATEGORIES.get(cat_id, "Trending")

            viral_videos.append({
                "video_id": vid_id,
                "title": title,
                "views": views,
                "channel": channel,
                "category": category_name,
                "category_id": cat_id,
                "description": desc[:600],
                "tags": tags[:8],
                "thumbnail_url": thumb_url,
                "published_at": published_at,
                "source": "YouTube Trending"
            })

        logger.info(f"🚀 [Viral Service] Found {len(viral_videos)} videos with >= {min_views:,} views on YouTube.")
    except Exception as e:
        logger.error(f"❌ [Viral Service] Error querying YouTube API: {e}")

    return viral_videos


def fetch_google_trends_india() -> List[Dict[str, Any]]:
    """
    Scrapes Google Trends Daily RSS for India (geo=IN)
    extracts high-velocity trending keywords and traffic counts.
    """
    trends = []
    url = "https://trends.google.com/trending/rss?geo=IN"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        req = urllib.request.Request(url, headers=headers)
        data = urllib.request.urlopen(req, timeout=12).read()
        root = ET.fromstring(data)
        items = root.findall(".//item")
        
        for item in items:
            title_elem = item.find("title")
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
            
            traffic_elem = item.find("{https://trends.google.com/trending/rss}approx_traffic")
            traffic_text = traffic_elem.text.strip() if traffic_elem is not None and traffic_elem.text else "50K+"
            traffic_num = parse_views_count(traffic_text)
            
            desc_elem = item.find("description")
            desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""
            
            link_elem = item.find("link")
            link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
            
            news_items = item.findall("{https://trends.google.com/trending/rss}news_item")
            news_snippets = []
            img_url = ""
            for ni in news_items[:3]:
                nt = ni.find("{https://trends.google.com/trending/rss}news_item_title")
                ns = ni.find("{https://trends.google.com/trending/rss}news_item_snippet")
                nu = ni.find("{https://trends.google.com/trending/rss}news_item_url")
                npic = ni.find("{https://trends.google.com/trending/rss}news_item_picture")
                if nt is not None and nt.text:
                    news_snippets.append(nt.text)
                if npic is not None and npic.text and not img_url:
                    img_url = npic.text

            trends.append({
                "keyword": title,
                "title": f"Viral Trend: {title.title()} - {' | '.join(news_snippets[:2]) if news_snippets else desc}",
                "views": traffic_num,
                "view_text": traffic_text,
                "description": desc or " ".join(news_snippets),
                "link": link,
                "image_url": img_url,
                "category": "Trending News",
                "source": "Google Trends India"
            })

        logger.info(f"📈 [Viral Service] Found {len(trends)} trending topics on Google Trends India.")
    except Exception as e:
        logger.warning(f"⚠️ [Viral Service] Google Trends fetch failed: {e}")

    return trends


def get_top_viral_stories(min_views: int = MIN_VIRAL_VIEWS, limit: int = 15) -> List[NewsArticle]:
    """
    Main aggregator: returns ranked NewsArticle objects for viral topics
    guaranteed to have massive audience traction (>=1M views or top trending).
    """
    yt_videos = fetch_youtube_viral_videos(min_views=min_views)
    g_trends = fetch_google_trends_india()

    articles: List[NewsArticle] = []

    # 1. Convert YouTube viral videos into NewsArticle objects
    for v in yt_videos:
        # Clean title from clickbait fluff like [HINDI], #shorts, etc.
        clean_title = re.sub(r'\[.*?\]|\(.*?\)|#\w+', '', v["title"]).strip()
        if len(clean_title) < 10:
            clean_title = v["title"]

        summary = (
            f"Viral topic with {v['views']:,} views on YouTube trending. "
            f"Channel: {v['channel']}. {v['description']}"
        )

        article = NewsArticle(
            title=clean_title,
            link=f"https://www.youtube.com/watch?v={v['video_id']}",
            summary=summary,
            category=v["category"],
            published_at=v.get("published_at") or datetime.now(timezone.utc).isoformat(),
            trending_score=float(v["views"]) / 100_000.0,
            is_breaking=True,
            image_url=v["thumbnail_url"]
        )
        articles.append(article)

    # 2. Add high-traffic Google Trends
    for gt in g_trends:
        article = NewsArticle(
            title=gt["title"][:120],
            link=gt["link"] or "https://trends.google.com",
            summary=gt["description"][:500] if gt["description"] else f"Viral search topic {gt['keyword']}",
            category=gt["category"],
            published_at=datetime.now(timezone.utc).isoformat(),
            trending_score=float(gt["views"]) / 10_000.0,
            is_breaking=True,
            image_url=gt.get("image_url", "")
        )
        articles.append(article)

    # Sort descending by viral traction
    articles.sort(key=lambda x: getattr(x, "trending_score", 0.0), reverse=True)
    return articles[:limit]
