import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from services.fluent_script_service import generate_fluent_news_script

title = "वाराणसी के सभी घाट डूबे, छतों पर आरती-अंतिम संस्कार: MP-UP समेत 4 राज्यों में आज भारी बारिश; राजस्थान में अलर्ट"
context = "वाराणसी में गंगा का जलस्तर खतरे के निशान के करीब पहुंच गया है। सभी 84 घाट जलमग्न हो चुके हैं। मणिकर्णिका और हरिश्चंद्र घाट पर छतों और गलियों में अंतिम संस्कार किया जा रहा है। दशाश्वमेध घाट पर प्रसिद्ध गंगा आरती अब छत पर हो रही है। मौसम विभाग ने मध्य प्रदेश, उत्तर प्रदेश, राजस्थान और गुजरात में भारी बारिश का रेड अलर्ट जारी किया है। NDRF और SDRF की टीमें अलर्ट पर हैं।"

print("Generating Fluent News Script...")
narr, takeaways, head = generate_fluent_news_script(
    title=title,
    category="National",
    context=context,
    target_minutes=2
)

print("\n" + "=" * 60)
print(f"HEADLINE: {head}")
print(f"WORD COUNT: {len(narr.split())}")
print("=" * 60)
print(f"NARRATION:\n{narr}")
print("=" * 60)
print(f"SLIDE TAKEAWAYS ({len(takeaways)}):")
for i, t in enumerate(takeaways, 1):
    print(f"  [{i}] {t}")
print("=" * 60)
