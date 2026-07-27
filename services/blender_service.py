"""
services/blender_service.py
============================
Blender integration service for AI-NewsTube.

Responsibilities:
  1. Auto-detect Blender 4.x executable (C:\\Program Files\\Blender Foundation\\Blender 4.x\\blender.exe)
  2. Run Blender in headless/background mode (no UI clicks required)
  3. Execute scripts/process_avatar.py inside Blender's Python interpreter
  4. Return path to processed_anchor.glb output

Usage:
    from services.blender_service import process_custom_avatar
    result = process_custom_avatar(Path("assets/avatar/anchor.fbx"))
"""

import os
import sys
import glob
import shutil
import subprocess
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import BLENDER_PATH, AVATAR_DIR, PROCESSED_AVATAR_PATH
from utils.logger import logger

# Path to the dedicated Blender automation script
PROCESS_AVATAR_SCRIPT = BASE_DIR / "scripts" / "process_avatar.py"


# ─────────────────────────────────────────
# Blender Executable Detection
# ─────────────────────────────────────────

def find_blender_binary() -> Optional[Path]:
    """
    Auto-detects Blender 4.x executable on Windows.

    Search order:
      1. BLENDER_PATH config / env variable
      2. System PATH (shutil.which)
      3. C:\\Program Files\\Blender Foundation\\Blender 4.x\\blender.exe
      4. Blender 3.x fallback
      5. Steam installation paths
      6. Custom drive locations
    """
    # 1. User-configured path (env or settings.py)
    if BLENDER_PATH and Path(BLENDER_PATH).exists():
        logger.info(f"  Blender: Found via config: {BLENDER_PATH}")
        return Path(BLENDER_PATH)

    # 2. System PATH
    path_blender = shutil.which("blender")
    if path_blender:
        logger.info(f"  Blender: Found in system PATH: {path_blender}")
        return Path(path_blender)

    # 3. Windows Registry — most reliable method for finding installed apps
    try:
        import winreg
        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BlenderFoundation"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\BlenderFoundation"),
            (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\BlenderFoundation"),
        ]
        for hive, key_path in registry_keys:
            try:
                key = winreg.OpenKey(hive, key_path)
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        try:
                            install_dir = winreg.QueryValueEx(subkey, "Install_Dir")[0]
                            candidate = Path(install_dir) / "blender.exe"
                            if candidate.exists():
                                logger.info(f"  Blender: Found via Windows Registry [{subkey_name}]: {candidate}")
                                return candidate
                        except OSError:
                            pass
                        i += 1
                    except OSError:
                        break
            except OSError:
                continue
    except Exception:
        pass

    # 4. Windows — Blender Foundation standard install paths (5.x first, then 4.x, then 3.x)
    search_patterns = [
        # Blender 5.x — newest
        r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 5*\blender.exe",
        # Blender 4.x
        r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4*\blender.exe",
        # Blender 3.x fallback
        r"C:\Program Files\Blender Foundation\Blender 3*\blender.exe",
        # x86
        r"C:\Program Files (x86)\Blender Foundation\Blender 5*\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender 4*\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender 3*\blender.exe",
        # AppData (portable installs / user installs)
        os.path.expanduser(r"~\AppData\Local\Programs\Blender Foundation\Blender 5*\blender.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Blender Foundation\Blender 4*\blender.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Blender Foundation\Blender 3*\blender.exe"),
        # Steam
        r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
        r"C:\SteamLibrary\steamapps\common\Blender\blender.exe",
        r"D:\SteamLibrary\steamapps\common\Blender\blender.exe",
        r"E:\SteamLibrary\steamapps\common\Blender\blender.exe",
        # Custom drive locations
        r"C:\blender*\blender.exe",
        r"D:\blender*\blender.exe",
        r"D:\Program Files\Blender Foundation\Blender 5*\blender.exe",
        r"D:\Program Files\Blender Foundation\Blender 4*\blender.exe",
    ]

    for pattern in search_patterns:
        matches = glob.glob(pattern)
        if matches:
            matches.sort(reverse=True)  # Pick highest version first
            blender_bin = Path(matches[0])
            if blender_bin.exists():
                logger.info(f"  Blender: Auto-detected [{blender_bin.parent.name}] -> {blender_bin}")
                return blender_bin

    logger.warning("  Blender: Executable not found. Tried all standard Windows paths.")
    logger.warning("  Tip: Set BLENDER_PATH=/path/to/blender.exe in your .env file.")
    return None


# ─────────────────────────────────────────
# Main Processing Function
# ─────────────────────────────────────────

