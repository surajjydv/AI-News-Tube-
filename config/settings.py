import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base Project Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Fix sys.path to ensure 'config', 'models', 'services', 'utils' are importable from anywhere
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load environment variables
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE, override=True)

# Application Details
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "AI-NewsTube")
OWNER = os.getenv("OWNER", "Suraj")
VERSION = "1.1.0"

# Directories Management
LOGS_DIR = BASE_DIR / "logs"
VOICE_DIR = BASE_DIR / "voice"
VIDEOS_DIR = BASE_DIR / "videos"
THUMBNAILS_DIR = BASE_DIR / "thumbnails"
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
ASSETS_DIR = BASE_DIR / "assets"
AVATAR_DIR = ASSETS_DIR / "avatar"
PROCESSED_AVATAR_PATH = AVATAR_DIR / "processed_anchor.glb"

# Ensure directories exist
for directory in [LOGS_DIR, VOICE_DIR, VIDEOS_DIR, THUMBNAILS_DIR, DATA_DIR, UPLOADS_DIR, ASSETS_DIR, AVATAR_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Blender Auto-Detection Configuration
BLENDER_PATH = os.getenv("BLENDER_PATH", None)

# LLM & API Configuration
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
DEFAULT_TTS_VOICE = os.getenv("DEFAULT_TTS_VOICE", "hi-IN-SwaraNeural")  # Hindi Female Anchor Voice