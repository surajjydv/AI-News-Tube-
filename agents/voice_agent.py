import asyncio
import re
from datetime import datetime
from pathlib import Path
from edge_tts import Communicate
from config.settings import VOICE_DIR, DEFAULT_TTS_VOICE
from services.groq_service import generate_speech_groq
from models.news_models import GeneratedScript
from utils.logger import logger
from utils.exceptions import VoiceGenerationError


def format_ssml_script(text: str) -> str:
    """
    Cleans and inserts prosody pause points for natural human news anchor cadence.
    """
    cleaned = re.sub(r'[*#_`~]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Add slight pause punctuation for natural anchor rhythm
    cleaned = cleaned.replace("!", "! ").replace("?", "? ").replace(".", ". ")
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


async def _generate_voice_async(text: str, output_path: Path, voice: str, rate: str = "+3%", pitch: str = "+0Hz") -> None:
    communicate = Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(str(output_path))


def voice_agent(script_obj: GeneratedScript, voice: str = DEFAULT_TTS_VOICE) -> GeneratedScript:
    """
    Emotional Voice Agent: Converts retention script into high-impact AI Voice MP3.
    Primary Engine: Groq CanopyLabs Orpheus model (`canopylabs/orpheus-v1-english`)
    Fallback Engine: Edge TTS / gTTS
    """
    logger.info("=" * 50)
    logger.info("🎙️ EMOTIONAL VOICE AGENT (Groq CanopyLabs Orpheus & Neural TTS Engine)")
    logger.info("=" * 50)

    try:
        script_text = format_ssml_script(script_obj.script_text)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voice_{timestamp}.mp3"
        output_file = VOICE_DIR / filename

        # 1. Try Groq CanopyLabs Orpheus (`canopylabs/orpheus-v1-english`)
        #    Requires GROQ_ORPHEUS_ENABLED=true in .env after accepting terms:
        #    https://console.groq.com/playground?model=canopylabs%2Forpheus-v1-english
        groq_success = generate_speech_groq(
            text=script_text,
            output_path=str(output_file),
            model="canopylabs/orpheus-v1-english",
            voice="daniel"
        )

        if groq_success and output_file.exists() and output_file.stat().st_size > 1000:
            logger.info(f"✅ Voiceover generated via Groq Orpheus: {output_file.name} ({output_file.stat().st_size} bytes)")
            script_obj.audio_path = str(output_file)
            return script_obj

        # 2. Fallback: Edge TTS
        logger.info("  🔄 Falling back to Neural Edge-TTS voice engine...")
        if "breaking" in script_obj.topic_title.lower() or "dhamaka" in script_text.lower():
            rate = "+5%"
            pitch = "+2Hz"
            logger.info("  ⚡ Prosody mode: URGENT BREAKING NEWS (+5% rate, +2Hz pitch)")
        else:
            rate = "+2%"
            pitch = "+0Hz"
            logger.info("  🎙️ Prosody mode: HIGH-RETENTION ANCHOR CADENCE (+2% rate)")

        logger.info(f"Generating AI Voiceover (Voice: {voice}, Rate: {rate}, Pitch: {pitch})...")
        asyncio.run(_generate_voice_async(script_text, output_file, voice, rate=rate, pitch=pitch))

        if output_file.exists() and output_file.stat().st_size > 0:
            logger.info(f"✅ Voiceover generated successfully: {output_file.name} ({output_file.stat().st_size} bytes)")
            script_obj.audio_path = str(output_file)
            return script_obj
        else:
            raise VoiceGenerationError("Audio file was not generated or is 0 bytes.")

    except Exception as e:
        logger.error(f"Error in Voice Agent: {e}")
        raise VoiceGenerationError(f"Failed to generate voiceover: {e}") from e
