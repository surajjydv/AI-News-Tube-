from services.scraper_service import get_article_context
from services.groq_service import generate_text
from config.settings import CHANNEL_NAME
from models.news_models import NewsArticle, GeneratedScript
from utils.logger import logger


def build_prompt(title: str, context: str, category: str = "General", is_breaking: bool = False) -> str:
    breaking_prefix = "🚨 बड़ी खबर! " if is_breaking else ""
    return f"""आप एक आदरणीय हिंदी न्यूज़ एंकर हैं। {CHANNEL_NAME} के लिए ऐसी हिंदी न्यूज़ स्क्रिप्ट लिखें जो इतनी सरल, स्पष्ट और सहज हो कि 80 साल के बुजुर्ग दादाजी भी एक-एक बात आसानी से समझ सकें।

Category: {category}
Topic: {breaking_prefix}{title}

Article Context:
\"\"\"
{context}
\"\"\"

स्क्रिप्ट संरचना (MUST FOLLOW):
1. हुक (HOOK - 5 सेकंड): आसान भाषा में सबसे महत्वपूर्ण और ध्यान खींचने वाली बात।
2. समस्या (PROBLEM): मामला क्या है, इसे बेहद सरल शब्दों में समझाएं।
3. मुख्य समाचार (WHAT HAPPENED): आसान उदाहरणों और साफ़ हिंदी में मुख्य तथ्य दें।
4. प्रभाव (IMPACT): यह ख़बर हमारे आम जीवन और परिवार के लिए क्यों ज़रूरी है।
5. भविष्य (FUTURE): आगे क्या होगा या क्या ध्यान रखना चाहिए।
6. सब्सक्राइब अपील (CTA): {CHANNEL_NAME} चैनल को सब्सक्राइब करने का विनम्र अनुरोध।

अति आवश्यक नियम (CRITICAL RULES FOR ELDERLY ACCESSIBILITY):
- 100% शुद्ध देवनागरी हिंदी में लिखें।
- भाषा 'सरल और बोलचाल वाली हिंदी' (Saral Hindi) होनी चाहिए—कोई भी कठिन अंग्रेज़ी शब्द या भारी भरकम संस्कृत शब्द न इस्तेमाल करें।
- वाक्य छोटे, साफ़ और स्पष्ट रखें ताकि सुनने में कोई भ्रम न हो।
- कोई ब्रैकेट, हेडिंग या ब्रैकेट लेबल ([HOOK] आदि) न लिखें, केवल एंकर के बोलने का लगातार सहज हिंदी टेक्स्ट।
- शब्द सीमा: 180-240 शब्द।
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
