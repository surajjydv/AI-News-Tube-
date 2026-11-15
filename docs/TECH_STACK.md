# 🚀 AI-NewsTube — Complete Tech Stack & System Architecture

Welcome to the official tech stack documentation of **AI-NewsTube** — an autonomous, end-to-end multi-agent AI video production engine and automated news broadcasting pipeline.

---

## 🛠️ Overview of Core Tech Stack

| Category | Primary Technologies / Tools |
| :--- | :--- |
| **Core Language & Runtime** | Python 3.10+, HTML5, JavaScript (ES6+), WebGL |
| **Multi-Agent Orchestration** | 10 Custom Autonomous Agents (CEO, News Hunter, Fact Checker, Script Writer, Visuals, Graphics, Voice, Video, Thumbnail, Uploader, Analytics) |
| **AI / LLM Model** | Groq API (`llama-3.3-70b-versatile`) |
| **Audio & Neural TTS** | Edge-TTS (`hi-IN-SwaraNeural`), Groq CanopyLabs Orpheus TTS, gTTS (Fallback) |
| **3D & Studio Graphics** | Three.js, WebGL, Playwright (Headless Frame Capture), PIL 2.5D Spatial Engine |
| **Video Compositing & Processing** | MoviePy 2.x, FFmpeg, OpenCV (`cv2`), NumPy, PIL (Pillow) |
| **News Ingestion & Scraping** | Feedparser (Google News RSS Ingestion), Trafilatura (Full-text Scraping) |
| **Visual Asset Procurement** | Wikimedia Commons API, NASA API, Pexels API, Pixabay API, Unsplash API |
| **Configuration & State** | Python Dataclasses (`news_models.py`), `python-dotenv`, `graphics_config.json` |

---

## 🤖 1. Multi-Agent Architecture (10 Autonomous Agents)

The system operates via a sequential multi-agent pipeline orchestrated by the **CEO Agent**:

```
[News Hunter] ➔ [Fact Checker] ➔ [Script Writer] ➔ [Visuals Agent] ➔ [Graphics Agent]
                                                                          │
[Analytics Agent] ⬅ [Uploader Agent] ⬅ [Thumbnail Agent] ⬅ [Video Agent] ⬅ [Voice Agent]
```

1. **CEO Agent (`agents/ceo_agent.py`)**: System orchestrator managing the pipeline lifecycle, agent handoffs, error recovery, and status tracking.
2. **News Hunter Agent (`agents/news_hunter.py`)**: Real-time news discovery engine aggregating Google News RSS across 9 categories with virality ranking algorithms.
3. **Fact Checker Agent (`agents/fact_checker.py`)**: Credibility analysis engine using LLM verification to calculate risk levels (`LOW`, `MEDIUM`, `HIGH`).
4. **Script Writer Agent (`agents/script_writer.py`)**: Generates 6-stage high-retention news scripts (Hook, Intro, Context, Deep-Dive, Climax, Outro/CTA).
5. **Visuals Agent (`agents/visuals_agent.py`)**: Multi-tier media research procuring real HD news photography and PiP visual content cards.
6. **Graphics Agent (`agents/graphics_agent.py`)**: Renders 2.5D virtual studio backdrops, 3D extruded glass slabs, dynamic lower-thirds ticker banners, and channel logos.
7. **Voice Agent (`agents/voice_agent.py`)**: Neural Text-To-Speech (TTS) voiceover generator using Microsoft Edge Neural TTS with fallback to gTTS/Orpheus.
8. **Video Agent (`agents/video_agent.py`)**: Composes 1080p MP4 broadcast videos with real-time lip-sync, Hindi/Devanagari kinetic captions, RMS audio visualizers, and studio backgrounds.
9. **Thumbnail & SEO Agent (`agents/thumbnail_agent.py`)**: Composes click-through optimized 1080p thumbnails and generates YouTube SEO titles, descriptions, and tags.
10. **Uploader Agent (`agents/uploader_agent.py`)**: Automated staging and video publishing package preparation.
11. **Analytics Agent (`agents/analytics_agent.py`)**: Performance logging and telemetry feedback loop.

---

## 🧠 2. Artificial Intelligence & LLM Services

* **Groq API Gateway (`services/groq_service.py`)**: Ultra-fast LLM inference client.
* **LLaMA 3.3 70B (`llama-3.3-70b-versatile`)**:
  * 6-stage broadcast script writing.
  * Fact-checking reasoning & source credibility assessment.
  * SEO headline, viral tags, and description generation.
* **Groq CanopyLabs Orpheus TTS (`canopylabs/orpheus-v1-english`)**: Expressive voice model supporting emotional direction tags (`[urgent]`, `[dramatic]`, `[cheerful]`).

---

## 🎙️ 3. Neural Voice & Audio Engineering

* **Edge-TTS (`edge-tts`)**: Primary neural text-to-speech engine using Microsoft Swara (`hi-IN-SwaraNeural`) for realistic Hindi news anchoring.
* **gTTS (`gtts`)**: Reliable fallback voice generator.
* **RMS Audio Signal Processing (`agents/video_agent.py`)**: Calculates real-time Root Mean Square (RMS) volume levels from audio streams to drive mouth lip-sync and audio visualizer waveforms.

