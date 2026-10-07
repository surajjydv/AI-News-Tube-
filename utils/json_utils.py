"""
utils/json_utils.py
===================
Robust JSON Extraction from LLM Responses.
Strips thinking tags (<think>...</think>), markdown code blocks, and conversational preambles.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union

def clean_thinking_tags(text: str) -> str:
    """Removes model thinking/reasoning tags such as <think>...</think>."""
    if not text:
        return ""
    # If closed think tag exists, grab the text AFTER </think>
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    if "</thought>" in text:
        text = text.split("</thought>")[-1].strip()
        
    # If unclosed <think> exists, find the first { and return from there
    if "<think>" in text:
        first_brace = text.find("{")
        if first_brace != -1:
            text = text[first_brace:]
        else:
            text = re.sub(r'<think>.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()

def extract_json_from_llm(text: str) -> Union[Dict[str, Any], List[Any]]:
    """
    Extracts and parses JSON (dict or list) from LLM output text,
    stripping markdown code blocks, thinking tags, preamble text, and trailing commentary.
    """
    if not text:
        raise ValueError("Empty LLM output")
        
    s = clean_thinking_tags(text)
    
    # 1. Direct parse
    try:
        return json.loads(s)
    except Exception:
        pass
        
    # 2. Markdown block extraction
    if "```" in s:
        matches = re.findall(r"```(?:json)?\s*(.*?)\s*```", s, re.DOTALL | re.IGNORECASE)
        for match in matches:
            block = clean_thinking_tags(match).strip()
            try:
                return json.loads(block)
            except Exception:
                pass

    # 3. Substring JSON match for balanced curly braces
    # Find the first '{' and last '}'
    first_brace = s.find('{')
    last_brace = s.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = s[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except Exception:
            # Try cleaning trailing commas
            cleaned_cand = re.sub(r',\s*([\}\]])', r'\1', candidate)
            try:
                return json.loads(cleaned_cand)
            except Exception:
                pass

    # 4. Substring JSON match for list brackets '[' and ']'
    first_bracket = s.find('[')
    last_bracket = s.rfind(']')
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        candidate = s[first_bracket:last_bracket + 1]
        try:
            return json.loads(candidate)
        except Exception:
            cleaned_cand = re.sub(r',\s*([\}\]])', r'\1', candidate)
            try:
                return json.loads(cleaned_cand)
            except Exception:
                pass

    # 5. Regex-based key extractor as last-resort recovery for script dictionaries
    res_dict = {}
    head_match = re.search(r'["\']broadcast_headline["\']\s*:\s*["\']([^"\']+)["\']', s)
    if head_match:
        res_dict["broadcast_headline"] = head_match.group(1).strip()

    narr_match = re.search(r'["\']full_narration["\']\s*:\s*["\']([^"\']+)["\']', s, re.DOTALL)
    if narr_match:
        res_dict["full_narration"] = narr_match.group(1).strip()

    takeaways_match = re.search(r'["\']slide_takeaways["\']\s*:\s*\[(.*?)\]', s, re.DOTALL)
    if takeaways_match:
        items = re.findall(r'["\']([^"\']+)["\']', takeaways_match.group(1))
        if items:
            res_dict["slide_takeaways"] = [it.strip() for it in items if len(it.strip()) > 3]

    if "full_narration" in res_dict and len(res_dict["full_narration"]) > 50:
        return res_dict

    raise ValueError(f"Could not parse valid JSON from text: {text[:120]}")
