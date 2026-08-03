import os
import sys
import random
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import CHANNEL_NAME, OWNER, VERSION
from agents.news_hunter import news_hunter
from agents.fact_checker import fact_checker
from agents.script_writer import script_writer
from agents.visuals_agent import visuals_agent
from agents.graphics_agent import graphics_agent
from agents.voice_agent import voice_agent
from agents.video_agent import video_agent
from agents.thumbnail_agent import thumbnail_agent
from agents.uploader_agent import uploader_agent
from agents.analytics_agent import analytics_agent
from models.news_models import GeneratedScript
from utils.logger import logger
from utils.exceptions import AINewsTubeException


def ceo_agent() -> Optional[GeneratedScript]:
    """
    CEO Agent: Orchestrates the Production AI-NewsTube Autonomous Pipeline.
    Sequence:
    News Hunter -> Fact Checker -> Script Writer -> Visuals Agent -> Graphics Agent -> Voice Agent -> Video Agent -> Thumbnail Agent -> Uploader Agent -> Analytics Agent
    """
    logger.info("=" * 50)
    logger.info("🤖 CEO AGENT (Production Orchestrator)")
    logger.info("=" * 50)

    logger.info(f"Channel : {CHANNEL_NAME}")
    logger.info(f"Owner   : {OWNER}")
    logger.info(f"Version : {VERSION}")

    try:
        # 1. News Hunter
        logger.info("\n📢 CEO: 1. Smart News Hunter, find today's top virality-ranked news!")
        news_items = news_hunter()
        if not news_items:
            logger.warning("No news items found. Pipeline stopping.")
            return None

        # 2. Fact Checker
        selected_news = None
        fact_check_verdict = None

        logger.info("\n📢 CEO: 2. Fact Checker, verify top virality-ranked topics for credibility...")
        for candidate in news_items:
            verdict = fact_checker(candidate)
            if verdict.is_credible and verdict.risk_level != "HIGH":
                selected_news = candidate
                fact_check_verdict = verdict
                break
            else:
                logger.warning(f"Skipping topic [{candidate.category}] '{candidate.title}' (Risk: {verdict.risk_level})")

        if not selected_news:
            logger.warning("No topic passed Fact Checker verification. Pipeline stopping.")
            return None

        logger.info(f"🎯 Approved Topic: [{selected_news.category}] {selected_news.title}")

        # 3. Script Writer
        logger.info("\n📢 CEO: 3. High-Retention Script Writer, generate 6-stage script...")
        script_obj = script_writer(selected_news)

        # 4. Visuals Agent
        logger.info("\n📢 CEO: 4. Visuals Agent, generate studio assets & fetch PiP news photos...")
        script_obj = visuals_agent(script_obj)

        # 5. Graphics Agent
        logger.info("\n📢 CEO: 5. Graphics Agent, generate studio background, 3D logo, & ticker...")
        script_obj = graphics_agent(script_obj)

        # 6. Voice Agent
        logger.info("\n📢 CEO: 6. Emotional Voice Agent, generate Neural Voiceover...")
        script_obj = voice_agent(script_obj)

        # 7. Video Editor Agent
        logger.info("\n📢 CEO: 7. Video Editor Agent, render 1080p MP4 broadcast video...")
        script_obj = video_agent(script_obj)

        # 8. Thumbnail & SEO Agent
        logger.info("\n📢 CEO: 8. Thumbnail Agent, generate High-CTR Thumbnail & SEO metadata...")
        script_obj = thumbnail_agent(script_obj)

        # 9. Uploader Agent
        logger.info("\n📢 CEO: 9. Uploader Agent, stage & publish video package...")
        script_obj = uploader_agent(script_obj)

        # 10. Analytics Agent
        logger.info("\n📢 CEO: 10. Analytics Agent, update performance logs & feedback loop...")
        script_obj = analytics_agent(script_obj)

        logger.info("=" * 50)
        logger.info("🎉 CEO: 100% End-to-End Multi-Agent Pipeline Completed Successfully!")
        logger.info(f"🎥 Video File     : {script_obj.video_path}")
        logger.info(f"🎙️ Audio Voice    : {script_obj.audio_path}")
        logger.info(f"🖼️ Thumbnail File : {script_obj.thumbnail_path}")
        logger.info("=" * 50)

        return script_obj

    except AINewsTubeException as e:
        logger.error(f"❌ CEO Agent pipeline encountered a known error: {e}")
        return None
    except Exception as e:
        logger.critical(f"💥 CEO Agent pipeline unexpected failure: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    ceo_agent()