---

## 🎨 4. 3D Studio & 2.5D Spatial Graphics Engine

* **Three.js WebGL 3D Studio Engine (`services/threejs_studio.html` & `services/threejs_render_service.py`)**:
  * WebGL 3D Virtual Newsroom featuring a curved LED video wall, metallic news desk, specular lighting, spotlights, and camera orbits.
* **Headless Playwright (`playwright`)**: Captures 1080p WebGL frames directly from headless Chromium for video rendering.
* **2.5D Spatial Visual Effects (`agents/graphics_agent.py`)**:
  * Homography quad perspective transformation (OpenCV / PIL).
  * 3D glass slab extrusion with depth shadow blur and edge highlights.
  * Studio desk floor reflections with exponential opacity decay.
  * Volumetric light sweeps and particle effects.
* **Avatar Engine (`services/avatar_provider.py` & `services/avatar_asset_downloader.py`)**:
  * Validates and manages rigged 3D anchor presenter models (`.glb`/`.fbx`) with PBR business suit materials.

---

## 🎬 5. Video Compositing & Processing Engine

* **MoviePy 2.x (`moviepy`)**: Core video timeline composer, audio-video synchronization, clip concatenation, and MP4 exporting.
* **FFmpeg**: Video encoding engine generating 1080p MP4 broadcasts with H.264 (`libx264`) video codec.
* **OpenCV (`cv2`) & NumPy**: Spatial matrices, perspective transformations, array math, and frame manipulation.
* **Pillow (`PIL`)**: Lower-third ticker banners, Devanagari Hindi font rendering (`NotoSansDevanagari`, `Mangal`, `Nirmala UI`), mouth shape overlay lip-sync, and visual content cards.

---

## 📰 6. News Discovery & Scraping

* **Feedparser (`feedparser`)**: Aggregates real-time news across 9 Google News RSS categories (Top Stories, India, World, Business, Tech, Entertainment, Sports, Science, Health).
* **Trafilatura (`trafilatura`)**: Web scraping engine for full-text article extraction used in RAG script context.

---

## 🖼️ 7. Multi-Tier Visual Asset Research API

1. **Wikimedia Commons API**: Historical events and public domain news imagery.
2. **NASA API**: Official space and astronomy mission photography.
3. **Pexels API**: High-definition HD stock photos and media.
4. **Pixabay API**: High-quality visual fallbacks.
5. **Unsplash API**: Supplementary HD photography.
* **Visual Content Card Generator**: Automatic fallback card generator rendering category-styled graphic cards if no suitable photo is available.

---

## 📂 8. Project Directory Structure

```
AI-NewsTube/
├── agents/                  # 10 Autonomous Pipeline Agents
│   ├── ceo_agent.py         # Main orchestrator
│   ├── news_hunter.py       # RSS News discovery & ranking
│   ├── fact_checker.py      # LLM Fact verification
│   ├── script_writer.py     # 6-Stage news script writer
│   ├── visuals_agent.py     # Multi-tier visual procurement
│   ├── graphics_agent.py    # 2.5D graphics & studio engine
│   ├── voice_agent.py       # Neural TTS voiceover generator
│   ├── video_agent.py       # 1080p MP4 broadcast compositor
│   ├── thumbnail_agent.py   # High-CTR thumbnail & SEO agent
│   ├── uploader_agent.py    # Staging & distribution agent
│   └── analytics_agent.py   # Feedback loop & telemetry agent
├── assets/                  # Fonts, avatars, studio backdrops, frames
├── config/                  # Settings (settings.py) & Graphics config (graphics_config.json)
├── data/                    # Telemetry & news data logs
├── logs/                    # System runtime logs
├── models/                  # Dataclass schemas (news_models.py)
├── services/                # Core services (Groq, Three.js, RSS, Visual Research)
├── thumbnails/              # Rendered YouTube thumbnails
├── utils/                   # Logger (logger.py) & Exceptions (exceptions.py)
├── videos/                  # Output 1080p MP4 videos
├── voice/                   # Generated neural MP3 voiceover files
├── main.py                  # CLI Pipeline entry point
├── requirements.txt         # Python dependencies
└── TECH_STACK.md            # Tech Stack Documentation
```

---

## 📦 9. Python Dependencies (`requirements.txt`)

```txt
feedparser         # Google News RSS ingestion
groq               # Groq LLM API client
python-dotenv      # Environment variable management
trafilatura        # Web article content extraction
edge-tts           # Microsoft Edge Neural Speech TTS
pillow             # Image processing & 2.5D graphics
requests           # HTTP client for APIs
moviepy            # Video compositing & rendering
numpy              # Matrix math & RMS audio calculations
```

---

## 🚀 How to Run the Pipeline

```bash
# 1. Install required Python packages
pip install -r requirements.txt

# 2. Add your Groq API key in .env
GROQ_API_KEY=gsk_your_groq_api_key_here

# 3. Launch the complete autonomous AI news pipeline
python main.py
```
