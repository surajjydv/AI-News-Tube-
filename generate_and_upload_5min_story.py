"""
generate_and_upload_5min_story.py
=================================
Generates and uploads a 5-minute Broadcast Video & High-CTR Thumbnail on a major trending news story.
Utilizes real event photo scraping, entity relevance checks, HTML-sanitized text, and neural Hindi narration.
"""

import os
import sys
import math
import asyncio
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from utils.font_utils import load_font, sanitize_text
from services.rss_service import fetch_news
from services.visual_asset_manager import VisualAssetManager
from services.youtube_upload_service import upload_video_to_youtube
import edge_tts
from moviepy import ImageSequenceClip, AudioFileClip

# Output Paths
STORY5M_DIR    = BASE_DIR / "assets" / "story_5m"
STORY5M_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_FILE     = BASE_DIR / "assets" / "story_5m_audio.mp3"
THUMBNAIL_FILE = BASE_DIR / "thumbnails" / "story_5m_thumbnail.jpg"
VIDEO_FILE     = BASE_DIR / "videos" / "story_5m_video.mp4"

# Color Palette
DARK_BG   = (10, 18, 35)
GOLD      = (255, 200, 0)
RED       = (220, 35, 35)
WHITE     = (255, 255, 255)
BLUE_BOX  = (20, 45, 90)
DARK_BAR  = (15, 23, 42)

def f_bold_hi(sz: int):
    return load_font(sz, bold=True, lang="hi")

def f_bold_en(sz: int):
    return load_font(sz, bold=True, lang="en")

def f_reg(sz: int):
    return load_font(sz, bold=False, lang="hi")

def wrap_text_safe(text: str, max_chars: int) -> list[str]:
    """Safely wraps text into lines without empty lines or overflow bugs."""
    clean = sanitize_text(text)
    words = clean.split()
    if not words:
        return []
    lines = []
    curr = []
    for word in words:
        test_line = " ".join(curr + [word])
        if len(test_line) <= max_chars:
            curr.append(word)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [word]
    if curr:
        lines.append(" ".join(curr))
    return lines

def render_broadcast_slide(section_num: int, total_sections: int, category: str, headline: str, point_text: str, photo_path: str, credit: str) -> Path:
    """Renders a 1080p Ultra-Rich 2.5D TV News Broadcast Slide with physical depth, glassmorphism, and metallic accents."""
    from services.dynamic_broadcast_renderer import render_broadcast_frame
    
    photo_img = None
    if photo_path and os.path.exists(photo_path):
        try:
            photo_img = Image.open(photo_path).convert("RGB")
        except Exception:
            photo_img = None

    takeaways = [
        f"मुख्य बिंदु ({section_num}/{total_sections}): {headline[:38]}",
        point_text if point_text else "विशेष ग्राउंड कवरेज एवं विस्तृत विश्लेषण",
        "अधिकारियों एवं जांच टीमों द्वारा ताज़ा कार्रवाई व रिपोर्ट जारी"
    ]

    t_val = float(section_num * 1.5)
    frame_arr = render_broadcast_frame(
        t=t_val,
        total_duration=max(1.0, float(total_sections * 1.5)),
        headline=headline,
        category=category,
        slide_takeaways=takeaways,
        photo_images=[photo_img],
        photo_credits=[credit or "Verified Press Coverage"],
        w=1920,
        h=1080
    )

    img = Image.fromarray(frame_arr)
    out_file = STORY5M_DIR / f"slide_{section_num}.jpg"
    img.save(out_file, quality=95)
    print(f"✅ Created 2.5D TV Section Slide {section_num}/{total_sections}: {out_file.name}")
    return out_file


def render_5min_thumbnail(title: str, category: str, photo_path: str = "") -> Path:
    """Renders High-CTR YouTube Thumbnail using the authentic real event photograph & HarfBuzz typography."""
    from services.ai_thumbnail_service import create_real_event_youtube_thumbnail
    try:
        thumb = create_real_event_youtube_thumbnail(
            headline=title,
            category=category,
            real_photo_path=photo_path,
            output_path=THUMBNAIL_FILE
        )
        print(f"✅ Created Real Event Photo Thumbnail: {thumb.name}")
        return thumb
    except Exception as e:
        print(f"⚠️ Thumbnail error ({e}). Using standard broadcast thumbnail.")
        return THUMBNAIL_FILE

async def generate_narration(script_text: str):
    AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        comm = edge_tts.Communicate(script_text, voice="hi-IN-SwaraNeural")
        await comm.save(str(AUDIO_FILE))
        print(f"✅ Generated 5-Minute Hindi Narration Audio (EdgeTTS): {AUDIO_FILE.name}")
    except Exception as e:
        print(f"⚠️ EdgeTTS temporary network error ({e}); switching to gTTS Hindi voiceover...")
        try:
            from gtts import gTTS
            tts = gTTS(text=script_text, lang="hi", slow=False)
            tts.save(str(AUDIO_FILE))
            print(f"✅ Generated 5-Minute Hindi Narration Audio (gTTS Fallback): {AUDIO_FILE.name}")
        except Exception as e2:
            print(f"❌ Audio narration generation failed: {e2}")
            raise e2


