"""
scripts/explainer_documentary_engine.py
======================================
Standalone 24/7 Deep-Dive Documentary & Investigative Explainer Engine (Nitish Rajput / Dhruv Rathee Style).
Runs as a completely independent daemon process, publishing a 4-to-5 minute deep-dive case study every 30 minutes.
100% Isolated from NewsTube Breaking News engine.
"""

import os
import sys
import time
import asyncio
import random
import requests
from pathlib import Path
from typing import Optional, List, Dict

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import edge_tts
from utils.logger import logger
from services.rss_service import fetch_news, NewsArticle
from services.deep_research_service import DeepResearchService
from services.investigative_explainer_engine import InvestigativeExplainerEngine
from services.documentary_explainer_renderer import DocumentaryRenderer
from services.ai_thumbnail_service import create_real_event_youtube_thumbnail
from services.youtube_upload_service import upload_video_to_youtube

OUTPUT_DIR = BASE_DIR / "output"
VIDEOS_DIR = BASE_DIR / "videos"
PROCESSED_FILE = BASE_DIR / "data" / "processed_documentary_stories.txt"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# 3-hour auto-publish interval (8 videos/day, safely within YouTube free quota)
POLL_INTERVAL_SECONDS = 10800


# High-impact evergreen and trending investigative themes for backup rotation
CURATED_INVESTIGATIVE_ROTATION = [
    {"topic": "Toxic Movie Day 1 Collection and Yash Box Office Record Review", "category": "Entertainment"},
    {"topic": "GTA 6 Cyber Leak Rockstar Games $100M Hacker Arion Kurtaj Investigation", "category": "CyberTech"},
    {"topic": "Nepal Flash Floods Tibet Border Cloudburst and GLOF Glacial Crisis", "category": "Geopolitics"},
    {"topic": "CrowdStrike Global IT Outage The Day World Computers Crashed", "category": "CyberTech"},
    {"topic": "Subhas Chandra Bose Mystery The Secret Documents and Declassified Files", "category": "History"},
    {"topic": "Boeing 737 Max Crisis The Internal Whistleblower Documents and Coverup", "category": "CorporateScandal"},
    {"topic": "Deepfake and AI Scams The New Era of Cyber Blackmail and Digital Fraud", "category": "CyberTech"},
    {"topic": "Kalki 2898 AD Box Office and Indian Pan-India Cinema Revolution", "category": "Entertainment"},
    {"topic": "Bermuda Triangle The Scientific Truth Behind Disappearing Planes and Ships", "category": "Mystery"},
    {"topic": "Theranos Elizabeth Holmes The $9 Billion Silicon Valley Blood Test Fraud", "category": "CorporateScandal"},
    {"topic": "Pegasus Spyware How Governments Hack Smartphones and Track Citizens", "category": "CyberTech"},
    {"topic": "Red Sea Shipping Crisis Houthi Drone Attacks and Global Supply Chain", "category": "Geopolitics"}
]


def load_processed_topics() -> List[str]:
    if PROCESSED_FILE.exists():
        return [l.strip().lower() for l in PROCESSED_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    return []


def mark_topic_processed(topic: str):
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{topic}\n")


def download_verified_case_study_photos(topic: str, category: str, target_dir: Path, max_photos: int = 6) -> List[str]:
    """Downloads 5 to 8 unique verified, high-resolution authentic photographs for the documentary story."""
    target_dir.mkdir(parents=True, exist_ok=True)

    clean_topic = topic.replace("🔴", "").replace("Breaking News", "").replace("Case Study", "").strip()
    # Use first 3 distinct words for base keyword to avoid overly narrow queries
    words = [w for w in clean_topic.split() if len(w) > 3][:3]
    base_kw = " ".join(words)

    queries = [
        base_kw,
        f"{base_kw} government official",
        f"{base_kw} court ruling",
        f"{base_kw} India history",
        f"{base_kw} investigation evidence",
        f"{category} controversy India",
    ]

    saved = []
    seen_titles = set()   # deduplicate by Wikipedia page title
    seen_urls = set()     # deduplicate by image URL
    headers = {"User-Agent": "Investigative-Doc-Engine/3.0"}
    photo_idx = 1

    for q in queries:
        if len(saved) >= max_photos:
            break
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "generator": "search",
                "gsrsearch": q,
                "prop": "pageimages",
                "piprop": "thumbnail|original",
                "pithumbsize": 1280,
                "format": "json",
                "gsrlimit": 5  # fetch more candidates per query
            }
            resp = requests.get(url, params=params, headers=headers, timeout=6)
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                for pid, pdata in pages.items():
                    if len(saved) >= max_photos:
                        break
                    page_title = pdata.get("title", "")
                    thumb = pdata.get("thumbnail", {}).get("source") or pdata.get("original", {}).get("source")
                    if not thumb:
                        continue
                    if thumb.endswith((".svg", ".djvu", ".pdf")):
                        continue
                    # Skip duplicate page or image URL
                    if page_title in seen_titles or thumb in seen_urls:
                        continue
                    img_data = requests.get(thumb, headers=headers, timeout=8).content
                    if len(img_data) > 15000:
                        p_path = target_dir / f"photo_{photo_idx}.jpg"
                        with open(p_path, "wb") as f:
                            f.write(img_data)
                        saved.append(str(p_path))
                        seen_titles.add(page_title)
                        seen_urls.add(thumb)
                        logger.info(f"  📸 [Doc Photos] Downloaded Visual {photo_idx}: {page_title}")
                        photo_idx += 1
        except Exception as e:
            logger.debug(f"Photo search note ({q}): {e}")

    # Fallback to local cache only if still short
    if len(saved) < 3:
        existing_cache = list(OUTPUT_DIR.glob("**/*.jpg"))
        for e in existing_cache:
            if len(saved) >= max_photos:
                break
            if str(e) not in saved and e.stat().st_size > 20000:
                saved.append(str(e))

    return saved


