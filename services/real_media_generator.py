import os
import sys
import time
import shutil
import subprocess
import asyncio
import re
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

from services.groq_service import generate_text
from services.neon_service import neon_db
from services.visual_asset_manager import VisualAssetManager
import edge_tts


def _sync_fetch_llm_and_image(prompt: str, content_type: str, tone: str, ts: int):
    # 1. Groq LLM Caption & Hashtags
    llm_prompt = f"""Write a high-impact, professional broadcast news and viral social caption for:
Topic: "{prompt}"
Tone: {tone}
Channel: SRJ UNDERRATED

Format Requirements:
- 1 bold breaking headline with emoji (e.g. 🔴 BREAKING)
- 2 concise factual bullet points on the key development
- 1 call-to-action: "Subscribe to @SRJUNDERRATED for 24/7 verified breaking news & analysis."
At the end, add:
HASHTAGS: #tag1 #tag2 #tag3 #tag4 #tag5 #tag6"""

    try:
        raw_text = generate_text(llm_prompt, max_tokens=350)
    except Exception as e:
        print(f"[Generator] Groq error: {e}")
        raw_text = ""

    caption = (
        f"🔴 {prompt.title()}\n\n"
        f"• ताजा घटनाक्रम पर विशेष विश्लेषण एवं आधिकारिक रिपोर्ट।\n"
        f"• संबंधित अधिकारियों एवं टीमों द्वारा कार्रवाई जारी।\n\n"
        f"👉 Subscribe to @SRJUNDERRATED for 24/7 verified breaking news & ground reports."
    )
    hashtags = ["#TodayNews", "#BreakingNews", "#HindiNews", "#SRJUNDERRATED", "#LiveUpdates"]

    if "HASHTAGS:" in raw_text:
        parts = raw_text.split("HASHTAGS:")
        cap = parts[0].replace("CAPTION:", "").strip()
        if cap:
            caption = cap
        tags = re.findall(r"#[A-Za-z0-9_]+", parts[1])
        if tags:
            hashtags = tags[:8]
    elif raw_text:
        caption = raw_text.strip()

    # 2. Topic Photo Retrieval via VisualAssetManager (Wikipedia Official / Press Wire / Wikimedia / Flux.1)
    img_filename = f"image_{ts}.jpg"
    img_path = STATIC_DIR / img_filename

    temp_asset_dir = STATIC_DIR / f"temp_{ts}"
    temp_asset_dir.mkdir(parents=True, exist_ok=True)

    real_photo_found = False
    try:
        assets = VisualAssetManager.get_multi_visual_assets(
            headline=prompt,
            category="general",
            output_dir=temp_asset_dir,
            max_photos=1
        )
        if assets and len(assets) > 0 and Path(assets[0].file_path).exists():
            shutil.copyfile(assets[0].file_path, str(img_path))
            real_photo_found = True
            print(f"[Generator] Picked real editorial photo: {assets[0].file_path} ({assets[0].on_screen_credit})")
    except Exception as e:
        print(f"[Generator] VisualAssetManager warning: {e}")

    # Fallback to Flux.1 photorealistic AI if web retrieval did not return image
    if not real_photo_found or not img_path.exists():
        try:
            from services.ai_thumbnail_service import _generate_ai_visual
            print(f"[Generator] Synthesizing photorealistic visual via Flux.1 for: '{prompt}'...")
            ai_img = _generate_ai_visual(f"Editorial news photograph of {prompt}, dramatic photojournalism, authentic lighting, 8k")
            if ai_img:
                ai_img.convert("RGB").save(str(img_path), quality=95)
                real_photo_found = True
        except Exception as e:
            print(f"[Generator] Flux.1 fallback error: {e}")

    # Ultimate fallback to high-res news editorial photo
    if not img_path.exists() or img_path.stat().st_size == 0:
        import urllib.request
        fallback_url = "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=1080&auto=format&fit=crop&q=80"
        try:
            urllib.request.urlretrieve(fallback_url, str(img_path))
        except Exception:
            pass

    # Clean temp dir
    try:
        shutil.rmtree(temp_asset_dir, ignore_errors=True)
    except Exception:
        pass

    return caption, hashtags, img_path, img_filename


def _sync_render_ffmpeg_reel(img_path: Path, audio_path: Path, aspect_ratio: str, ts: int) -> tuple[Path, str]:
    video_filename = f"reel_{ts}.mp4"
    video_path = STATIC_DIR / video_filename

    # Aspect ratio scale filter
    if aspect_ratio == "16:9":
        vf_filter = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"
    elif aspect_ratio == "1:1":
        vf_filter = "scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080"
    elif aspect_ratio == "4:5":
        vf_filter = "scale=1080:1350:force_original_aspect_ratio=increase,crop=1080:1350"
    else:
        # Default 9:16 vertical reel
        vf_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

    if img_path.exists() and audio_path.exists():
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(img_path),
            "-i", str(audio_path),
            "-vf", vf_filter,
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-ar", "44100", "-ac", "2", "-c:a", "aac", "-strict", "-2", "-b:a", "128k",
            "-shortest",
            str(video_path)
        ]
        try:
            subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
        except Exception as e:
            print(f"[Generator] FFmpeg reel error: {e}")

    return video_path, video_filename


async def generate_real_media_pack(
    prompt: str,
    content_type: str = "reel",
    aspect_ratio: str = "9:16",
    tone: str = "Prime-Time News & Documentary",
    account_id: str = "acc_1"
) -> Dict[str, Any]:
    """Non-blocking async media generation using real editorial photos and neural narration."""
    ts = int(time.time())

    # 1. Fetch real photo & LLM caption
    caption, hashtags, img_path, img_filename = await asyncio.to_thread(
        _sync_fetch_llm_and_image, prompt, content_type, tone, ts
    )

    # 2. Audio synthesis with edge-tts
    audio_filename = f"voice_{ts}.mp3"
    audio_path = STATIC_DIR / audio_filename
    first_sentence = caption.split("\n")[0]
    clean_hook = re.sub(r"[^\w\s.,!?-]", "", first_sentence).strip() or prompt

    default_voice = os.getenv("DEFAULT_TTS_VOICE", "hi-IN-MadhurNeural")
    if "female" in tone.lower():
        voice_name = "hi-IN-SwaraNeural"
    elif "english" in tone.lower():
        voice_name = "en-IN-PrabhatNeural"
    else:
        voice_name = default_voice

    try:
        comm = edge_tts.Communicate(clean_hook, voice_name)
        await comm.save(str(audio_path))
    except Exception as e:
        print(f"[Generator] Edge-TTS error: {e}")

    # 3. Render video
    video_path, video_filename = await asyncio.to_thread(
        _sync_render_ffmpeg_reel, img_path, audio_path, aspect_ratio, ts
    )

    base_server = "http://127.0.0.1:8000/static"
    image_url = f"{base_server}/{img_filename}"
    video_url = f"{base_server}/{video_filename}" if video_path.exists() else image_url
    audio_url = f"{base_server}/{audio_filename}" if audio_path.exists() else ""
    thumbnail_url = image_url

    asset = {
        "accountId": account_id,
        "imageUrl": image_url,
        "videoUrl": video_url,
        "audioUrl": audio_url,
        "thumbnailUrl": thumbnail_url,
        "caption": caption,
        "hashtags": hashtags,
        "aspectRatio": aspect_ratio,
        "contentType": content_type,
        "prompt": prompt,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # Save into Neon Database
    asset_id = neon_db.save_generated_asset(asset)
    asset["id"] = asset_id
    return asset
