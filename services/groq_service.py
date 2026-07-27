import os
import sys
from dotenv import load_dotenv, set_key
from groq import Groq
from config.settings import DEFAULT_GROQ_MODEL, ENV_FILE
from utils.logger import logger
from utils.exceptions import APIKeyError, ScriptGenerationError


def get_client() -> Groq:
    """
    Initializes and returns the Groq client after verifying GROQ_API_KEY.
    """
    load_dotenv(ENV_FILE, override=True)
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or api_key.strip() == "" or api_key == "your_groq_api_key_here":
        # Interactive prompt if running in terminal
        if sys.stdin and sys.stdin.isatty():
            print("\n" + "=" * 50)
            print("🔑 GROQ API KEY REQUIRED")
            print("=" * 50)
            print("To generate news scripts, a free Groq API key is required.")
            print("Get yours at: https://console.groq.com/keys\n")
            try:
                user_key = input("Paste your GROQ_API_KEY here: ").strip()
                if user_key:
                    api_key = user_key
                    os.environ["GROQ_API_KEY"] = api_key
                    set_key(str(ENV_FILE), "GROQ_API_KEY", api_key)
                    logger.info("GROQ_API_KEY saved to .env successfully.")
            except Exception as e:
                logger.warning(f"Could not interactively save GROQ_API_KEY: {e}")

    if not api_key or api_key.strip() == "" or api_key == "your_groq_api_key_here":
        raise APIKeyError(
            "GROQ_API_KEY not found or invalid.\n"
            "Please open .env file and set: GROQ_API_KEY=gsk_your_actual_key_here\n"
            "Get a free key at https://console.groq.com/keys"
        )

    return Groq(api_key=api_key)


def generate_text(prompt: str, model: str = DEFAULT_GROQ_MODEL, temperature: float = 0.7, max_tokens: int = 800) -> str:
    """
    Generates text using Groq API with robust error handling.
    """
    try:
        client = get_client()
        logger.info(f"Calling Groq LLM API (Model: {model})...")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        result = response.choices[0].message.content.strip()
        return result
    except APIKeyError:
        raise
    except Exception as e:
        logger.error(f"Error during Groq text generation: {e}")
        raise ScriptGenerationError(f"Failed to generate text using Groq: {e}") from e


def generate_speech_groq(
    text: str,
    output_path: str,
    model: str = "canopylabs/orpheus-v1-english",
    voice: str = "daniel",
    response_format: str = "mp3"
) -> bool:
    """
    Generates ultra-expressive AI voice audio using Groq CanopyLabs Orpheus model:
    `canopylabs/orpheus-v1-english`
    Voices: 'daniel', 'austin', 'troy', 'diana', 'hannah', 'autumn'
    Supports vocal direction tags: [urgent], [dramatic], [cheerful], [whisper]

    Requires:
      1. Accepting model terms at https://console.groq.com/playground?model=canopylabs%2Forpheus-v1-english
      2. Setting GROQ_ORPHEUS_ENABLED=true in .env
    """
    from dotenv import load_dotenv as _load
    _load(ENV_FILE, override=True)
    orpheus_enabled = os.getenv("GROQ_ORPHEUS_ENABLED", "false").strip().lower()

    if orpheus_enabled != "true":
        logger.info("  [Orpheus] GROQ_ORPHEUS_ENABLED=false — skipping Groq TTS (using Edge-TTS fallback).")
        logger.info("  [Orpheus] To enable: accept terms at https://console.groq.com/playground?model=canopylabs%2Forpheus-v1-english")
        logger.info("            then set GROQ_ORPHEUS_ENABLED=true in .env")
        return False

    try:
        client = get_client()
        logger.info(f"  [Orpheus] Calling Groq Speech API (Model: {model}, Voice: {voice})...")

        # Apply vocal direction tag based on content
        if not any(text.startswith(f"[{tag}]") for tag in ["urgent", "dramatic", "cheerful", "whisper", "calm"]):
            text = f"[urgent] {text}"

        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format=response_format,
        )

        content = response.content if hasattr(response, "content") else response.read()
        if content and len(content) > 1000:
            with open(output_path, "wb") as f:
                f.write(content)
            size_kb = len(content) // 1024
            logger.info(f"  [Orpheus] Audio saved: {output_path} ({size_kb} KB)")
            return True
        logger.warning("  [Orpheus] Empty audio response from Groq.")
        return False

    except Exception as e:
        err_str = str(e)
        if "model_terms_required" in err_str:
            logger.warning("  [Orpheus] Terms not yet accepted on Groq Console.")
            logger.warning("  Accept here: https://console.groq.com/playground?model=canopylabs%2Forpheus-v1-english")
            logger.warning("  Then set GROQ_ORPHEUS_ENABLED=true in .env — falling back to Edge-TTS.")
        else:
            logger.warning(f"  [Orpheus] Groq Speech API error: {e}")
        return False


