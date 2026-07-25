from services.rss_service import fetch_news


def news_hunter():
    print("=" * 50)
    print("📰 NEWS HUNTER AGENT")
    print("=" * 50)

    print("\n🌐 Fetching Real News (All Categories)...\n")

    news = fetch_news()

    for i, item in enumerate(news, start=1):
        print(f"{i}. [{item['category']}] {item['title']}")

    print(f"\n✅ News Hunter Ready — {len(news)} items across {len(set(n['category'] for n in news))} categories")

    return news
