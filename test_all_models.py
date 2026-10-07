import os, sys
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(Path(__file__).parent / ".env")
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

test_models = ['allam-2-7b', 'groq/compound-mini', 'qwen/qwen3.6-27b']

for m in test_models:
    try:
        print(f"\n================ Testing {m} ================")
        resp = client.chat.completions.create(
            model=m,
            messages=[
                {"role": "user", "content": "वाराणसी में बाढ़ पर 100 शब्दों का हिंदी समाचार लिखें।"}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        content = resp.choices[0].message.content
        print(f"Success with {m}! Length: {len(content)}")
        print("Preview:\n", content[:300])
    except Exception as e:
        print(f"Error on {m}: {e}")
