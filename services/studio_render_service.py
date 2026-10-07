"""
StudioRenderService
--------------------
Renders the AI-NewsTube virtual news studio background (curved LED wall,
anchor desk, ceiling spotlights, side headline panels, animated 3D headline
lower-third, ticker, clock) as a sequence of 1920x1080 PNG frames.

Replaces the old Panda3D pipeline (which depended on texture files that were
never shipped in assets/studio_3d/, so every surface rendered as a blank/
placeholder card) and the old Three.js pipeline (which depended on loading
three.js from a public CDN at render time, so it silently failed in any
environment without outbound internet access).

studio_render.html is 100% self-contained (pure CSS3D + Canvas2D, zero
external script/font/image dependencies), so this renders identically
whether the machine has internet access or not.
"""
import math
import shutil
from pathlib import Path
from typing import List, Optional, Sequence

from config.settings import ASSETS_DIR
from utils.logger import logger

HTML_PATH = Path(__file__).resolve().parent / "studio_render.html"
FRAMES_DIR = ASSETS_DIR / "studio_frames"


class StudioRenderService:
    """Renders the CSS3D news studio background frame-by-frame via headless Chromium."""

    @classmethod
    def render_background_frames(
        cls,
        duration_sec: float,
        fps: int,
        headline: str,
        summary: str = "",
        category: str = "DEFAULT",
        ticker_items: Optional[Sequence[str]] = None,
        market_items: Optional[Sequence[str]] = None,
        side_items: Optional[Sequence[str]] = None,
        clock_text: str = "",
        date_text: str = "",
    ) -> List[Path]:
        """
        Renders `duration_sec * fps` frames of the studio background and
        returns the sorted list of PNG file paths. Falls back to a simpler
        procedural PIL background sequence if headless Chromium is
        unavailable for any reason (sandboxed CI, missing browser install).
        """
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
        FRAMES_DIR.mkdir(parents=True, exist_ok=True)

        total_frames = max(1, int(round(duration_sec * fps)))

        ok = cls._capture_with_playwright(
            total_frames, fps, headline, summary, category,
            ticker_items, market_items, side_items, clock_text, date_text,
        )
        if not ok:
            logger.warning("  ⚠️ Studio renderer: headless browser capture failed — using procedural PIL fallback.")
            cls._render_fallback_frames(total_frames, fps, headline, summary, category)

        return sorted(FRAMES_DIR.glob("frame_*.png"))

    # ------------------------------------------------------------------
    @classmethod
    def _capture_with_playwright(
        cls, total_frames, fps, headline, summary, category,
        ticker_items, market_items, side_items, clock_text, date_text,
    ) -> bool:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("  ⚠️ Playwright not installed — cannot render studio via headless browser.")
            return False

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                page = browser.new_page(viewport={"width": 1920, "height": 1080})
                page.goto(HTML_PATH.as_uri())
                page.wait_for_selector("#stage")

                page.evaluate(
                    """(cfg) => {
                        window.NEWS_STUDIO.setCategory(cfg.category);
                        window.NEWS_STUDIO.setHeadline(cfg.headline, cfg.summary);
                        window.NEWS_STUDIO.setTickerItems(cfg.ticker);
                        window.NEWS_STUDIO.setMarketRow(cfg.market);
                        window.NEWS_STUDIO.setSideLists(cfg.side);
                        window.NEWS_STUDIO.setClock(cfg.clock, cfg.date);
                        window.NEWS_STUDIO.playIntro();
                    }""",
                    {
                        "category": category or "DEFAULT",
                        "headline": headline or "",
                        "summary": summary or "",
                        "ticker": list(ticker_items) if ticker_items else [],
                        "market": list(market_items) if market_items else [],
                        "side": list(side_items) if side_items else [],
                        "clock": clock_text or "",
                        "date": date_text or "",
                    },
                )

                logger.info(f"  🎥 Rendering {total_frames} studio frames ({total_frames/fps:.1f}s @ {fps}fps) via headless Chromium...")
                for f in range(total_frames):
                    t = f / float(fps)
                    page.evaluate("(t) => window.NEWS_STUDIO.renderFrameAtTime(t)", t)
                    frame_path = FRAMES_DIR / f"frame_{f + 1:05d}.png"
                    page.screenshot(path=str(frame_path))

                browser.close()
            return True
        except Exception as e:
            logger.warning(f"  ⚠️ Studio headless-browser capture failed: {e}")
            return False

    # ------------------------------------------------------------------
    @classmethod
    def _render_fallback_frames(cls, total_frames, fps, headline, summary, category):
        """Procedural PIL fallback used only if headless Chromium is unavailable."""
        from PIL import Image, ImageDraw
        from utils.font_utils import load_font

        w, h = 1920, 1080
        theme = {
            "FINANCE_MARKETS": (6, 45, 30),
            "TECH_AI_CYBER": (35, 12, 85),
            "POLITICS_GOVT": (60, 45, 10),
            "WEATHER_SPACE": (5, 50, 60),
            "SPORTS": (85, 12, 20),
        }.get(category, (10, 30, 70))

        font_h = load_font(46, bold=True)
        font_s = load_font(22, bold=False)

        for f in range(total_frames):
            t = f / float(fps)
            img = Image.new("RGB", (w, h), (5, 8, 16))
            draw = ImageDraw.Draw(img)

            for i in range(10):
                shade = tuple(min(255, c + i * 4) for c in theme)
                draw.rectangle([(0, 90 + i * 60), (w, 90 + (i + 1) * 60)], fill=shade)
            draw.rectangle([(0, h - 300), (w, h)], fill=(10, 16, 32))

            draw.rectangle([(0, 0), (420, 70)], fill=(200, 16, 46))
            draw.text((20, 20), "LIVE  |  AI-NEWSTUBE", fill=(255, 255, 255), font=font_s)

            draw.rectangle([(0, h - 260), (w, h - 190)], fill=(10, 18, 40))
            draw.rectangle([(0, h - 260), (230, h - 140)], fill=(200, 16, 46))
            draw.text((20, h - 245), "BREAKING", fill=(255, 255, 255), font=font_s)
            draw.text((250, h - 250), headline[:70], fill=(255, 255, 255), font=font_h)
            if summary:
                draw.text((250, h - 195), summary[:110], fill=(180, 210, 255), font=font_s)

            draw.rectangle([(0, h - 60), (w, h)], fill=(6, 10, 22))
            draw.text((20, h - 45), "BREAKING NEWS TICKER — AI-NEWSTUBE STUDIO", fill=(255, 255, 255), font=font_s)

            frame_path = FRAMES_DIR / f"frame_{f + 1:05d}.png"
            img.save(frame_path)


if __name__ == "__main__":
    frames = StudioRenderService.render_background_frames(
        duration_sec=2.0, fps=24,
        headline="Test Headline For Studio Renderer",
        summary="This is a quick smoke test of the new studio background.",
        category="TECH_AI_CYBER",
        ticker_items=["Sample ticker item one", "Sample ticker item two"],
    )
    print(f"Rendered {len(frames)} frames -> {frames[0].parent if frames else 'none'}")
