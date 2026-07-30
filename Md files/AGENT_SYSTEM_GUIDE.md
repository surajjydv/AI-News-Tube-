# 🤖 AI-NewsTube — Agent System Specification Guide

This guide provides a comprehensive specification for each of the **10 Autonomous AI Agents** that comprise the AI-NewsTube broadcasting system.

---

## 📋 Agent Roster Overview

| # | Agent Name | File Location | Primary Function |
| :-: | :--- | :--- | :--- |
| **1** | **CEO Agent** | `agents/ceo_agent.py` | Pipeline Orchestrator & Lifecycle Supervisor |
| **2** | **News Hunter** | `agents/news_hunter.py` | RSS Feed Aggregator & Virality Ranker |
| **3** | **Fact Checker** | `agents/fact_checker.py` | Credibility Auditor & Risk Evaluator |
| **4** | **Script Writer** | `agents/script_writer.py` | 6-Stage Broadcast Script Generator |
| **5** | **Visuals Agent** | `agents/visuals_agent.py` | Multi-Tier HD Media Procurement |
| **6** | **Graphics Agent** | `agents/graphics_agent.py` | 2.5D Studio Background & Ticker Engine |
| **7** | **Voice Agent** | `agents/voice_agent.py` | Expressive Neural TTS Audio Engine |
| **8** | **Video Agent** | `agents/video_agent.py` | 1080p MP4 Video Compositor & Lip-Sync Engine |
| **9** | **Thumbnail & SEO Agent** | `agents/thumbnail_agent.py` | High-CTR Thumbnail & YouTube Metadata Package |
| **10**| **Uploader Agent** | `agents/uploader_agent.py` | Package Staging & Distribution Supervisor |
| **11**| **Analytics Agent** | `agents/analytics_agent.py` | Telemetry Logger & Feedback Loop Engine |

---

## 🔍 Detailed Agent Specifications

### 1. 🤖 CEO Agent (`agents/ceo_agent.py`)
* **Role**: Chief Executive Officer & Pipeline Supervisor.
* **Input**: User trigger / System schedule.
* **Processing**:
  * Manages linear execution from Ingestion to Analytics.
  * Captures `AINewsTubeException` errors and ensures graceful degradation.
  * Logs pipeline progression with high-visibility colorized console outputs.
* **Output**: Final `GeneratedScript` containing paths to output video, thumbnail, audio, and SEO tags.

---

### 2. 📢 News Hunter Agent (`agents/news_hunter.py`)
* **Role**: Current Affairs Discovery & Trend Evaluation.
* **Input**: RSS Feeds across 9 categories (Top Stories, India, World, Business, Tech, Entertainment, Sports, Science, Health).
* **Processing**:
  * Parses Google News RSS feeds using `feedparser`.
  * Computes a **Virality Score** (0–100) based on keyword density (`breaking`, `ai`, `isro`, `crisis`, `ban`, etc.).
  * Deduplicates stories using Jaccard word-similarity threshold ($> 0.45$).
* **Output**: Sorted `List[NewsArticle]` ranked by virality.

---

### 3. 🛡️ Fact Checker Agent (`agents/fact_checker.py`)
* **Role**: Story Verification & Risk Evaluation.
* **Input**: `NewsArticle` item.
* **Processing**:
  * Invokes Groq LLaMA 3.3 70B to evaluate story plausibility and cross-reference context.
  * Assigns a **Risk Level** (`LOW`, `MEDIUM`, `HIGH`).
  * Rejects clickbait, unverified rumors, and high-risk misinformation.
* **Output**: `FactCheckResult` dataclass.

---

### 4. ✍️ Script Writer Agent (`agents/script_writer.py`)
* **Role**: Broadcast Script Generation.
* **Input**: Verified `NewsArticle`.
* **Processing**:
  * Prompts LLaMA 3.3 70B to write a **6-Stage Retention Script**:
    1. **Hook**: Punchy attention-grabbing opening line.
    2. **Intro**: Channel intro & news anchor greeting.
    3. **Context**: Background overview of the breaking news.
    4. **Deep Dive**: In-depth analysis and facts.
    5. **Climax**: Key takeaway or major implication.
    6. **Outro/CTA**: Call-to-action (Like, Subscribe, Comment).
