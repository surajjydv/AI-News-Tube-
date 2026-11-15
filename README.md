# NewsTube & OmniBlast Studio

A production-grade content distribution suite and autonomous AI video generation pipeline. Post existing media everywhere in 1-click or generate high-impact broadcast videos directly from words and auto-publish across YouTube, Telegram, Twitter/X, Instagram, and Facebook.

## Features

- **1-Click Multi-Platform Media Blast**: Upload any video or image, enter title and description, and broadcast simultaneously across YouTube, Telegram, Twitter/X, Instagram, and Facebook.
- **AI Word-to-Video & Auto-Blast**: Input a topic headline or prompt to automatically trigger research, scriptwriting, neural voice synthesis, 1080p video rendering, and multi-channel publication.
- **Dynamic On-Screen Broadcast Engine**: Generates 1080p full-HD landscape (16:9) broadcasts and vertical shorts (9:16) with tickers, chapter cards, and real event photography.
- **High-CTR Thumbnail Synthesis**: Programmatic thumbnail generation featuring 3D typography and authentic event visuals.
- **Neural Voice Narration**: Multi-speaker neural voiceover in Hindi and English powered by Edge-TTS.
- **Multi-Platform Dispatcher**: Unified orchestrator connecting YouTube Data API v3, Telegram Bot API, Twitter v2 API, and Meta Graph API.
- **OmniBlast Web Studio**: Integrated single-page dashboard served directly via FastAPI (`http://localhost:8000/`) with real-time audit logs and platform status indicators.

## Architecture

```
[User Media Upload / Words Prompt]
                 │
                 ├──▶ [1-Click Multi-Platform Dispatcher]
                 │           │
                 │           ├──▶ YouTube Data API v3
                 │           ├──▶ Telegram Bot API
                 │           ├──▶ Twitter / X API v2
                 │           ├──▶ Instagram Graph API
                 │           └──▶ Facebook Page API
                 │
                 └──▶ [Autonomous AI Video Pipeline]
                             │
                             ▼
                    [Fact Research & Ingestion]
                             │
                             ▼
                    [Script & Voice Synthesis]
                             │
                             ▼
                    [FFmpeg 1080p Video Rendering]
                             │
                             ▼
                    [Auto-Publish Everywhere]
```

## Setup

### Prerequisites

- Python 3.10+
- FFmpeg installed and configured in system `PATH`
- Google Chrome or modern web browser

### Installation

```bash
git clone https://github.com/your-org/AI-NewsTube.git
cd AI-NewsTube

# Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
CHANNEL_NAME="Your Channel"
GROQ_API_KEY="your_groq_api_key"
DEFAULT_TTS_VOICE="hi-IN-MadhurNeural"
PORT=8000
YOUTUBE_STREAM_KEY="your_youtube_rtmp_key"
```

For YouTube uploads, place your OAuth client secret file at `client_secret.json` and generate credentials via:

```bash
python auth/auth_youtube.py
```

## Usage

### 1. Launch OmniBlast Studio (Web UI & Next.js App)

Start the unified FastAPI application:

```bash
uvicorn app:app --reload --port 8000
```

Start the Next.js Frontend Studio:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000/` (Next.js Studio) or `http://localhost:8000/` (FastAPI Web UI).

- **API Keys & Platforms**: Open the **API Keys & Platforms** tab to save your Instagram, YouTube, Groq, Telegram, Twitter, and Facebook credentials in 1 click.
- **1-Click Media Blast**: Drag and drop any video or image, enter your headline and caption, select target channels, and click **Blast Everywhere**.
- **AI Word-to-Video**: Enter a topic or prompt, select format (16:9 or 9:16), choose narrator voice, and click **Generate Video & Auto-Blast**.


### 2. Command-Line Execution

Generate a video for an automated top story:

```bash
python main.py
```

Generate for a custom topic:

```bash
python main.py --topic "Union Budget 2026 Key Highlights"
```

### 3. Background Autopublishers

```bash
# 24/7 continuous news video autopublisher
python scripts/run_realtime_news_autopublisher.py

# 24/7 RTMP live stream to YouTube
python scripts/continuous_live_stream.py
```

## Deployment

### Linux / Production Server

```bash
# Run FastAPI server
python -m uvicorn app:app --host 0.0.0.0 --port 8000

# Run daemon with background output logging
nohup python -u scripts/run_realtime_news_autopublisher.py > logs/publisher.log 2>&1 &
```

### Docker

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

## License

MIT
