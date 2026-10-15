# NewsTube

An automated content generation and multi-platform publishing platform that produces high-retention 1080p broadcast stories, vertical shorts, and custom thumbnails from real-time viral topics and breaking news wires.

## Features

- **Viral Topic Discovery Engine**: Continuously tracks YouTube Trending (India) for videos with $\ge$ 1M views and cross-references with Google Trends traffic velocity.
- **Dynamic 3D Headline Engine**: Multi-layered metallic bevel slabs with 3D text extrusion and per-slide headline transitions that refresh context on every scene.
- **AI-Powered 3D Thumbnails**: High-CTR YouTube packaging with photorealistic scene generation (Gemini Imagen, OpenAI DALL-E, Pollinations Flux.1) and bold 3D extruded typography.
- **Multi-Scene Visuals**: Resolves a minimum of 5 distinct high-resolution editorial press and event photographs per production.
- **Neural Hindi & English Narration**: Fluent journalistic scripts synthesized via Edge-TTS neural voices without robotic intros or filler labels.
- **Multi-Format Video Rendering**: 1080p landscape broadcasts (16:9) with Ken Burns motion, data callouts, and running tickers, plus vertical shorts (9:16) via hardware-optimized FFmpeg.
- **Multi-Platform Distribution**: Automated publishing pipelines for YouTube Data API v3, Telegram channels, Twitter/X, Facebook Pages, and Instagram.
- **Web Management Studio**: FastAPI dashboard with white ivory theme for manual video triggering, schedule management, and live logs.

## Architecture

```
[YouTube Trending (1M+ Views) & Google Trends]
                     │
                     ▼
          [Viral Topic Discovery]
                     │
                     ▼
  [Deep Research & Multi-Scene Press Visuals (5+ Images)]
                     │
                     ▼
    [Fluent Journalistic Narration & Neural TTS]
                     │
                     ▼
  [FFmpeg 1080p Synthesis & Dynamic 3D Headline Plates]
                     │
                     ▼
    [High-CTR 3D AI Thumbnail & Metadata Packaging]
                     │
                     ▼
        [Multi-Platform Publishing]
   (YouTube VOD / Shorts, Telegram, X, Meta)
```

## Setup

### Prerequisites

- Python 3.10+
- FFmpeg installed and configured in system `PATH`

### Installation

```bash
git clone https://github.com/your-org/AI-NewsTube.git
cd AI-NewsTube
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
CHANNEL_NAME="SRJ UNDERRATED"
GROQ_API_KEY=your_groq_api_key
DEFAULT_TTS_VOICE="hi-IN-MadhurNeural"
PORT=80
```

For YouTube video uploads, place `client_secret.json` in the root directory and run authentication:

```bash
python auth_youtube.py
```

## Usage

### Web Studio Dashboard

Run the management interface:

```bash
python app.py
```

Open `http://localhost/` in any browser.

### Autonomous Publishing Daemon

Run the continuous 24/7 autonomous publisher:

```bash
python scripts/realtime_breaking_news_autouploader.py
```

### Single Story Generation

Generate a standalone video for a specific topic:

```bash
python test_generate_one_video.py --topic "Your Topic or Headline Here"
```

## Deployment

### Linux / AWS EC2 (tmux)

```bash
# Web Dashboard
tmux new-session -d -s studio_app 'sudo PYTHONPATH=. python3 -m uvicorn app:app --host 0.0.0.0 --port 80'

# Auto-Publisher Daemon
tmux new-session -d -s autopublisher 'python3 -u scripts/realtime_breaking_news_autouploader.py >> logs/publisher.log 2>&1'
```

### Docker

```bash
docker compose up -d --build
```

## License

MIT
