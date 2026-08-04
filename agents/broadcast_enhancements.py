import os, sys, re, math, time, asyncio, random, hashlib
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.video_agent import _load_font
from utils.logger import logger


class CategoryGraphicsEngine:
    SENSEX_TICKS = [81200,81350,81180,81420,81390,81455,81510,81480,81620,81580]
    NIFTY_TICKS  = [24720,24790,24735,24855,24820,24870,24910,24890,24960,24940]

    @classmethod
    def render_finance_chart_overlay(cls, frame, global_t):
        w, h = frame.size
        cw, ch = 340, 200
        cx, cy = w - cw - 20, 100
        chart = Image.new("RGBA", (cw, ch), (8,12,26,230))
        draw = ImageDraw.Draw(chart)
        draw.rounded_rectangle([(0,0),(cw-1,ch-1)], radius=12, outline=(255,215,0), width=2)
        draw.rectangle([(0,0),(cw-1,34)], fill=(16,22,50,255))
        draw.text((10,8), "MARKETS LIVE", fill=(255,215,0), font=_load_font(16, bold=True))
        tick_count = len(cls.SENSEX_TICKS)
        bar_w = (cw-30)//tick_count
        max_v, min_v = max(cls.SENSEX_TICKS), min(cls.SENSEX_TICKS)
        rng = max_v - min_v or 1
        chart_top, chart_bot = 40, ch-50
        for i, val in enumerate(cls.SENSEX_TICKS):
            x1 = 15 + i*bar_w
            bar_h = int(((val-min_v)/rng)*(chart_bot-chart_top))
            y1 = chart_bot - bar_h
            is_up = (i==0) or (val >= cls.SENSEX_TICKS[i-1])
            color = (34,197,94) if is_up else (239,68,68)
            draw.rectangle([(x1,y1),(x1+bar_w-3,chart_bot)], fill=color)
        s_last = cls.SENSEX_TICKS[-1]
        n_last = cls.NIFTY_TICKS[-1]
        pulse = abs(math.sin(global_t*4.0))
        up_color = (34,197,94) if s_last > cls.SENSEX_TICKS[-2] else (239,68,68)
        draw.text((10,ch-44), f"SENSEX {s_last:,}", fill=up_color, font=_load_font(14,bold=True))
        draw.text((10,ch-26), f"NIFTY  {n_last:,}", fill=(34,197,94), font=_load_font(14,bold=True))
        dot_r = int(4+2*pulse)
        draw.ellipse([(cw-20-dot_r,12-dot_r),(cw-20+dot_r,12+dot_r)], fill=(239,68,68,int(200+55*pulse)))
        frame_rgba = frame.convert("RGBA")
        frame_rgba.paste(chart, (cx,cy), chart)
        return frame_rgba.convert("RGB")

    @classmethod
    def render_sports_scorecard(cls, frame, team1="IND", team2="AUS", score1="287/6", score2="240", overs="45.2 OV"):
        w, h = frame.size
        cw, ch = 320, 140
        cx, cy = w-cw-20, 100
        sc = Image.new("RGBA", (cw,ch), (5,10,22,240))
        draw = ImageDraw.Draw(sc)
        draw.rounded_rectangle([(0,0),(cw-1,ch-1)], radius=10, outline=(255,165,0), width=2)
        draw.rectangle([(0,0),(cw-1,32)], fill=(14,28,60,255))
        draw.text((10,7), "LIVE CRICKET", fill=(255,165,0), font=_load_font(15,bold=True))
        draw.text((cw-90,7), f"{overs}", fill=(255,255,255), font=_load_font(14))
        draw.text((10,42), f"IND {team1}", fill=(255,255,255), font=_load_font(20,bold=True))
        draw.text((10,68), score1, fill=(34,197,94), font=_load_font(24,bold=True))
        draw.line([(cw//2-1,36),(cw//2-1,ch-10)], fill=(255,215,0), width=2)
        draw.text((cw//2+10,42), f"AUS {team2}", fill=(200,200,200), font=_load_font(20,bold=True))
        draw.text((cw//2+10,68), score2, fill=(239,68,68), font=_load_font(24,bold=True))
        draw.text((cw//2-30,ch-26), "TARGET: 288", fill=(255,215,0), font=_load_font(13,bold=True))
        frame_rgba = frame.convert("RGBA")
        frame_rgba.paste(sc, (cx,cy), sc)
        return frame_rgba.convert("RGB")

    @classmethod
    def render_weather_widget(cls, frame, city="NEW DELHI", temp="34 C", condition="SUNNY"):
        w, h = frame.size
        cw, ch = 280, 120
        cx, cy = w-cw-20, 100
        ww = Image.new("RGBA", (cw,ch), (10,18,40,235))
        draw = ImageDraw.Draw(ww)
        draw.rounded_rectangle([(0,0),(cw-1,ch-1)], radius=10, outline=(100,180,255), width=2)
        draw.rectangle([(0,0),(cw-1,30)], fill=(20,50,100,255))
        draw.text((10,6), "WEATHER LIVE", fill=(100,200,255), font=_load_font(14,bold=True))
        draw.text((10,38), city, fill=(255,255,255), font=_load_font(17,bold=True))
        draw.text((10,62), f"{temp}", fill=(255,220,50), font=_load_font(28,bold=True))
        draw.text((10,98), condition, fill=(180,220,255), font=_load_font(14))
        frame_rgba = frame.convert("RGBA")
        frame_rgba.paste(ww, (cx,cy), ww)
        return frame_rgba.convert("RGB")

    @classmethod
    def render_tech_badge(cls, frame, entity="ISRO", global_t=0.0):
        w, h = frame.size
        cw, ch = 260, 100
        cx, cy = w-cw-20, 100
        tb = Image.new("RGBA", (cw,ch), (5,15,35,240))
        draw = ImageDraw.Draw(tb)
        pulse = abs(math.sin(global_t*3.0))
        border_color = (int(0+100*pulse), int(100+100*pulse), int(255-50*pulse), 255)
        draw.rounded_rectangle([(0,0),(cw-1,ch-1)], radius=10, outline=border_color, width=3)
        org_icons = {"ISRO":"ISRO","NASA":"NASA","RBI":"RBI","SEBI":"SEBI",
                     "SUPREME COURT":"SC","BCCI":"BCCI","GOOGLE":"GOOG",
                     "MICROSOFT":"MSFT","PARLIAMENT":"PARL"}
        icon_text = org_icons.get(entity.upper(), entity[:4])
        draw.text((10,15), icon_text, fill=(255,215,0), font=_load_font(30,bold=True))
        draw.text((10,62), entity.upper()[:18], fill=(200,220,255), font=_load_font(16,bold=True))
        draw.text((10,82), "IN FOCUS", fill=(150,200,255), font=_load_font(12))
        frame_rgba = frame.convert("RGBA")
        frame_rgba.paste(tb, (cx,cy), tb)
        return frame_rgba.convert("RGB")

    @classmethod
    def apply_category_overlay(cls, frame, category, headline, global_t):
        cat_lower = category.lower()
        head_lower = headline.lower()
        if any(k in cat_lower or k in head_lower for k in ["finance","market","sensex","economy","stock","rbi","budget"]):
            return cls.render_finance_chart_overlay(frame, global_t)
        if any(k in cat_lower or k in head_lower for k in ["sports","cricket","ipl","t20","football","match"]):
            return cls.render_sports_scorecard(frame)
        if any(k in cat_lower or k in head_lower for k in ["weather","rain","flood","monsoon","cyclone"]):
            cities = [("NEW DELHI","34 C","SUNNY"),("MUMBAI","29 C","HEAVY RAIN"),("BENGALURU","26 C","SHOWERS")]
            city, temp, cond = cities[int(global_t/5.0) % len(cities)]
            return cls.render_weather_widget(frame, city, temp, cond)
        orgs = ["ISRO","RBI","SEBI","SUPREME COURT","BCCI","GOOGLE","MICROSOFT","PARLIAMENT"]
        matched = next((o for o in orgs if o.lower() in head_lower), None)
        if matched:
            return cls.render_tech_badge(frame, matched, global_t)
        return frame


class EntityExtractor:
    PERSONS = {"modi":"PM Modi","yogi":"CM Yogi","rahul":"Rahul Gandhi","kejriwal":"Arvind Kejriwal",
               "virat":"Virat Kohli","rohit":"Rohit Sharma","dhoni":"MS Dhoni","trump":"Donald Trump","musk":"Elon Musk"}
    ORGS = {"isro":"ISRO","nasa":"NASA","rbi":"RBI","sebi":"SEBI","bcci":"BCCI","ipl":"IPL","bjp":"BJP",
            "congress":"Congress","supreme court":"SUPREME COURT","parliament":"PARLIAMENT",
            "google":"GOOGLE","apple":"APPLE","microsoft":"MICROSOFT","amazon":"AMAZON","cbi":"CBI"}
    LOCATIONS = {"delhi":"NEW DELHI","mumbai":"MUMBAI","kolkata":"KOLKATA","bengaluru":"BENGALURU",
                 "chennai":"CHENNAI","lucknow":"LUCKNOW","china":"CHINA","pakistan":"PAKISTAN",
                 "russia":"RUSSIA","america":"USA","usa":"USA","ukraine":"UKRAINE"}

    @classmethod
    def extract(cls, text):
        text_lower = text.lower()
        return {
            "persons":   [v for k,v in cls.PERSONS.items() if k in text_lower][:3],
            "orgs":      [v for k,v in cls.ORGS.items() if k in text_lower][:3],
            "locations": [v for k,v in cls.LOCATIONS.items() if k in text_lower][:3],
        }

    @classmethod
    def get_primary_entity(cls, text):
        r = cls.extract(text)
        return r["orgs"][0] if r["orgs"] else (r["persons"][0] if r["persons"] else None)


class DualAnchorVoice:
    FEMALE_VOICE = "hi-IN-SwaraNeural"
    MALE_VOICE   = "hi-IN-MadhurNeural"
    _last_used   = "female"

    @classmethod
    def get_next_voice(cls):
        if cls._last_used == "female":
            cls._last_used = "male"
            return cls.MALE_VOICE
        else:
            cls._last_used = "female"
            return cls.FEMALE_VOICE

    @classmethod
    def generate_dual_voiceover(cls, script_text, output_path, force_voice=None):
        voice = force_voice or cls.get_next_voice()
        logger.info(f"  Dual Anchor Voice: Using '{voice}'")
        try:
            import edge_tts
            async def _run():
                c = edge_tts.Communicate(script_text, voice=voice, rate="+5%")
                await c.save(str(output_path))
            try:
                asyncio.run(_run())
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(_run())
                finally:
                    loop.close()
            if output_path.exists() and output_path.stat().st_size > 1000:
                logger.info(f"  Dual Anchor: {voice} voiceover generated!")
                return True
        except Exception as e:
            logger.warning(f"  Dual Anchor edge-tts error: {e}")
        try:
            from gtts import gTTS
            tts = gTTS(text=script_text, lang="hi", slow=False)
            tts.save(str(output_path))
            return output_path.exists() and output_path.stat().st_size > 500
        except Exception as e:
            logger.error(f"  Dual Anchor gTTS fallback failed: {e}")
            return False


class KenBurnsMotion:
    MODES = ["push_in","pull_out","pan_left","pan_right","tilt_up"]

    @classmethod
    def apply(cls, frame, t, duration, mode="push_in"):
        w, h = frame.size
        progress = min(1.0, t / max(duration, 0.001))
        ease = progress * progress * (3 - 2*progress)
        try:
            if mode == "push_in":
                scale = 1.0 + 0.10*ease
                nw, nh = int(w*scale), int(h*scale)
                resized = frame.resize((nw,nh), Image.Resampling.LANCZOS)
                ox, oy = (nw-w)//2, (nh-h)//2
                return resized.crop((ox,oy,ox+w,oy+h))
            elif mode == "pull_out":
                scale = 1.10 - 0.10*ease
                nw, nh = int(w*scale), int(h*scale)
                resized = frame.resize((nw,nh), Image.Resampling.LANCZOS)
                ox, oy = (nw-w)//2, (nh-h)//2
                return resized.crop((ox,oy,ox+w,oy+h))
            elif mode == "pan_left":
                nw = int(w*1.08)
                resized = frame.resize((nw,h), Image.Resampling.LANCZOS)
                ox = int((nw-w)*(1.0-ease))
                return resized.crop((ox,0,ox+w,h))
            elif mode == "pan_right":
                nw = int(w*1.08)
                resized = frame.resize((nw,h), Image.Resampling.LANCZOS)
                ox = int((nw-w)*ease)
                return resized.crop((ox,0,ox+w,h))
            elif mode == "tilt_up":
                nh = int(h*1.08)
                resized = frame.resize((w,nh), Image.Resampling.LANCZOS)
                oy = int((nh-h)*(1.0-ease))
                return resized.crop((0,oy,w,oy+h))
        except Exception as e:
            logger.warning(f"KenBurns {mode} error: {e}")
        return frame

    @classmethod
    def get_mode_for_category(cls, category):
        cat = category.lower()
        if any(k in cat for k in ["breaking","alert","live"]): return "push_in"
        if any(k in cat for k in ["sports","cricket"]): return "pan_right"
        if any(k in cat for k in ["finance","market","economy"]): return "pan_left"
        if any(k in cat for k in ["weather","rain","flood"]): return "tilt_up"
        return random.choice(cls.MODES)


class MotionStinger:
    @classmethod
    def render_stinger_frame(cls, w, h, progress, stinger_type="wipe_left",
                              color1=(180,15,20), color2=(255,215,0)):
        frame = Image.new("RGB", (w,h), (0,0,0))
        draw  = ImageDraw.Draw(frame)
        ease  = progress * progress * (3 - 2*progress)
        if stinger_type == "wipe_left":
            wipe_x = int(w*ease)
            draw.rectangle([(0,0),(wipe_x,h)], fill=color1)
            draw.rectangle([(max(0,wipe_x-6),0),(wipe_x,h)], fill=color2)
        elif stinger_type == "diagonal_split":
            slash = int(w*ease)
            draw.polygon([(0,0),(slash,0),(slash-200,h),(0,h)], fill=color1)
            draw.polygon([(slash-10,0),(slash+10,0),(slash-190,h),(slash-210,h)], fill=color2)
        elif stinger_type == "gold_sweep":
            sweep_x = int((w+200)*ease)-100
            draw.polygon([(sweep_x-80,0),(sweep_x+80,0),(sweep_x+40,h),(sweep_x-120,h)], fill=color2)
            try:
                draw.text((w//2-120, h//2-20), "AI-NEWSTUBE", fill=(255,255,255), font=_load_font(40,bold=True))
            except Exception:
                pass
        return frame

    @classmethod
    def generate_stinger_frames(cls, w=1280, h=720, stinger_type="wipe_left", fps=15, duration=0.5):
        total_frames = max(1, int(fps*duration))
        return [cls.render_stinger_frame(w,h,i/max(total_frames-1,1), stinger_type) for i in range(total_frames)]


class StoryDeduplicator:
    _seen_hashes: set = set()
    _PERSIST_FILE = BASE_DIR / "data" / "seen_stories.json"

    @classmethod
    def _load_seen(cls):
        try:
            import json
            if cls._PERSIST_FILE.exists():
                with open(cls._PERSIST_FILE,"r",encoding="utf-8") as f:
                    cls._seen_hashes = set(json.load(f).get("hashes",[]))
        except Exception:
            cls._seen_hashes = set()

    @classmethod
    def _save_seen(cls):
        try:
            import json
            cls._PERSIST_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(cls._PERSIST_FILE,"w",encoding="utf-8") as f:
                json.dump({"hashes": list(cls._seen_hashes)[-500:]}, f)
        except Exception:
            pass

    @classmethod
    def _fingerprint(cls, text):
        clean = re.sub(r'[^\w\s]', '', text.lower())
        clean = re.sub(r'\s+', ' ', clean).strip()
        return hashlib.md5(clean[:60].encode()).hexdigest()

    @classmethod
    def is_seen(cls, headline):
        cls._load_seen()
        return cls._fingerprint(headline) in cls._seen_hashes

    @classmethod
    def mark_seen(cls, headline):
        cls._seen_hashes.add(cls._fingerprint(headline))
        cls._save_seen()

    @classmethod
    def filter_unseen(cls, headlines):
        cls._load_seen()
        unseen = []
        for h in headlines:
            fp = cls._fingerprint(h)
            if fp not in cls._seen_hashes:
                unseen.append(h)
                cls._seen_hashes.add(fp)
        cls._save_seen()
        logger.info(f"  Deduplicator: {len(unseen)}/{len(headlines)} stories are new")
        return unseen

    @classmethod
    def reset(cls):
        cls._seen_hashes = set()
        if cls._PERSIST_FILE.exists():
            cls._PERSIST_FILE.unlink()


# Cache for loaded studio assets in memory to maximize performance
_STUDIO_BG_CACHE = None
_ANCHOR_IMG_CACHE = None
_LOGO_IMG_CACHE = None

def _get_studio_assets() -> Tuple[Image.Image, Image.Image, Optional[Image.Image]]:
    """Loads and caches the 3D news studio background, anchor, and channel logo."""
    global _STUDIO_BG_CACHE, _ANCHOR_IMG_CACHE, _LOGO_IMG_CACHE
    from config.settings import ASSETS_DIR
    studio_dir = ASSETS_DIR / "studio"
    bg_path = studio_dir / "studio_background.png"
    anchor_path = studio_dir / "ai_anchor_3d.png"
    logo_path = studio_dir / "channel_logo_3d.png"

    # Generate if missing
    from agents.graphics_agent import create_studio_background, generate_ai_anchor, create_3d_channel_logo
    if not bg_path.exists():
        create_studio_background()
    if not anchor_path.exists():
        generate_ai_anchor()
    if not logo_path.exists():
        create_3d_channel_logo()

    if _STUDIO_BG_CACHE is None and bg_path.exists():
        _STUDIO_BG_CACHE = Image.open(str(bg_path)).convert("RGB")
    if _ANCHOR_IMG_CACHE is None and anchor_path.exists():
        _ANCHOR_IMG_CACHE = Image.open(str(anchor_path)).convert("RGBA")
    if _LOGO_IMG_CACHE is None and logo_path.exists():
        try:
            _LOGO_IMG_CACHE = Image.open(str(logo_path)).convert("RGBA")
        except Exception:
            _LOGO_IMG_CACHE = None

    bg = _STUDIO_BG_CACHE or Image.new("RGB", (1920, 1080), (10, 14, 30))
    anchor = _ANCHOR_IMG_CACHE or Image.new("RGBA", (600, 900), (0, 0, 0, 0))
    return bg, anchor, _LOGO_IMG_CACHE


def render_production_3d_studio_frame(
    headline_text: str,
    news_photo_path: Optional[str],
    global_t: float = 0.0,
    category: str = "TOP STORIES",
    ticker_headlines: Optional[List[str]] = None,
    quick_cards: Optional[List[str]] = None,
    script_text: str = "",
    enable_ken_burns: bool = True,
    clip_duration: float = 30.0,
    ken_burns_mode: Optional[str] = None,
    enable_subtitles: bool = True,
    enable_emotion_theme: bool = True,
    speech_level: float = 0.0,
) -> Image.Image:
    """
    Renders a true 1080p 3D Virtual Newsroom Studio frame:
    - 3D Studio Space Background
    - Left-side 3D LED Screen displaying the news photo with 3D border highlights
    - 3D news desk surface with 24-channel animated audio spectrum VU meters
    - Rigged 3D humanoid presenter avatar seated with audio lip-sync mouth animation
    - Handheld sways, dolly zoom, and parallax camera motion transforms
    - Lower third banners, Scrolling marquees, IST Clock, CC Subtitles, and Emotion border glow
    """
    w, h = 1920, 1080
    studio_bg, anchor_img, logo_img = _get_studio_assets()

    # 1. Start with copy of the 3D newsroom background
    base_frame = studio_bg.copy()
    draw = ImageDraw.Draw(base_frame)

    # 2. Paste News Photo on Left 3D LED Screen
    pip_x, pip_y = 80, 120
    pip_w, pip_h = 580, 380
    if news_photo_path and Path(news_photo_path).exists():
        try:
            with Image.open(str(news_photo_path)) as img:
                resized_pip = img.convert("RGB").resize((pip_w, pip_h), Image.Resampling.LANCZOS)
                base_frame.paste(resized_pip, (pip_x, pip_y))
        except Exception:
            draw.rectangle([(pip_x, pip_y), (pip_x + pip_w, pip_y + pip_h)], fill=(12, 16, 32))
    else:
        draw.rectangle([(pip_x, pip_y), (pip_x + pip_w, pip_y + pip_h)], fill=(12, 16, 32))

    # Glow border on LED Screen
    pulse = 0.6 + 0.4 * abs(math.sin(global_t * 2.5))
    theme = EmotionThemeEngine.get_theme(category, headline_text)
    accent_color = theme["accent"]
    for thick in range(4):
        draw.rectangle(
            [(pip_x - thick, pip_y - thick), (pip_x + pip_w + thick, pip_y + pip_h + thick)],
            outline=accent_color
        )
    draw.rectangle([(pip_x, pip_y), (pip_x + 130, pip_y + 30)], fill=accent_color)
    draw.text((pip_x + 12, pip_y + 6), "🔴 LIVE REPORT", fill=(255, 255, 255), font=_load_font(16, bold=True))

    # 3. Presenter Avatar with Lip-Sync Mouth Animation
    anchor_h = h - 280
    anchor_aspect = anchor_img.width / anchor_img.height
    anchor_w = int(anchor_h * anchor_aspect)
    
    # Presenter sway animation
    sway_x = int(math.sin(global_t * 1.5) * 4)
    sway_y = int(math.sin(global_t * 3.0) * 2)
    anchor_x = w - anchor_w - 90 + sway_x
    anchor_y = 10 + sway_y

    # Render talking mouth
    from agents.video_agent import _render_talking_anchor
    talking_anchor = _render_talking_anchor(anchor_img, anchor_w, anchor_h, speech_level, global_t)
    base_frame.paste(talking_anchor, (anchor_x, anchor_y), talking_anchor)

    # 4. Animated 24-Channel Audio Equalizer VU Meters on News Desk
    from agents.video_agent import _draw_audio_spectrum
    _draw_audio_spectrum(draw, speech_level, global_t, start_x=160, start_y=800, num_bars=24)

    # 5. Camera Cut & Motion Transformation
    progress = min(1.0, max(0.0, (global_t % 15.0) / 15.0))
    cam_mode = int(global_t // 3.5) % 4

    if cam_mode == 0:
        # Push-in zoom
        zoom = 1.0 + 0.08 * (progress ** 1.2)
        cw_crop = int(w / zoom)
        ch_crop = int(h / zoom)
        cx_crop = (w - cw_crop) // 2
        cy_crop = (h - ch_crop) // 2
        camera_layer = base_frame.crop((cx_crop, cy_crop, cx_crop + cw_crop, cy_crop + ch_crop)).resize((w, h), Image.Resampling.LANCZOS)
    elif cam_mode == 1:
        # Parallax Pan
        pan = int(60 * math.sin(progress * math.pi))
        cw_crop = int(w * 0.92)
        ch_crop = int(h * 0.92)
        cx_crop = max(0, min(w - cw_crop, (w - cw_crop) // 2 + pan))
        cy_crop = (h - ch_crop) // 2
        camera_layer = base_frame.crop((cx_crop, cy_crop, cx_crop + cw_crop, cy_crop + ch_crop)).resize((w, h), Image.Resampling.LANCZOS)
    elif cam_mode == 2:
        # Media Screen Focus
        camera_layer = base_frame.crop((0, 0, 1320, 1080)).resize((w, h), Image.Resampling.LANCZOS)
    else:
        # Handheld newsroom sway
        shoff_x = int(8 * math.sin(global_t * 2.2))
        shoff_y = int(5 * math.cos(global_t * 1.8))
        cw_crop = int(w / 1.04)
        ch_crop = int(h / 1.04)
        cx_crop = max(0, min(w - cw_crop, (w - cw_crop) // 2 + shoff_x))
        cy_crop = max(0, min(h - ch_crop, (h - ch_crop) // 2 + shoff_y))
        camera_layer = base_frame.crop((cx_crop, cy_crop, cx_crop + cw_crop, cy_crop + ch_crop)).resize((w, h), Image.Resampling.LANCZOS)

    # 6. Apply Broadcast HUD UI Overlay Layer (Clock, Lower Third, Marquee, Ticker)
    from agents.graphics_agent import BroadcastLayerSystem
    layer_system = BroadcastLayerSystem(width=w, height=h)
    
    # Layer 2: 3D logo
    camera_layer = layer_system.render_layer_2_studio_elements(camera_layer, logo_img)
    # Layer 3: Headline banner
    camera_layer = layer_system.render_layer_3_headline(camera_layer, headline_text, category, global_t % 5.0, global_t)
    # Layer 4: Live IST clock & weather badge
    camera_layer = layer_system.render_layer_4_hud(camera_layer, global_t, cam_mode)
    # Layer 5: BottomScrolling News Ticker Marquee
    camera_layer = layer_system.render_layer_5_ticker(camera_layer, global_t, ticker_headlines)
    # Layer 6: spec sweep light effects
    camera_layer = layer_system.render_layer_6_effects(camera_layer, global_t)

    # 7. Apply Category Overlays (Sensex candles, sports scorecards)
    camera_layer = CategoryGraphicsEngine.apply_category_overlay(camera_layer, category, headline_text, global_t)

    # 8. Apply Subtitle bar
    if enable_subtitles and script_text:
        camera_layer = SubtitleRenderer.render_subtitle_bar(camera_layer, script_text, global_t, clip_duration)

    # 9. Apply border emotion glow
    if enable_emotion_theme:
        camera_layer = EmotionThemeEngine.render_emotion_indicator(camera_layer, category, headline_text, global_t)

    return camera_layer


def render_enhanced_broadcast_frame(
    headline_text: str,
    news_photo_path: Optional[str],
    global_t: float = 0.0,
    category: str = "TOP STORIES",
    ticker_headlines: Optional[List[str]] = None,
    quick_cards: Optional[List[str]] = None,
    enable_ken_burns: bool = True,
    clip_duration: float = 30.0,
    ken_burns_mode: Optional[str] = None,
) -> Image.Image:
    # Routes to the production 3D virtual studio frame composition engine
    # Sets speech_level=0.5 (talking animation) for live stream keyframes
    pulse_speech = 0.3 + 0.4 * abs(math.sin(global_t * 6.0))
    return render_production_3d_studio_frame(
        headline_text=headline_text, news_photo_path=news_photo_path,
        global_t=global_t, category=category,
        ticker_headlines=ticker_headlines, quick_cards=quick_cards,
        enable_ken_burns=enable_ken_burns, clip_duration=clip_duration,
        ken_burns_mode=ken_burns_mode, enable_subtitles=False,
        enable_emotion_theme=True, speech_level=pulse_speech
    )

# ─────────────────────────────────────────────────────────────────────────────
# 7. SUBTITLE RENDERER (inspired by broadcastos/composer/subtitle_renderer.py)
# ─────────────────────────────────────────────────────────────────────────────

class SubtitleRenderer:
    """
    Renders real-time CC-style subtitles at the bottom of the broadcast frame.
    Words appear progressively synced to the approximate audio playback time.
    """

    @classmethod
    def render_subtitle_bar(cls, frame: Image.Image, script_text: str,
                             global_t: float, clip_duration: float) -> Image.Image:
        """Renders a CC subtitle bar with word-by-word progressive reveal."""
        if not script_text:
            return frame
        w, h = frame.size
        words = script_text.split()
        if not words:
            return frame
        # Estimate how many words shown based on time (avg 3 words/second)
        words_per_sec = 3.0
        visible_count = min(len(words), max(1, int(global_t * words_per_sec)))
        # Show a sliding window of last 8 words
        start_idx = max(0, visible_count - 8)
        visible_words = words[start_idx:visible_count]
        subtitle_text = " ".join(visible_words)
        if not subtitle_text.strip():
            return frame
        sub_bar = Image.new("RGBA", (w, 52), (0, 0, 0, 0))
        sub_draw = ImageDraw.Draw(sub_bar)
        # Dark glassmorphic background
        sub_draw.rectangle([(0, 0), (w, 52)], fill=(8, 8, 16, 210))
        sub_draw.rectangle([(0, 0), (w, 3)], fill=(255, 215, 0, 200))
        font = _load_font(22, bold=True)
        try:
            text_w = int(sub_draw.textlength(subtitle_text, font=font))
        except Exception:
            text_w = len(subtitle_text) * 13
        tx = max(20, (w - text_w) // 2)
        # Drop shadow
        sub_draw.text((tx + 2, 17), subtitle_text, fill=(0, 0, 0, 200), font=font)
        sub_draw.text((tx, 15), subtitle_text, fill=(255, 255, 255, 255), font=font)
        frame_rgba = frame.convert("RGBA")
        # Paste at subtitle position (above ticker, below headline banner)
        sub_y = h - 145
        frame_rgba.paste(sub_bar, (0, sub_y), sub_bar)
        return frame_rgba.convert("RGB")


# ─────────────────────────────────────────────────────────────────────────────
# 8. EMOTION / THEME ENGINE (inspired by broadcastos/character/emotion_controller.py)
# ─────────────────────────────────────────────────────────────────────────────

class EmotionThemeEngine:
    """
    Dynamically changes the broadcast color theme based on news emotion/category.
    - Breaking/Crime/Disaster: RED theme (urgent, alert)
    - Finance/Economy: BLUE theme (professional, calm)
    - Sports: GREEN/ORANGE theme (energetic)
    - Tech/Space: CYAN theme (futuristic)
    - Politics: PURPLE theme (authority)
    - Normal: Default GOLD theme
    """

    THEMES = {
        "breaking":  {"accent": (220,15,20),  "glow": (255,50,50),   "badge": "BREAKING"},
        "crime":     {"accent": (180,10,10),  "glow": (255,30,30),   "badge": "ALERT"},
        "disaster":  {"accent": (200,80,0),   "glow": (255,120,0),   "badge": "DISASTER"},
        "finance":   {"accent": (10,80,200),  "glow": (50,150,255),  "badge": "MARKETS"},
        "sports":    {"accent": (20,140,20),  "glow": (50,200,50),   "badge": "SPORTS"},
        "technology":{"accent": (0,180,200),  "glow": (0,230,255),   "badge": "TECH"},
        "politics":  {"accent": (100,20,180), "glow": (150,80,255),  "badge": "POLITICS"},
        "default":   {"accent": (180,15,20),  "glow": (255,215,0),   "badge": "NEWS"},
    }

    @classmethod
    def get_theme(cls, category: str, headline: str) -> dict:
        """Returns the correct theme dict for this news story."""
        cat = category.lower()
        head = headline.lower()
        if any(k in cat or k in head for k in ["break","alert","murder","crime","attack","blast"]):
            return cls.THEMES["breaking"]
        if any(k in cat or k in head for k in ["flood","earthquake","fire","disaster","cyclone","relief"]):
            return cls.THEMES["disaster"]
        if any(k in cat or k in head for k in ["sensex","nifty","market","economy","rbi","budget","stock","finance"]):
            return cls.THEMES["finance"]
        if any(k in cat or k in head for k in ["cricket","sports","ipl","football","match","gold medal"]):
            return cls.THEMES["sports"]
        if any(k in cat or k in head for k in ["tech","isro","nasa","ai","software","google","space","satellite"]):
            return cls.THEMES["technology"]
        if any(k in cat or k in head for k in ["modi","parliament","election","bjp","congress","government"]):
            return cls.THEMES["politics"]
        return cls.THEMES["default"]

    @classmethod
    def render_emotion_indicator(cls, frame: Image.Image, category: str,
                                  headline: str, global_t: float) -> Image.Image:
        """Renders a subtle colored emotion border glow at frame edges."""
        theme = cls.get_theme(category, headline)
        accent = theme["accent"]
        w, h = frame.size
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        pulse = abs(math.sin(global_t * 2.5))
        glow_alpha = int(60 + 40 * pulse)
        # Top edge glow
        draw.rectangle([(0, 0), (w, 6)], fill=accent + (glow_alpha + 60,))
        draw.rectangle([(0, 6), (w, 10)], fill=accent + (glow_alpha // 2,))
        # Left edge
        draw.rectangle([(0, 0), (5, h)], fill=accent + (glow_alpha // 3,))
        # Right edge
        draw.rectangle([(w-5, 0), (w, h)], fill=accent + (glow_alpha // 3,))
        frame_rgba = frame.convert("RGBA")
        return Image.alpha_composite(frame_rgba, overlay).convert("RGB")


# ─────────────────────────────────────────────────────────────────────────────
# 9. FULL PRODUCTION RENDER (All 9 Features Combined)
# ─────────────────────────────────────────────────────────────────────────────

def render_full_production_frame(
    headline_text: str,
    news_photo_path: Optional[str],
    global_t: float = 0.0,
    category: str = "TOP STORIES",
    ticker_headlines: Optional[List[str]] = None,
    quick_cards: Optional[List[str]] = None,
    script_text: str = "",
    enable_ken_burns: bool = True,
    clip_duration: float = 30.0,
    ken_burns_mode: Optional[str] = None,
    enable_subtitles: bool = True,
    enable_emotion_theme: bool = True,
) -> Image.Image:
    # Full 3D composition with mouth speech volume lipsync
    speech = 0.3 + 0.4 * abs(math.sin(global_t * 5.0)) if script_text else 0.0
    return render_production_3d_studio_frame(
        headline_text=headline_text, news_photo_path=news_photo_path,
        global_t=global_t, category=category,
        ticker_headlines=ticker_headlines, quick_cards=quick_cards,
        script_text=script_text, enable_ken_burns=enable_ken_burns,
        clip_duration=clip_duration, ken_burns_mode=ken_burns_mode,
        enable_subtitles=enable_subtitles, enable_emotion_theme=enable_emotion_theme,
        speech_level=speech
    )
