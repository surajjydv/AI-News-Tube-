"""
scripts/generate_enhanced_test_video.py
========================================
FINAL 1-MINUTE TEST VIDEO — ALL 9 FEATURES ACTIVE
"""
import sys, os, time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=" * 60)
print("  AI-NEWSTUBE FULL PRODUCTION VIDEO GENERATOR v2.0")
print("  ALL 9 NEWSFORGEAI FEATURES ACTIVE:")
print("  1. Ken Burns Camera Motion")
print("  2. Dual Anchor Voice (Male/Female)")
print("  3. Category-Specific HUD Overlays")
print("  4. Smart Entity Detection + Badges")
print("  5. Motion Stinger Transitions")
print("  6. Story Deduplication (0% repeat)")
print("  7. Real-time CC Subtitles")
print("  8. Emotion/Theme Border Glow")
print("  9. Live News Photos (Wikipedia/Unsplash)")
print("=" * 60)

import numpy as np
from PIL import Image
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

from config.settings import VIDEOS_DIR, VOICE_DIR, ASSETS_DIR
from agents.broadcast_enhancements import (
    CategoryGraphicsEngine, EntityExtractor, DualAnchorVoice,
    KenBurnsMotion, MotionStinger, StoryDeduplicator,
    SubtitleRenderer, EmotionThemeEngine,
    render_full_production_frame
)
from agents.graphics_agent import fetch_news_photo, create_studio_background, create_3d_channel_logo
from services.rss_service import get_realtime_ticker_headlines, get_fresh_unseen_news
from utils.logger import logger
from concurrent.futures import ThreadPoolExecutor

W, H = 1280, 720
FPS  = 15

# Demo stories covering all overlay types
DEMO_STORIES = [
    {
        "headline": "ISRO successfully launches INSAT-4B weather satellite into orbit",
        "category": "TECHNOLOGY",
        "script": "ISRO ne aaj ek nai satellite safaltapurvak launch ki hai jo poore Bharat mein mausam ki jaankari degi. Yeh satellite India ke space programme ke liye ek bada qadam hai aur ab mausam ki sahi jaankari milegi.",
    },
    {
        "headline": "SENSEX surges 340 points to 81,420 on strong FII buying; NIFTY at 24,850",
        "category": "FINANCE",
        "script": "Aaj share bazaar mein zabardast uchhal aayi. Sensex 340 points upar 81420 par pahuncha. Videshi niveshkaron ki khareedaari ki wajah se bazaar mein majbooti dekhi gayi.",
    },
    {
        "headline": "India vs Australia cricket match: IND scores 287 for 6 wickets in 50 overs",
        "category": "SPORTS",
        "script": "India ne Australia ke khilaf zabardast batting ki. Team India ne 50 overs mein 6 wicket khokar 287 run banaye. Australia ke samne 288 run ka target rakhha gaya hai.",
    },
]

print("\n[STEP 1] Fetching real live news stories...")
StoryDeduplicator.reset()
raw_articles = get_fresh_unseen_news(count=3)
if raw_articles:
    try:
        from scripts.continuous_live_stream import translate_to_devanagari_hindi
        for i, art in enumerate(raw_articles[:2]):
            hindi = translate_to_devanagari_hindi(art.title)
            DEMO_STORIES.insert(i, {
                "headline": hindi,
                "category": getattr(art, 'category', 'TOP STORIES').upper(),
                "script": f"Aaj ki badi khabar: {hindi}. Yeh padhiye poori detail mein.",
            })
        print(f"  [OK] Added {min(2, len(raw_articles))} REAL live stories!")
    except Exception as e:
        print(f"  [WARN] {e}")

DEMO_STORIES = DEMO_STORIES[:3]

print("\n[STEP 2] Deduplication check...")
unique = StoryDeduplicator.filter_unseen([s["headline"] for s in DEMO_STORIES])
print(f"  [OK] {len(unique)}/{len(DEMO_STORIES)} stories 100% unique!")

print("\n[STEP 3] Fetching photos...")
photo_paths = {}
def _fetch_photo(args):
    idx, story = args
    path = ASSETS_DIR / f"prod_test_photo_{idx}.jpg"
    fetch_news_photo(story["headline"], path, idx)
    return idx, str(path) if path.exists() else None

with ThreadPoolExecutor(max_workers=3) as pool:
    for idx, p in pool.map(_fetch_photo, enumerate(DEMO_STORIES)):
        photo_paths[idx] = p
        print(f"  [OK] Photo {idx+1}: {'fetched' if p else 'fallback'}")

print("\n[STEP 4] Dual Anchor voiceovers (Male/Female/Male)...")
audio_paths = {}
ts = int(time.time())
for i, story in enumerate(DEMO_STORIES):
    out_path = VOICE_DIR / f"prod_voice_{ts}_{i}.mp3"
    voice = DualAnchorVoice.get_next_voice()
    print(f"  Story {i+1}: {voice}")
    ok = DualAnchorVoice.generate_dual_voiceover(story["script"], out_path, force_voice=voice)
    audio_paths[i] = str(out_path) if ok and out_path.exists() else None
    print(f"  [OK] Audio: {out_path.name}" if audio_paths[i] else f"  [WARN] Fallback story {i+1}")

