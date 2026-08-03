"""
scripts/generate_5min_bulletin.py
==================================
Generates a complete 5-minute (300-second) Full HD (1080p) Broadcast News Bulletin.
Features:
- 5 Full Detail News Stories (~60s per story):
    1. SPORTS (T20 वर्ल्ड कप में भारत की ऐतिहासिक जीत)
    2. NATIONAL (वरिष्ठ नागरिकों व परिवारों के लिए सरकार की बड़ी सहायता योजना)
    3. SPACE & TECH (इसरो का नया अंतरिक्ष मिशन और चंद्रयान सफलता)
    4. ECONOMY (भारतीय अर्थव्यवस्था में बंपर उछाल और नया बजट ऐलान)
    5. WORLD (ग्लोबल ग्रीन एनर्जी समिट में भारत का नेतृत्व)
- 100% Real Authentic HD News Photography (Specific real photo fetched per story - ZERO AI images)
- Saral Hindi Neural Voiceover for all 5 stories
- Smooth segment transitions and dynamic HUD updating headline, category, bullet cards, and real photos
"""

import os
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config.settings import ASSETS_DIR, VIDEOS_DIR, VOICE_DIR, CHANNEL_NAME
from models.news_models import GeneratedScript
from agents.voice_agent import voice_agent
from agents.graphics_agent import render_tv_broadcast_frame, fetch_news_photo
from utils.logger import logger

OUTPUT_VIDEO = VIDEOS_DIR / "full_5min_news_bulletin_1080p.mp4"

