import sys, os, time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from services.dynamic_broadcast_renderer import render_dynamic_broadcast_video

headline = "वाराणसी में गंगा का रौद्र रूप: सभी 84 घाट डूबे, छतों पर अंतिम संस्कार और आरती"
category = "National"
takeaways = [
    "वाराणसी के 84 घाट जलमग्न, अंतिम संस्कार छतों पर हो रहे",
    "गंगा जलस्तर 7.5 मीटर, पूर्व रिकॉर्ड से 1.2 मीटर अधिक पहुंचा",
    "मध्य प्रदेश, उत्तर प्रदेश, राजस्थान, गुजरात में रेड अलर्ट जारी",
    "NDRF-SDRF टीमें तैनात, राहत शिविर और पुनर्वास योजना शुरू"
]

# Find an audio file
audio_path = None
voice_dir = BASE_DIR / "voice"
if voice_dir.exists():
    mp3s = list(voice_dir.glob("*.mp3"))
    if mp3s:
        audio_path = mp3s[0]

output_video = BASE_DIR / "videos" / "test_25d_proof_broadcast.mp4"

print(f"Using audio: {audio_path}")
if audio_path and audio_path.exists():
    print(f"Rendering 2.5D Broadcast Video to {output_video}...")
    t0 = time.time()
    res = render_dynamic_broadcast_video(
        headline=headline,
        category=category,
        slide_takeaways=takeaways,
        photo_paths=[str(BASE_DIR / "assets" / "test_visual_check" / "story_photo_1.jpg")],
        photo_credits=["Dainik Bhaskar Verified Editorial Wire"],
        audio_path=audio_path,
        output_video_path=output_video,
        fps=15
    )
    print(f"✅ Finished in {time.time() - t0:.1f}s! Video path: {res}")
else:
    print("No audio found, skipping video test.")
