"""
agents/avatar_agent.py
========================
Avatar Agent — Manages 3D AI news anchor assets.

Pipeline:
  assets/avatar/anchor.fbx  (or Ch33_nonPBR.fbx)
       ↓
  blender_service.py   (Blender 4.x headless)
       ↓
  scripts/process_avatar.py  (runs inside Blender)
       ↓
  assets/avatar/processed_anchor.glb
       ↓
  lip_sync_agent.py → video_agent.py
"""

import os
import sys
import shutil
import requests
from pathlib import Path
from PIL import Image, ImageDraw

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import ASSETS_DIR, AVATAR_DIR, PROCESSED_AVATAR_PATH
from services.blender_service import process_custom_avatar
from models.news_models import GeneratedScript
from utils.logger import logger

STUDIO_ASSETS_DIR = ASSETS_DIR / "studio"
STUDIO_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

# Output portrait image path
DEFAULT_IMAGE_PATH = STUDIO_ASSETS_DIR / "ai_anchor_3d.png"

# Free Ready Player Me portrait render (fallback)
RPM_RENDER_URL = (
    "https://render.readyplayer.me/render"
    "?model=https://models.readyplayer.me/64b7a421c607a0487428f522.glb"
    "&scene=fullbody-portrait-v1&expression=happy&camera=portrait"
)


# ─────────────────────────────────────────
# Avatar Asset Detection & Preparation
# ─────────────────────────────────────────

def find_avatar_fbx() -> Path | None:
    """Find the best available avatar FBX file in assets/avatar/."""
    candidates = [
        AVATAR_DIR / "anchor.fbx",          # Preferred name
        AVATAR_DIR / "Ch33_nonPBR.fbx",      # Mixamo Mixamo downloaded
        *list(AVATAR_DIR.glob("*.fbx")),     # Any other FBX
        *list(AVATAR_DIR.glob("*.blend")),   # Blender scene
    ]
    seen = set()
    for p in candidates:
        if p not in seen and p.exists():
            seen.add(p)
            return p
    return None


def prepare_anchor_portrait() -> Path:
    """Ensure we have an anchor portrait image for compositing."""
    if DEFAULT_IMAGE_PATH.exists() and DEFAULT_IMAGE_PATH.stat().st_size > 5000:
        return DEFAULT_IMAGE_PATH

    logger.info("  Avatar Agent: Fetching 3D presenter portrait...")
    try:
        resp = requests.get(RPM_RENDER_URL, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 10_000:
            with open(DEFAULT_IMAGE_PATH, "wb") as f:
                f.write(resp.content)
            logger.info(f"  Avatar Agent: Portrait saved ({DEFAULT_IMAGE_PATH.name})")
            return DEFAULT_IMAGE_PATH
    except Exception:
        pass

    _create_avatar_placeholder()
    return DEFAULT_IMAGE_PATH


def _create_avatar_placeholder():
    """Creates a minimal fallback anchor silhouette image."""
    img = Image.new("RGBA", (800, 1080), (10, 12, 30, 255))
    draw = ImageDraw.Draw(img)
    # Head
    draw.ellipse([(300, 80), (500, 300)], fill=(60, 62, 80, 255))
    # Body / suit
    draw.polygon([(250, 300), (550, 300), (600, 800), (200, 800)], fill=(35, 38, 60, 255))
    img.save(DEFAULT_IMAGE_PATH, "PNG")
    logger.info(f"  Avatar Agent: Fallback placeholder portrait created.")


def prepare_3d_anchor_avatar() -> tuple:
    """
    Main avatar preparation pipeline.

    Returns:
        (glb_path: Path | None, img_path: Path)
    """
    avatar_fbx = find_avatar_fbx()

    if avatar_fbx:
        logger.info(f"  Avatar Agent: Found custom 3D avatar: {avatar_fbx.name}")

        # Run Blender headless processing
        processed_glb = process_custom_avatar(
            input_avatar_path=avatar_fbx,
            output_glb_path=PROCESSED_AVATAR_PATH,
        )

        if processed_glb and processed_glb.exists():
            logger.info(f"  Avatar Agent: Blender processing complete -> {processed_glb.name}")
            img_path = prepare_anchor_portrait()
            return processed_glb, img_path
        else:
            logger.warning("  Avatar Agent: Blender processing failed. Using static portrait fallback.")
    else:
        logger.info(f"  Avatar Agent: No FBX found in {AVATAR_DIR}. Using default presenter portrait.")

    img_path = prepare_anchor_portrait()
    return None, img_path


# ─────────────────────────────────────────
# Avatar Agent Entry Point
# ─────────────────────────────────────────

def avatar_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    Avatar Agent: Manages 3D anchor presenter model and passes assets to script_obj.

    Full pipeline:
      anchor.fbx -> Blender 4.x (headless) -> processed_anchor.glb -> lip_sync_agent -> video_agent
    """
    logger.info("=" * 55)
    logger.info("AVATAR AGENT — 3D Anchor Character Engine")
    logger.info("=" * 55)

    glb_path, img_path = prepare_3d_anchor_avatar()

    # Attach GLB path to script object (for lip_sync_agent)
    script_obj.glb_avatar_path = str(glb_path) if (glb_path and glb_path.exists()) else None

    # Attach portrait image (for video compositing fallback)
    if not script_obj.image_paths:
        script_obj.image_paths = [str(img_path)]
    else:
        script_obj.image_paths[0] = str(img_path)

    if script_obj.glb_avatar_path:
        logger.info(f"  Active 3D Anchor  : {Path(script_obj.glb_avatar_path).name} (GLB ready for lip-sync)")
    else:
        logger.info(f"  Active Presenter  : {img_path.name} (static portrait — Blender not available)")

    logger.info("=" * 55)
    return script_obj
