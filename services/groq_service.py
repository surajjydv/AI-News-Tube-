import os
import sys
from dotenv import load_dotenv, set_key
from groq import Groq

# Groq's currently supported Llama model.
DEFAULT_MODEL = "llama-3.3-70b-versatile"

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))


def get_client():
    load_dotenv(ENV_PATH, override=True)
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
                    # Auto-save to .env
                    with open(ENV_PATH, "a") as f:
                        pass
                    set_key(ENV_PATH, "GROQ_API_KEY", api_key)
                    print(f"✅ GROQ_API_KEY saved to .env!\n")
            except Exception:
                pass

    if not api_key or api_key.strip() == "" or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY not found or not set.\n"
            "Please open the .env file in the project folder and paste your Groq API key:\n"
            "GROQ_API_KEY=gsk_your_actual_key_here\n"
            "Get a free key at https://console.groq.com/keys"
        )

    return Groq(api_key=api_key)


def generate_text(prompt, model=DEFAULT_MODEL, temperature=0.7, max_tokens=800):
    client = get_client()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content.strip()

