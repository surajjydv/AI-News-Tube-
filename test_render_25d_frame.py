import sys, os
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from services.broadcast_25d_engine import render_broadcast_frame_25d

headline = "वाराणसी में गंगा का रौद्र रूप: सभी 84 घाट डूबे, छतों पर अंतिम संस्कार और आरती"
category = "National"
takeaways = [
    "वाराणसी के 84 घाट जलमग्न, अंतिम संस्कार छतों पर हो रहे",
    "गंगा जलस्तर 7.5 मीटर, पूर्व रिकॉर्ड से 1.2 मीटर अधिक पहुंचा",
    "मध्य प्रदेश, उत्तर प्रदेश, राजस्थान, गुजरात में रेड अलर्ट जारी",
    "NDRF-SDRF टीमें तैनात, राहत शिविर और पुनर्वास योजना शुरू"
]

# Find an authentic photo if available
sample_photo_path = BASE_DIR / "assets" / "test_visual_check" / "story_photo_1.jpg"
sample_photo = None
if sample_photo_path.exists():
    sample_photo = Image.open(sample_photo_path).convert("RGB")
    print(f"Loaded real event photo: {sample_photo_path} ({sample_photo.size})")

output_frame_path = BASE_DIR / "thumbnails" / "proof_25d_render_frame.png"
output_frame_path.parent.mkdir(parents=True, exist_ok=True)

print("Rendering true 2.5D physical layered broadcast frame...")
canvas = render_broadcast_frame_25d(
    t=3.5,
    total_duration=60.0,
    headline=headline,
    category=category,
    slide_takeaways=takeaways,
    photo_images=[sample_photo] if sample_photo else [],
    photo_credits=["Dainik Bhaskar Verified Editorial Wire"]
)

canvas.save(output_frame_path, "PNG")
print(f"✅ Saved True 2.5D Broadcast Frame to: {output_frame_path}")
