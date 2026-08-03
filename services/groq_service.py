import os
import sys
import hashlib
import json
import threading
import time
from pathlib import Path
from dotenv import load_dotenv, set_key
from groq import Groq
from config.settings import DEFAULT_GROQ_MODEL, ENV_FILE
from utils.logger import logger
from utils.exceptions import APIKeyError, ScriptGenerationError

LLM_CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "llm_cache.json"
LLM_CACHE_LOCK = threading.Lock()
MODEL_COOLDOWN_UNTIL = {}
DEFAULT_FALLBACK_MODELS = ["llama-3.1-8b-instant", "gemma2-9b-it"]


def _cache_key(prompt: str) -> str:
    return hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()


def _read_cache() -> dict:
    try:
        return json.loads(LLM_CACHE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _cached_response(prompt: str):
    with LLM_CACHE_LOCK:
        return _read_cache().get(_cache_key(prompt))


def _store_response(prompt: str, result: str):
    with LLM_CACHE_LOCK:
        cache = _read_cache()
        cache[_cache_key(prompt)] = result
        # Keep the cache bounded for a long-running 24/7 process.
        if len(cache) > 500:
            cache = dict(list(cache.items())[-500:])
        LLM_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = LLM_CACHE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        tmp.replace(LLM_CACHE_FILE)


def _is_rate_limit_error(error: Exception) -> bool:
    status = getattr(error, "status_code", None) or getattr(error, "response", None)
    message = str(error).lower()
    return status == 429 or "429" in message or "rate limit" in message or "tokens per day" in message


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
    Generates text with bounded token usage, disk cache, cooldowns, and fallback.
    """
    cached = _cached_response(prompt)
    if cached:
        logger.info("Using cached LLM response; skipping Groq request.")
        return cached

    # 70B is opt-in only. The 8B model is sufficient for routine headline and
    # bulletin copy and avoids exhausting the daily token budget.
    configured_model = model or DEFAULT_GROQ_MODEL
    models_to_try = [configured_model] + DEFAULT_FALLBACK_MODELS
    # De-duplicate while preserving order
    unique_models = []
    for m in models_to_try:
        if m not in unique_models:
            unique_models.append(m)

    last_error = None
    for m in unique_models:
        if MODEL_COOLDOWN_UNTIL.get(m, 0) > time.time():
            logger.info(f"Skipping Groq model {m}; rate-limit cooldown is active.")
            continue
        try:
            client = get_client()
            logger.info(f"Calling Groq LLM API (Model: {m})...")
            response = client.chat.completions.create(
                model=m,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=min(max_tokens, 500),
            )
            result = response.choices[0].message.content.strip()
            if result:
                _store_response(prompt, result)
            return result
        except APIKeyError:
            raise
        except Exception as e:
            last_error = e
            if _is_rate_limit_error(e):
                MODEL_COOLDOWN_UNTIL[m] = time.time() + 3600
                logger.warning(f"Groq model {m} rate-limited; switching to fallback without retry.")
            else:
                logger.warning(f"Groq LLM model {m} attempt failed ({e}), trying fallback model...")

    logger.error(f"Error during Groq text generation across all models: {last_error}")
    raise ScriptGenerationError(f"Failed to generate text using Groq: {last_error}")


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
