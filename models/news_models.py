from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class NewsArticle:
    """Dataclass representing a fetched news article."""
    title: str
    link: str
    summary: str
    category: str
    published_at: Optional[str] = None
    scraped_content: Optional[str] = None
    trending_score: float = 0.0
    is_breaking: bool = False
    unique_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "link": self.link,
            "summary": self.summary,
            "category": self.category,
            "published_at": self.published_at,
            "scraped_content": self.scraped_content,
            "trending_score": self.trending_score,
            "is_breaking": self.is_breaking,
            "unique_hash": self.unique_hash,
        }


@dataclass
class FactCheckResult:
    """Dataclass representing fact-checking verification result."""
    is_credible: bool
    confidence_score: float  # 0.0 to 1.0
    verified_facts: List[str]
    reasoning: str
    risk_level: str  # "LOW", "MEDIUM", "HIGH"

    def to_dict(self) -> dict:
        return {
            "is_credible": self.is_credible,
            "confidence_score": self.confidence_score,
            "verified_facts": self.verified_facts,
            "reasoning": self.reasoning,
            "risk_level": self.risk_level,
        }


@dataclass
class MediaAsset:
    """Dataclass representing a researched news media asset with source attribution."""
    media_type: str  # "real_video", "real_image", "stock_footage", "ai_generated"
    file_path: str
    source_name: str  # "NASA", "Reuters", "AP", "Wikimedia", "Pexels", "AI Generated"
    source_url: str = ""
    on_screen_credit: str = ""  # e.g., "Image: NASA", "Source: Reuters"

    def to_dict(self) -> dict:
        return {
            "media_type": self.media_type,
            "file_path": self.file_path,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "on_screen_credit": self.on_screen_credit,
        }


@dataclass
class GeneratedScript:
    """Dataclass representing a generated script and its media assets."""
    topic_title: str
    category: str
    script_text: str
    word_count: int
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    audio_path: Optional[str] = None
    image_paths: List[str] = field(default_factory=list)
    media_assets: List[MediaAsset] = field(default_factory=list)
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    ticker_headlines: List[str] = field(default_factory=list)
    talking_anchor_path: Optional[str] = None
    glb_avatar_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "topic_title": self.topic_title,
            "category": self.category,
            "script_text": self.script_text,
            "word_count": self.word_count,
            "created_at": self.created_at,
            "audio_path": self.audio_path,
            "image_paths": self.image_paths,
            "media_assets": [m.to_dict() for m in self.media_assets],
            "video_path": self.video_path,
            "thumbnail_path": self.thumbnail_path,
            "ticker_headlines": self.ticker_headlines,
            "talking_anchor_path": self.talking_anchor_path,
            "glb_avatar_path": self.glb_avatar_path,
        }