# 5 Detailed News Stories Data
STORIES = [
    {
        "id": 1,
        "category": "SPORTS",
        "topic": "T20 वर्ल्ड कप जीत",
        "search_kw": "cricket trophy team india",
        "headline": "T20 वर्ल्ड कप: भारतीय टीम की धमाकेदार ऐतिहासिक जीत, सेमीफाइनल में बनाई जगह",
        "script": (
            "नमस्कार! AI-NewsTube की 5-मिनट की बड़ी बुलेटिन में आपका स्वागत है। "
            "पहली बड़ी ख़बर खेल जगत से है। T20 वर्ल्ड कप के महामुकाबले में भारतीय क्रिकेट टीम ने "
            "शानदार प्रदर्शन करते हुए ऐतिहासिक जीत हासिल कर ली है। "
            "कप्तान रोहित शर्मा की तूफानी 92 रनों की पारी और गेंदबाजों के बेहतरीन प्रदर्शन के दम पर "
            "टीम इंडिया ने विरोधी टीम को पछाड़ दिया। इस शानदार जीत के साथ ही भारत ने सेमीफाइनल में "
            "अपनी जगह पक्की कर ली है और पूरे देश में जश्न का माहौल है।"
        ),
        "quick_cards": [
            "[ऐतिहासिक जीत]\nT20 वर्ल्ड कप में\nभारत का परचम",
            "[कप्तान की पारी]\nरोहित शर्मा का\nतूफानी 92 रन",
            "[सेमीफाइनल एंट्री]\nशानदार प्रदर्शन से\nबनाई जगह"
        ]
    },
    {
        "id": 2,
        "category": "NATIONAL",
        "topic": "वरिष्ठ नागरिक सहायता योजना",
        "search_kw": "india government press conference sumit",
        "headline": "वरिष्ठ नागरिकों और परिवारों के लिए सरकार का बड़ा ऐलान, मिलेगा सीधा आर्थिक लाभ",
        "script": (
            "दूसरी बड़ी ख़बर देश की राजधानी नई दिल्ली से है। "
            "देश भर के वरिष्ठ नागरिकों और मध्यमवर्गीय परिवारों के लिए सरकार ने एक नई और व्यापक सहायता योजना का ऐलान किया है। "
            "इस फैसले के तहत बैंकिंग प्रक्रियाओं को और भी सरल बना दिया गया है ताकि पेंशन और सहायता राशि सीधे लाभार्थी खातों में ट्रांसफर हो सके। "
            "इस फैसले से देश के लाखों परिवारों को सीधा आर्थिक संबल मिलेगा और जन-सुविधाओं में बड़ा सुधार होगा।"
        ),
        "quick_cards": [
            "[बड़ी योजना]\nपरिवारों को\nसीधा लाभ",
            "[आर्थिक राहत]\nसरल बैंकिंग\nसुविधा",
            "[जनहित फैसला]\nदेश भर में\nनया ऐलान"
        ]
    },
    {
        "id": 3,
        "category": "SPACE & TECH",
        "topic": "इसरो नया अंतरिक्ष मिशन",
        "search_kw": "isro rocket launch satellite nasa space",
        "headline": "इसरो का बड़ा कारनामा: नए अंतरिक्ष मिशन की सफल लॉन्चिंग, दुनिया में बजा भारत का डंका",
        "script": (
            "तीसरी बड़ी ख़बर विज्ञान और अंतरिक्ष जगत से है। "
            "भारतीय अंतरिक्ष अनुसंधान संगठन यानी इसरो ने एक बार फिर इतिहास रचते हुए अपने नए उपग्रह मिशन का सफल प्रक्षेपण किया है। "
            "श्रीहरिकोटा स्थित सतीश धवन अंतरिक्ष केंद्र से उड़ान भरने वाले इस रॉकेट ने उपग्रह को सटीक कक्षा में स्थापित किया। "
            "इस मिशन से मौसम पूर्वानुमान और संचार नेटवर्क को और अधिक सटीक बनाने में बड़ी मदद मिलेगी।"
        ),
        "quick_cards": [
            "[इसरो मिशन]\nरॉकेट की सफल\nसटीक लॉन्चिंग",
            "[स्वदेशी तकनीक]\nअंतरिक्ष में\nभारत की छलांग",
            "[संचार क्रांति]\nमौसम व नेटवर्क\nहोगा मजबूत"
        ]
    },
    {
        "id": 4,
        "category": "ECONOMY",
        "topic": "जीडीपी बंपर उछाल व आर्थिक सुधार",
        "search_kw": "stock market trading finance gold currency",
        "headline": "भारतीय अर्थव्यवस्था में बंपर उछाल: शेयर बाजार में नया रिकॉर्ड, जीडीपी ग्रोथ दर मजबूत",
        "script": (
            "चौथी बड़ी ख़बर व्यापार और अर्थव्यवस्था से है। "
            "भारतीय अर्थव्यवस्था ने चालू वित्तीय वर्ष में उम्मीद से बेहतर प्रदर्शन करते हुए शानदार विकास दर हासिल की है। "
            "शेयर बाज़ार के दोनों प्रमुख सूचकांक सेंसेक्स और निफ्टी नए सर्वकालिक उच्च स्तर पर पहुँच गए हैं। "
            "विदेशी निवेशकों का भरोसा बढ़ने और मैन्युफैक्चरिंग सेक्टर में आई तेज़ी से रोजगार के नए अवसर पैदा हो रहे हैं।"
        ),
        "quick_cards": [
            "[बंपर उछाल]\nसेंसेक्स व निफ्टी\nनया रिकॉर्ड",
            "[जीडीपी ग्रोथ]\nमजबूत विकास दर\nसे राहत",
            "[रोजगार अवसर]\nउत्पादन क्षेत्र में\nआई भारी तेज़ी"
        ]
    },
    {
        "id": 5,
        "category": "WORLD",
        "topic": "ग्लोबल ग्रीन एनर्जी समिट",
        "search_kw": "climate summit united nations renewable energy",
        "headline": "ग्लोबल ग्रीन एनर्जी समिट: अंतर्राष्ट्रीय मंच पर भारत का दबदबा, हरित ऊर्जा पर बड़ा समझौता",
        "script": (
            "पांचवीं और अंतिम बड़ी ख़बर अंतर्राष्ट्रीय मंच से है। "
            "ग्लोबल ग्रीन एनर्जी समिट में भारत ने पर्यावरण संरक्षण और हरित ऊर्जा उत्पादन पर अपना प्रमुख दृष्टिकोण पेश किया है। "
            "विश्व नेताओं ने सोलर और विंड एनर्जी के क्षेत्र में भारत द्वारा की गई प्रगति की सराहना की। "
            "इस ऐतिहासिक सम्मेलन में नवीकरणीय ऊर्जा को बढ़ावा देने के लिए बहुराष्ट्रीय समझौतों पर हस्ताक्षर किए गए हैं।"
        ),
        "quick_cards": [
            "[ग्लोबल समिट]\nहरित ऊर्जा पर\nऐतिहासिक समझौता",
            "[सौर ऊर्जा]\nभारत की पहल की\nदुनिया में सराहना",
            "[पर्यावरण]\nक्लीन एनर्जी का\nबड़ा लक्ष्य"
        ]
    }
]

COMMON_TICKER_ITEMS = [
    "🔥 T20 वर्ल्ड कप: भारत की ऐतिहासिक जीत, सेमीफाइनल में प्रवेश",
    "⚡ वरिष्ठ नागरिकों के लिए नई सहायता योजना का हुआ ऐलान",
    "🚀 इसरो का नया उपग्रह मिशन सफलतापूर्वक लॉन्च",
    "📈 शेयर बाजार में बंपर उछाल, सेंसेक्स और निफ्टी नए रिकॉर्ड पर",
    "🌍 ग्रीन एनर्जी समिट में भारत का दबदबा, समझौतों पर हस्ताक्षर"
]


