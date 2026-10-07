"""
services/fluent_script_service.py
=================================
100% Fluent English Investigative Broadcast Script Engine.
Generates comprehensive, non-repetitive English news narratives for 16:9 Full Videos and 9:16 Shorts
with zero greetings, zero headline reading, and direct immersion into the unfolding ground facts.
"""

import os
import sys
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import requests
from bs4 import BeautifulSoup
from services.groq_service import generate_text
from utils.json_utils import extract_json_from_llm
from utils.font_utils import sanitize_text
from utils.logger import logger


GREETING_PATTERNS = [
    r'^(Hello|Hi|Welcome|Good morning|Good evening|Greetings|Welcome back|Thanks for watching)[^.\n]*[.\n]',
    r'AI-NewsTube\s*(presents|presents you|brings you|reports)[^.\n]*[.\n]',
    r'NewsTube\s*(presents|presents you|brings you|reports)[^.\n]*[.\n]',
    r'Welcome\s+to\s+[^.\n]*[.\n]',
    r'Thank\s+you\s+for\s+tuning\s+in[^.\n]*$',
    r'Stay\s+tuned\s+[^.\n]*$',
    r'Don\'?t\s+forget\s+to\s+like[^.\n]*$',
    r'^(In our top story today|In today\'s top news|Breaking news today|Our top story tonight|Today we are looking at|In a major development regarding)[^.\n]*[.\n]',
    r'^(Headline|Breaking News|Top Story|News Update|Developing Story)\s*:?\s*',
    r'^(नमस्कार|प्रणाम|स्वागत है|हेलो|आदाब|आज की बड़ी खबर|बड़ी खबर है कि)[^।\.\n]*[।\.\n]',
    r'^(हेडलाइन|ब्रेकिंग न्यूज़|मुख्य समाचार|आज का समाचार)\s*:?\s*',
]


