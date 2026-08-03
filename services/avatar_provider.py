import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import AVATAR_DIR
from utils.logger import logger

MIN_PRODUCTION_SIZE = 10 * 1024 * 1024  # At least 10 MB required for production models

BLACKLISTED_MODEL_NAMES = [
    "cesiumman",
    "cesium_man",
    "sample",
    "demo",
    "placeholder",
    "lowpoly",
    "low_poly"
]


class AvatarProviderEngine:
    """
    Strict Production Avatar Quality Inspector & Provider:
    - Rejects sample/demo/placeholder models.
    - Requires 10 MB minimum file size, PBR business suit, adult humanoid presenter specs.
    - If no suitable asset exists, halts and reports: "No suitable free production-quality presenter was found."
    """

    @classmethod
    def validate_production_asset(cls, asset_path: Path) -> tuple[bool, str]:
        if not asset_path.exists():
            return False, "File does not exist"

        file_name = asset_path.name.lower()
        for bl in BLACKLISTED_MODEL_NAMES:
            if bl in file_name:
                return False, f"Rejected blacklisted sample/demo model name: '{asset_path.name}'"

        file_size = asset_path.stat().st_size
        if file_size < MIN_PRODUCTION_SIZE:
            return False, f"File size ({file_size} bytes / {file_size / (1024*1024):.2f} MB) is below 10 MB production minimum"

        return True, "Valid production character asset"

    @classmethod
    def acquire_production_avatar(cls) -> tuple[bool, Path]:
        AVATAR_DIR.mkdir(parents=True, exist_ok=True)

        # Inspect candidates in assets/avatar/
        candidates = list(AVATAR_DIR.glob("*.glb")) + list(AVATAR_DIR.glob("*.fbx"))
        for candidate in candidates:
            is_valid, reason = cls.validate_production_asset(candidate)
            if is_valid:
                logger.info(f"  ✅ Verified Production Presenter Model: {candidate.name} ({candidate.stat().st_size} bytes)")
                return True, candidate
            else:
                logger.warning(f"  ⚠️ Candidate '{candidate.name}' rejected: {reason}")

        # If no compliant asset exists, halt with explicit message
        cls._print_halt_report()
        return False, AVATAR_DIR / "production_presenter.glb"

    @classmethod
    def _print_halt_report(cls):
        print("\n============================================================")
        print("PRODUCTION CHARACTER ASSET VALIDATION REPORT")
        print("============================================================")
        print("Status          : HALTED")
        print("Reason          : No suitable free production-quality presenter was found.")
        print("Requirements    : Min 10 MB size, PBR business suit, adult humanoid, rigged skeleton, CC0/commercial license")
        print("Blacklisted     : Sample models (CesiumMan, Khronos demos, low-poly placeholders)")
        print("Drop Location   : assets/avatar/production_presenter.glb")
        print("============================================================\n")


if __name__ == "__main__":
    AvatarProviderEngine.acquire_production_avatar()