def process_custom_avatar(
    input_avatar_path: Optional[Path] = None,
    output_glb_path: Optional[Path] = None,
    timeout: int = 180
) -> Optional[Path]:
    """
    Run Blender headlessly to process the avatar FBX and export processed_anchor.glb.

    Command executed:
        blender.exe -b --python scripts/process_avatar.py

    Args:
        input_avatar_path: Path to FBX/GLB/blend avatar file. Auto-detects if None.
        output_glb_path:   Output path for processed GLB. Defaults to PROCESSED_AVATAR_PATH.
        timeout:           Max seconds to allow Blender to run (default: 180s / 3min).

    Returns:
        Path to processed_anchor.glb on success, None on failure.
    """
    if output_glb_path is None:
        output_glb_path = PROCESSED_AVATAR_PATH

    # Auto-detect input avatar if not specified
    if input_avatar_path is None:
        candidates = [
            AVATAR_DIR / "anchor.fbx",
            AVATAR_DIR / "Ch33_nonPBR.fbx",
            AVATAR_DIR / "custom_anchor.fbx",
        ]
        for c in candidates:
            if c.exists():
                input_avatar_path = c
                break

    # Validate input
    if input_avatar_path is None or not input_avatar_path.exists():
        logger.warning(f"  Blender Service: No avatar FBX found in {AVATAR_DIR}")
        return None

    # Validate Blender script exists
    if not PROCESS_AVATAR_SCRIPT.exists():
        logger.error(f"  Blender Service: Blender script not found: {PROCESS_AVATAR_SCRIPT}")
        return None

    # Find Blender binary
    blender_bin = find_blender_binary()
    if not blender_bin:
        logger.warning("  Blender Service: Blender not found — using static avatar fallback.")
        return None

    # Already processed? Skip if GLB is fresh
    if (output_glb_path.exists()
            and output_glb_path.stat().st_size > 100_000
            and input_avatar_path.stat().st_mtime < output_glb_path.stat().st_mtime):
        size_mb = output_glb_path.stat().st_size / (1024 * 1024)
        logger.info(f"  Blender Service: processed_anchor.glb already up-to-date ({size_mb:.2f} MB). Skipping.")
        return output_glb_path

    logger.info("=" * 55)
    logger.info("  Blender Service: Starting avatar processing pipeline...")
    logger.info(f"  Input  : {input_avatar_path.name}")
    logger.info(f"  Script : {PROCESS_AVATAR_SCRIPT.name}")
    logger.info(f"  Output : {output_glb_path.name}")
    logger.info(f"  Blender: {blender_bin}")
    logger.info("=" * 55)

    # Build the subprocess command
    cmd = [
        str(blender_bin),
        "--background",           # -b  headless mode
        "--python", str(PROCESS_AVATAR_SCRIPT),
    ]

    # Pass paths via environment variables to the Blender script
    env = os.environ.copy()
    env["BLENDER_INPUT_AVATAR"] = str(input_avatar_path.resolve())
    env["BLENDER_OUTPUT_GLB"] = str(output_glb_path.resolve())

    try:
        logger.info(f"  Running: {blender_bin.name} --background --python {PROCESS_AVATAR_SCRIPT.name}")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            cwd=str(BASE_DIR),
            env=env,
        )

        # Show Blender script output lines
        for line in result.stdout.splitlines():
            if "[Blender Avatar]" in line or "ERROR" in line or "WARNING" in line:
                logger.info(f"    {line.strip()}")

        if result.returncode != 0:
            logger.warning(f"  Blender exited with code {result.returncode}")
            stderr_tail = result.stderr[-600:] if result.stderr else ""
            if stderr_tail:
                logger.warning(f"  Blender stderr: ...{stderr_tail}")

        # Validate output
        if output_glb_path.exists() and output_glb_path.stat().st_size > 10_000:
            size_mb = output_glb_path.stat().st_size / (1024 * 1024)
            logger.info(f"  Blender Service: SUCCESS — processed_anchor.glb ({size_mb:.2f} MB)")
            return output_glb_path
        else:
            logger.warning("  Blender Service: GLB output not created or too small — using fallback.")
            return None

    except subprocess.TimeoutExpired:
        logger.warning(f"  Blender Service: Timed out after {timeout}s — using fallback.")
        return None
    except FileNotFoundError:
        logger.error(f"  Blender Service: blender.exe not found at {blender_bin}")
        return None
    except Exception as e:
        logger.warning(f"  Blender Service: Unexpected error: {e}")
        return None


# ─────────────────────────────────────────
# Standalone Test
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("BLENDER SERVICE — Standalone Test")
    print("=" * 55)

    blender = find_blender_binary()
    if blender:
        print(f"Blender Found : {blender}")
    else:
        print("Blender Not Found — check installation or set BLENDER_PATH in .env")

    print()
    # Test avatar processing
    test_fbx = AVATAR_DIR / "anchor.fbx"
    if not test_fbx.exists():
        test_fbx = AVATAR_DIR / "Ch33_nonPBR.fbx"

    if test_fbx.exists():
        print(f"Processing    : {test_fbx.name}")
        result = process_custom_avatar(test_fbx)
        if result:
            print(f"Output GLB    : {result}")
        else:
            print("Processing failed — check Blender installation.")
    else:
        print(f"No avatar FBX found in: {AVATAR_DIR}")
        print("Place anchor.fbx inside assets/avatar/ and re-run.")
