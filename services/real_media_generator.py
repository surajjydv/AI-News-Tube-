import os
import sys
import time
import subprocess
import asyncio
import urllib.request
import re
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

from services.groq_service import generate_text
from services.neon_service import neon_storage, neon_db
import edge_tts


def _sync_fetch_llm_and_image(prompt: str, content_type: str, tone: str, ts: int):
    # 1. Groq LLM Caption
    llm_prompt = f"""Write a short, viral Instagram {content_type.upper()} caption for:
Topic: "{prompt}"
Tone: {tone}

Include 2-3 short bullet lines with emojis, call to action.
At the end, add:
HASHTAGS: #tag1 #tag2 #tag3 #tag4 #tag5"""
    try:
        raw_text = generate_text(llm_prompt, max_tokens=300)
    except Exception as e:
        print(f"[Generator] Groq fallback: {e}")
        raw_text = ""
        
    caption = f"? {prompt.capitalize()}\n\nBaked fresh with authentic ingredients and artisan care.\n\n?? Link in bio to reserve yours today!"
    hashtags = ["#ArtisanBaking", "#FreshBakes", "#WeekendSpecial", "#ViralReels", "#InstagramMarketing"]
    
    if "HASHTAGS:" in raw_text:
        parts = raw_text.split("HASHTAGS:")
        cap = parts[0].replace("CAPTION:", "").strip()
        if cap:
            caption = cap
        tags = re.findall(r"#[A-Za-z0-9_]+", parts[1])
        if tags:
            hashtags = tags[:10]
    elif raw_text:
        caption = raw_text.strip()

    # 2. Topic Photo
    img_filename = f"image_{ts}.jpg"
    img_path = STATIC_DIR / img_filename
    
    photo_urls = [
        "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1080&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=1080&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=1080&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=1080&auto=format&fit=crop&q=80",
    ]
    picked_url = photo_urls[ts % len(photo_urls)]
    try:
        urllib.request.urlretrieve(picked_url, str(img_path))
    except Exception as e:
        print(f"[Generator] Image fetch fallback: {e}")

    return caption, hashtags, img_path, img_filename


def _sync_render_ffmpeg_reel(img_path: Path, audio_path: Path, ts: int) -> tuple[Path, str]:
    video_filename = f"reel_{ts}.mp4"
    video_path = STATIC_DIR / video_filename
    
    if img_path.exists() and audio_path.exists():
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(img_path),
            "-i", str(audio_path),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-ar", "44100", "-ac", "2", "-c:a", "aac", "-strict", "-2", "-b:a", "128k",
            "-shortest",
            str(video_path)
        ]
        try:
            subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=True)
        except Exception as e:
            print(f"[Generator] FFmpeg reel error: {e}")
            
    return video_path, video_filename


async def generate_real_media_pack(
    prompt: str,
    content_type: str = "reel",
    aspect_ratio: str = "9:16",
    tone: str = "Warm & Artisanal",
    account_id: str = "acc_1"
) -> Dict[str, Any]:
    """Non-blocking async media generation."""
    ts = int(time.time())
    
    # Run Groq + Image download in threadpool
    caption, hashtags, img_path, img_filename = await asyncio.to_thread(
        _sync_fetch_llm_and_image, prompt, content_type, tone, ts
    )

    # Audio synthesis with edge-tts
    audio_filename = f"voice_{ts}.mp3"
    audio_path = STATIC_DIR / audio_filename
    first_sentence = caption.split("\n")[0]
    clean_hook = re.sub(r"[^\w\s.,!?-]", "", first_sentence).strip() or prompt
    voice_name = "en-US-ChristopherNeural" if "warm" in tone.lower() or "artisan" in tone.lower() else "en-US-GuyNeural"
    
    try:
        comm = edge_tts.Communicate(clean_hook, voice_name)
        await comm.save(str(audio_path))
    except Exception as e:
        print(f"[Generator] Edge-TTS error: {e}")

    # Render video in threadpool
    video_path, video_filename = await asyncio.to_thread(
        _sync_render_ffmpeg_reel, img_path, audio_path, ts
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
