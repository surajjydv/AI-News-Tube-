import os, json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

models = ['groq/compound', 'qwen/qwen3.6-27b', 'groq/compound-mini', 'openai/gpt-oss-20b']

for model_name in models:
    try:
        print(f"\n--- Testing {model_name} ---")
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a professional Hindi news anchor. Output ONLY valid JSON with keys: broadcast_headline, full_narration, slide_takeaways."},
                {"role": "user", "content": "Headline: वाराणसी के सभी घाट डूबे, छतों पर आरती-अंतिम संस्कार: MP-UP समेत 4 राज्यों में आज भारी बारिश\nWrite a 300-word detailed investigative spoken Hindi news narrative explaining all details, river water levels, ground administration actions, and public advisory."}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        content = resp.choices[0].message.content
        print(f"Result length for {model_name}: {len(content)}")
        print("First 300 chars:\n", content[:300])
    except Exception as e:
        print(f"Error on {model_name}: {e}")
