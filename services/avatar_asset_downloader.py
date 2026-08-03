import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import AVATAR_DIR
from utils.logger import logger

PRODUCTION_GLB_PATH = AVATAR_DIR / "production_presenter.glb"
PRODUCTION_FBX_PATH = AVATAR_DIR / "production_presenter.fbx"


def check_production_presenter_asset() -> tuple[bool, Path]:
    """
    Checks for user-provided production-quality rigged 3D human presenter model (.glb or .fbx).
    Returns (is_found, asset_path).
    """
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    if PRODUCTION_GLB_PATH.exists() and PRODUCTION_GLB_PATH.stat().st_size > 50000:
        return True, PRODUCTION_GLB_PATH

    if PRODUCTION_FBX_PATH.exists() and PRODUCTION_FBX_PATH.stat().st_size > 50000:
        return True, PRODUCTION_FBX_PATH

    return False, PRODUCTION_GLB_PATH


def print_asset_status_report():
    is_found, path = check_production_presenter_asset()

    print("\n============================================================")
    print("PRODUCTION CHARACTER ASSET STATUS REPORT")
    print("============================================================")
    if is_found:
        print(f"Status          : [READY] PRODUCTION ASSET AVAILABLE")
        print(f"Asset File      : {path.name} ({path.stat().st_size} bytes)")
        print(f"Absolute Path   : {path.resolve()}")
    else:
        print(f"Status          : [PENDING] WAITING FOR USER PRODUCTION ASSET")
        print(f"Required Specs  : Humanoid adult presenter, Rigged skeleton, PBR business suit")
        print(f"Allowed Formats : .glb (GLTF Binary) or .fbx")
        print(f"Target Location : {PRODUCTION_GLB_PATH.resolve()}")
        print(f"Note            : Sample test models (Cesium_Man) disabled for production.")
    print("============================================================\n")



if __name__ == "__main__":
    print_asset_status_report()
