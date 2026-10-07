import os, sys, json, re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

BASE_DIR = Path(__file__).resolve().parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(BASE_DIR / ".env")
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

prompt = (
    "You are an elite prime-time Hindi news anchor. Write a comprehensive, highly detailed 300-word spoken Hindi news narrative explaining this major story in full depth with real facts, river water levels, ground administration actions, and public advisory.\n\n"
    "Headline: वाराणसी के सभी घाट डूबे, छतों पर आरती-अंतिम संस्कार: MP-UP समेत 4 राज्यों में आज भारी बारिश\n"
    "Category: National\n\n"
    "Return a valid JSON object ONLY with:\n"
    "{\n"
    '  "broadcast_headline": "वाराणसी में गंगा का रौद्र रूप: सभी 84 घाट डूबे",\n'
    '  "full_narration": "(Full unbroken 300-word detailed Hindi narrative explaining the full story from start to finish)",\n'
    '  "slide_takeaways": [\n'
    '    "वाराणसी में गंगा का जलस्तर खतरे के निशान के पार पहुंचा",\n'
    '    "दशाश्वमेध घाट समेत सभी 84 प्रमुख घाट पूरी तरह जलमग्न",\n'
    '    "छतों और गलियों में शिफ्ट हुई प्रसिद्ध गंगा आरती और अंतिम संस्कार",\n'
    '    "एनडीआरएफ और राहत टीमों को अलर्ट पर रहने के निर्देश जारी"\n'
    '  ]\n'
    "}"
)

print("Calling groq/compound-mini...")
resp = client.chat.completions.create(
    model="groq/compound-mini",
    messages=[
        {"role": "system", "content": "You are a professional Hindi news anchor. Output ONLY valid JSON."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=2500
)

content = resp.choices[0].message.content.strip()
print(f"Raw length: {len(content)}")
print("Raw content:\n", content)

f_idx = content.find('{')
l_idx = content.rfind('}')
if f_idx != -1 and l_idx != -1:
    data = json.loads(content[f_idx:l_idx+1])
    print("\n✅ PERFECT JSON PARSED!")
    print("Headline:", data.get("broadcast_headline"))
    print("Narration Word Count:", len(data.get("full_narration", "").split()))
    print("\nFull Narration:\n", data.get("full_narration"))
    print("\nTakeaways:")
    for t in data.get("slide_takeaways", []):
        print("  -", t)
