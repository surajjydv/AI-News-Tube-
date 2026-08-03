import os
import sys
import re
import time
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import VOICE_DIR, DEFAULT_TTS_VOICE
from models.news_models import GeneratedScript
from services.groq_service import generate_speech_groq
from utils.logger import logger


def _clean_text_for_tts(raw_text: str) -> str:
    """Cleans markdown symbols, tags, and formatting so TTS reads clean spoken Hindi."""
    if not raw_text:
        return ""
    # Remove markdown bold/italics/headings/symbols
    cleaned = re.sub(r'[\*#_`~]', '', raw_text)
    # Remove section brackets like [HOOK], [PROBLEM] if present
    cleaned = re.sub(r'\[.*?\]', '', cleaned)
    # Normalize multiple whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def voice_agent(script_obj: GeneratedScript) -> GeneratedScript:
    """
    Voice Agent: Generates Neural TTS voiceover for the news script.
    Robust fallback hierarchy:
      1. Edge-TTS (Microsoft Neural Voice)
      2. Groq CanopyLabs Orpheus TTS
      3. gTTS (Google Text-To-Speech Fallback)
    """
    logger.info("=" * 50)
    logger.info("🎙️ VOICE AGENT (Neural TTS Engine)")
    logger.info("=" * 50)

    ts = int(time.time())
    voice_path = VOICE_DIR / f"voice_{ts}.mp3"
    
    raw_text = script_obj.script_text if script_obj.script_text else script_obj.topic_title
    full_text = _clean_text_for_tts(raw_text)

    if not full_text:
        full_text = "नमस्कार! AI-NewsTube में आपका स्वागत है।"

    # 1. Try Microsoft Edge-TTS
    try:
        import edge_tts

        async def _run_tts():
            communicate = edge_tts.Communicate(full_text, voice=DEFAULT_TTS_VOICE, rate="+0%")
            await communicate.save(str(voice_path))

        try:
            asyncio.run(_run_tts())
        except RuntimeError:
            # Handle case where an event loop is already running in current thread
            loop = asyncio.get_event_loop()
            loop.run_until_complete(_run_tts())

        if voice_path.exists() and voice_path.stat().st_size > 1000:
            logger.info(f"  ✅ Voice Agent: Generated Neural Edge-TTS voiceover ({voice_path.name})")
            script_obj.audio_path = str(voice_path)
            return script_obj
    except Exception as e:
        logger.warning(f"  ⚠️ Voice Agent Edge-TTS note: {e}")

    # 2. Try Groq CanopyLabs Orpheus TTS
    try:
        success = generate_speech_groq(full_text, str(voice_path))
        if success and voice_path.exists() and voice_path.stat().st_size > 1000:
            logger.info(f"  ✅ Voice Agent: Generated Groq Orpheus voiceover ({voice_path.name})")
            script_obj.audio_path = str(voice_path)
            return script_obj
    except Exception as e:
        logger.warning(f"  ⚠️ Voice Agent Groq Orpheus note: {e}")

    # 3. Fallback: gTTS
    try:
        from gtts import gTTS
        tts = gTTS(text=full_text, lang="hi" if "hi-" in DEFAULT_TTS_VOICE else "en", slow=False)
        tts.save(str(voice_path))
        if voice_path.exists() and voice_path.stat().st_size > 500:
            logger.info(f"  ✅ Voice Agent: Generated gTTS fallback voiceover ({voice_path.name})")
            script_obj.audio_path = str(voice_path)
            return script_obj
    except (ImportError, ModuleNotFoundError):
        logger.warning("  ⚠️ Voice Agent note: 'gTTS' package is not installed. Run 'pip install gtts' to enable gTTS fallback.")
    except Exception as e:
        logger.error(f"  ❌ Voice Agent gTTS error: {e}")

    return script_obj


if __name__ == "__main__":
    test_script = GeneratedScript(
        topic_title="टेस्ट न्यूज़",
        category="General",
        script_text="**बड़ी खबर!** भारत ने टेक्नोलॉजी के क्षेत्र में एक नया मील का पत्थर हासिल किया है।",
        word_count=15
    )
    voice_agent(test_script)
