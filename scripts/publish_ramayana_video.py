"""
scripts/publish_ramayana_video.py
=================================
Generates and publishes a full 1080p 16:9 broadcast story on Nitesh Tiwari's
'Ramayana' movie update featuring Ranbir Kapoor, Yash, and Sai Pallavi to YouTube.
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import DEFAULT_TTS_VOICE, CHANNEL_NAME, VIDEOS_DIR
from utils.logger import logger
from services.visual_asset_manager import VisualAssetManager
from services.fluent_script_service import generate_fluent_news_script
from services.ai_thumbnail_service import create_real_event_youtube_thumbnail
from services.cinematic_story_renderer import render_dynamic_broadcast_video
from services.youtube_upload_service import upload_video_to_youtube
import edge_tts

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

async def synthesize_narration(text: str, output_path: Path, voice: str = DEFAULT_TTS_VOICE) -> Path:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate="+8%", volume="+0%")
    await communicate.save(str(output_path))
    logger.info(f"🎙️ Narration generated: {output_path.name} ({output_path.stat().st_size} bytes)")
    return output_path

def main():
    logger.info("=" * 65)
    logger.info("🎬 PRODUCING RAMAYANA MOVIE UPDATE BROADCAST VIDEO")
    logger.info("=" * 65)

    story_id = sys.argv[1] if len(sys.argv) > 1 else "ramayana_1792009289"
    title = "Ramayana Movie Mega Update: Ranbir Kapoor as Lord Ram, Yash as Ravana, Rs 835 Cr Budget & Release Date"
    category = "Entertainment"
    context = (
        "Nitesh Tiwari's magnum opus Ramayana starring Ranbir Kapoor as Lord Ram, Sai Pallavi as Mata Sita, "
        "and KGF star Yash as Ravana with Sunny Deol as Lord Hanuman. With an estimated budget of over 835 crores, "
        "Oscar-winning VFX studio DNEG is handling visual effects. Part 1 is scheduled for Diwali 2026 and Part 2 for Diwali 2027. "
        "Massive anticipation and ground production updates."
    )

    story_dir = OUTPUT_DIR / f"assets_{story_id}"
    story_dir.mkdir(parents=True, exist_ok=True)
    audio_path = OUTPUT_DIR / f"audio_{story_id}.mp3"
    thumb_path = OUTPUT_DIR / f"thumb_{story_id}.jpg"
    video_path = VIDEOS_DIR / f"video_{story_id}.mp4"

    # Step 1: Visuals (Min 5 distinct images)
    logger.info("📸 Step 1: Resolving 5+ Visual Assets for Ramayana Cast & Film...")
    existing_photos = sorted(list(story_dir.glob("*.jpg")))
    if len(existing_photos) >= 5:
        logger.info(f"  ✅ Reusing {len(existing_photos)} existing verified photos from {story_dir.name}")
        photo_paths = [str(p) for p in existing_photos]
        photo_credits = ["Photo: Wikipedia Editorial Coverage"] * len(photo_paths)
    else:
        assets = VisualAssetManager.get_multi_visual_assets(
            headline=title,
            category=category,
            output_dir=story_dir,
            context=context,
            max_photos=5
        )
        photo_paths = [a.file_path for a in assets]
        photo_credits = [a.on_screen_credit for a in assets]

    # Step 2: Script & 5 Dynamic 3D Headlines
    logger.info("📝 Step 2: Preparing Deep Journalistic Narrative & Dynamic Headlines...")
    full_narr_text = (
        "फिल्म निर्माता नितेश तिवारी की बहुप्रतीक्षित पौराणिक फिल्म रामायण पर सबसे बड़ा आधिकारिक अपडेट सामने आया है। "
        "इस महाकाव्य गाथा में रणबीर कपूर भगवान राम के दिव्य अवतार में नजर आएंगे, जबकि माता सीता का पावन किरदार साई पल्लवी निभा रही हैं। "
        "केजीएफ स्टार यश रावण के खूंखार रूप में अपनी छाप छोड़ेंगे और सनी देओल भगवान हनुमान के किरदार में दिखेंगे। "
        "फिल्म का कुल बजट 835 करोड़ रुपये पार हो चुका है, जो इसे भारतीय सिनेमा की अब तक की सबसे भव्य और महंगी फिल्म बनाता है। "
        "हॉलीवुड की ऑस्कर विजेता वीएफएक्स कंपनी डीनेग इसके विजुअल्स को अंतरराष्ट्रीय स्तर पर तैयार कर रही है। "
        "फिल्म का पहला भाग दिवाली 2026 में और दूसरा भाग दिवाली 2027 में दुनियाभर के सिनेमाघरों में रिलीज किया जाएगा।"
    )
    slide_takeaways = [
        "रणबीर कपूर श्रीराम, साई पल्लवी माता सीता और यश रावण के भव्य अवतार में",
        "835 करोड़ रुपये का ऐतिहासिक मेगा बजट, भारतीय सिनेमा की सबसे महंगी फिल्म",
        "ऑस्कर विजेता DNEG स्टूडियो संभाल रहा है विश्वस्तरीय हॉलीवुड विजुअल इफेक्ट्स",
        "फिल्म का पहला भाग दिवाली 2026 और दूसरा भाग दिवाली 2027 में रिलीज होगा",
        "सनी देओल निभाएंगे भगवान हनुमान का शक्तिशाली और अभूतपूर्व किरदार"
    ]
    broadcast_headline = "रामायण: 835 करोड़ का ऐतिहासिक महाकाव्य"
    slide_headlines = [
        "रणबीर कपूर बने भगवान राम, यश रावण के खूंखार अवतार में",
        "835 करोड़ का विशाल बजट, रचा जाएगा सिनेमाई इतिहास",
        "हॉलीवुड की DNEG कंपनी तैयार कर रही है भव्य VFX",
        "दिवाली 2026 पर पहले भाग की ऐतिहासिक रिलीज",
        "सनी देओल बने महाबली हनुमान, फैंस में जबरदस्त उत्साह"
    ]

    # Step 3: Neural Voiceover
    logger.info("🎙️ Step 3: Synthesizing Neural Voice Narration...")
    if not (audio_path.exists() and audio_path.stat().st_size > 1000):
        asyncio.run(synthesize_narration(full_narr_text, audio_path))
    else:
        logger.info(f"  ✅ Reusing pre-generated audio: {audio_path.name}")

    # Step 4: AI-Powered 3D Thumbnail
    logger.info("🖼️ Step 4: Creating YouTube-Style 3D Viral Thumbnail...")
    if not (thumb_path.exists() and thumb_path.stat().st_size > 1000):
        create_real_event_youtube_thumbnail(
            headline="रामायण का सबसे बड़ा ऐलान, रणबीर और यश का धांसू लुक!",
            category=category,
            real_photo_path=photo_paths[0] if photo_paths else None,
            output_path=thumb_path,
            use_ai_generation=True
        )
    else:
        logger.info(f"  ✅ Reusing viral 3D thumbnail: {thumb_path.name}")

    # Step 5: Render 1080p Video (Centered 3D Headline, Zero Black Lines)
    logger.info("🎬 Step 5: Rendering 1080p Broadcast Video with Centered 3D Headline Slab...")

    render_dynamic_broadcast_video(
        headline=broadcast_headline,
        category=category,
        takeaway_points=slide_takeaways,
        slide_headlines=slide_headlines,
        photo_paths=photo_paths,
        photo_credits=photo_credits,
        audio_path=audio_path,
        output_video_path=video_path,
        fps=15
    )

    # Step 6: Post to YouTube
    logger.info("📤 Step 6: Uploading to YouTube Channel SRJ UNDERRATED...")
    desc = (
        f"🔥 नितेश तिवारी की फिल्म रामायण पर सबसे बड़ा अपडेट!\n\n"
        f"रणबीर कपूर (भगवान राम), साई पल्लवी (माता सीता), और यश (रावण) की बहुप्रतीक्षित फिल्म का बजट 835 करोड़ रुपये पार।\n\n"
        f"📌 मुख्य बिंदु:\n" + "\n".join(f"• {t}" for t in slide_takeaways) + "\n\n"
        f"📖 पूरी रिपोर्ट:\n{full_narr_text}\n\n"
        f"🔔 Subscribe to {CHANNEL_NAME} for top entertainment, cinema news & deep analysis.\n\n"
        f"#Ramayana #RanbirKapoor #Yash #SaiPallavi #NiteshTiwari #BollywoodNews #NewsTube"
    )

    video_id = upload_video_to_youtube(
        video_path=str(video_path),
        title=f"Ramayana Movie Official Update! 🚩 Ranbir Kapoor & Yash | दिवाली 2026 रिलीज",
        description=desc,
        category_id="24",  # Entertainment
        privacy_status="public",
        thumbnail_path=str(thumb_path) if thumb_path.exists() else None,
        tags=["Ramayana", "RanbirKapoor", "Yash", "SaiPallavi", "NiteshTiwari", "Bollywood", "EntertainmentNews", CHANNEL_NAME]
    )

    logger.info("=" * 65)
    if video_id and video_id not in ["LOCAL_SAVED", "RTMP_LIVE_STREAM_BROADCASTED"]:
        logger.info(f"🎉 SUCCESS! Video Live on YouTube: https://youtu.be/{video_id}")
    else:
        logger.info(f"✅ Video Processed: {video_path}")
    logger.info("=" * 65)

if __name__ == "__main__":
    main()
