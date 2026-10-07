"""
services/investigative_explainer_engine.py
=========================================
Deep-Dive Case Study & Documentary Script Engine (Nitish Rajput & Dhruv Rathee Style).
Transforms multi-source research dossiers into high-tension, analytical 4-chapter video essays.
"""

import os
import sys
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.groq_service import generate_text
from utils.json_utils import extract_json_from_llm
from utils.font_utils import sanitize_text
from utils.logger import logger


class InvestigativeExplainerEngine:
    @classmethod
    def generate_case_study_script(
        cls,
        topic: str,
        category: str,
        research_dossier: str,
        target_minutes: float = 6.0
    ) -> Tuple[str, List[Dict[str, str]], str, str, List[str]]:
        """
        Generates an in-depth 4-chapter investigative case study script (Nitish Rajput / Dhruv Rathee style).
        Returns: (full_narration, chapter_breakdown, on_screen_title, viral_youtube_title, tags)
        """
        clean_topic = sanitize_text(topic).split(" - ")[0].strip()
        word_min = int(target_minutes * 125)
        word_max = int(target_minutes * 160)

        prompt = (
            f"You are a top investigative documentary creator and video essayist (like Nitish Rajput, Dhruv Rathee, and Johnny Harris).\n"
            f"Write an exhaustive, fact-checked, deep-dive documentary script for this major trending event/controversy.\n\n"
            f"TOPIC: {clean_topic}\n"
            f"CATEGORY: {category.upper()}\n"
            f"TARGET DURATION: {target_minutes:.1f} Minutes ({word_min}-{word_max} spoken words)\n"
            f"RESEARCH DOSSIER & VERIFIED DOCUMENTS:\n{research_dossier[:3200]}\n\n"
            f"CRITICAL STORYTELLING STRUCTURE:\n"
            f"1. THE HOOK: Open with the dramatic scene, exact crisis moment, or conflict unfolding on the ground. ZERO greetings ('Welcome', 'Hello'), ZERO headline reading (never recite the topic title verbatim as the opening sentence).\n"
            f"2. CHAPTER 1 - THE GENESIS & TIMELINE: Take the audience back to where it all began. Explain the background history, the key individuals, companies, or institutions involved, and the initial warning signs.\n"
            f"3. CHAPTER 2 - THE TURNING POINT & CONFLICT: Unpack the investigation, official records, leaked memos, financial transactions, or critical decisions that triggered the crisis.\n"
            f"4. CHAPTER 3 - THE EVIDENCE & OFFICIAL REACTIONS: Breakdown what both sides are claiming, what independent investigators/regulators discovered, and the hard data.\n"
            f"5. CHAPTER 4 - THE IMPACT & THE FINAL THOUGHT: Provide an unbiased, intellectual analysis of what this means for citizens, the industry, or the future.\n"
            f"6. LANGUAGE: Fluent, natural, engaging English. Clear, objective, analytical, and gripping tone.\n"
            f"7. LENGTH: Write a full, detailed {word_min} to {word_max} spoken words.\n\n"
            f"OUTPUT FORMAT: Respond strictly with a valid JSON object matching this schema:\n"
            f"{{\n"
            f'  "viral_youtube_title": "(High-CTR mystery/case study title, e.g. The Real Story Behind the Crisis | Full Investigation)",\n'
            f'  "documentary_title": "(Clean on-screen documentary title, max 8 words)",\n'
            f'  "full_narration": "(The complete, exhaustive {word_min}-{word_max} words spoken documentary narrative starting directly with the core event scene)",\n'
            f'  "chapters": [\n'
            f'    {{"chapter_num": "01", "title": "The Spark", "summary": "Key fact for chapter 1 (10-14 words)"}},\n'
            f'    {{"chapter_num": "02", "title": "The Hidden Past", "summary": "Key fact for chapter 2 (10-14 words)"}},\n'
            f'    {{"chapter_num": "03", "title": "The Evidence", "summary": "Key fact for chapter 3 (10-14 words)"}},\n'
            f'    {{"chapter_num": "04", "title": "The Aftermath", "summary": "Key fact for chapter 4 (10-14 words)"}}\n'
            f'  ],\n'
            f'  "youtube_tags": ["Documentary", "Investigation", "CaseStudy", "Explained", "{category}", "RealStory"]\n'
            f"}}"
        )

        logger.info(f"📝 [Investigative Explainer Engine] Generating deep-dive documentary script ({target_minutes:.1f} min, {word_min}-{word_max} words)...")

        # Default chapter structure used when LLM omits or garbles the chapters field
        default_chapters = [
            {"chapter_num": "01", "title": "The Incident",   "summary": f"How the crisis around {clean_topic[:40]} began"},
            {"chapter_num": "02", "title": "The Background", "summary": "Key decisions and timeline leading to this moment"},
            {"chapter_num": "03", "title": "The Evidence",   "summary": "Official findings, documents and investigative data"},
            {"chapter_num": "04", "title": "The Aftermath",  "summary": "Long-term impact and what this means going forward"},
        ]

        try:
            response = generate_text(prompt, temperature=0.35, max_tokens=6000)
            data = extract_json_from_llm(response)
            if isinstance(data, dict) and "full_narration" in data:
                raw_narr = str(data["full_narration"])
                cleaned_narr = re.sub(r'[\.\s…]{2,}', '. ', raw_narr).strip()
                d_title = str(data.get("documentary_title", clean_topic)).strip()
                v_title = str(data.get("viral_youtube_title", f"{d_title} | Full Investigation")).strip()
                tags = data.get("youtube_tags", ["Documentary", "Investigation", "CaseStudy", "Explained", category])

                # Robust chapter extraction: handle missing, empty, or malformed chapters
                raw_chapters = data.get("chapters", [])
                if isinstance(raw_chapters, list) and len(raw_chapters) >= 2:
                    chapters = raw_chapters
                else:
                    # Auto-split narration into 4 chapters by paragraph if LLM skipped chapters
                    paragraphs = [p.strip() for p in cleaned_narr.split('\n') if len(p.strip()) > 60]
                    if len(paragraphs) >= 4:
                        chunk = max(1, len(paragraphs) // 4)
                        chapters = [
                            {"chapter_num": "01", "title": "The Incident",   "summary": paragraphs[0][:80]},
                            {"chapter_num": "02", "title": "The Background", "summary": paragraphs[chunk][:80]},
                            {"chapter_num": "03", "title": "The Evidence",   "summary": paragraphs[chunk*2][:80]},
                            {"chapter_num": "04", "title": "The Aftermath",  "summary": paragraphs[min(chunk*3, len(paragraphs)-1)][:80]},
                        ]
                    else:
                        chapters = default_chapters
                    logger.warning(f"  ⚠️ LLM returned {len(raw_chapters)} chapters — auto-generated 4 chapters from narration.")

                if len(cleaned_narr.split()) >= 180:
                    logger.info(f"  ✅ Investigative Case Study Generated: {len(cleaned_narr.split())} words, {len(chapters)} chapters.")
                    return cleaned_narr, chapters, d_title, v_title, tags
        except Exception as e:
            logger.warning(f"  Explainer engine LLM note: {e}")

        # Full fallback: safe minimal narration that will still render
        fallback_narr = (
            f"Behind closed doors and official boardrooms, a chain of high-stakes decisions has triggered a massive chain reaction. "
            f"To understand how {clean_topic} reached a critical boiling point, we need to examine the full timeline of events. "
            f"According to verified investigative findings and official filings, the roots of this crisis trace back to fundamental strategic choices. "
            f"Independent analysts and ground reporters confirm that the unfolding of this situation has wide-reaching consequences. "
            f"As official inquiries deepen, observers emphasize that the outcome of this case will set a major precedent for years to come."
        )
        return fallback_narr, default_chapters, clean_topic, f"{clean_topic} | The Untold Story", ["Documentary", "Investigation", "Explained"]
