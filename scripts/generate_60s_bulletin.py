"""
scripts/generate_60s_bulletin.py
================================
Generates a complete 1-Minute (60-second) Full HD (1080p) Broadcast News Video.
Features:
- Duration: 60 Seconds
- High-Impact 2.5D Headlines in Simple Easy-to-Understand Language (Hinglish/Romanized Hindi)
- 100% Real Authentic HD News Photography (ZERO AI images)
- Saral Hindi Neural Voiceover
- 2.5D Extruded Glassmorphic Lower Third with Gold Border Trim & Live Ticker
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

from config.settings import ASSETS_DIR, VIDEOS_DIR, CHANNEL_NAME
from models.news_models import GeneratedScript
from agents.voice_agent import voice_agent
from agents.graphics_agent import render_tv_broadcast_frame, fetch_news_photo
from services.rss_service import get_realtime_ticker_headlines
from utils.logger import logger

OUTPUT_VIDEO = VIDEOS_DIR / "bulletin_1min_1080p.mp4"
PHOTO_FILE_1  = ASSETS_DIR / "real_news_photo_60s_1.jpg"
PHOTO_FILE_2  = ASSETS_DIR / "real_news_photo_60s_2.jpg"

# 60-Second Full News Script (2 News Segments, 30s each)
NEWS_SEGMENTS = [
    {
        "id": 1,
        "category": "BREAKING NEWS",
        "topic": "Bharat Sarkar Ka Bada Faisla",
        "search_kw": "narendra modi india parliament summit",
        "headline": "BADI KHABAR: Desh Bhar Me Bada Badlav, Sarkar Ka Historic Policy Faisla Jari",
        "script": (
            "नमस्कार! AI-NewsTube की 1-मिनट की बड़ी बुलेटिन में आपका स्वागत है। "
            "आज की पहली बड़ी ख़बर केंद्र सरकार द्वारा लिए गए ऐतिहासिक फैसले को लेकर है। "
            "देश के बुनियादी ढांचे और आम जनता को सीधी राहत देने के लिए सरकार ने नए नीतिगत सुधार लागू कर दिए हैं। "
            "इस फैसले से रोजगार और औद्योगिक विकास में बड़ी वृद्धि होने की उम्मीद है।"
        )
    },
    {
        "id": 2,
        "category": "SPORTS",
        "topic": "T20 World Cup Me Team India Ki Jeet",
        "search_kw": "cricket team india win trophy stadium",
        "headline": "SPORTS UPDATE: T20 World Cup Me Team India Ki Historic Victory, Semifinal Me Entry",
        "script": (
            "दूसरी बड़ी ख़बर खेल जगत से है। T20 वर्ल्ड कप के महामुकाबले में "
            "भारतीय क्रिकेट टीम ने अपने शानदार प्रदर्शन के दम पर ऐतिहासिक जीत हासिल कर ली है। "
            "कप्तान रोहित शर्मा की तूफानी बल्लेबाजी और गेंदबाजों के बेहतरीन प्रदर्शन के दम पर "
            "टीम इंडिया ने सेमीफाइनल में अपनी जगह पक्की कर ली है।"
        )
    }
]


def main():
    print("=" * 65)
    print("📺 AI-NewsTube — 1-Minute (60s) Full HD Broadcast Video Generator")
    print("=" * 65)

    try:
        from moviepy import VideoClip, AudioFileClip, concatenate_videoclips
    except ImportError:
        from moviepy.video.VideoClip import VideoClip
        from moviepy.audio.AudioFileClip import AudioFileClip
        from moviepy.video.compositing.concatenate import concatenate_videoclips

    live_ticker = get_realtime_ticker_headlines(limit=10)
    segment_clips = []

    for seg in NEWS_SEGMENTS:
        print(f"\n📌 Processing Segment #{seg['id']}: [{seg['category']}] '{seg['topic']}'")
        photo_file = ASSETS_DIR / f"real_news_photo_60s_{seg['id']}.jpg"

        # Fetch 100% Real HD Photography (NO AI images)
        fetch_news_photo(seg["search_kw"], photo_file, seg["id"])

        # Synthesize Saral Hindi Voiceover
        script_obj = GeneratedScript(
            topic_title=seg["topic"],
            category=seg["category"],
            script_text=seg["script"],
            word_count=len(seg["script"].split())
        )
        res_script = voice_agent(script_obj)
        audio_path = Path(res_script.audio_path) if res_script.audio_path else None

        audio_clip = None
        if audio_path and audio_path.exists():
            try:
                audio_clip = AudioFileClip(str(audio_path))
            except Exception:
                pass

        duration = 30.0
        if audio_clip and audio_clip.duration > 5.0:
            duration = audio_clip.duration + 1.0

        def make_frame(t, s=seg, p=photo_file):
            frame_img = render_tv_broadcast_frame(
                headline_text=s["headline"],
                news_photo_path=str(p) if p.exists() else None,
                global_t=t,
                category=s["category"],
                ticker_headlines=live_ticker
            )
            return __import__("numpy").array(frame_img)

        clip = VideoClip(make_frame, duration=duration)
        if audio_clip:
            try:
                clip = clip.with_audio(audio_clip)
            except Exception:
                try:
                    clip.audio = audio_clip
                except Exception:
                    pass

        segment_clips.append(clip)
        print(f"   ✅ Segment #{seg['id']} Clip Ready ({clip.duration:.1f}s)")

    print(f"\n🎬 Concatenating {len(segment_clips)} Segments into 60-Second Video...")
    final_video = concatenate_videoclips(segment_clips, method="compose")

    print(f"🎥 Rendering 1080p MP4 Bulletin → {OUTPUT_VIDEO.name}...")
    temp_snd = str(ASSETS_DIR / f"temp_audio_{int(time.time())}.m4a")
    final_video.write_videofile(
        str(OUTPUT_VIDEO),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=temp_snd,
        remove_temp=True,
        threads=4
    )

    print("\n" + "=" * 65)
    print("🎉 1-MINUTE BROADCAST VIDEO GENERATED SUCCESSFULLY!")
    print(f"  🎥 File Path : {OUTPUT_VIDEO}")
    print(f"  📊 File Size : {OUTPUT_VIDEO.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"  ⏱️ Duration  : {final_video.duration:.1f} seconds")
    print("=" * 65)


if __name__ == "__main__":
    main()
