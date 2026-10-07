"""
font_utils.py
-------------
Centralized font loader and text sanitizer for all PIL/Pillow text rendering
across the app (video_agent, graphics_agent, thumbnail_agent, studio renderer, etc).

Uses bundled Noto Sans Devanagari font (assets/fonts/) so both English and Hindi
headlines render correctly, avoiding missing glyph tofu boxes (□).
Also provides emoji/symbol sanitization to strip/convert unrenderable glyphs.
"""
import re
from pathlib import Path
from typing import Dict, Tuple, Optional
from PIL import ImageFont, ImageDraw, Image

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

def _download_mukta_fonts():
    import urllib.request
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    for name in ["Mukta-Regular.ttf", "Mukta-Bold.ttf"]:
        dest = FONT_DIR / name
        if not dest.exists():
            url = f"https://github.com/google/fonts/raw/main/ofl/mukta/{name}"
            try:
                print(f"Downloading bilingual font {name}...")
                urllib.request.urlretrieve(url, str(dest))
            except Exception as e:
                print(f"Failed to download {name}: {e}")

# Download Mukta fonts to prevent tofu boxes on mixed English/Hindi text
_download_mukta_fonts()

# Hind font is Google's premier TV broadcast Hindi font with flawless ligature support
_BOLD_CANDIDATES = [
    FONT_DIR / "Hind-Bold.ttf",
    FONT_DIR / "Hind-Medium.ttf",
    FONT_DIR / "Mukta-Bold.ttf",
    FONT_DIR / "NotoSansDevanagari-Bold.ttf",
    FONT_DIR / "NotoSans-Bold.ttf",
    FONT_DIR / "DejaVuSans-Bold.ttf",
    Path("C:/Windows/Fonts/segoeuib.ttf"),
    Path("C:/Windows/Fonts/arialbd.ttf"),
]
_REGULAR_CANDIDATES = [
    FONT_DIR / "Hind-Regular.ttf",
    FONT_DIR / "Hind-Medium.ttf",
    FONT_DIR / "Mukta-Regular.ttf",
    FONT_DIR / "NotoSansDevanagari-Regular.ttf",
    FONT_DIR / "NotoSans-Regular.ttf",
    FONT_DIR / "DejaVuSans.ttf",
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
]

_cache: Dict[Tuple[int, bool, str], ImageFont.FreeTypeFont] = {}
_resolved_path: Dict[Tuple[bool, str], Optional[Path]] = {}

EMOJI_REPLACEMENT_MAP = {
    '🚨': '', '⚡': '', '📷': '', '🌐': '', '❌': 'X', '✅': 'V',
    '▲': '+', '▼': '-', '🔥': '', '📰': '', '📡': '', '📌': '',
    '📶': '', '🔢': '#', '🖼️': '', '📁': '', '📐': '', '⚠️': '!',
    '☀️': '', '🌧️': '', '⛅': '', '⛈️': '', '🔴': '', '🟢': '',
    '【': '[', '】': ']', '〔': '[', '〕': ']', '「': '[', '」': ']',
    '『': '[', '』': ']', '《': '<', '》': '>', '〈': '<', '〉': '>',
    '•': '-', '●': '-', '▪': '-', '◆': '-', '◇': '-', '★': '*', '☆': '*',
    '▶': '>', '►': '>', '◀': '<', '◄': '<', '✔': 'V', '✓': 'V',
    '—': '-', '–': '-', '―': '-', '’': "'", '‘': "'", '“': '"', '”': '"',
    '₹': 'Rs.', '°': 'C', '…': '...',
}

import html as html_lib
import unicodedata

def sanitize_text(text: str) -> str:
    """
    Strips raw HTML tags, unescapes HTML entities, canonicalizes Unicode Devanagari marks,
    maps all decorative/CJK brackets and symbols to safe ASCII, and eliminates tofu box (□) glyphs.
    """
    if not text:
        return ""
    text_str = str(text)
    # Canonicalize Unicode (combining marks / matras / nuktas)
    text_str = unicodedata.normalize('NFC', text_str)
    # Strip HTML tags
    text_str = re.sub(r'<[^>]+>', ' ', text_str)
    # Unescape HTML entities
    text_str = html_lib.unescape(text_str)
    # Remove zero-width spaces, soft hyphens, byte-order marks
    text_str = re.sub(r'[\u200B-\u200D\uFEFF\u00AD\u00A0]', ' ', text_str)
    for char, replacement in EMOJI_REPLACEMENT_MAP.items():
        text_str = text_str.replace(char, replacement)
    # Strip remaining emojis, surrogate pairs, decorative symbols, and CJK blocks
    text_str = re.sub(r'[\U00010000-\U0010FFFF\u2600-\u27BF\uFE00-\uFE0F\u3000-\u303F]', '', text_str)
    # Clean up multiple spaces
    return re.sub(r'\s+', ' ', text_str).strip()


def _resolve_font_path(bold: bool, lang: str = "hi"):
    cache_key = (bold, lang)
    if cache_key in _resolved_path and _resolved_path[cache_key] is not None:
        return _resolved_path[cache_key]

    # NotoSansDevanagari supports both English and Hindi.
    # We check bundled Devanagari font candidates first regardless of lang
    # so Hindi characters never break even if caller requested lang="en".
    candidates = _BOLD_CANDIDATES if bold else _REGULAR_CANDIDATES

    for path in candidates:
        if path.exists():
            _resolved_path[cache_key] = path
            return path

    # Fall back across system font locations as a last resort.
    for sys_path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]:
        p = Path(sys_path)
        if p.exists():
            _resolved_path[cache_key] = p
            return p

    _resolved_path[cache_key] = None
    return None


