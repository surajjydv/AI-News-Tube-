"""
test_render_video.py
Quick local render test — NO YouTube upload.
Tests: Hindi font fix + smooth cross-fade between photos.
"""
import os, sys, asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from services.live_feed_renderer import LiveFeedRenderer
import edge_tts

AUDIO_OUT  = BASE_DIR / "assets" / "test_render_audio.mp3"
VIDEO_OUT  = BASE_DIR / "videos" / "test_render_output.mp4"

# --- Use whatever photos exist in assets ---
PHOTO_DIRS = [
    BASE_DIR / "assets",
    BASE_DIR / "assets" / "test",
    BASE_DIR / "assets" / "test_images",
]
photo_paths = []
for d in PHOTO_DIRS:
    if d.exists():
        for f in sorted(d.iterdir()):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png") and f.stat().st_size > 5000:
                photo_paths.append(str(f))
            if len(photo_paths) >= 4:
                break
    if len(photo_paths) >= 4:
        break

print(f"📸 Found {len(photo_paths)} photos: {[Path(p).name for p in photo_paths]}")

if not photo_paths:
    from PIL import Image
    for i, color in enumerate([(30,60,120),(120,30,30),(30,120,60),(60,30,120)]):
        p = BASE_DIR / "assets" / f"_test_color_{i}.jpg"
        Image.new("RGB", (1280,720), color).save(str(p))
        photo_paths.append(str(p))
    print("Created solid-color test frames (no real photos found).")

async def gen_audio():
    AUDIO_OUT.parent.mkdir(parents=True, exist_ok=True)
    if AUDIO_OUT.exists() and AUDIO_OUT.stat().st_size > 1000:
        print(f"Using existing test audio file: {AUDIO_OUT.name}")
        return
    script = (
        "नमस्कार! AI-NewsTube पर आपका स्वागत है। "
        "यह एक परीक्षण वीडियो है जो हिंदी टेक्स्ट रेंडरिंग और "
        "स्मूथ फोटो ट्रांज़िशन को जांचने के लिए बनाया गया है। "
        "देवनागरी फॉन्ट अब सही तरीके से काम कर रहा है। "
        "फ्रेम जंप की समस्या भी ठीक हो गई है।"
    )
    try:
        comm = edge_tts.Communicate(script, voice="hi-IN-SwaraNeural")
        await comm.save(str(AUDIO_OUT))
        print(f"Audio: {AUDIO_OUT.name}")
    except Exception as e:
        print(f"Audio generation skipped ({e}). Reusing placeholder audio.")

asyncio.run(gen_audio())

VIDEO_OUT.parent.mkdir(parents=True, exist_ok=True)
LiveFeedRenderer.render_live_feed_video(
    headline="झारखंड छात्र प्रदर्शन: विधानसभा मार्च और भारी पुलिस बल तैनात",
    category="INDIA",
    photo_paths=photo_paths,
    photo_credits=["Source: Press News Photo"] * len(photo_paths),
    audio_path=str(AUDIO_OUT),
    output_path=VIDEO_OUT,
    sub_text="परीक्षा में धांधली को लेकर सीबीआई जांच की मांग, सुरक्षा के कड़े इंतजाम",
    ticker_text="झारखंड विधानसभा मार्च पर पुलिस हाई अलर्ट | छात्र संघ का विशाल प्रदर्शन | सीबीआई जांच जारी"
)

print(f"\nVideo saved: {VIDEO_OUT}")
print(f"Open: {VIDEO_OUT.resolve()}")
