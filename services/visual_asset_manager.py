import os
import sys
import requests
from pathlib import Path
from typing import Optional, List
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ASSETS_DIR, PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_API_KEY
from models.news_models import MediaAsset
from utils.logger import logger

class VisualAssetManager:
    """
    Visual Asset Manager:
    Workflow:
    Headline -> Translate Hindi to English Search Keywords via Groq LLM ->
    Wikimedia Commons -> Pexels -> Pixabay -> Unsplash ->
    Download highest-quality landscape image -> Validate dimensions (Min 1280x720) -> Render image.

    Diagnostic Features:
    - ZERO silent error swallowing (no 'except Exception: pass').
    - Prints Query, API Name, HTTP Status, Response Body snippet (300 chars), Image URL, File Path, Size, and Validation Result for every attempt.
    - If all APIs fail, prints an explicit diagnostic breakdown explaining why each API failed.
    """

    @classmethod
    def get_visual_asset(cls, headline: str, category: str, output_path: Path) -> MediaAsset:
        """Executes the exact 4-tier fallback search workflow and returns a validated MediaAsset."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Step 1: Translate Devanagari Hindi headline to English search keywords
        english_keywords = cls._translate_to_english_keywords(headline, category)
        logger.info("=" * 60)
        logger.info(f"📸 VISUAL ASSET MANAGER (4-TIER DIAGNOSTIC SEARCH)")
        logger.info(f"  📌 Original Headline : '{headline}'")
        logger.info(f"  🌐 English Keywords   : {english_keywords}")
        logger.info("=" * 60)

        failure_reasons = {}

        for kw in english_keywords:
            # 1. Wikimedia Commons API
            asset = cls._search_wikimedia(kw, output_path, failure_reasons)
            if asset:
                return asset

            # 2. Pexels API
            asset = cls._search_pexels(kw, output_path, failure_reasons)
            if asset:
                return asset

            # 3. Pixabay API
            asset = cls._search_pixabay(kw, output_path, failure_reasons)
            if asset:
                return asset

            # 4. Unsplash API
            asset = cls._search_unsplash(kw, output_path, failure_reasons)
            if asset:
                return asset

        # DIAGNOSTIC FAILURE REPORT: Print why each API tier failed
        logger.error("=" * 60)
        logger.error("❌ VISUAL ASSET MANAGER: ALL IMAGE APIS FAILED FOR STORY!")
        for api_name, reason in failure_reasons.items():
            logger.error(f"   - {api_name:<20}: {reason}")
        logger.error("=" * 60)

        # FALLBACK: Render Professional "Visual currently unavailable" Placeholder Card
        logger.info("  📌 Rendering 'Visual currently unavailable' placeholder card...")
        cls._render_placeholder_card(headline, category, output_path)
        return MediaAsset(
            media_type="real_image",
            file_path=str(output_path),
            source_name="AI-NewsTube Visual Manager",
            source_url="",
            on_screen_credit="Visual: AI-NewsTube Studio Coverage"
        )

    @classmethod
    def _translate_to_english_keywords(cls, headline: str, category: str) -> List[str]:
        """Translates Devanagari Hindi headline into concise English search keywords using Groq LLM API."""
        from services.groq_service import generate_text
        try:
            prompt = (
                f"Given news headline '{headline}' in Hindi and category '{category}', "
                f"return 3 short English search query strings for press photography as a JSON list of strings. "
                f"Example: [\"India US trade agreement\", \"Narendra Modi press summit\", \"trade negotiation news\"]"
            )
            response = generate_text(prompt, temperature=0.2).strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            import json
            kw_list = json.loads(response)
            if isinstance(kw_list, list) and len(kw_list) > 0:
                return [str(k) for k in kw_list[:3]]
        except Exception as e:
            logger.warning(f"  ⚠️ Groq keyword translation note ({e}). Using direct fallback keywords.")

        words = [w for w in headline.split() if len(w) > 3]
        return [
            f"{category} news event",
            f"India {category} breaking news",
            "global news coverage"
        ]

    @classmethod
    def _validate_image_dimensions(cls, file_path: Path) -> tuple[bool, str]:
        """Validates image dimensions (minimum 1280x720 or minimum 600x400 landscape)."""
        try:
            with Image.open(file_path) as img:
                w, h = img.size
                dim_str = f"{w}x{h}"
                if w >= 600 and h >= 400 and (w / h) >= 1.1:
                    return True, f"PASSED ({dim_str}, aspect ratio {w/h:.2f})"
                else:
                    return False, f"FAILED (Dimensions {dim_str} below required min 1280x720/600x400 landscape)"
        except Exception as e:
            return False, f"FAILED (Corrupted image file: {e})"

    @classmethod
    def _search_wikimedia(cls, query: str, output_path: Path, failure_reasons: dict) -> Optional[MediaAsset]:
        """1. Search Wikimedia Commons API with full diagnostic logging."""
        api_name = "Wikimedia Commons API"
        url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={requests.utils.quote(query)}&gsrnamespace=6&prop=imageinfo&iiprop=url|size&format=json&gsrlimit=5"
        headers = {"User-Agent": "AI-NewsTube-Bot/1.0 (https://ainewstube.org; newsbot@ainewstube.org)"}
        logger.info(f"  🌐 [{api_name}] Search Query: '{query}'")

        try:
            resp = requests.get(url, headers=headers, timeout=8)

            snippet = resp.text[:300].replace("\n", " ")
            logger.info(f"     📶 HTTP Status : {resp.status_code}")
            logger.info(f"     📄 Response Body: {snippet}...")

            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                if not pages:
                    failure_reasons[api_name] = f"HTTP 200 - 0 search results for query '{query}'"
                    return None

                for page_id, page_info in pages.items():
                    imageinfo = page_info.get("imageinfo", [])
                    if imageinfo and "url" in imageinfo[0]:
                        img_url = imageinfo[0]["url"]
                        if img_url.lower().endswith(('.jpg', '.jpeg', '.png')):
                            logger.info(f"     🔗 Download URL : {img_url}")
                            r = requests.get(img_url, timeout=10)
                            if r.status_code == 200 and len(r.content) > 10000:
                                with open(output_path, "wb") as f:
                                    f.write(r.content)

                                is_valid, val_reason = cls._validate_image_dimensions(output_path)
                                logger.info(f"     📁 Saved File   : {output_path.name}")
                                logger.info(f"     📐 Validation   : {val_reason}")

                                if is_valid:
                                    logger.info(f"  ✅ [{api_name}] Photo Validated Successfully!")
                                    return MediaAsset(
                                        media_type="real_image",
                                        file_path=str(output_path),
                                        source_name="Wikimedia Commons",
                                        source_url=img_url,
                                        on_screen_credit="Source: Wikimedia Commons / CC License"
                                    )
                                else:
                                    failure_reasons[api_name] = f"Validation failed: {val_reason}"
            else:
                failure_reasons[api_name] = f"HTTP {resp.status_code} Error"
        except Exception as e:
            logger.error(f"     ❌ [{api_name}] Exception: {e}")
            failure_reasons[api_name] = f"Exception: {e}"

        return None

    @classmethod
    def _search_pexels(cls, query: str, output_path: Path, failure_reasons: dict) -> Optional[MediaAsset]:
        """2. Search Pexels API with full diagnostic logging."""
        api_name = "Pexels API"
        if not PEXELS_API_KEY:
            failure_reasons[api_name] = "PEXELS_API_KEY environment variable not set"
            return None

        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=3&orientation=landscape"
        logger.info(f"  🌐 [{api_name}] Search Query: '{query}'")

        try:
            resp = requests.get(url, headers=headers, timeout=8)
            snippet = resp.text[:300].replace("\n", " ")
            logger.info(f"     📶 HTTP Status : {resp.status_code}")
            logger.info(f"     📄 Response Body: {snippet}...")

            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                if not photos:
                    failure_reasons[api_name] = f"HTTP 200 - 0 search results for query '{query}'"
                    return None

                for p in photos:
                    img_url = p.get("src", {}).get("large2x") or p.get("src", {}).get("large")
                    photographer = p.get("photographer", "Pexels")
                    if img_url:
                        logger.info(f"     🔗 Download URL : {img_url}")
                        r = requests.get(img_url, timeout=10)
                        if r.status_code == 200 and len(r.content) > 10000:
                            with open(output_path, "wb") as f:
                                f.write(r.content)

                            is_valid, val_reason = cls._validate_image_dimensions(output_path)
                            logger.info(f"     📁 Saved File   : {output_path.name}")
                            logger.info(f"     📐 Validation   : {val_reason}")

                            if is_valid:
                                logger.info(f"  ✅ [{api_name}] Photo Validated Successfully!")
                                return MediaAsset(
                                    media_type="real_image",
                                    file_path=str(output_path),
                                    source_name="Pexels",
                                    source_url=img_url,
                                    on_screen_credit=f"Photo: {photographer} / Pexels"
                                )
                            else:
                                failure_reasons[api_name] = f"Validation failed: {val_reason}"
            else:
                failure_reasons[api_name] = f"HTTP {resp.status_code} Error: {snippet}"
        except Exception as e:
            logger.error(f"     ❌ [{api_name}] Exception: {e}")
            failure_reasons[api_name] = f"Exception: {e}"

        return None

    @classmethod
    def _search_pixabay(cls, query: str, output_path: Path, failure_reasons: dict) -> Optional[MediaAsset]:
        """3. Search Pixabay API with full diagnostic logging."""
        api_name = "Pixabay API"
        if not PIXABAY_API_KEY:
            failure_reasons[api_name] = "PIXABAY_API_KEY environment variable not set"
            return None

        url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={requests.utils.quote(query)}&image_type=photo&orientation=horizontal&per_page=3"
        logger.info(f"  🌐 [{api_name}] Search Query: '{query}'")

        try:
            resp = requests.get(url, timeout=8)
            snippet = resp.text[:300].replace("\n", " ")
            logger.info(f"     📶 HTTP Status : {resp.status_code}")
            logger.info(f"     📄 Response Body: {snippet}...")

            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if not hits:
                    failure_reasons[api_name] = f"HTTP 200 - 0 search results for query '{query}'"
                    return None

                for hit in hits:
                    img_url = hit.get("largeImageURL") or hit.get("webformatURL")
                    user = hit.get("user", "Pixabay")
                    if img_url:
                        logger.info(f"     🔗 Download URL : {img_url}")
                        r = requests.get(img_url, timeout=10)
                        if r.status_code == 200 and len(r.content) > 10000:
                            with open(output_path, "wb") as f:
                                f.write(r.content)

                            is_valid, val_reason = cls._validate_image_dimensions(output_path)
                            logger.info(f"     📁 Saved File   : {output_path.name}")
                            logger.info(f"     📐 Validation   : {val_reason}")

                            if is_valid:
                                logger.info(f"  ✅ [{api_name}] Photo Validated Successfully!")
                                return MediaAsset(
                                    media_type="real_image",
                                    file_path=str(output_path),
                                    source_name="Pixabay",
                                    source_url=img_url,
                                    on_screen_credit=f"Image: {user} / Pixabay"
                                )
                            else:
                                failure_reasons[api_name] = f"Validation failed: {val_reason}"
            else:
                failure_reasons[api_name] = f"HTTP {resp.status_code} Error"
        except Exception as e:
            logger.error(f"     ❌ [{api_name}] Exception: {e}")
            failure_reasons[api_name] = f"Exception: {e}"

        return None

    @classmethod
    def _search_unsplash(cls, query: str, output_path: Path, failure_reasons: dict) -> Optional[MediaAsset]:
        """4. Search Unsplash API with full diagnostic logging."""
        api_name = "Unsplash API"
        if not UNSPLASH_API_KEY:
            failure_reasons[api_name] = "UNSPLASH_API_KEY environment variable not set"
            return None

        headers = {"Authorization": f"Client-ID {UNSPLASH_API_KEY}"}
        url = f"https://api.unsplash.com/search/photos?query={requests.utils.quote(query)}&per_page=3&orientation=landscape"
        logger.info(f"  🌐 [{api_name}] Search Query: '{query}'")

        try:
            resp = requests.get(url, headers=headers, timeout=8)
            snippet = resp.text[:300].replace("\n", " ")
            logger.info(f"     📶 HTTP Status : {resp.status_code}")
            logger.info(f"     📄 Response Body: {snippet}...")

            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if not results:
                    failure_reasons[api_name] = f"HTTP 200 - 0 search results for query '{query}'"
                    return None

                for res in results:
                    img_url = res.get("urls", {}).get("regular")
                    username = res.get("user", {}).get("name", "Unsplash")
                    if img_url:
                        logger.info(f"     🔗 Download URL : {img_url}")
                        r = requests.get(img_url, timeout=10)
                        if r.status_code == 200 and len(r.content) > 10000:
                            with open(output_path, "wb") as f:
                                f.write(r.content)

                            is_valid, val_reason = cls._validate_image_dimensions(output_path)
                            logger.info(f"     📁 Saved File   : {output_path.name}")
                            logger.info(f"     📐 Validation   : {val_reason}")

                            if is_valid:
                                logger.info(f"  ✅ [{api_name}] Photo Validated Successfully!")
                                return MediaAsset(
                                    media_type="real_image",
                                    file_path=str(output_path),
                                    source_name="Unsplash",
                                    source_url=img_url,
                                    on_screen_credit=f"Photo: {username} / Unsplash"
                                )
                            else:
                                failure_reasons[api_name] = f"Validation failed: {val_reason}"
            else:
                failure_reasons[api_name] = f"HTTP {resp.status_code} Error"
        except Exception as e:
            logger.error(f"     ❌ [{api_name}] Exception: {e}")
            failure_reasons[api_name] = f"Exception: {e}"

        return None


    @classmethod
    def _render_placeholder_card(cls, headline: str, category: str, output_path: Path):
        """Renders professional placeholder card saying 'Visual currently unavailable'."""
        w, h = 1200, 750
        card = Image.new("RGB", (w, h), (10, 16, 35))
        draw = ImageDraw.Draw(card)

        # Ambient Dark Gradient Background
        for y in range(h):
            prog = y / h
            r = int(10 + 20 * prog)
            g = int(16 + 28 * prog)
            b = int(35 + 50 * prog)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # Neon Accent Border
        draw.rectangle([(10, 10), (w - 10, h - 10)], outline=(37, 99, 235), width=3)
        draw.rectangle([(20, 20), (w - 20, h - 20)], outline=(30, 64, 175), width=1)

        from agents.video_agent import _load_font
        font_lg = _load_font(32, bold=True)
        font_sm = _load_font(20, bold=True)

        # Category Badge
        draw.rounded_rectangle([(50, 50), (320, 95)], radius=8, fill=(220, 38, 38))
        draw.text((65, 60), f"⚡ {category.upper()} COVERAGE", fill=(255, 255, 255), font=font_sm)

        # Headline & Visual Currently Unavailable Notice
        draw.text((50, 140), "VISUAL REPORTING", fill=(255, 215, 0), font=font_sm)
        draw.rounded_rectangle([(50, 180), (600, 235)], radius=8, fill=(30, 45, 90), outline=(50, 90, 180), width=1)
        draw.text((65, 195), "📷 Visual currently unavailable", fill=(220, 235, 255), font=font_sm)

        # Wrapped Headline
        words = headline.split()
        lines = []
        curr = []
        for word in words:
            curr.append(word)
            if len(" ".join(curr)) > 30:
                lines.append(" ".join(curr[:-1]))
                curr = [word]
        if curr:
            lines.append(" ".join(curr))

        ty = 260
        for line in lines[:4]:
            draw.text((50, ty), line, fill=(240, 245, 255), font=font_lg)
            ty += 48

        # Brand Footer
        draw.rectangle([(50, h - 80), (w - 50, h - 76)], fill=(37, 99, 235))
        draw.text((50, h - 60), "AI-NEWSTUBE  |  SPECIAL BROADCAST REPORTING", fill=(180, 200, 230), font=font_sm)

        card.save(output_path)
