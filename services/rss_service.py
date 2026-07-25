import feedparser

# Google News topic-based feeds -> covers all major current-affairs categories.
# Change hl/gl/ceid if you want a different country/language edition.
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


def fetch_news(limit_per_category=5):
    """
    Fetches news items across ALL categories (not just tech), each item
    tagged with its category, title, link, and summary (for RAG context).
    """
    news = []
    seen = set()

    for category, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)

        count_for_category = 0
        for entry in feed.entries:
            if count_for_category >= limit_per_category:
                break

            title = entry.title.strip()

            if title in seen:
                continue
            seen.add(title)

            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary.strip()
            elif hasattr(entry, "description"):
                summary = entry.description.strip()

            news.append({
                "title": title,
                "link": entry.link,
                "summary": summary,
                "category": category
            })

            count_for_category += 1

    return news