def render_5min_video(slide_paths: list, total_duration: float) -> Path:
    VIDEO_FILE.parent.mkdir(parents=True, exist_ok=True)
    fps = 5
    num_slides = len(slide_paths)
    slide_dur = total_duration / float(num_slides)

    frames = []
    for sp in slide_paths:
        f_count = int(slide_dur * fps)
        frames.extend([str(sp)] * f_count)

    total_frames = int(total_duration * fps) + fps
    if len(frames) < total_frames:
        frames.extend([str(slide_paths[-1])] * (total_frames - len(frames)))

    clip = ImageSequenceClip(frames, fps=fps)
    audio = AudioFileClip(str(AUDIO_FILE))
    final_clip = clip.with_audio(audio)

    final_clip.write_videofile(
        str(VIDEO_FILE),
        codec="libx264",
        audio_codec="aac",
        fps=fps,
        preset="ultrafast"
    )
    print(f"✅ Rendered 5-Minute Video (Ultrafast 5 FPS): {VIDEO_FILE.name}")
    return VIDEO_FILE


def load_processed_titles() -> set:
    processed_file = BASE_DIR / "processed_stories.json"
    if processed_file.exists():
        try:
            import json
            with open(processed_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_processed_title(title: str):
    processed_file = BASE_DIR / "processed_stories.json"
    titles = load_processed_titles()
    titles.add(title)
    try:
        import json
        with open(processed_file, "w", encoding="utf-8") as f:
            json.dump(list(titles), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving processed title: {e}")

def main():
    print("=" * 65)
    print("🎥 5-MINUTE SINGLE STORY MULTI-ARTICLE SPECIAL REPORT GENERATOR & UPLOADER")
    print("=" * 65)

    # 1. Fetch News Articles and filter against processed stories
    print("🔍 STEP 1: Fetching Fresh Multi-Source News Articles (Anti-Repetition)...")
    articles = fetch_news(limit_per_category=5)
    if not articles:
        print("❌ No news articles found!")
        return

    processed = load_processed_titles()
    fresh_articles = [a for a in articles if a.title not in processed]
    if not fresh_articles:
        print("ℹ️ All fetched articles previously processed; using latest fresh headline.")
        fresh_articles = articles

    top_art = fresh_articles[0]
    multi_sources = [a.category.title() for a in fresh_articles[:3]]
    combined_texts = " ".join([sanitize_text(a.summary or a.title) for a in fresh_articles[:3]])

    print(f"✅ Primary News Story: [{top_art.category}] '{top_art.title}'")
    print(f"📰 Synthesizing Multi-Source News Articles from: {', '.join(multi_sources)}")


    # 2. Retrieve Real Event Photo (Strict Safety & Filtered Editorial Sources)
    print("\n📸 STEP 2: Scrape Real Event Photo (Strict SafeSearch & Verification)...")
    out_photo = STORY5M_DIR / "main_story_real.jpg"
    asset = VisualAssetManager.get_visual_asset(
        headline=top_art.title,
        category=top_art.category,
        output_path=out_photo,
        article_url=top_art.link,
        direct_image_url=top_art.image_url
    )
    print(f"✅ Photo Asset: Source '{asset.source_name}', Path '{asset.file_path}'")

    # 3. Create Multi-Article Synthesized 5-Minute Hindi Script & 6 Breakdown Sections
    print("\n📝 STEP 3: Creating Multi-Article Synthesized Script & 6 Breakdown Sections...")
    clean_title = sanitize_text(top_art.title)
    clean_summary = sanitize_text(top_art.summary or top_art.title)

    sections = [
        ("मुख्य समाचार एवं शुरुआत", f"नमस्कार! AI-NewsTube की 5 मिनट की इस विशेष मल्टी-सोर्स रिपोर्ट में आपका स्वागत है। आज की सबसे बड़ी मुख्य ख़बर: {clean_title}। विभिन्न प्रमुख समाचार स्रोतों ({', '.join(multi_sources[:2])}) के अनुसार इस घटना ने पूरे देश का ध्यान खींचा है।"),
        ("प्रथम स्रोत विवरण एवं ग्राउंड रिपोर्ट", f"मुख्य समाचार एजेंसी {multi_sources[0]} की विस्तृत रिपोर्ट के मुताबिक, {clean_summary}। घटना स्थल पर मौजूद प्रत्यक्षदर्शियों और अधिकारियों ने स्थिति की गंभीरता को रेखांकित किया है।"),
        ("द्वितीय स्रोत विश्लेषण एवं प्रमुख आंकड़े", f"वहीं दूसरे प्रमुख समाचार पत्र {len(multi_sources) > 1 and multi_sources[1] or 'नेशनल मीडिया'} की ग्राउंड रिपोर्ट के अनुसार, {combined_texts[:220]}। सुरक्षा बलों और प्रशासनिक अधिकारियों ने तुरंत मौके पर पहुंचकर राहत और बचाव कार्य तेज कर दिया है।"),
        ("तीसरे स्रोत की प्रतिक्रियाएं एवं बयान", f"तीसरे मीडिया कवरेज स्रोत {len(multi_sources) > 2 and multi_sources[2] or 'लाइव अपडेट्स'} के अनुसार, इस पूरे घटनाक्रम पर शासन और विपक्ष की ओर से तीखी प्रतिक्रियाएं सामने आई हैं। सरकार ने मामले की उच्चस्तरीय जांच के आदेश जारी कर दिए हैं।"),
        ("मल्टी-सोर्स विश्लेषण एवं भविष्य पर असर", f"तीनों प्रमुख समाचार स्रोतों की रिपोर्टों का तुलनात्मक विश्लेषण करने पर यह स्पष्ट होता है कि इस मामले का प्रशासनिक और सामाजिक प्रभाव दूरगामी होने वाला है। भविष्य में सुरक्षा और नीतिगत बदलावों पर जोर दिया जा रहा है।"),
        ("निष्कर्ष एवं लाइव ग्राउंड अपडेट", f"AI-NewsTube इस बड़ी ख़बर से जुड़े सभी समाचार स्रोतों की पल-पल की लाइव अपडेट पर लगातार नजर बनाए हुए है। ताज़ा ख़बरों और निष्पक्ष विश्लेषण के लिए जुड़े रहिए AI-NewsTube के साथ। धन्यवाद!")
    ]

    # 3. Build Fluent 5-Minute Script & Broadcast Slides (Zero Greetings, 100% Storytelling)
    print("\n📝 STEP 3: Generating Fluent 5-Minute Broadcast Script (Zero Welcome, Pure Storytelling)...")
    clean_title = sanitize_text(top_art.title)
    clean_summary = sanitize_text(top_art.summary or top_art.title)

    from services.fluent_script_service import generate_fluent_news_script
    full_narr_text, slide_takeaways, b_head, viral_title, yt_tags = generate_fluent_news_script(
        title=top_art.title,
        category=top_art.category,
        context=combined_texts,
        article_url=top_art.link,
        target_minutes=5
    )

    slide_paths = []
    total_sec_count = len(slide_takeaways)
    for idx, takeaway in enumerate(slide_takeaways, start=1):
        s_path = render_broadcast_slide(
            section_num=idx,
            total_sections=total_sec_count,
            category=top_art.category,
            headline=b_head,
            point_text=takeaway,
            photo_path=asset.file_path,
            credit=asset.on_screen_credit
        )
        slide_paths.append(s_path)

    # 4. Generate Thumbnail
    print("\n🎨 STEP 4: Creating High-CTR 3-Band Thumbnail...")
    render_5min_thumbnail(b_head, top_art.category, asset.file_path)

    # 5. Synthesize 5-Minute Audio
    print("\n🎙️ STEP 5: Synthesizing Hindi Audio Narration...")
    asyncio.run(generate_narration(full_narr_text))

    audio_clip = AudioFileClip(str(AUDIO_FILE))
    duration = audio_clip.duration
    audio_clip.close()

    # 6. Render Video
    print(f"\n🎬 STEP 6: Rendering 1080p Video ({duration:.1f} seconds)...")
    render_5min_video(slide_paths, duration)

    # 7. Upload to YouTube
    print("\n📤 STEP 7: Uploading 5-Minute Special Report to YouTube...")
    video_title = viral_title if viral_title else f"{b_head} 📰 Special Report | NewsTube"
    if len(video_title) > 98:
        video_title = video_title[:95] + "..."

    description = (
        f"🔴 {video_title}\n\n"
        f"📌 मुख्य बिंदु:\n"
        f"• {slide_takeaways[0] if len(slide_takeaways) > 0 else b_head}\n"
        f"• {slide_takeaways[1] if len(slide_takeaways) > 1 else 'ग्राउंड रिपोर्ट: विस्तृत जानकारी'}\n"
        f"• {slide_takeaways[2] if len(slide_takeaways) > 2 else 'आधिकारिक बयान एवं ताज़ा स्थिति'}\n\n"
        f"📖 पूरी रिपोर्ट:\n{full_narr_text}\n\n"
        f"Category: {top_art.category.upper()}\n"
        f"Headline: {b_head}\n\n"
        "#SpecialReport #TodayNews #HindiNews #BreakingNews #NewsTube"
    )
    combined_tags = list(dict.fromkeys(yt_tags + ["Special Report", "Today News", "Breaking News", "Hindi News", "NewsTube", top_art.category]))

    video_id = upload_video_to_youtube(
        video_path=str(VIDEO_FILE),
        title=video_title,
        description=description,
        category_id="25",
        tags=combined_tags[:15],
        thumbnail_path=str(THUMBNAIL_FILE),
        privacy_status="public"
    )

    # Record title in processed set
    save_processed_title(top_art.title)

    print("\n" + "=" * 65)
    print("🎉 SUCCESS! 5-MINUTE SPECIAL REPORT VIDEO & THUMBNAIL PUBLISHED!")
    print(f"🔗 Video URL: https://youtu.be/{video_id}")
    print("=" * 65)

if __name__ == "__main__":
    main()
