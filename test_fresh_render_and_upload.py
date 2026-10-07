import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from services.dynamic_broadcast_renderer import render_dynamic_broadcast_video
from services.ai_thumbnail_service import create_real_event_youtube_thumbnail
from services.youtube_upload_service import upload_video_to_youtube
from utils.logger import logger

import asyncio
import edge_tts

# Synthesize a clean 15-second Hindi voiceover
audio_file = BASE_DIR / "assets" / "realtime_story" / "test_fresh_narr.mp3"
audio_file.parent.mkdir(parents=True, exist_ok=True)

test_script = "राजधानी दिल्ली और आसपास के इलाकों में एच वन एन वन संक्रमण के मामलों में भारी बढ़ोतरी दर्ज की गई है। स्वास्थ्य विभाग ने सभी नागरिकों से सतर्क रहने की अपील की है।"

async def make_audio():
    comm = edge_tts.Communicate(text=test_script, voice="hi-IN-MadhurNeural", rate="+6%", pitch="+1Hz")
    await comm.save(str(audio_file))

asyncio.run(make_audio())
print("Synthesized Fresh Audio:", audio_file, "Size:", audio_file.stat().st_size)

output_vid = BASE_DIR / "videos" / "test_fresh_verified.mp4"
output_thumb = BASE_DIR / "thumbnails" / "test_fresh_verified.jpg"

headline = "🔴 LIVE: दिल्ली में H1N1 वायरस का अलर्ट - स्वास्थ्य मंत्रालय की सख्त एडवाइजरी जारी"
category = "Health Alert"
takeaways = [
    "दिल्ली-एनसीआर में H1N1 संक्रमण के मामलों में भारी उछाल दर्ज",
    "अस्पतालों की ओपीडी में मरीजों की संख्या 40% तक बढ़ी",
    "स्वास्थ्य मंत्रालय ने जारी की एडवाइजरी: मास्क और दूरी जरूरी",
    "डॉक्टरों की सलाह: लक्षण दिखने पर तुरंत कराएं जांच"
]
photo_paths = [str(BASE_DIR / "assets" / "realtime_story" / "story_photo_1.jpg")]

print("Step 1: Creating Thumbnail...")
create_real_event_youtube_thumbnail(
    headline=headline,
    category=category,
    real_photo_path=photo_paths[0],
    output_path=output_thumb
)
print("Thumbnail Created:", output_thumb)

print("Step 2: Rendering 1080p 2.5D Broadcast Video (with yuv420p & moov atom)...")
render_dynamic_broadcast_video(
    headline=headline,
    category=category,
    slide_takeaways=takeaways,
    photo_paths=photo_paths,
    audio_path=audio_file,
    output_video_path=output_vid,
    fps=15
)
print("Video Rendered Successfully:", output_vid, "Size:", output_vid.stat().st_size)

print("Step 3: Uploading Verified Video to YouTube (PUBLIC)...")
vid = upload_video_to_youtube(
    video_path=str(output_vid),
    title="🔴 LIVE: H1N1 Virus Alert In Delhi - Health Ministry Releases Strict Advisory",
    description="Full investigative ground report on rising H1N1 cases in Delhi and government advisories.\n\n#BreakingNews #HindiNews #HealthAlert #NewsTube",
    category_id="25",
    privacy_status="public",
    thumbnail_path=str(output_thumb),
    tags=["Breaking News", "H1N1", "Health News", "Hindi News", "NewsTube"]
)
print("=" * 60)
print(f"🎉 SUCCESS! Published Video URL: https://youtu.be/{vid}")
print("=" * 60)
