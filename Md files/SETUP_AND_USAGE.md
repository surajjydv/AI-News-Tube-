# ⚙️ AI-NewsTube — Setup, Configuration & Operator Manual

This guide provides step-by-step instructions for installing, configuring, operating, and troubleshooting **AI-NewsTube**.

---

## 💻 System Requirements

### Hardware Requirements
* **CPU**: Quad-core Intel Core i5 / AMD Ryzen 5 or better.
* **RAM**: Minimum 8 GB (16 GB recommended for smooth video rendering).
* **Storage**: 2 GB free disk space.
* **GPU**: Optional (WebGL hardware acceleration speeds up frame rendering).

### Software Requirements
* **Operating System**: Windows 10/11, macOS, or Linux (Ubuntu 20.04+).
* **Python**: Version **3.10** or higher.
* **FFmpeg**: Required for MoviePy audio/video encoding.

---

## 🛠️ Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/AI-NewsTube.git
cd AI-NewsTube
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Python Packages
```bash
pip install -r requirements.txt
```

### 4. Install FFmpeg
* **Windows**: Download from [FFmpeg official website](https://ffmpeg.org/download.html) or run:
  ```powershell
  winget install FFmpeg
  ```
* **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```
* **macOS**:
  ```bash
  brew install ffmpeg
  ```

---

## 🔑 Environment Variables Setup (`.env`)

Create a `.env` file in the root `AI-NewsTube` directory:

```env
# Required Key for Script Writing & Fact Checking (FREE)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Optional Media API Keys for HD Stock Visuals
PEXELS_API_KEY=your_pexels_api_key_here
PIXABAY_API_KEY=your_pixabay_api_key_here
UNSPLASH_API_KEY=your_unsplash_api_key_here

# Channel & System Settings
CHANNEL_NAME=AI-NewsTube
OWNER=Suraj
DEFAULT_TTS_VOICE=hi-IN-SwaraNeural
GROQ_MODEL=llama-3.3-70b-versatile
```

### How to Get a Free Groq API Key:
1. Go to [https://console.groq.com/keys](https://console.groq.com/keys).
2. Sign up or log in.
3. Click **Create API Key**.
4. Paste the key into your `.env` file (`GROQ_API_KEY=gsk_...`).

---

## 🎨 Graphics Customization (`config/graphics_config.json`)

You can customize the visual style of your newsroom without changing code by editing `config/graphics_config.json`:

```json
{
  "theme": "premium_news",
  "headline_style": "breaking_news",
  "camera_motion": "push_in",
  "lighting": "studio_volumetric",
  "parallax_intensity": 1.0,
  "glass_opacity": 220,
  "enable_perspective_warp": true,
  "enable_light_sweeps": true,
  "enable_particles": true
}
```

---

## 🚀 Running the Pipeline

To execute a complete autonomous video production run:

```bash
python main.py
```

### What Happens When You Run `main.py`:
1. **News Hunter** fetches today's breaking stories and selects the top viral topic.
2. **Fact Checker** verifies story credibility via Groq LLM.
3. **Script Writer** generates a 6-stage news broadcast script.
4. **Visuals Agent** fetches HD news photography.
5. **Graphics Agent** generates 3D/2.5D studio graphics and ticker banner.
6. **Voice Agent** generates neural voiceover audio (`voice/voice_xxx.mp3`).
7. **Video Agent** composites 1080p MP4 broadcast video (`videos/video_xxx.mp4`).
8. **Thumbnail Agent** creates a 1080p thumbnail (`thumbnails/thumbnail_xxx.png`).
9. **Analytics Agent** logs telemetry output.

---

## ❓ Frequently Asked Questions & Troubleshooting

### Q1: `APIKeyError: GROQ_API_KEY not found`
* **Fix**: Ensure `.env` exists in the root folder and contains `GROQ_API_KEY=gsk_...`. Avoid putting quotes around your API key.

### Q2: Subtitles display as square boxes (`□□□□`)
* **Fix**: This happens when Windows Devanagari fonts are missing. Install the free **Noto Sans Devanagari** font into `assets/fonts/NotoSansDevanagari-Bold.ttf`.

### Q3: `MoviePy / FFmpeg not found`
* **Fix**: Ensure FFmpeg is installed on your operating system and added to your system PATH environment variable.

### Q4: How do I change the TTS Voice to English?
* **Fix**: Change `DEFAULT_TTS_VOICE` in `.env` to an English voice such as `en-US-AriaNeural` or `en-US-GuyNeural`.
