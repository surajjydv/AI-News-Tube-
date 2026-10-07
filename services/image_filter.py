"""
image_filter.py — AI-NewsTube Image Safety Filter
===================================================
Multi-layer content safety filter that rejects:
  - NSFW / adult / nude / pornographic images
  - Objectionable or violent imagery
  - Low-quality / corrupted images
  - Images from blocked domains

Layers:
  1. URL/domain blocklist
  2. URL/filename keyword blocklist
  3. PIL skin-tone pixel ratio heuristic (>50% rejected)
  4. Minimum resolution checks
"""

import re
import os
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
from utils.logger import logger


# ---------------------------------------------------------------------------
# Blocklists
# ---------------------------------------------------------------------------

BLOCKED_DOMAINS = {
    "pornhub.com", "xvideos.com", "xhamster.com", "redtube.com",
    "youporn.com", "tube8.com", "spankbang.com", "xnxx.com",
    "hotmovies.com", "sex.com", "nude.com", "nakedgirls.com",
    "onlyfans.com", "fansly.com", "camwhores.tv", "manyvids.com",
    "brazzers.com", "bangbros.com", "realitykings.com", "playboy.com",
    "liveleak.com", "bestgore.com", "goregrish.com", "rotten.com",
}

BLOCKED_URL_KEYWORDS = {
    "nude", "naked", "porn", "nsfw", "xxx", "adult", "erotic",
    "sex", "topless", "fetish", "hentai", "gore", "murder",
    "beheading", "corpse", "dead-body",
}

BLOCKED_FILENAME_KEYWORDS = {
    "nude", "naked", "porn", "nsfw", "sex", "adult", "erotic",
    "gore", "dead", "corpse",
}


class ImageFilter:
    """
    Multi-layer image safety filter.

    Usage:
        ok, reason = ImageFilter.is_safe_url("https://example.com/photo.jpg")
        ok, reason = ImageFilter.is_safe_image(Path("/tmp/photo.jpg"))
        ok, reason = ImageFilter.filter(url, image_path)
    """

    @staticmethod
    def is_safe_url(url: str) -> Tuple[bool, str]:
        if not url:
            return False, "Empty URL"
        url_lower = url.lower()
        try:
            from urllib.parse import urlparse
            domain = urlparse(url_lower).netloc.lstrip("www.")
            for blocked in BLOCKED_DOMAINS:
                if domain == blocked or domain.endswith("." + blocked):
                    return False, f"Blocked domain: {domain}"
        except Exception:
            pass
        for kw in BLOCKED_URL_KEYWORDS:
            pattern = r"(?<![a-z])" + re.escape(kw) + r"(?![a-z])"
            if re.search(pattern, url_lower):
                return False, f"Blocked URL keyword: '{kw}'"
        filename = url_lower.split("?")[0].split("/")[-1]
        name_no_ext = os.path.splitext(filename)[0]
        for kw in BLOCKED_FILENAME_KEYWORDS:
            if kw in name_no_ext:
                return False, f"Blocked filename keyword: '{kw}'"
        return True, "OK"

    @staticmethod
    def is_safe_image(
        image_path: Path,
        min_width: int = 640,
        min_height: int = 360,
        max_skin_ratio: float = 0.50,
    ) -> Tuple[bool, str]:
        path = Path(image_path)
        if not path.exists():
            return False, "File does not exist"
        if path.stat().st_size < 2048:
            return False, "File too small (< 2 KB), likely corrupt"
        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            return False, f"Cannot open image: {e}"
        w, h = img.size
        if w < min_width or h < min_height:
            return False, f"Resolution too low: {w}x{h} (min {min_width}x{min_height})"
        skin_ratio = ImageFilter._skin_pixel_ratio(img)
        if skin_ratio > max_skin_ratio:
            return False, f"Skin-tone ratio {skin_ratio:.1%} > {max_skin_ratio:.0%} — possible NSFW image"
        return True, "OK"

    @classmethod
    def filter(
        cls,
        url: str,
        image_path: Optional[Path] = None,
        min_width: int = 640,
        min_height: int = 360,
        max_skin_ratio: float = 0.50,
    ) -> Tuple[bool, str]:
        url_ok, url_reason = cls.is_safe_url(url)
        if not url_ok:
            logger.warning(f"[ImageFilter] REJECTED URL  | {url_reason} | {url[:80]}")
            return False, url_reason
        if image_path:
            img_ok, img_reason = cls.is_safe_image(image_path, min_width, min_height, max_skin_ratio)
            if not img_ok:
                logger.warning(f"[ImageFilter] REJECTED IMAGE | {img_reason} | {Path(image_path).name}")
                return False, img_reason
        logger.debug(f"[ImageFilter] PASSED | {url[:80]}")
        return True, "OK"

    @staticmethod
    def _skin_pixel_ratio(img: Image.Image, sample_step: int = 4) -> float:
        pixels = img.getdata()
        total = 0
        skin = 0
        for i, (r, g, b) in enumerate(pixels):
            if i % sample_step != 0:
                continue
            total += 1
            if (
                r > 95 and g > 40 and b > 20
                and r > g and r > b
                and abs(r - g) > 15
                and r > 150
                and (r - b) > 20
            ):
                skin += 1
        return skin / total if total > 0 else 0.0
