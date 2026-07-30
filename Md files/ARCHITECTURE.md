# 🏗️ AI-NewsTube — Technical System Architecture & Engineering Specifications

This document provides a technical deep-dive into the system design, software architecture, data models, rendering pipeline, audio-video synchronization algorithms, and fallback mechanisms of **AI-NewsTube**.

---

## 🏛️ System Architecture Overview

AI-NewsTube follows a **Decoupled Multi-Agent Architecture** orchestrated sequentially by the `CEOAgent`. Each agent is an isolated module responsible for a single domain (Ingestion, Verification, Scriptwriting, Media Research, Graphics Rendering, Voice Generation, Video Compositing, Packaging).

```
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                         CEO AGENT ORCHESTRATOR                              │
 └──────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────┘
        │          │          │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼          ▼          ▼
   [News Hunter] [Fact Check] [Script]  [Visuals]  [Graphics] [Voice]   [Video]
        │          │          │          │          │          │          │
        └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
                                      │
                                      ▼
                             [GeneratedScript Data]
                                      │
                                      ▼
                           [Thumbnail & SEO Agent]
                                      │
                                      ▼
                             [Uploader Agent]
                                      │
                                      ▼
                            [Analytics Telemetry]
```

---

## 📄 Core Data Schemas (`models/news_models.py`)

The pipeline relies on strictly typed Python Dataclasses to pass state between agents:

### 1. `NewsArticle`
```python
@dataclass
class NewsArticle:
    title: str
    link: str
    summary: str
    category: str
    published_at: Optional[str] = None
    scraped_content: Optional[str] = None
    trending_score: float = 0.0
    is_breaking: bool = False
    unique_hash: str = ""
```

### 2. `FactCheckResult`
```python
@dataclass
class FactCheckResult:
    is_credible: bool
    confidence_score: float  # 0.0 to 1.0
    verified_facts: List[str]
    reasoning: str
    risk_level: str          # "LOW", "MEDIUM", "HIGH"
```

### 3. `MediaAsset`
```python
@dataclass
class MediaAsset:
    media_type: str          # "real_image", "stock_footage", "ai_generated"
    file_path: str
    source_name: str         # "Wikimedia", "NASA", "Pexels", "Pixabay"
    source_url: str = ""
    on_screen_credit: str = ""
```

### 4. `GeneratedScript` (Central Pipeline Payload)
```python
@dataclass
class GeneratedScript:
    topic_title: str
    category: str
    script_text: str
    word_count: int
    created_at: str
    audio_path: Optional[str] = None
    image_paths: List[str] = field(default_factory=list)
    media_assets: List[MediaAsset] = field(default_factory=list)
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    ticker_headlines: List[str] = field(default_factory=list)
    talking_anchor_path: Optional[str] = None
    glb_avatar_path: Optional[str] = None
```

---

## 🎨 Dual-Engine Graphics & Rendering Pipeline

AI-NewsTube employs a hybrid graphics architecture combining 3D WebGL rendering with 2.5D spatial Pillow quads:

```
                          ┌───────────────────────────┐
                          │   GRAPHICS PIPELINE      │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┴────────────────────────────┐
           ▼                                                         ▼
┌─────────────────────────────┐                           ┌───────────────────────────┐
│  3D WebGL Engine (Three.js) │                           │  2.5D Spatial PIL Engine │
├─────────────────────────────┤                           ├───────────────────────────┤
│ - Curved LED Wall Mesh      │                           │ - Perspective Warp Quads  │
│ - Specular News Desk        │                           │ - Glass Slab Extrusion    │
│ - Spotlights & Camera Orbit │                           │ - Floor Reflections       │
│ - Headless Chromium Frame   │                           │ - Lower-Third Ticker      │
│   Capture via Playwright    │                           │ - Devanagari Kinetic Font │
└─────────────────────────────┘                           └───────────────────────────┘
```

### 1. 3D WebGL Studio Engine (`services/threejs_render_service.py`)
* Renders a 3D newsroom environment using **Three.js** inside `services/threejs_studio.html`.
* Captures high-definition 1080p WebGL PNG frames using headless **Playwright Chromium**.
* Encodes frame sequence directly into 1080p broadcast MP4 using `MoviePy` / `FFmpeg`.

### 2. 2.5D PIL Spatial Effects (`agents/graphics_agent.py`)
* **Perspective Warping**: Uses OpenCV `cv2.getPerspectiveTransform` and `cv2.warpPerspective` (with PIL Quad fallback) to project media into 3D camera angles.
* **Extruded Glass Panels**: Renders semi-transparent news cards with depth shadows, specular highlights, and gold borders.
* **Floor Reflections**: Calculates inverted region crops with exponential opacity decay alpha masks ($y^{1.8}$).

---

## 🎙️ Audio Signal Processing & Lip-Sync Mechanics

### Audio RMS Volume Extraction (`agents/video_agent.py`)
To animate the anchor presenter's mouth without complex face-mesh models, the system extracts real-time Root Mean Square (RMS) volume from the audio track:

$$\text{RMS}(t) = \sqrt{\frac{1}{N} \sum_{i=1}^{N} x_i^2}$$

* **Speech Opacity Threshold**: If $\text{RMS}(t) > 0.015$, speech activity is detected.
* **Mouth Opening Ratio**: 
  $$\text{speech\_level} = \text{clamp}\left( \frac{\text{RMS}(t) - 0.015}{0.12}, 0.0, 1.0 \right)$$
* **Dynamic Canvas Rendering**: Overlays an open mouth ellipse/texture on the anchor model scaled to `speech_level` on every frame $t$.

---

## 🛡️ Robustness & Fallback Chain

AI-NewsTube is engineered to operate without crashing even if external APIs or tools fail:

| Module | Primary Engine | Fallback 1 | Fallback 2 |
| :--- | :--- | :--- | :--- |
| **TTS Voice** | Edge-TTS (`hi-IN-SwaraNeural`) | Groq Orpheus TTS | gTTS (Google TTS) |
| **Visual Search** | Wikimedia Commons API | Pexels / NASA / Pixabay | Visual Content Card Generator |
| **3D Rendering** | WebGL / Playwright | PIL 3D Specular Generator | Static Studio PNG |
| **Perspective Warp** | OpenCV (`cv2.warpPerspective`) | PIL Quad Transform | Un-warped panel overlay |
| **Devanagari Font** | `NotoSansDevanagari-Bold.ttf` | Windows Mangal / Nirmala UI | System default font |