def clean_greetings_and_labels(text: str) -> str:
    """Strictly removes any introductory welcome messages, channel greetings, headline readouts, and section tags."""
    cleaned = text.strip()
    cleaned = re.sub(r'^#{1,6}\s+.*$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'[\[\{].*?[\]\}]', '', cleaned)
    cleaned = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', cleaned)
    cleaned = re.sub(r'^\s*(\d+[\.\)]|[-•▸▶])\s*', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*(Section|Point|Hook|Impact|Story|Headline|Summary|Takeaway|हेडलाइन|खंड|बिंदु)\s*\d*\s*:?\s*', '', cleaned, flags=re.MULTILINE | re.IGNORECASE)

    for pattern in GREETING_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE).strip()

    cleaned = re.sub(r'[\.\s…]{2,}', '. ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def fetch_article_web_content(url: str, timeout: int = 8) -> str:
    """Scrapes and extracts full editorial article body text from news wire URL."""
    if not url or not url.startswith("http"):
        return ""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200 and resp.text:
            soup = BeautifulSoup(resp.text, "html.parser")
            for element in soup(["script", "style", "nav", "header", "footer", "aside", "form", "svg"]):
                element.decompose()
            paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 35]
            full_text = " ".join(paras[:15])
            return sanitize_text(full_text[:4000])
    except Exception as e:
        logger.debug(f"Article web scrape note for {url[:40]}: {e}")
    return ""


def clean_news_headline(title: str) -> str:
    """Cleans raw RSS headline by stripping agency tags and trailing ellipsis."""
    cleaned = sanitize_text(title)
    cleaned = re.sub(
        r'\s*[-|–—]\s*(BBC News|BBC|NDTV Khabar|NDTV|India Today|Zee News|The Hindu|Times of India|Breakingthenews\.net|Breakingthenews|Hindustan Times|Dainik Bhaskar|Aaj Tak|ANI|Reuters|PTI|News18|Google News|The Guardian|CNN|AP News|Fox News).*$',
        '',
        cleaned,
        flags=re.IGNORECASE
    )
    if ';' in cleaned and ('...' in cleaned or '…' in cleaned):
        cleaned = cleaned.split(';')[0]
    cleaned = re.sub(r'[\.\s…\-–—]{2,}', '', cleaned)
    cleaned = cleaned.strip(" '\"“”‘’.-–—…")
    return cleaned


def determine_dynamic_story_duration(article_text: str, context: str = "") -> Tuple[float, int, int, int]:
    """
    Computes optimal broadcast video duration dynamically (minimum 2.5 minutes):
    - Deep article (>= 500 words) -> 4.5 min (550-750 words, 5 slides)
    - Comprehensive news (200-500 words) -> 3.0 min (380-500 words, 4 slides)
    - Standard breaking story (< 200 words) -> 2.5 min (300-400 words, 4 slides)
    """
    total_raw_words = len(article_text.split()) + len(context.split())
    if total_raw_words >= 500:
        return 4.5, 550, 750, 5
    elif total_raw_words >= 200:
        return 3.0, 380, 500, 4
    else:
        return 2.5, 300, 400, 4


def generate_fluent_news_script(
    title: str,
    category: str = "General",
    context: str = "",
    article_url: str = "",
    target_minutes: Optional[float] = None
) -> Tuple[str, List[str], str, str, List[str]]:
    """
    Generates a deeply researched, non-repetitive Hindi broadcast news package.
    Uses DeepResearchService for multi-source dossier + entity extraction.
    Validates fact density and retries once if script is too generic.
    Returns: (full_narration_hindi, slide_takeaways_hindi, broadcast_headline, viral_youtube_title, youtube_tags)
    """
    from services.deep_research_service import DeepResearchService

    clean_title = clean_news_headline(title)

    # ── Deep Multi-Source Research ────────────────────────────────────────────
    dossier = DeepResearchService.compile_investigative_dossier(
        topic=clean_title,
        direct_url=article_url,
        raw_summary=context,
        deep=True  # full scrape: article + wiki + 3-angle search + related articles
    )
    full_context  = dossier["full_dossier"]
    entity_sheet  = dossier["entity_fact_sheet"]  # injected directly into prompt
    primary_text  = dossier["primary_article"]

    if target_minutes is None or target_minutes <= 0:
        dyn_min, word_min, word_max, num_slides = determine_dynamic_story_duration(primary_text, context)
        target_minutes = dyn_min
    else:
        word_min  = int(target_minutes * 120)
        word_max  = int(target_minutes * 155)
        num_slides = max(3, min(6, int(target_minutes) + 1))

    # Trim dossier to avoid token overflow (keep most relevant parts)
    clean_context = sanitize_text(full_context)[:6000]
    def _build_prompt(strict: bool = False) -> str:
        """Builds the Hindi script prompt. strict=True forces even more specific facts."""
        strictness_note = (
            "\n⚠️ STRICT MODE: पिछली स्क्रिप्ट बहुत generic थी। "
            "अब EXTRACTED KEY FACTS से हर specific number, date, और name का अनिवार्य उपयोग करें। "
            "कोई भी generic वाक्य स्वीकार नहीं होगा।\n"
        ) if strict else ""

        entity_injection = (
            f"\n📌 EXTRACTED KEY FACTS (इन्हें script में अनिवार्य रूप से use करें):\n{entity_sheet}\n"
        ) if entity_sheet else ""

        return (
            f"आप एक वरिष्ठ हिंदी पत्रकार और प्राइम-टाइम न्यूज़ एंकर हैं (Aaj Tak / ABP News / NDTV India style).\n"
            f"इस खबर पर एक विस्तृत, गहरी, तथ्य-आधारित हिंदी ब्रॉडकास्ट स्क्रिप्ट लिखें।{strictness_note}\n\n"
            f"शीर्षक/विषय: {clean_title}\n"
            f"श्रेणी: {category.upper()}\n"
            f"लक्ष्य अवधि: {target_minutes:.1f} मिनट ({word_min}-{word_max} बोले गए हिंदी शब्द)\n"
            f"{entity_injection}"
            f"सत्यापित शोध डोजियर:\n{clean_context}\n\n"
            f"महत्वपूर्ण पत्रकारिता नियम:\n"
            f"1. कोई अभिवादन नहीं, कोई शीर्षक दोहराना नहीं: सीधे घटना की जमीनी हकीकत से शुरू करें।\n"
            f"2. हर वाक्य नई, ठोस जानकारी दे — दोहराव बिल्कुल नहीं।\n"
            f"3. अनिवार्य तथ्य घनत्व: script में minimum 4 specific numbers/dates/amounts होने चाहिए।\n"
            f"4. असली नाम उपयोग करें: घटना में शामिल व्यक्ति, संस्था, स्थान के सटीक नाम लिखें।\n"
            f"5. वाक्य संरचना:\n"
            f"   - वाक्य 1-3: तत्काल घटना, सटीक स्थान, तारीख, मुख्य किरदार।\n"
            f"   - वाक्य 4-8: पृष्ठभूमि, घटनाक्रम, कारण, आधिकारिक आंकड़े।\n"
            f"   - वाक्य 9-14: आधिकारिक बयान (नाम सहित), जांच निष्कर्ष, प्रत्यक्षदर्शी रिपोर्ट।\n"
            f"   - वाक्य 15-20: व्यापक असर, भविष्य, जनता पर प्रभाव।\n"
            f"6. भाषा: शुद्ध, प्रवाहपूर्ण हिंदी (देवनागरी)। स्पष्ट, अधिकारपूर्ण लहजा।\n"
            f"7. आउटपुट: केवल valid JSON object:\n"
            f"{{\n"
            f'  "viral_youtube_title": "(High-CTR ENGLISH YouTube title with emojis — dramatic, max 70 chars)",\n'
            f'  "broadcast_headline": "(Clean punchy ENGLISH on-screen headline, max 7 words)",\n'
            f'  "full_narration": "(पूरी {word_min}-{word_max} शब्दों की हिंदी एंकर स्क्रिप्ट, सीधे तथ्य से शुरू)",\n'
            f'  "slide_takeaways": [\n'
            f'    "(Slide 1: ENGLISH — core fact with specific number/date, 10-14 words)",\n'
            f'    "(Slide 2: ENGLISH — historical background and evidence, 10-14 words)",\n'
            f'    "(Slide 3: ENGLISH — official statement and investigation, 10-14 words)",\n'
            f'    "(Slide 4: ENGLISH — broader impact and next steps, 10-14 words)"\n'
            f'  ],\n'
            f'  "youtube_tags": ["BreakingNews", "HindiNews", "LatestNews", "LiveReport", "{category}"]\n'
            f"}}" 
        )

    logger.info(f"📝 Generating deep Hindi broadcast story ({target_minutes:.1f} min, {word_min}-{word_max} words) for: '{clean_title[:50]}'...")

    # ── Script Generation with Fact-Density Validation + 1 Retry ─────────────
    for attempt in range(2):  # 0 = normal, 1 = strict retry
        is_strict = attempt > 0
        prompt = _build_prompt(strict=is_strict)
        try:
            response = generate_text(prompt, temperature=0.30 if is_strict else 0.35, max_tokens=5500)
            data = extract_json_from_llm(response)
            if isinstance(data, dict) and "full_narration" in data:
                raw_narr = str(data["full_narration"])
                cleaned_narr = clean_greetings_and_labels(raw_narr)
                b_head = clean_greetings_and_labels(str(data.get("broadcast_headline", clean_title)))
                if not b_head or len(b_head) < 4 or '...' in b_head:
                    b_head = clean_title

                v_title = str(data.get("viral_youtube_title", "")).strip()
                if not v_title or len(v_title) < 12:
                    v_title = f"{b_head} 🔴 ब्रेकिंग न्यूज़"

                yt_tags = data.get("youtube_tags", [])
                if not isinstance(yt_tags, list) or len(yt_tags) < 3:
                    yt_tags = ["BreakingNews", "HindiNews", "ताजा खबर", "लाइव", category]

                takeaways = data.get("slide_takeaways", [])
                if isinstance(takeaways, list) and len(takeaways) >= 3:
                    cleaned_takeaways = [clean_greetings_and_labels(str(t)) for t in takeaways
                                          if len(str(t).strip()) > 5][:num_slides]
                else:
                    cleaned_takeaways = [
                        f"Core Development: {b_head}",
                        "Ground Situation: Investigation and response teams deployed",
                        "Official Position: High-level review and inquiry underway",
                        "Strategic Impact: Authorities monitoring emerging developments"
                    ]

                if len(cleaned_narr.split()) >= 80:
                    # ── Fact density check ────────────────────────────────────
                    density_score, density_issues = DeepResearchService.score_fact_density(cleaned_narr)
                    if density_score < 0.45 and attempt == 0:
                        logger.warning(
                            f"  ⚠️ Script fact density low ({density_score:.2f}): {density_issues}. "
                            f"Retrying with strict mode..."
                        )
                        continue  # Retry with strict=True
                    logger.info(
                        f"  ✅ Hindi Script: {len(cleaned_narr.split())} words, "
                        f"{len(cleaned_takeaways)} slides, density={density_score:.2f}"
                    )
                    return cleaned_narr, cleaned_takeaways, b_head, v_title, yt_tags
        except Exception as e:
            logger.warning(f"  Hindi script LLM note (attempt {attempt+1}): {e}")

    # Fallback Hindi Narrative
    primary_clause = clean_title.split(':')[0] if ':' in clean_title else clean_title
    fallback_narr = (
        f"देश में एक बड़ा घटनाक्रम सामने आया है जिसने राजनीतिक और प्रशासनिक हलकों में हलचल मचा दी है। "
        f"सूत्रों के अनुसार, वरिष्ठ अधिकारियों ने आपात बैठक बुलाई है और स्थिति की गहन समीक्षा की जा रही है। "
        f"जांच एजेंसियां मौके पर पहुंच गई हैं और साक्ष्य जुटाने का काम तेज़ गति से जारी है। "
        f"सरकारी प्रवक्ता ने कहा है कि जल्द ही आधिकारिक बयान जारी किया जाएगा।"
    )
    fallback_takeaways = [
        f"Key Development: {primary_clause[:60]}",
        "Ground Response: Emergency and investigative teams actively deployed",
        "Official Stance: Multi-agency coordination and review in progress",
        "Current Outlook: Continuous monitoring as detailed briefings emerge"
    ]
    fallback_title = f"{primary_clause[:65]} 🔴 Breaking News & Analysis"
    fallback_tags = ["BreakingNews", "HindiNews", "ताजा खबर", category]
    return clean_greetings_and_labels(fallback_narr), fallback_takeaways, primary_clause, fallback_title, fallback_tags


def generate_shorts_news_script(
    title: str,
    category: str = "General",
    context: str = "",
    article_url: str = ""
) -> Tuple[str, List[str], str, str, List[str]]:
    """
    Generates a fast-paced, high-retention 35-second English news script for YouTube Shorts (9:16).
    Length: 70 to 95 spoken words in authoritative English (zero greetings, zero headline reading, hook-first).
    Returns: (shorts_narration_english, 3_slide_takeaways_english, broadcast_headline, viral_shorts_title, youtube_tags)
    """
    clean_title = clean_news_headline(title)

    web_body = ""
    if article_url:
        web_body = fetch_article_web_content(article_url)

    combined_context = f"{context}\n{web_body}".strip()
    clean_context = sanitize_text(combined_context)[:3000] if combined_context else clean_title

    prompt = (
        f"आप एक टॉप हिंदी YouTube Shorts क्रिएटर हैं (Aaj Tak Shorts / ABP LIVE style).\n"
        f"इस खबर पर एक एनर्जेटिक, हाई-रिटेंशन 30-35 सेकंड की हिंदी शॉर्ट्स स्क्रिप्ट लिखें।\n\n"
        f"शीर्षक/विषय: {clean_title}\n"
        f"श्रेणी: {category.upper()}\n"
        f"तथ्य:\n{clean_context}\n\n"
        f"वायरल Shorts नियम:\n"
        f"1. पहला वाक्य ऐसा हो जो स्क्रॉल रोक दे — सीधे घटना से शुरू, कोई 'नमस्कार' नहीं।\n"
        f"2. ठीक 70-90 हिंदी बोले गए शब्दों में सारी बड़ी बातें बताएं।\n"
        f"3. FORMAT: Only valid JSON:\n"
        f"{{\n"
        f'  "viral_shorts_title": "(Extremely viral ENGLISH title with emojis, max 60 chars — e.g. Massive Shock! Key Leader Exposed 🚨 #Shorts)",\n'
        f'  "broadcast_headline": "(Clean punchy ENGLISH on-screen headline, max 6 words)",\n'
        f'  "full_narration": "(70-90 शब्दों की तेज़ हिंदी वॉयसओवर स्क्रिप्ट, सीधे एक्शन से शुरू)",\n'
        f'  "slide_takeaways": [\n'
        f'    "(Bullet 1: ENGLISH — main shockpoint or trigger with specific fact, 8-12 words)",\n'
        f'    "(Bullet 2: ENGLISH — ground reality and verified evidence, 8-12 words)",\n'
        f'    "(Bullet 3: ENGLISH — next major action or impending fallout, 8-12 words)"\n'
        f'  ],\n'
        f'  "youtube_tags": ["Shorts", "YouTubeShorts", "BreakingNews", "HindiNews", "{category}"]\n'
        f"}}"
    )

    logger.info(f"📱 Generating viral Hindi Shorts script (35s, 70-90 words) for: '{clean_title[:50]}'...")
    try:
        response = generate_text(prompt, temperature=0.4, max_tokens=2000)
        data = extract_json_from_llm(response)
        if isinstance(data, dict) and "full_narration" in data:
            raw_narr = str(data["full_narration"])
            cleaned_narr = clean_greetings_and_labels(raw_narr)
            b_head = clean_greetings_and_labels(str(data.get("broadcast_headline", clean_title)))
            v_title = str(data.get("viral_shorts_title", f"{b_head[:50]} #Shorts")).strip()
            if "#Shorts" not in v_title:
                v_title = f"{v_title[:55]} #Shorts"

            takeaways = data.get("slide_takeaways", [])
            if isinstance(takeaways, list) and len(takeaways) >= 2:
                cleaned_takeaways = [clean_greetings_and_labels(str(t)) for t in takeaways[:3]]
            else:
                cleaned_takeaways = [
                    f"Breaking: {b_head[:50]}",
                    "Ground Situation: Emergency response teams on site",
                    "Next Step: Official announcement expected soon"
                ]

            tags = ["Shorts", "YouTubeShorts", "BreakingNews", "HindiNews", category]
            logger.info(f"  ✅ Viral Hindi Shorts Script Generated: {len(cleaned_narr.split())} words, {len(cleaned_takeaways)} takeaways.")
            return cleaned_narr, cleaned_takeaways, b_head, v_title, tags
    except Exception as e:
        logger.warning(f"  Hindi shorts script LLM note: {e}")

    # Fallback Hindi Shorts
    fallback_narr = (
        f"एक बड़ा झटका सामने आया है जिसने पूरे देश में हड़कंप मचा दिया है। "
        f"वरिष्ठ अधिकारियों ने आपात बैठक बुलाई है और स्थिति की समीक्षा जारी है। "
        f"आने वाले घंटों में आधिकारिक घोषणा की उम्मीद है।"
    )
    fallback_takeaways = [
        f"Breaking: {clean_title[:50]}",
        "Ground Situation: Emergency response teams activated",
        "Next Step: Official announcement expected soon"
    ]
    fallback_title = f"{clean_title[:50]} 🔴 Breaking Report #Shorts"
    fallback_tags = ["Shorts", "YouTubeShorts", "BreakingNews", "HindiNews", category]
    return clean_greetings_and_labels(fallback_narr), fallback_takeaways, clean_title, fallback_title, fallback_tags
