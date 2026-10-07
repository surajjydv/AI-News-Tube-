"""
test_25d_video_render.py
Tests rendering a 5-second 2.5D broadcast video using MoviePy + PIL + FFmpeg.
"""
import os
import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import edge_tts
from services.dynamic_broadcast_renderer import render_dynamic_broadcast_video

TEST_AUDIO = BASE_DIR / "assets" / "test_25d_audio.mp3"
TEST_VIDEO = BASE_DIR / "videos" / "test_25d_video.mp4"

async def ensure_test_audio():
    TEST_AUDIO.parent.mkdir(parents=True, exist_ok=True)
    if not TEST_AUDIO.exists() or TEST_AUDIO.stat().st_size < 1000:
        script = "सुप्रीम कोर्ट ने बड़ा फैसला सुनाते हुए सभी पक्षों को सख्त निर्देश जारी किए हैं। ग्राउंड रिपोर्ट में नई जानकारी सामने आई है।"
        comm = edge_tts.Communicate(script, voice="hi-IN-MadhurNeural")
        await comm.save(str(TEST_AUDIO))
        print("Generated test audio:", TEST_AUDIO)

def run_test():
    asyncio.run(ensure_test_audio())
    photo = BASE_DIR / "assets" / "real_event_photo_1.jpg"
    photo_paths = [str(photo)] if photo.exists() else []

    out = render_dynamic_broadcast_video(
        headline="सुप्रीम कोर्ट का ऐतिहासिक फैसला: केंद्र सरकार को दिए कड़े निर्देश",
        category="NATIONAL",
        slide_takeaways=[
            "मुख्य घटनाक्रम: संविधान पीठ ने सर्वसम्मति से पारित किया आदेश",
            "ग्राउंड रिपोर्ट: सभी संबंधित पक्षों को नोटिस जारी कर मांगा हलफनामा",
            "आगामी सुनवाई: अगली तारीख पर विस्तृत समीक्षा एवं जांच रिपोर्ट पेश होगी"
        ],
        photo_paths=photo_paths,
        photo_credits=["Verified Press Wire / Supreme Court Bureau"],
        audio_path=TEST_AUDIO,
        output_video_path=TEST_VIDEO,
        fps=15
    )
    print("✅ Successfully rendered 2.5D Video:", out)
    print("Video size:", out.stat().st_size, "bytes")

if __name__ == "__main__":
    run_test()