* **Output**: `GeneratedScript` object populated with structured news text.

---

### 5. 🖼️ Visuals Agent (`agents/visuals_agent.py`)
* **Role**: Visual Procurement & Asset Curation.
* **Input**: `GeneratedScript` news headline & keywords.
* **Processing**:
  * Executes a 5-tier search sequence:
    1. NASA API (for space/astronomy topics).
    2. Wikimedia Commons API (for real news & public domain images).
    3. Pexels API (for HD stock imagery).
    4. Pixabay API (secondary stock fallback).
    5. Unsplash API (tertiary stock fallback).
  * If no photo is found, generates a **Visual Content Card** graphic.
* **Output**: `List[MediaAsset]` attached to script object.

---

### 6. 🎨 Graphics Agent (`agents/graphics_agent.py`)
* **Role**: Broadcast Graphics & Studio Rendering.
* **Input**: `GeneratedScript` and `graphics_config.json`.
* **Processing**:
  * Generates 2.5D virtual studio backdrop (`studio_background.png`).
  * Creates 3D extruded glass panels, floor reflections, and light sweeps.
  * Fetches real-time ticker news headlines for the lower-thirds ticker banner.
  * Renders 3D channel logo overlay (`channel_logo_3d.png`).
* **Output**: Generated graphic assets in `assets/studio/`.

---

### 7. 🎙️ Voice Agent (`agents/voice_agent.py`)
* **Role**: Neural Audio Synthesis.
* **Input**: Script text from `GeneratedScript`.
* **Processing**:
  * Synthesizes audio using `edge-tts` with voice `hi-IN-SwaraNeural` (Hindi/English).
  * Applies `+5%` rate boost for broadcast energy.
  * Fallbacks to Groq CanopyLabs Orpheus TTS or `gTTS` if Edge-TTS is offline.
* **Output**: Saved MP3 audio file path in `voice/`.

---

### 8. 🎬 Video Agent (`agents/video_agent.py`)
* **Role**: 1080p MP4 Video Compositor.
* **Input**: Script text, audio file, media assets, studio background, and font assets.
* **Processing**:
  * Computes real-time audio RMS levels for anchor lip-sync animation.
  * Renders lower-thirds ticker, audio visualizer waveform, and channel branding watermark.
  * Overlay kinetic Hindi/Devanagari subtitles (`NotoSansDevanagari`).
  * Composites final timeline using `MoviePy` and encodes via `FFmpeg` (`libx264`).
* **Output**: Rendered 1080p broadcast MP4 in `videos/`.

---

### 9. 🖼️ Thumbnail & SEO Agent (`agents/thumbnail_agent.py`)
* **Role**: Packaging & Click-Through Optimization.
* **Input**: `GeneratedScript` & topic context.
* **Processing**:
  * Composes a 1080p thumbnail with high-contrast text, split-screen news image, and emergency breaking badge.
  * Generates high-CTR YouTube title, description, and hashtag keywords via LLaMA 3.3 70B.
* **Output**: Saved thumbnail PNG in `thumbnails/` and metadata dict.

---

### 10. 📦 Uploader Agent (`agents/uploader_agent.py`)
* **Role**: Staging & Distribution.
* **Input**: Complete video package.
* **Processing**: Verifies file integrity of MP4, MP3, PNG, and JSON metadata before publishing staging.

---

### 11. 📊 Analytics Agent (`agents/analytics_agent.py`)
* **Role**: Telemetry & Feedback Loop.
* **Input**: Video metadata & execution timestamp.
* **Processing**: Appends performance analytics, processing duration, and topic category metrics to `data/analytics_log.json`.
