"""
services/deep_research_service.py
==================================
Deep Multi-Source Research Engine.
Aggregates factual dossiers from:
  - Multi-angle DuckDuckGo search (3 query variants)
  - Full Wikipedia article text (not just intro)
  - Direct article body scraping
  - Related article scraping from search results
  - Structured entity extraction (names, numbers, dates, places, orgs)
"""

import os
import sys
import re
import time
import urllib.parse
import requests
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.logger import logger
from utils.font_utils import sanitize_text


class DeepResearchService:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    }

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Article Scraper — pulls full body (up to 8000 chars)
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def scrape_article_body(cls, url: str, max_chars: int = 8000) -> str:
        """Scrapes full text from a single article/report URL."""
        if not url or not url.startswith("http"):
            return ""
        try:
            resp = requests.get(url, headers=cls.HEADERS, timeout=10, allow_redirects=True)
            if resp.status_code == 200 and resp.text:
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "nav", "header", "footer",
                                  "aside", "form", "svg", "figure", "figcaption"]):
                    tag.decompose()
                # Prefer <article> body if present, else all <p>
                article_tag = soup.find("article")
                if article_tag:
                    paras = [p.get_text(strip=True) for p in article_tag.find_all("p")
                             if len(p.get_text(strip=True)) > 35]
                else:
                    paras = [p.get_text(strip=True) for p in soup.find_all("p")
                             if len(p.get_text(strip=True)) > 35]
                # Take more paragraphs — up to 35
                text = " ".join(paras[:35])
                return sanitize_text(text[:max_chars])
        except Exception as e:
            logger.debug(f"Article scrape note ({url[:40]}): {e}")
        return ""

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Wikipedia — full article (not just intro), up to 4000 chars
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def fetch_wikipedia_dossier(cls, topic: str) -> str:
        """Fetches Wikipedia full article extracts for background context."""
        try:
            clean_topic = re.sub(
                r'\s*[-|–—]\s*(?:BBC|NDTV|Reuters|The Hindu|CNN|AP|ANI|PTI|Aaj Tak).*$',
                '', topic, flags=re.I
            ).split(":")[0].strip()

            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "generator": "search",
                "gsrsearch": clean_topic,
                "prop": "extracts",
                "exintro": 0,          # Full article, not just intro
                "explaintext": 1,
                "exsectionformat": "plain",
                "format": "json",
                "gsrlimit": 2,         # Top 2 relevant articles
                "exsentences": 30,     # Up to 30 sentences per article
            }
            resp = requests.get(url, params=params,
                                headers={"User-Agent": "AI-News-Research/2.0"}, timeout=8)
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                extracts = []
                for pid, p in pages.items():
                    title = p.get("title", "")
                    extract = p.get("extract", "")
                    if extract and len(extract) > 80:
                        # Clean Wikipedia boilerplate
                        extract = re.sub(r'\n{3,}', '\n\n', extract)
                        extracts.append(f"[Wikipedia — {title}]\n{extract[:2000]}")
                if extracts:
                    return "\n\n".join(extracts)
        except Exception as e:
            logger.debug(f"Wikipedia research note: {e}")
        return ""

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Multi-angle DuckDuckGo search (3 query variants)
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def search_web_context(cls, query: str) -> str:
        """3-angle DuckDuckGo search: facts, timeline, and official statements."""
        clean_q = re.sub(
            r'\s*[-|–—]\s*(?:BBC|NDTV|Reuters|The Hindu|CNN|AP|Zee News|Google News).*$',
            '', query, flags=re.I
        ).strip()

        queries = [
            f"{clean_q} latest facts details",
            f"{clean_q} timeline background history",
            f"{clean_q} official statement government reaction",
        ]

        all_snippets = []
        seen = set()
        for q in queries:
            try:
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
                resp = requests.get(search_url, headers=cls.HEADERS, timeout=7)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for result in soup.find_all("a", class_="result__snippet")[:6]:
                        txt = result.get_text(strip=True)
                        if len(txt) > 40 and txt not in seen:
                            seen.add(txt)
                            all_snippets.append(txt)
                time.sleep(0.3)  # Polite delay between queries
            except Exception as e:
                logger.debug(f"Web search note ({q[:30]}): {e}")

        return " | ".join(all_snippets[:15])

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Related article scraper — finds and scrapes 2 related URLs from search
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def scrape_related_articles(cls, query: str, skip_domains: List[str] = None) -> str:
        """Finds and scrapes 2 related news articles from DuckDuckGo search results."""
        skip_domains = skip_domains or ["youtube.com", "twitter.com", "facebook.com",
                                         "instagram.com", "t.co", "bit.ly"]
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}+news+report"
            resp = requests.get(search_url, headers=cls.HEADERS, timeout=7)
            if resp.status_code != 200:
                return ""

            soup = BeautifulSoup(resp.text, "html.parser")
            candidate_urls = []
            for link in soup.find_all("a", class_="result__url")[:10]:
                href = link.get("href", "").strip()
                if not href.startswith("http"):
                    href = "https://" + href
                if any(d in href for d in skip_domains):
                    continue
                if href not in candidate_urls:
                    candidate_urls.append(href)

            scraped_texts = []
            for url in candidate_urls[:2]:
                text = cls.scrape_article_body(url, max_chars=3000)
                if len(text) > 200:
                    scraped_texts.append(f"[Related Report — {url[:60]}]\n{text}")
                time.sleep(0.4)

            return "\n\n".join(scraped_texts)
        except Exception as e:
            logger.debug(f"Related article scrape note: {e}")
        return ""

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Entity Extractor — pulls real names, dates, numbers, places, orgs
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def extract_key_entities(cls, text: str) -> Dict[str, List[str]]:
        """
        Extracts structured entities from raw text using regex patterns.
        Returns: { numbers, dates, percentages, rupee_amounts, orgs, places }
        """
        entities: Dict[str, List[str]] = {
            "numbers":      [],
            "dates":        [],
            "percentages":  [],
            "rupee_amounts":[],
            "orgs":         [],
            "places":       [],
        }

        # Numbers (e.g. 14,500 or 3.2 lakh or 500 crore)
        entities["numbers"] = list(set(re.findall(
            r'\b\d[\d,]*(?:\.\d+)?\s*(?:lakh|crore|million|billion|thousand|km|kg|MW|GW)?\b',
            text
        )))[:10]

        # Dates (e.g. September 5, 2024 / 05-09-2024 / 2024)
        entities["dates"] = list(set(re.findall(
            r'\b(?:\d{1,2}\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)'
            r'(?:\s+\d{1,2})?(?:,?\s+\d{4})?\b|\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b|\b20\d{2}\b',
            text, re.I
        )))[:8]

        # Percentages
        entities["percentages"] = list(set(re.findall(r'\b\d+(?:\.\d+)?%\b', text)))[:6]

        # Rupee / Dollar amounts
        entities["rupee_amounts"] = list(set(re.findall(
            r'(?:Rs\.?|INR|₹|\$|USD)\s*\d[\d,]*(?:\.\d+)?(?:\s*(?:lakh|crore|million|billion))?',
            text, re.I
        )))[:6]

        # Organisations (Caps-starting, 2+ words: e.g. Supreme Court, Ministry of Finance)
        orgs_raw = re.findall(
            r'\b(?:Ministry|Department|Supreme Court|High Court|Reserve Bank|SEBI|CBI|ED|NHRC|'
            r'Parliament|Rajya Sabha|Lok Sabha|Cabinet|Government|Police|Army|Air Force|Navy|'
            r'ISRO|DRDO|WHO|UN|UNESCO|World Bank|IMF|NATO|G20|BJP|Congress|AAP|TMC|NDA|UPA)\b'
            r'(?:\s+of\s+[A-Z][a-z]+)?',
            text
        )
        entities["orgs"] = list(set(orgs_raw))[:8]

        # Indian places / states (common)
        place_pattern = (
            r'\b(?:Delhi|Mumbai|Kolkata|Chennai|Bangalore|Bengaluru|Hyderabad|Ahmedabad|Pune|'
            r'Jaipur|Lucknow|Patna|Bhopal|Chandigarh|Dehradun|Guwahati|Srinagar|Jammu|'
            r'Uttar Pradesh|Bihar|Maharashtra|Gujarat|Rajasthan|Punjab|Haryana|Madhya Pradesh|'
            r'West Bengal|Tamil Nadu|Kerala|Andhra Pradesh|Telangana|Karnataka|Odisha|Assam|'
            r'Jharkhand|Chhattisgarh|Uttarakhand|Himachal Pradesh|Manipur|Tripura|Meghalaya|'
            r'India|Pakistan|China|Bangladesh|Nepal|Sri Lanka|USA|Russia|Ukraine|Israel|Gaza|'
            r'Afghanistan|Iran|UK|France|Germany|Canada|Australia)\b'
        )
        entities["places"] = list(set(re.findall(place_pattern, text)))[:8]

        return entities

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Fact Density Validator — ensures script isn't generic
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def score_fact_density(cls, script_text: str) -> Tuple[float, List[str]]:
        """
        Scores a script's fact density (0.0–1.0).
        Returns (score, list_of_issues).
        A score < 0.45 means the script is too generic and should be retried.
        """
        issues = []
        score = 1.0

        words = script_text.split()
        word_count = len(words)

        # Check for specific numbers
        numbers_found = re.findall(r'\b\d[\d,]*(?:\.\d+)?\b', script_text)
        if len(numbers_found) < 3:
            issues.append("कम संख्यात्मक तथ्य (< 3 specific numbers)")
            score -= 0.20

        # Check for dates or years
        dates_found = re.findall(r'\b20\d{2}\b|\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b', script_text, re.I)
        if not dates_found:
            issues.append("कोई तारीख या वर्ष नहीं")
            score -= 0.15

        # Check script is not just generic filler
        generic_phrases = [
            "authorities have said", "officials have confirmed", "reports suggest",
            "sources indicate", "it is believed", "according to reports",
            "अधिकारियों ने कहा", "सूत्रों के अनुसार", "रिपोर्टों के अनुसार",
        ]
        generic_count = sum(1 for p in generic_phrases if p.lower() in script_text.lower())
        if generic_count > 4:
            issues.append(f"अत्यधिक generic phrases ({generic_count})")
            score -= 0.15

        # Minimum length
        if word_count < 200:
            issues.append(f"Script बहुत छोटी ({word_count} words)")
            score -= 0.20

        # Repetition check — same 5-gram appearing 3+ times
        five_grams = [" ".join(words[i:i+5]) for i in range(len(words)-4)]
        from collections import Counter
        repeated = [g for g, c in Counter(five_grams).items() if c >= 3]
        if repeated:
            issues.append(f"{len(repeated)} repeated phrases found")
            score -= 0.10

        return max(0.0, score), issues

    # ──────────────────────────────────────────────────────────────────────────
    # 7. Master Compiler — full dossier with entities
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def compile_investigative_dossier(
        cls,
        topic: str,
        direct_url: str = "",
        raw_summary: str = "",
        deep: bool = True
    ) -> Dict[str, str]:
        """
        Compiles an exhaustive multi-source research dossier.
        - deep=True: full scrape + related articles (used for full videos)
        - deep=False: primary article + wiki only (used for Shorts, faster)
        """
        logger.info(f"🔍 [Deep Research] Compiling dossier for: '{topic[:60]}'...")

        # 1. Primary article
        primary_text = cls.scrape_article_body(direct_url) if direct_url else ""
        if not primary_text and raw_summary:
            primary_text = raw_summary

        # 2. Wikipedia background
        wiki_text = cls.fetch_wikipedia_dossier(topic)

        # 3. Web search snippets
        web_snippets = cls.search_web_context(topic)

        # 4. Related article scraping (full videos only)
        related_text = ""
        if deep:
            related_text = cls.scrape_related_articles(topic)

        # 5. Entity extraction from all sources
        combined_raw = f"{primary_text} {wiki_text} {web_snippets} {related_text}"
        entities = cls.extract_key_entities(combined_raw)

        # Format entity fact-sheet for LLM injection
        entity_lines = []
        if entities["dates"]:
            entity_lines.append(f"EXTRACTED DATES: {', '.join(entities['dates'][:5])}")
        if entities["numbers"]:
            entity_lines.append(f"EXTRACTED NUMBERS: {', '.join(entities['numbers'][:6])}")
        if entities["percentages"]:
            entity_lines.append(f"EXTRACTED PERCENTAGES: {', '.join(entities['percentages'])}")
        if entities["rupee_amounts"]:
            entity_lines.append(f"EXTRACTED AMOUNTS: {', '.join(entities['rupee_amounts'])}")
        if entities["orgs"]:
            entity_lines.append(f"KEY ORGANIZATIONS: {', '.join(entities['orgs'])}")
        if entities["places"]:
            entity_lines.append(f"KEY PLACES: {', '.join(entities['places'])}")
        entity_fact_sheet = "\n".join(entity_lines)

        full_dossier = (
            f"=== PRIMARY REPORT ===\n{primary_text}\n\n"
            f"=== HISTORICAL BACKGROUND (Wikipedia) ===\n{wiki_text}\n\n"
            f"=== LATEST WEB FACTS & TIMELINE ===\n{web_snippets}\n\n"
            + (f"=== RELATED REPORTS ===\n{related_text}\n\n" if related_text else "")
            + (f"=== AUTO-EXTRACTED KEY FACTS ===\n{entity_fact_sheet}" if entity_fact_sheet else "")
        )

        logger.info(
            f"  📊 Dossier: Primary({len(primary_text)}c) Wiki({len(wiki_text)}c) "
            f"Web({len(web_snippets)}c) Related({len(related_text)}c) "
            f"Entities: {len(entities.get('numbers', []))} nums, "
            f"{len(entities.get('dates', []))} dates, {len(entities.get('orgs', []))} orgs"
        )

        return {
            "topic": topic,
            "primary_article": primary_text,
            "wikipedia_context": wiki_text,
            "web_snippets": web_snippets,
            "related_articles": related_text,
            "entity_fact_sheet": entity_fact_sheet,
            "entities": entities,
            "full_dossier": full_dossier,
        }
