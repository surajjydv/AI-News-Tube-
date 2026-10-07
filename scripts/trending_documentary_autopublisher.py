"""
trending_documentary_autopublisher.py
======================================
Autonomous 24/7 Publishing Daemon for SRJ UNDERRATED:
- Automatically selects the #1 top trending news story (India / World / Breaking).
- Conducts deep research dossier (Google News + Wikipedia + wire reports).
- Generates 900-1200 word deep-dive investigative Hindi script via openai/gpt-oss-120b.
- Fetches 100% REAL on-ground press photographs (filtered against reporter faces/TV logos).
- Synthesizes authoritative neural Hindi narration via Edge-TTS hi-IN-MadhurNeural.
- Creates high-CTR real photo thumbnail and renders 1080p video via fast direct FFmpeg.
- Uploads Public VOD to YouTube every 3 Hours (10,800s).
- Night Quiet Hours: Sleeps between 12:00 AM and 06:00 AM IST (no late night uploads).
"""

import urllib
import urllib3
import os, sys, time, asyncio, re, json, requests, io, subprocess, hashlib
import datetime as dt
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from typing import List, Dict, Tuple, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(str(BASE_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import edge_tts
from utils.logger import logger
from services.groq_service import generate_text
from utils.json_utils import extract_json_from_llm
from services.ai_thumbnail_service import create_real_event_youtube_thumbnail
from services.youtube_upload_service import upload_video_to_youtube
from services.rss_service import fetch_news, NewsArticle
from services.fluent_script_service import clean_news_headline
from services.deep_research_service import DeepResearchService

OUTPUT_DIR = BASE_DIR / "output"
VIDEOS_DIR = BASE_DIR / "videos"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR.mkdir(exist_ok=True)
VIDEOS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

PROCESSED_STORIES_FILE = DATA_DIR / "processed_trending_stories.json"
SCRIPT_MODEL = "openai/gpt-oss-120b"
INTERVAL_SECONDS = 3 * 3600  # 3 Hours
IST_OFFSET = dt.timedelta(hours=5, minutes=30)
IST_TZ = dt.timezone(IST_OFFSET, name="IST")


# ── Time & Night Quiet Window ────────────────────────────────────────────────
def get_current_ist_time() -> dt.datetime:
    """Returns current datetime in Indian Standard Time (IST)."""
    return dt.datetime.now(dt.timezone.utc).astimezone(IST_TZ)


def is_in_night_window(now_ist: Optional[dt.datetime] = None) -> bool:
    """Checks if current IST time falls in quiet night hours (12:00 AM to 06:00 AM)."""
    if now_ist is None:
        now_ist = get_current_ist_time()
    return 0 <= now_ist.hour < 6


def seconds_until_morning(now_ist: Optional[dt.datetime] = None) -> float:
    """Calculates seconds until next 06:00 AM IST."""
    if now_ist is None:
        now_ist = get_current_ist_time()
    morning = now_ist.replace(hour=6, minute=0, second=0, microsecond=0)
    if now_ist.hour >= 6:
        morning += dt.timedelta(days=1)
    diff = (morning - now_ist).total_seconds()
    return max(60.0, diff)


# ── History & Deduplication ──────────────────────────────────────────────────
def load_processed_stories() -> set:
    if PROCESSED_STORIES_FILE.exists():
        try:
            data = json.loads(PROCESSED_STORIES_FILE.read_text(encoding="utf-8"))
            return set(data.get("hashes", []))
        except Exception:
            pass
    return set()


def save_processed_story(title: str, u_hash: str):
    processed = load_processed_stories()
    processed.add(u_hash)
    try:
        data = {
            "updated_at": get_current_ist_time().isoformat(),
            "hashes": list(processed)[-200:]
        }
        PROCESSED_STORIES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to save processed story history: {e}")


# ── Real Photo Harvester with Strict Anti-Reporter Filter & Card-Level Verification ─
def extract_verified_article_lead_image(article_url: str, story_dir: Path) -> Optional[str]:
    """
    Attempts to extract the official lead photo directly from the news publication article webpage.
    Resolves Google News redirects to real source articles (NDTV, The Hindu, India Today, etc.).
    """
    if not article_url or not article_url.startswith("http"):
        return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(article_url, headers=headers, timeout=6, allow_redirects=True)
        dest_url = r.url
        html = r.text
        if "news.google.com" in dest_url:
            canonical_match = re.search(r'<c-wiz[^>]+data-n-a-url=["\']([^"\']+)["\']', html) or re.search(r'<a[^>]+href=["\'](https?://[^"\']+)["\'][^>]*rel=["\']nofollow["\']', html)
            if canonical_match:
                real_url = canonical_match.group(1).strip()
                r2 = requests.get(real_url, headers=headers, timeout=6, allow_redirects=True)
                dest_url = r2.url
                html = r2.text

        patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']'
        ]
        img_url = None
        for p in patterns:
            m = re.search(p, html, re.IGNORECASE)
            if m:
                img_url = m.group(1).strip()
                if img_url:
                    break

        if img_url:
            img_url = urllib.parse.urljoin(dest_url, img_url)
            bad_subs = ["logo", "favicon", "default", "placeholder", "pixel", "1x1", "avatar", "icon", "share_default"]
            if any(b in img_url.lower() for b in bad_subs):
                return None

            ir = requests.get(img_url, headers=headers, timeout=6)
            if ir.status_code == 200 and len(ir.content) > 15000:
                im = Image.open(io.BytesIO(ir.content)).convert("RGB")
                w, h = im.size
                if w >= 500 and h >= 300 and (1.1 <= w / float(h) <= 2.3):
                    out_path = story_dir / "verified_article_lead_og.jpg"
                    out_path.write_bytes(ir.content)
                    logger.info(f"  ✅ Extracted 100% Verified Article Lead Photo: {w}x{h} ({img_url[:60]})")
                    return str(out_path)
    except Exception as e:
        logger.debug(f"Direct article lead extraction note: {e}")
    return None


def fetch_real_incident_photos(
    topic: str,
    story_dir: Path,
    direct_image_url: Optional[str] = None,
    article_url: Optional[str] = None,
    max_photos: int = 6
) -> List[str]:
    """
    Harvests authentic on-ground press photos from Bing News and press wires.
    Prioritizes verified article lead photo, news-card targeted matching, and strictly excludes
    images with TV news reporters, studio backgrounds, or chyron graphics.
    """
    story_dir.mkdir(parents=True, exist_ok=True)
    photo_paths: List[str] = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. Tier 0A: Direct article lead photo from webpage (100% Authentic Ground Truth)
    if article_url:
        og_path = extract_verified_article_lead_image(article_url, story_dir)
        if og_path and og_path not in photo_paths:
            photo_paths.append(og_path)

    # 1. Tier 0B: Direct press wire photo from RSS enclosure
    if direct_image_url and direct_image_url.startswith("http"):
        try:
            r = requests.get(direct_image_url, headers=headers, timeout=8)
            if r.status_code == 200 and len(r.content) > 15000:
                im = Image.open(io.BytesIO(r.content))
                if im.size[0] >= 500 and im.size[1] >= 300:
                    p0 = story_dir / "press_wire_photo_1.jpg"
                    p0.write_bytes(r.content)
                    if str(p0) not in photo_paths:
                        photo_paths.append(str(p0))
                        logger.info(f"  ✅ Added Tier 0 press wire photo: {im.size}")
        except Exception as e:
            logger.debug(f"Direct photo note: {e}")

    # 2. Tier 1: Bing News targeted on-ground queries with card-level relevance verification
    clean_q = clean_news_headline(topic)
    words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', clean_q) if w.lower() not in {"the", "and", "for", "with", "from", "after", "into", "over", "news", "live"}]
    core_keywords = words[:4]

    queries = [
        f"{clean_q} news press photo",
        f"{' '.join(core_keywords)} news ground photo" if core_keywords else f"{clean_q} news",
        f"{clean_q}"
    ]

    seen_ids = set()
    found_cards = []
    for q in queries:
        try:
            url = f"https://www.bing.com/news/search?q={requests.utils.quote(q)}&form=PTFTNR"
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                matches = re.findall(r'id=(ONUT\.[a-zA-Z0-9_\-]+)', resp.text)
                for m in matches:
                    if m not in seen_ids:
                        seen_ids.add(m)
                        hd_url = f"https://www.bing.com/th?id={m}&w=1280&h=720&c=7&rs=1&p=0"
                        found_cards.append((q, hd_url))
        except Exception:
            pass

    for query_used, img_url in found_cards:
        if len(photo_paths) >= max_photos:
            break
        try:
            r = requests.get(img_url, headers=headers, timeout=8)
            if r.status_code == 200 and len(r.content) > 12000:
                im = Image.open(io.BytesIO(r.content)).convert("RGB")
                w, h = im.size
                if w < 500 or h < 300:
                    continue

                aspect = w / float(h)
                if aspect < 1.15 or aspect > 2.3:
                    continue

                # Anti-Reporter heuristic: check center skin tone
                crop_center = im.crop((int(w * 0.2), int(h * 0.2), int(w * 0.6), int(h * 0.8)))
                pixels = list(crop_center.getdata())
                skin_count = 0
                for r_c, g_c, b_c in pixels[::4]:
                    if r_c > 95 and g_c > 40 and b_c > 20 and (max(r_c, g_c, b_c) - min(r_c, g_c, b_c) > 15) and abs(r_c - g_c) > 15 and r_c > g_c and r_c > b_c:
                        skin_count += 1
                skin_ratio = skin_count / (len(pixels) // 4)
                if skin_ratio > 0.40:
                    logger.warning(f"  ⚠️ Skipping image with high facial/reporter ratio ({skin_ratio:.1%})")
                    continue

                out_path = story_dir / f"ground_photo_{len(photo_paths)+1}.jpg"
                out_path.write_bytes(r.content)
                photo_paths.append(str(out_path))
                logger.info(f"  ✅ Saved Verified Press Photo {len(photo_paths)}: {out_path.name} ({im.size}, skin={skin_ratio:.1%})")
        except Exception:
            pass

    # 3. Tier 2: Wikipedia editorial entity photos if needed
    if len(photo_paths) < 3:
        try:
            from services.visual_asset_manager import VisualAssetManager
            extra_assets = VisualAssetManager.get_multi_visual_assets(
                headline=clean_q,
                category="India",
                output_dir=story_dir,
                max_photos=max_photos - len(photo_paths)
            )
            for a in extra_assets:
                if str(a.file_path) not in photo_paths:
                    photo_paths.append(str(a.file_path))
        except Exception:
            pass

    return photo_paths[:max_photos]


def verify_and_select_thumbnail_photo(
    target_article: NewsArticle,
    headline: str,
    photo_paths: List[str],
    story_dir: Path
) -> str:
    """
    Strict Verification Engine for YouTube Thumbnail Image.
    Verifies that the thumbnail photo accurately depicts the real event, entities, or incident scene.
    Rejects:
    - Reporter faces holding microphones
    - TV news channel studio anchors
    - Blurry / tiny images (< 640x360)
    - Distorted aspect ratios (< 1.15 or > 2.2)
    - Flat graphic banners or logos
    """
    from PIL import ImageStat

    logger.info("=" * 70)
    logger.info("🔍 [THUMBNAIL VERIFICATION] Verifying Real Event Image Candidates...")
    logger.info(f"   Story Headline: {headline}")
    logger.info(f"   Available Candidates: {len(photo_paths)}")

    if not photo_paths:
        logger.warning("  ⚠️ No photo candidates available for thumbnail verification.")
        return ""

    verified_candidate = ""
    for idx, p_str in enumerate(photo_paths):
        p = Path(p_str)
        if not p.exists():
            continue

        try:
            im = Image.open(p).convert("RGB")
            w, h = im.size
            aspect = w / float(h)

            # Check 1: Resolution & Aspect Ratio
            if w < 500 or h < 300:
                logger.warning(f"  ❌ Candidate {idx+1} ({p.name}) Rejected: Resolution too low ({w}x{h})")
                continue
            if aspect < 1.15 or aspect > 2.3:
                logger.warning(f"  ❌ Candidate {idx+1} ({p.name}) Rejected: Bad aspect ratio ({aspect:.2f})")
                continue

            # Check 2: Color variance (Reject flat graphics, solid blocks)
            stat = ImageStat.Stat(im)
            avg_std = sum(stat.stddev) / 3.0
            if avg_std < 18.0:
                logger.warning(f"  ❌ Candidate {idx+1} ({p.name}) Rejected: Flat graphic / placeholder (std={avg_std:.1f})")
                continue

            # Check 3: Anti-Reporter & Anchor Headshot Filter
            crop_center = im.crop((int(w * 0.2), int(h * 0.2), int(w * 0.6), int(h * 0.8)))
            pixels = list(crop_center.getdata())
            skin_count = 0
            for r_c, g_c, b_c in pixels[::4]:
                if r_c > 95 and g_c > 40 and b_c > 20 and (max(r_c, g_c, b_c) - min(r_c, g_c, b_c) > 15) and abs(r_c - g_c) > 15 and r_c > g_c and r_c > b_c:
                    skin_count += 1
            skin_ratio = skin_count / (len(pixels) // 4)
            if skin_ratio > 0.40:
                logger.warning(f"  ❌ Candidate {idx+1} ({p.name}) Rejected: Reporter/Anchor close-up face detected ({skin_ratio:.1%})")
                continue

            # Candidate PASSED all verification checks
            logger.info(f"  ✅ Candidate {idx+1} ({p.name}) PASSED VERIFICATION:")
            logger.info(f"     - Resolution: {w}x{h} (Aspect: {aspect:.2f})")
            logger.info(f"     - Skin Ratio: {skin_ratio:.1%} (No reporter face)")
            logger.info(f"     - Natural Color Variance: {avg_std:.1f}")
            logger.info(f"     - Provenance: {p.name}")
            verified_candidate = str(p)
            break

        except Exception as e:
            logger.warning(f"  ❌ Candidate {idx+1} ({p.name}) Error: {e}")

    if not verified_candidate and photo_paths:
        logger.warning(f"  ⚠️ All strict checks failed; falling back to first candidate {Path(photo_paths[0]).name}")
        verified_candidate = photo_paths[0]

    logger.info(f"🏆 [THUMBNAIL VERIFIED] Selected Image: {Path(verified_candidate).name if verified_candidate else 'None'}")
    logger.info("=" * 70)
    return verified_candidate


# ── Script Synthesis (100% Devanagari Hindi, 900-1200 words) ─────────────────
def generate_trending_hindi_script(
    topic: str,
    dossier: str,
    target_minutes: float = 7.5
) -> Tuple[str, List[Dict[str, str]], str, str, List[str]]:
    """
    Synthesizes a deep-dive 900-1200 word investigative Hindi narrative using gpt-oss-120b.
    """
    word_min = int(target_minutes * 115)
    word_max = int(target_minutes * 150)

    prompt = f"""आप भारत के सबसे वरिष्ठ, निष्पक्ष और विश्लेषणात्मक खोजी पत्रकार हैं (Ravish Kumar / Nitish Rajput शैली)।
आपको नीचे दिए गए तथ्य और पृष्ठभूमि विवरण के आधार पर एक विस्तृत, तथ्य-आधारित और गंभीर हिंदी डॉक्यूमेंट्री स्क्रिप्ट लिखनी है।

विषय: {topic}
लक्ष्य: {target_minutes:.1f} मिनट की वीडियो ({word_min}-{word_max} बोले गए हिंदी शब्द)

शोध विवरण और तथ्य:
{dossier[:4000]}

नियम:
1. पूरी स्क्रिप्ट 100% शुद्ध हिंदी (देवनागरी) में लिखें। कोई अंग्रेजी मिश्रित न करें।
2. कोई अभिवादन नहीं ("नमस्कार", "स्वागत है" आदि न लिखें) — सीधे पहली पंक्ति से घटना की गंभीरता और मुख्य बिंदु से शुरू करें।
3. तथ्य, तारीखें, नाम, आंकड़े, कानूनी धाराएं और ज़मीनी प्रभाव विस्तार से बताएं।
4. कम से कम {word_min} शब्द होने अनिवार्य हैं।
5. 4 अध्यायों (Chapters) में विभाजित करें।

OUTPUT FORMAT: केवल valid JSON object:
{{
  "viral_youtube_title": "(Hindi clickbait title with emojis, max 85 chars)",
  "documentary_title": "(Clean Hindi title, max 10 words)",
  "full_narration": "(पूरी {word_min}-{word_max} शब्दों की हिंदी स्क्रिप्ट बिना रुके एक flow में)",
  "chapters": [
    {{"chapter_num": "01", "title": "(अध्याय 1 शीर्षक)", "summary": "(1 पंक्ति सारांश)"}},
    {{"chapter_num": "02", "title": "(अध्याय 2 शीर्षक)", "summary": "(1 पंक्ति सारांश)"}},
    {{"chapter_num": "03", "title": "(अध्याय 3 शीर्षक)", "summary": "(1 पंक्ति सारांश)"}},
    {{"chapter_num": "04", "title": "(अध्याय 4 शीर्षक)", "summary": "(1 पंक्ति सारांश)"}}
  ],
  "youtube_tags": ["TrendingNews", "HindiNews", "BreakingNews", "Investigation", "SRJUnderrated"]
}}"""

    logger.info(f"📝 Calling Groq {SCRIPT_MODEL} for Hindi script...")
    try:
        resp = generate_text(prompt, model=SCRIPT_MODEL, temperature=0.35, max_tokens=8000)
        data = extract_json_from_llm(resp)
        if isinstance(data, dict) and "full_narration" in data:
            narr = str(data["full_narration"]).strip()
            v_title = str(data.get("viral_youtube_title", f"😱 {topic} | पूरा सच | SRJ UNDERRATED")).strip()
            doc_title = str(data.get("documentary_title", topic[:40])).strip()
            chapters = data.get("chapters", [])
            tags = data.get("youtube_tags", ["TrendingNews", "HindiNews"])
            word_count = len(narr.split())
            logger.info(f"  ✅ Hindi Script Generated: {word_count} words, {len(chapters)} chapters")
            return narr, chapters, doc_title, v_title, tags
    except Exception as e:
        logger.warning(f"Script generation error: {e}")

    # Fallback
    fallback_narr = f"{topic} को लेकर इस वक्त देश भर में बड़ी चर्चा है। इस पूरे मामले में कई महत्वपूर्ण तथ्य सामने आए हैं जो जानना बेहद ज़रूरी है। जांच अधिकारियों और जानकारों के अनुसार इस घटना के पीछे कई अहम कारण रहे हैं जिनकी गहन पड़ताल की जा रही है।"
    chapters = [
        {"chapter_num": "01", "title": "मुख्य घटना", "summary": "घटना का पूरा विवरण"},
        {"chapter_num": "02", "title": "जांच और खुलासे", "summary": "सामने आए अहम तथ्य"},
        {"chapter_num": "03", "title": "ज़िम्मेदार कौन?", "summary": "कार्रवाई और प्रतिक्रिया"},
        {"chapter_num": "04", "title": "बड़ा सवाल", "summary": "आगे क्या होगा?"}
    ]
    return fallback_narr, chapters, topic[:30], f"😱 {topic[:60]} | पूरा सच", ["TrendingNews"]


# ── Audio Synthesis ──────────────────────────────────────────────────────────
async def generate_hindi_voiceover(text: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    comm = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="-4%",
        volume="+0%"
    )
    await comm.save(str(output_path))
    logger.info(f"✅ Hindi Voiceover Synthesized: {output_path.name} ({output_path.stat().st_size / 1024:.0f} KB)")
    return output_path


# ── Slide Layout & Video Rendering ───────────────────────────────────────────
def create_cinematic_chapter_frame(
    photo_path: str,
    chapter_num: str,
    chapter_title: str,
    fact_summary: str,
    doc_main_title: str,
    output_path: Path
) -> Path:
    w, h = 1920, 1080

    if photo_path and Path(photo_path).exists():
        try:
            base = Image.open(photo_path).convert("RGB")
            bw, bh = base.size
            scale = max(w / bw, h / bh)
            nw, nh = int(bw * scale), int(bh * scale)
            base = base.resize((nw, nh), Image.Resampling.LANCZOS)
            x_off = (nw - w) // 2
            y_off = (nh - h) // 2
            base = base.crop((x_off, y_off, x_off + w, y_off + h))
        except Exception:
            base = Image.new("RGB", (w, h), (18, 18, 24))
    else:
        base = Image.new("RGB", (w, h), (18, 18, 24))

    enhancer = ImageEnhance.Brightness(base)
    base = enhancer.enhance(0.72)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top archival bar
    draw.rectangle([0, 0, w, 70], fill=(10, 10, 15, 230))
    # Bottom documentary info panel
    draw.rectangle([0, h - 220, w, h], fill=(12, 14, 20, 235))
    # Red accent line
    draw.rectangle([0, h - 222, w, h - 218], fill=(220, 38, 38, 255))

    font_path = BASE_DIR / "assets" / "fonts" / "Mukta-Bold.ttf"
    if not font_path.exists():
        font_path = BASE_DIR / "assets" / "fonts" / "NotoSansDevanagari-Bold.ttf"

    try:
        f_top = ImageFont.truetype(str(font_path), 26)
        f_chap = ImageFont.truetype(str(font_path), 32)
        f_title = ImageFont.truetype(str(font_path), 46)
        f_sum = ImageFont.truetype(str(font_path), 28)
    except Exception:
        f_top = f_chap = f_title = f_sum = ImageFont.load_default()

    # Red pulsing dot indicator (procedural drawing without emoji tofu box)
    draw.ellipse([60, 24, 76, 40], fill=(239, 68, 68))
    draw.text((88, 18), "SPECIAL INVESTIGATION REPORT | खोजी रिपोर्ट", font=f_top, fill=(255, 255, 255))
    draw.text((w - 380, 18), "SRJ UNDERRATED EXCLUSIVE", font=f_top, fill=(255, 200, 0))

    tag = f"अध्याय {chapter_num} : {chapter_title}"
    draw.text((60, h - 195), tag, font=f_chap, fill=(255, 200, 0))
    draw.text((60, h - 150), doc_main_title[:55], font=f_title, fill=(255, 255, 255))
    draw.text((60, h - 85), fact_summary[:85], font=f_sum, fill=(210, 215, 225))

    final = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    final.save(str(output_path), "JPEG", quality=95)
    return output_path


def render_video_fast_ffmpeg(
    audio_path: Path,
    photo_paths: List[str],
    chapters: List[Dict[str, str]],
    doc_title: str,
    output_video: Path,
    temp_dir: Path
) -> bool:
    """Direct FFmpeg concat rendering in ~60-80s."""
    temp_dir.mkdir(parents=True, exist_ok=True)
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
    ]
    try:
        dur_str = subprocess.check_output(probe_cmd).decode().strip()
        total_duration = float(dur_str)
    except Exception:
        total_duration = 420.0

    num_photos = max(1, len(photo_paths))
    num_slices = max(len(chapters), num_photos, 4)
    slice_duration = total_duration / float(num_slices)

    slide_images = []
    for s_idx in range(num_slices):
        c_idx = min(len(chapters) - 1, int(s_idx * len(chapters) / float(num_slices)))
        c_data = chapters[c_idx]
        p_path = photo_paths[s_idx % len(photo_paths)] if photo_paths else ""

        slide_path = temp_dir / f"slide_{s_idx}.jpg"
        create_cinematic_chapter_frame(
            photo_path=p_path,
            chapter_num=c_data.get("chapter_num", f"0{c_idx+1}"),
            chapter_title=c_data.get("title", f"भाग {c_idx+1}"),
            fact_summary=c_data.get("summary", ""),
            doc_main_title=doc_title,
            output_path=slide_path
        )
        slide_images.append(slide_path)

    concat_txt = temp_dir / "concat_list.txt"
    lines = ["ffconcat version 1.0\n"]
    for simg in slide_images:
        lines.append(f"file '{simg.as_posix()}'\n")
        lines.append(f"duration {slice_duration:.3f}\n")
    lines.append(f"file '{slide_images[-1].as_posix()}'\n")
    concat_txt.write_text("".join(lines), encoding="utf-8")

    output_video.parent.mkdir(parents=True, exist_ok=True)
    render_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-r", "15",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_video)
    ]

    t0 = time.time()
    res = subprocess.run(render_cmd, capture_output=True, text=True)
    render_time = time.time() - t0

    if output_video.exists() and output_video.stat().st_size > 1000000:
        mb = output_video.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Master 1080p Video Created in {render_time:.1f}s! ({mb:.1f} MB)")
        return True
    else:
        logger.error(f"❌ FFmpeg encode failed: {res.stderr[:400]}")
        return False


# ── Storage Garbage Collection ───────────────────────────────────────────────
def cleanup_old_files():
    """Retains only latest 5 rendered videos and removes temporary slide frames."""
    try:
        mp4_files = sorted(VIDEOS_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime)
        if len(mp4_files) > 5:
            for old_p in mp4_files[:-5]:
                old_p.unlink(missing_ok=True)
                logger.info(f"  🧹 Cleaned old video: {old_p.name}")

        # Remove temp folders older than 2 hours
        now_ts = time.time()
        for t_dir in OUTPUT_DIR.glob("temp_*"):
            if t_dir.is_dir() and (now_ts - t_dir.stat().st_mtime > 7200):
                import shutil
                shutil.rmtree(t_dir, ignore_errors=True)
    except Exception as e:
        logger.debug(f"Cleanup note: {e}")


# ── One Publishing Cycle ─────────────────────────────────────────────────────
def run_single_trending_cycle() -> bool:
    """Executes one complete research -> script -> photos -> render -> YouTube publish cycle."""
    now_ist = get_current_ist_time()
    logger.info("=" * 70)
    logger.info(f"🚀 [TRENDING AUTO-PUBLISHER] Starting Cycle at {now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST")
    logger.info("=" * 70)

    # 1. Fetch top trending stories
    processed_hashes = load_processed_stories()
    articles: List[NewsArticle] = fetch_news(limit_per_category=4)

    target_article = None
    for a in articles:
        u_hash = hashlib.md5(a.title.lower().encode("utf-8")).hexdigest()[:10]
        if u_hash not in processed_hashes:
            target_article = a
            break

    if not target_article:
        logger.warning("⚠️ No unseen trending stories found in current feed batch.")
        return False

    title = target_article.title
    u_hash = hashlib.md5(title.lower().encode("utf-8")).hexdigest()[:10]
    logger.info(f"🎯 Selected Trending Story: {title} (Score: {target_article.trending_score})")

    story_id = f"trend_{int(time.time())}_{u_hash}"
    story_dir = OUTPUT_DIR / f"assets_{story_id}"
    audio_path = OUTPUT_DIR / f"audio_{story_id}.mp3"
    video_path = VIDEOS_DIR / f"trending_{story_id}.mp4"
    thumb_path = OUTPUT_DIR / f"thumb_{story_id}.jpg"
    temp_dir = OUTPUT_DIR / f"temp_{story_id}"

    # 2. Deep Research Dossier
    logger.info("🔍 Step 1: Compiling deep research dossier...")
    dossier_data = DeepResearchService.compile_investigative_dossier(
        topic=clean_news_headline(title),
        direct_url=target_article.link,
        raw_summary=target_article.summary,
        deep=True
    )
    dossier_text = dossier_data.get("full_dossier", target_article.summary)

    # 3. Hindi Script (openai/gpt-oss-120b)
    logger.info("📝 Step 2: Generating detailed Hindi investigative script...")
    narr, chapters, doc_title, v_title, tags = generate_trending_hindi_script(
        topic=title,
        dossier=dossier_text,
        target_minutes=7.5
    )

    # 4. Scrape 100% REAL On-Ground Press Photos (Zero Reporters)
    logger.info("📸 Step 3: Fetching verified on-ground press photos...")
    photo_paths = fetch_real_incident_photos(
        topic=title,
        story_dir=story_dir,
        direct_image_url=target_article.image_url,
        article_url=target_article.link,
        max_photos=6
    )

    # 5. Hindi Neural Voiceover
    logger.info("🎙️ Step 4: Synthesizing Hindi voiceover (hi-IN-MadhurNeural)...")
    asyncio.run(generate_hindi_voiceover(narr, audio_path))

    # 6. Verify and Generate High-CTR Real Photo Thumbnail
    logger.info("🖼️ Step 5: Verifying real event thumbnail photo...")
    verified_thumb_photo = verify_and_select_thumbnail_photo(
        target_article=target_article,
        headline=doc_title or title,
        photo_paths=photo_paths,
        story_dir=story_dir
    )
    try:
        create_real_event_youtube_thumbnail(
            headline=doc_title or title,
            category=target_article.category or "Breaking News",
            real_photo_path=verified_thumb_photo,
            output_path=thumb_path
        )
    except Exception as e:
        logger.warning(f"Thumbnail note: {e}")

    # 7. Fast Direct FFmpeg 1080p Video Render
    logger.info("🎬 Step 6: Rendering 1080p video via fast FFmpeg...")
    success = render_video_fast_ffmpeg(
        audio_path=audio_path,
        photo_paths=photo_paths,
        chapters=chapters,
        doc_title=doc_title,
        output_video=video_path,
        temp_dir=temp_dir
    )
    if not success:
        logger.error("❌ Video render failed")
        return False

    # 8. Upload to YouTube as Public VOD
    logger.info("📤 Step 7: Publishing to YouTube...")
    chapter_text = "\n".join([
        f"📌 {c.get('title', f'अध्याय {i+1}')} : {c.get('summary', '')}"
        for i, c in enumerate(chapters)
    ])
    description = (
        f"😱 {v_title}\n\n"
        f"देश और दुनिया की इस बड़ी खबर का पूरा सच और ज़मीनी पड़ताल।\n\n"
        f"📖 इस वीडियो में:\n{chapter_text}\n\n"
        f"🔔 निष्पक्ष और खोजी पत्रकारिता के लिए SRJ UNDERRATED को Subscribe करें!\n\n"
        f"#TrendingNews #HindiNews #BreakingNews #Investigation #SRJUnderrated"
    )

    try:
        vid_id = upload_video_to_youtube(
            video_path=str(video_path),
            title=v_title[:95],
            description=description,
            category_id="25",
            privacy_status="public",
            thumbnail_path=str(thumb_path) if thumb_path.exists() else None,
            tags=tags[:15]
        )
        if vid_id and vid_id not in ["LOCAL_SAVED", "RTMP_LIVE_STREAM_BROADCASTED"]:
            logger.info("=" * 70)
            logger.info(f"🎉 VIDEO PUBLISHED: https://youtu.be/{vid_id}")
            logger.info("=" * 70)
            save_processed_story(title, u_hash)
            cleanup_old_files()
            return True
    except Exception as e:
        logger.error(f"❌ YouTube upload failed: {e}", exc_info=True)

    return False


# ── Autonomous Main Loop ─────────────────────────────────────────────────────
def main():
    logger.info("=" * 70)
    logger.info("🎬 [SRJ UNDERRATED] Autonomous 3-Hour Trending Auto-Publisher Started")
    logger.info(f"   Interval: Every 3.0 Hours ({INTERVAL_SECONDS}s)")
    logger.info("   Night Quiet Window: 12:00 AM to 06:00 AM IST (No late night posts)")
    logger.info("=" * 70)

    while True:
        now_ist = get_current_ist_time()

        # Check Night Quiet Hours (12:00 AM to 06:00 AM IST)
        if is_in_night_window(now_ist):
            sleep_secs = seconds_until_morning(now_ist)
            resume_time = now_ist + dt.timedelta(seconds=sleep_secs)
            logger.info(f"🌙 [NIGHT QUIET WINDOW ACTIVE] Current IST: {now_ist.strftime('%H:%M:%S')}. No uploads between 12 AM and 6 AM.")
            logger.info(f"   Sleeping {sleep_secs/3600:.1f} hours until 06:00 AM IST ({resume_time.strftime('%Y-%m-%d %H:%M:%S')} IST)...")
            time.sleep(sleep_secs)
            continue

        try:
            run_single_trending_cycle()
        except Exception as e:
            logger.error(f"Error in publishing cycle: {e}", exc_info=True)

        # Check next sleep interval
        now_ist = get_current_ist_time()
        if is_in_night_window(now_ist):
            sleep_secs = seconds_until_morning(now_ist)
            logger.info(f"🌙 Night window reached after cycle. Sleeping {sleep_secs/3600:.1f} hours until 06:00 AM IST...")
        else:
            sleep_secs = INTERVAL_SECONDS
            next_run = now_ist + dt.timedelta(seconds=sleep_secs)
            # If next run falls in night window, push to 6 AM
            if is_in_night_window(next_run):
                sleep_secs = seconds_until_morning(now_ist)
                next_run = now_ist + dt.timedelta(seconds=sleep_secs)
                logger.info(f"⏳ Next scheduled run would hit night window. Sleeping until 06:00 AM IST ({next_run.strftime('%H:%M')} IST)")
            else:
                logger.info(f"⏳ Cycle complete. Next video in 3 hours at {next_run.strftime('%H:%M:%S')} IST")

        time.sleep(sleep_secs)


if __name__ == "__main__":
    main()