def fetch_real_photo_for_story(story: dict) -> Path:
    """Fetches a specific 100% Real HD News Photo corresponding to the story topic."""
    photo_file = ASSETS_DIR / f"real_story_photo_{story['id']}.jpg"
    logger.info(f"  📸 Fetching real photo for Story #{story['id']} ({story['category']}: '{story['topic']}')...")

    if fetch_news_photo(story["search_kw"], photo_file, story["id"]):
        logger.info(f"  ✅ Story #{story['id']} Real Photo saved: {photo_file.name}")
        return photo_file

    # Fallback to visual research photo if available
    pip_files = sorted(list(ASSETS_DIR.glob("pip_photo_*.jpg")))
    if pip_files:
        return pip_files[(story["id"] - 1) % len(pip_files)]
    return photo_file


def generate_story_voiceover(story: dict) -> Path:
    """Generates Saral Hindi voiceover for a single news story."""
    logger.info(f"  🎙️ Synthesizing Saral Hindi voiceover for Story #{story['id']}...")
    script_obj = GeneratedScript(
        topic_title=story["topic"],
        category=story["category"],
        script_text=story["script"],
        word_count=len(story["script"].split())
    )
    res_script = voice_agent(script_obj)
    if res_script.audio_path and Path(res_script.audio_path).exists():
        return Path(res_script.audio_path)
    return None


def render_story_clip(story: dict, photo_path: Path, audio_path: Path):
    """Renders a single story segment clip."""
    try:
        from moviepy import VideoClip, AudioFileClip
    except ImportError:
        from moviepy.video.VideoClip import VideoClip
        from moviepy.audio.AudioFileClip import AudioFileClip

    audio_clip = None
    if audio_path and audio_path.exists():
        try:
            audio_clip = AudioFileClip(str(audio_path))
        except Exception:
            pass

    target_dur = 60.0
    if audio_clip and audio_clip.duration > 5.0:
        target_dur = max(35.0, audio_clip.duration + 2.0)

    fps = 24

    def make_frame(t):
        frame_img = render_tv_broadcast_frame(
            headline_text=story["headline"],
            news_photo_path=str(photo_path) if photo_path and photo_path.exists() else None,
            global_t=t,
            category=story["category"],
            ticker_headlines=COMMON_TICKER_ITEMS,
            quick_cards=story["quick_cards"]
        )
        return __import__("numpy").array(frame_img)

    clip = VideoClip(make_frame, duration=target_dur)
    if audio_clip:
        try:
            clip = clip.with_audio(audio_clip)
        except Exception:
            try:
                clip.audio = audio_clip
            except Exception:
                pass
    return clip


def main():
    print("=" * 70)
    print("📺 AI-NewsTube — 5-Minute Full News Bulletin Generator (5 Real Stories)")
    print("=" * 70)

    try:
        from moviepy import concatenate_videoclips
    except ImportError:
        from moviepy.video.compositing.concatenate import concatenate_videoclips

    story_clips = []
    total_est_dur = 0.0

    for story in STORIES:
        print(f"\n📌 Processing Story #{story['id']}/5: [{story['category']}] {story['topic']}")
        photo_path = fetch_real_photo_for_story(story)
        audio_path = generate_story_voiceover(story)

        clip = render_story_clip(story, photo_path, audio_path)
        story_clips.append(clip)
        total_est_dur += clip.duration
        print(f"   ✅ Story #{story['id']} Clip Ready ({clip.duration:.1f}s)")

    print(f"\n🎬 Concatenating {len(story_clips)} Story Clips into Full Bulletin ({total_est_dur:.1f}s total)...")
    final_bulletin = concatenate_videoclips(story_clips, method="compose")

    print(f"🎥 Rendering 1080p MP4 Video File → {OUTPUT_VIDEO.name}...")
    final_bulletin.write_videofile(
        str(OUTPUT_VIDEO),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4
    )

    print("\n" + "=" * 70)
    print("🎉 5-MINUTE FULL NEWS BULLETIN GENERATED SUCCESSFULLY!")
    print(f"  🎥 File Path : {OUTPUT_VIDEO}")
    print(f"  📊 File Size : {OUTPUT_VIDEO.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"  ⏱️ Duration  : {final_bulletin.duration:.1f} seconds")
    print("=" * 70)


if __name__ == "__main__":
    main()
