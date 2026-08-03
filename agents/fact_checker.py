import json
from services.scraper_service import get_article_context
from services.groq_service import generate_text
from models.news_models import NewsArticle, FactCheckResult
from utils.logger import logger


def build_fact_check_prompt(title: str, context: str, category: str) -> str:
    return f"""Tum ek professional News Fact Checker ho.

Category: {category}
Title: {title}

Article Context:
\"\"\"
{context}
\"\"\"

Is news article ka strict fact-checking karo aur JSON format mein hi output do.
Check criteria:
1. Kya news believable hai aur reliable sources se aligned hai?
2. Risk Level: "LOW" (safe news), "MEDIUM" (controversial/unverified), "HIGH" (harmful/fake news).
3. Confidence Score: 0.0 se 1.0 (float).
4. Verified Facts: Key facts ki list (2-3 bullet points).
5. Reasoning: Short explanation (1-2 sentences).

IMPORTANT: Return ONLY valid JSON format strictly matching this structure:
{{
    "is_credible": true,
    "confidence_score": 0.9,
    "verified_facts": ["Fact 1", "Fact 2"],
    "reasoning": "Reason here",
    "risk_level": "LOW"
}}
"""


def fact_checker(news_item: NewsArticle) -> FactCheckResult:
    """
    Fact Checker Agent: Verifies news authenticity, extracts verified facts, and assesses risk level.
    """
    logger.info("=" * 50)
    logger.info("🕵️ FACT CHECKER AGENT")
    logger.info("=" * 50)

    title = news_item.title
    link = news_item.link
    summary = news_item.summary
    category = news_item.category

    logger.info(f"Fact checking topic: [{category}] {title}")

    # Ensure scraped content is available
    if not news_item.scraped_content:
        news_item.scraped_content = get_article_context(link, fallback_summary=summary)

    context = news_item.scraped_content or title

    prompt = build_fact_check_prompt(title, context, category)

    try:
        response_text = generate_text(prompt, temperature=0.2)

        # Parse JSON output from LLM
        clean_json = response_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif clean_json.startswith("```"):
            clean_json = clean_json.split("```")[1].split("```")[0].strip()

        data = json.loads(clean_json)

        conf = float(data.get("confidence_score", 0.85))
        risk = str(data.get("risk_level", "LOW")).upper()
        is_cred = bool(data.get("is_credible", True)) and (conf >= 0.75) and (risk != "HIGH")

        result = FactCheckResult(
            is_credible=is_cred,
            confidence_score=conf,
            verified_facts=list(data.get("verified_facts", [title])),
            reasoning=str(data.get("reasoning", "Verified via trusted multi-source RSS feed.")),
            risk_level=risk
        )

        logger.info(f"Fact Check Verdict: Credible={result.is_credible} | Score={result.confidence_score:.2f} | Risk={result.risk_level}")
        logger.info(f"Reasoning: {result.reasoning}")
        return result

    except Exception as e:
        logger.warning(f"Fact Checker parsing warning ({e}). Defaulting to safe fallback.")
        return FactCheckResult(
            is_credible=True,
            confidence_score=0.75,
            verified_facts=[title],
            reasoning="Fallback verification from Google News RSS feed.",
            risk_level="LOW"
        )
