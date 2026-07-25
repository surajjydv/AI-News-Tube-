from services.scraper_service import get_article_context
from services.groq_service import generate_text


def build_prompt(title, context, category="General"):
    return f"""Tum ek popular Hindi YouTube News channel ke liye script writer ho.

Category: {category}
Topic: {title}

Yeh raha is khabar ka context (asli article se liya gaya):
\"\"\"
{context}
\"\"\"

Upar diye gaye context ke aadhar par, is khabar par ek accurate, engaging
YouTube script likho Hinglish (Hindi + English mix) mein. Rules:
- Sirf context mein diye gaye facts use karo, kuch bhi ghadna mat (no hallucination)
- Simple, conversational tone, jaise ek news anchor bol raha ho
- 150-200 words
- Start "Namaskar dosto!" se
- End mein Subscribe + Bell icon ka reminder do
- Kisi bhi tarah ka markdown ya heading mat do, sirf spoken script text do
"""


def script_writer(news_item):
    print("=" * 50)
    print("✍️ SCRIPT WRITER AGENT")
    print("=" * 50)

    title = news_item["title"]
    link = news_item.get("link", "")
    summary = news_item.get("summary", "")
    category = news_item.get("category", "General")

    print(f"\n📝 Writing script for: [{category}] {title}")
    print("🔎 Fetching article context for RAG...")

    context = get_article_context(link, fallback_summary=summary)

    if not context:
        context = title  # last-resort fallback so the prompt isn't empty

    prompt = build_prompt(title, context, category)

    script = generate_text(prompt)

    print("\n✅ Script Generated Successfully.")

    return script