def load_font(size: int, bold: bool = False, lang: str = "hi") -> ImageFont.FreeTypeFont:
    """
    Loads (and caches) a TrueType font at the given pixel size.
    Supports Hindi/Devanagari text out of the box via the bundled Noto font.
    Always returns a usable font object.
    """
    size = max(1, int(size))
    key = (size, bool(bold), lang)
    if key in _cache:
        return _cache[key]

    path = _resolve_font_path(bool(bold), lang)
    font = None
    if path:
        try:
            font = ImageFont.truetype(str(path), size)
        except Exception:
            font = None

    if font is None:
        try:
            font = ImageFont.load_default(size=size)
        except TypeError:
            font = ImageFont.load_default()

    _cache[key] = font
    return font


def draw_clean_text(draw: ImageDraw.ImageDraw, xy, text: str, font=None, fill=None, **kwargs):
    """
    Wrapper around draw.text that automatically sanitizes text to remove unrenderable glyphs.
    """
    clean = sanitize_text(text)
    # Strip layout_engine parameter if passed to avoid Pillow Windows warnings
    kwargs.pop("layout_engine", None)
    return draw.text(xy, clean, font=font, fill=fill, **kwargs)


# Cache for HarfBuzz and FreeType face instances
_HB_FACES: dict = {}
_FT_FACES: dict = {}

def draw_shaped_text(
    canvas_img: Image.Image,
    xy: tuple,
    text: str,
    font_size: int = 36,
    bold: bool = True,
    text_color: tuple = (255, 255, 255),
    shadow: bool = False,
    shadow_color: tuple = (0, 0, 0)
):
    """
    Renders complex Devanagari Hindi and mixed Latin typography with 100% accurate OpenType ligatures,
    conjuncts, and matra positioning via HarfBuzz + FreeType rasterization.
    """
    clean = sanitize_text(text)
    if not clean:
        return

    try:
        import uharfbuzz as hb
        import freetype
        import numpy as np

        font_path = FONT_DIR / ("Hind-Bold.ttf" if bold else "Hind-Regular.ttf")
        if not font_path.exists():
            font_path = FONT_DIR / ("Mukta-Bold.ttf" if bold else "Mukta-Regular.ttf")
        if not font_path.exists():
            font_path = FONT_DIR / ("NotoSansDevanagari-Bold.ttf" if bold else "NotoSansDevanagari-Regular.ttf")

        f_key = str(font_path)
        if f_key not in _HB_FACES:
            with open(font_path, "rb") as f:
                _HB_FACES[f_key] = f.read()
            _FT_FACES[f_key] = freetype.Face(str(font_path))

        font_data = _HB_FACES[f_key]
        ft_face = _FT_FACES[f_key]

        face = hb.Face(font_data)
        hb_font = hb.Font(face)
        scale = int(font_size * 64)
        hb_font.scale = (scale, scale)

        buf = hb.Buffer()
        buf.add_str(clean)
        buf.guess_segment_properties()
        hb.shape(hb_font, buf)

        infos = buf.glyph_infos
        positions = buf.glyph_positions

        ft_face.set_char_size(font_size * 64)
        ascent = ft_face.size.ascender >> 6
        descent = ft_face.size.descender >> 6
        total_w = max(10, (sum(pos.x_advance for pos in positions) >> 6) + 40)
        total_h = max(10, ascent - descent + 20)

        # Render glyphs into RGBA alpha surface
        text_surf = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
        pen_x = 10
        pen_y = ascent + 5

        for info, pos in zip(infos, positions):
            ft_face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER)
            bitmap = ft_face.glyph.bitmap
            left = pen_x + (pos.x_offset >> 6) + ft_face.glyph.bitmap_left
            top = pen_y - (pos.y_offset >> 6) - ft_face.glyph.bitmap_top

            bw, bh = bitmap.width, bitmap.rows
            if bw > 0 and bh > 0:
                arr = np.array(bitmap.buffer, dtype=np.uint8).reshape((bh, bw))
                glyph_alpha = Image.fromarray(arr)
                colored_glyph = Image.new("RGBA", (bw, bh), text_color + (0,))
                colored_glyph.putalpha(glyph_alpha)
                text_surf.paste(colored_glyph, (left, top), colored_glyph)

            pen_x += (pos.x_advance >> 6)

        x, y = int(xy[0]) - 10, int(xy[1]) - 5
        if shadow:
            s_arr = np.array(text_surf)
            # Create drop shadow layer
            shadow_surf = Image.new("RGBA", (total_w, total_h), shadow_color + (180,))
            shadow_surf.putalpha(text_surf.getchannel("A"))
            canvas_img.paste(shadow_surf, (x + 3, y + 3), shadow_surf)

        canvas_img.paste(text_surf, (x, y), text_surf)

    except Exception as e:
        # Fallback to standard Pillow text rendering
        draw = ImageDraw.Draw(canvas_img)
        font = load_font(font_size, bold=bold)
        if shadow:
            draw.text((xy[0] + 3, xy[1] + 3), clean, font=font, fill=shadow_color)
        draw.text(xy, clean, font=font, fill=text_color)


def draw_cairo_text(canvas_img: Image.Image, xy: tuple, text: str, font_size: int = 40, font_name: str = "Hind", text_color: tuple = (255, 255, 255), is_bold: bool = True):
    """Draws styled text onto canvas using HarfBuzz/Pillow."""
    return draw_shaped_text(canvas_img, xy, text, font_size=font_size, bold=is_bold, text_color=text_color)