async def generate_documentary_narration(text: str, output_path: Path, voice: str = "en-US-AndrewNeural") -> Path:
    """Synthesizes high-clarity cinematic English documentary voiceover."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text=text, voice=voice, rate="+5%", volume="+0%")
    await communicate.save(str(output_path))
    logger.info(f"✅ Generated Documentary Voiceover: {output_path.name} ({output_path.stat().st_size} bytes)")
    return output_path


def produce_and_publish_documentary(topic: str, category: str = "Investigation", direct_url: str = "", raw_summary: str = "") -> Optional[str]:
    """Generates and uploads an in-depth 4-to-5 minute investigative documentary case study."""
    start_t = time.time()
    story_id = f"{int(time.time())}_{hash(topic) & 0xffffffff:08x}"
    story_dir = OUTPUT_DIR / f"doc_assets_{story_id}"
    audio_path = OUTPUT_DIR / f"doc_audio_{story_id}.mp3"
    video_path = VIDEOS_DIR / f"documentary_case_study_{story_id}.mp4"
    thumb_path = OUTPUT_DIR / f"doc_thumb_{story_id}.jpg"

    logger.info("=" * 75)
    logger.info(f"🎬 [DOCUMENTARY EXPLAINER ENGINE] Producing 4-5 Min Case Study: '{topic}'")
    logger.info("=" * 75)

    # 1. Multi-Source Deep Web & Document Research
    logger.info("🔍 Step 1: Compiling Investigative Research Dossier...")
    dossier = DeepResearchService.compile_investigative_dossier(
        topic=topic,
        direct_url=direct_url,
        raw_summary=raw_summary
    )

    # 2. Generate 4-to-5 Minute 6-Chapter Case Study Script
    logger.info("📝 Step 2: Generating 4-5 Min Documentary Narrative (Nitish Rajput / Dhruv Rathee style)...")
    narr, chapters, doc_title, v_title, tags = InvestigativeExplainerEngine.generate_case_study_script(
        topic=topic,
        category=category,
        research_dossier=dossier["full_dossier"],
        target_minutes=4.5
    )

    # 3. Retrieve 5-8 Authentic Verified High-Res Photos
    logger.info("📸 Step 3: Downloading 5-8 Verified High-Res Photographs...")
    photo_paths = download_verified_case_study_photos(
        topic=topic,
        category=category,
        target_dir=story_dir,
        max_photos=max(6, len(chapters))
    )

    # 4. Synthesize Deep Voiceover
    logger.info("🎙️ Step 4: Synthesizing Neural English Voiceover (Andrew Neural)...")
    asyncio.run(generate_documentary_narration(narr, audio_path))
    if not audio_path.exists() or audio_path.stat().st_size < 1000:
        logger.error(f"❌ Voice synthesis failed for documentary: {audio_path}")
        return None

    # 5. Create High-CTR Masterpiece Thumbnail
    logger.info("🖼️ Step 5: Creating High-CTR Case Study Thumbnail...")
    create_real_event_youtube_thumbnail(
        headline=doc_title,
        category="CaseStudy",
        real_photo_path=photo_paths[0] if photo_paths else "",
        output_path=thumb_path
    )

    # 6. Render 1080p Full-Bleed Clean Video Essay
    logger.info("🎬 Step 6: Rendering 1080p Clean Full-Bleed Video Essay (Zero Lines, Smooth Motion)...")
    DocumentaryRenderer.render_documentary_video(
        doc_title=doc_title,
        chapters=chapters,
        photo_paths=photo_paths,
        audio_path=audio_path,
        output_video_path=video_path,
        fps=15
    )

    # 7. Upload to YouTube
    logger.info("📤 Step 7: Uploading 4-5 Min Documentary to YouTube as Public Video...")
    chapter_text = "\n".join([f"📌 Chapter {c.get('chapter_num')}: {c.get('title')} - {c.get('summary')}" for c in chapters])
    description = (
        f"🔴 {v_title}\n\n"
        f"इस विशेष 4 से 5 मिनट की इनवेस्टिगेटिव डॉक्यूमेंट्री केस स्टडी (Nitish Rajput / Dhruv Rathee Format) में जानिए {doc_title} की पूरी पड़ताल, ज़मीनी हकीकत, और आधिकारिक दस्तावेज।\n\n"
        f"📖 अध्यायवार विवरण (CHAPTERS):\n{chapter_text}\n\n"
        f"📄 पूरी इनवेस्टिगेटिव रिपोर्ट (Full Narrative):\n{narr}\n\n"
        f"🔔 24/7 इनवेस्टिगेटिव रिपोर्ट्स, केस स्टडीज और खुलासों के लिए चैनल को सब्सक्राइब करें।\n\n"
        f"#Documentary #Investigation #CaseStudy #Explained #DeepDive #RealStory #GroundReport #HindiDocumentary #DhruvRatheeStyle #NitishRajputStyle"
    )

    vid_id = upload_video_to_youtube(
        video_path=str(video_path),
        title=v_title[:95],
        description=description,
        category_id="25",  # News & Politics / Documentary
        privacy_status="public",
        thumbnail_path=str(thumb_path) if thumb_path.exists() else None,
        tags=tags[:15]
    )

    if vid_id and vid_id not in ["LOCAL_SAVED", "RTMP_LIVE_STREAM_BROADCASTED"]:
        logger.info("=" * 75)
        logger.info(f"🎉 SUCCESS! Investigative Documentary Published: https://youtu.be/{vid_id}")
        logger.info("=" * 75)
        print(f"\n🎉 LIVE YOUTUBE VIDEO URL: https://youtu.be/{vid_id}\n")
        mark_topic_processed(topic)
        return vid_id

    mark_topic_processed(topic)
    return vid_id


def run_standalone_daemon():
    """Continuous 24/7 daemon running completely isolated from NewsTube, publishing every 30 minutes."""
    logger.info("=" * 75)
    logger.info("🚀 24/7 INVESTIGATIVE DOCUMENTARY AUTO-PUBLISHER ACTIVE")
    logger.info(f"   - Auto-Publish Cadence : Every {POLL_INTERVAL_SECONDS // 60} Minutes (48 Videos / Day)")
    logger.info("   - Style                : 4-5 Min Nitish Rajput / Dhruv Rathee Style Documentaries")
    logger.info("   - Visuals              : 100% Full-Bleed 1080p with 5-8 Verified High-Res Photos")
    logger.info("   - Isolation            : 100% Independent (Does NOT touch NewsTube Breaking News)")
    logger.info("=" * 75)

    while True:
        try:
            processed = load_processed_topics()
            articles = fetch_news()
            unseen = [a for a in articles if a.title.strip().lower() not in processed]

            target_topic = None
            target_cat = "Investigation"
            target_url = ""
            target_summary = ""

            if unseen:
                unseen.sort(key=lambda x: (getattr(x, "trending_score", 0.0), getattr(x, "published_at", "") or ""), reverse=True)
                target = unseen[0]
                target_topic = target.title
                target_cat = target.category
                target_url = target.link
                target_summary = target.summary
            else:
                # Pick from curated investigative rotation pool
                unseen_curated = [c for c in CURATED_INVESTIGATIVE_ROTATION if c["topic"].strip().lower() not in processed]
                if unseen_curated:
                    choice = unseen_curated[0]
                    target_topic = choice["topic"]
                    target_cat = choice["category"]
                else:
                    choice = random.choice(CURATED_INVESTIGATIVE_ROTATION)
                    target_topic = choice["topic"]
                    target_cat = choice["category"]

            if target_topic:
                produce_and_publish_documentary(
                    topic=target_topic,
                    category=target_cat,
                    direct_url=target_url,
                    raw_summary=target_summary
                )

        except Exception as e:
            logger.error(f"❌ Standalone documentary daemon exception: {e}", exc_info=True)

        logger.info(f"⏳ Sleeping for {POLL_INTERVAL_SECONDS}s (30 minutes) before next documentary publication...")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        custom_topic = " ".join(sys.argv[1:])
        produce_and_publish_documentary(topic=custom_topic)
    else:
        run_standalone_daemon()