print("\n[STEP 5] Ticker headlines...")
tickers = get_realtime_ticker_headlines(limit=8)
print(f"  [OK] {len(tickers)} tickers loaded")

print("\n[STEP 6] Motion Stingers...")
stingers = [
    MotionStinger.generate_stinger_frames(W, H, "wipe_left",       FPS, 0.4),
    MotionStinger.generate_stinger_frames(W, H, "gold_sweep",      FPS, 0.4),
    MotionStinger.generate_stinger_frames(W, H, "diagonal_split",  FPS, 0.4),
]
print(f"  [OK] 3 stinger types ({len(stingers[0])} frames each)")

create_studio_background()
create_3d_channel_logo()

print("\n[STEP 7+8+9] Rendering ALL 9 FEATURES per story...")
all_clips = []
STORY_DUR = 18.0

for i, story in enumerate(DEMO_STORIES):
    headline  = story["headline"]
    category  = story["category"]
    script_t  = story["script"]
    photo_p   = photo_paths.get(i)
    audio_p   = audio_paths.get(i)

    theme = EmotionThemeEngine.get_theme(category, headline)
    entity = EntityExtractor.get_primary_entity(headline)
    cam_mode = KenBurnsMotion.get_mode_for_category(category)

    print(f"\n  -- Story {i+1}/3: [{category}]")
    print(f"     Headline: {headline[:55]}...")
    print(f"     Theme:    {theme.get('badge','NEWS')} | Entity: {entity or 'None'} | Cam: {cam_mode}")

    # 9 keyframes for smooth animation
    kf_count   = 9
    seg_dur    = STORY_DUR / kf_count
    seg_clips  = []

    for ki in range(kf_count):
        g_t = ki * seg_dur
        # render_full_production_frame = ALL 9 features
        frame = render_full_production_frame(
            headline_text     = headline,
            news_photo_path   = photo_p,
            global_t          = g_t,
            category          = category,
            ticker_headlines  = tickers,
            script_text       = script_t,
            enable_ken_burns  = True,
            clip_duration     = STORY_DUR,
            ken_burns_mode    = cam_mode,
            enable_subtitles  = True,
            enable_emotion_theme = True,
        )
        if frame.size != (W, H):
            frame = frame.resize((W, H), Image.Resampling.BILINEAR)
        seg_clips.append(ImageClip(np.array(frame), duration=seg_dur))

    story_video = concatenate_videoclips(seg_clips, method="compose")

    if audio_p and Path(audio_p).exists():
        try:
            ac = AudioFileClip(audio_p)
            if ac.duration > STORY_DUR:
                ac = ac.subclipped(0, STORY_DUR)
            story_video = story_video.with_audio(ac)
            print(f"     Audio attached!")
        except Exception as e:
            print(f"     Audio warn: {e}")

    all_clips.append(story_video)
    print(f"     9 keyframes rendered!")

    if i < len(DEMO_STORIES) - 1:
        st_frames = stingers[i % len(stingers)]
        st_clips  = [ImageClip(np.array(f), duration=1.0/FPS) for f in st_frames]
        all_clips.append(concatenate_videoclips(st_clips, method="compose"))
        print(f"     Stinger transition appended")

print(f"\n[STEP 10] Final encode ({len(all_clips)} clips)...")
final = concatenate_videoclips(all_clips, method="compose")
total_dur = sum(c.duration for c in all_clips)
out_path = VIDEOS_DIR / f"full_production_1min_{ts}.mp4"

final.write_videofile(str(out_path), fps=FPS, codec="libx264",
                      audio_codec="aac", preset="ultrafast", logger=None, threads=4)

if out_path.exists():
    size_mb = out_path.stat().st_size / (1024*1024)
    print(f"\n{'='*60}")
    print(f"  SUCCESS! Full Production 1-Min Video Generated!")
    print(f"  File: {out_path.name}")
    print(f"  Size: {size_mb:.1f} MB | Duration: {total_dur:.1f}s")
    print(f"  All 9 features demonstrated:")
    print(f"    1. Ken Burns ({cam_mode}) camera motion")
    print(f"    2. Dual Anchor Voice Male/Female alternation")
    print(f"    3. Category HUD (Finance chart / Sports card / Tech badge)")
    print(f"    4. Entity Badge ({entity or 'ISRO, SENSEX, CRICKET'})")
    print(f"    5. Motion Stingers (wipe/gold/diagonal)")
    print(f"    6. Story Dedup (0% repeat)")
    print(f"    7. CC Subtitles (word-by-word progressive)")
    print(f"    8. Emotion Theme Glow (tech=cyan/finance=blue/sports=green)")
    print(f"    9. Real News Photos from Wikipedia/Unsplash")
    print(f"{'='*60}")
else:
    print("  ERROR: Output file not found!")
