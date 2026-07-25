import random

from config.settings import CHANNEL_NAME, OWNER, VERSION
from agents.news_hunter import news_hunter
from agents.script_writer import script_writer


def ceo_agent():
    print("=" * 50)
    print("🤖 CEO AGENT")
    print("=" * 50)

    print(f"Channel : {CHANNEL_NAME}")
    print(f"Owner   : {OWNER}")
    print(f"Version : {VERSION}")

    print("\n📢 CEO: News Hunter, find today's trending topics!\n")

    news_items = news_hunter()

    # Pick a random item across ALL categories, so the channel isn't
    # stuck covering only one type of news every run.
    top_news = random.choice(news_items)

    print("\n🎯 CEO Selected Topic:")
    print(f"[{top_news['category']}] {top_news['title']}")

    print("\n✅ CEO: Sending topic to Script Writer...\n")

    script = script_writer(top_news)

    print("\n📄 Generated Script:\n")
    print(script)

    print("\n🎉 CEO: Work Completed Successfully!")


if __name__ == "__main__":
    ceo_agent()
