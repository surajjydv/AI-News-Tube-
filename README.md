# NewsTube & OmniBlast Studio

A media production and distribution engine designed for automated content generation and multi-platform publishing. Generate broadcast-grade videos, vertical shorts, and real-time live streams with neural voice synthesis and direct delivery across YouTube, Telegram, Twitter/X, Instagram, and Facebook.

## Features

- **24/7 YouTube Live Streaming**: Continuous RTMP streaming engine with dynamic playlist rotation, loop failover, and zero dead air.
- **1-Click Multi-Platform Dispatch**: Publish videos and images simultaneously across YouTube, Telegram, Twitter/X, Instagram, and Meta platforms.
- **Topic-to-Video Engine**: Automatically generates 1080p landscape (16:9) broadcasts and vertical shorts (9:16) with tickers, badges, and verified editorial photography.
- **Studio Dashboard**: Web-based control center for API keys, manual video rendering, live stream monitoring, and channel analytics.
- **Neural Voice Narration**: Multi-lingual text-to-speech with natural pacing and broadcast audio mastering.
- **High-CTR Thumbnail Generation**: Automated graphic composition with bold typography and editorial imagery.

## Architecture

```
[Web Dashboard / REST API]
            │
            ├──▶ [Live Stream Manager] ──▶ 24/7 RTMP Engine ──▶ YouTube Live
            │
            ├──▶ [Multi-Platform Dispatcher]
            │           ├──▶ YouTube Data API v3
            │           ├──▶ Telegram Bot API
            │           ├──▶ Twitter / X API v2
            │           └──▶ Meta Graph API (Instagram / Facebook)
            │
            └──▶ [Video Production Engine]
                        ├──▶ Story Research & Summarization
                        ├──▶ Neural Voice Synthesis (Edge-TTS)
                        ├──▶ Editorial Visual Asset Sourcing
                        └──▶ FFmpeg 1080p Broadcast Compositor
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ & npm
- FFmpeg installed and available in system `PATH`

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/AI-NewsTube.git
cd AI-NewsTube

# Setup Python environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Setup Frontend
cd frontend
npm install
cd ..
```

### Configuration

Create a `.env` file in the root directory:

```env
CHANNEL_NAME="Your Channel Name"
YOUTUBE_CHANNEL_ID="your_channel_id"
YOUTUBE_STREAM_KEY="your_rtmp_stream_key"
GROQ_API_KEY="your_groq_api_key"
DEFAULT_TTS_VOICE="hi-IN-MadhurNeural"
PORT=8000
```

For YouTube OAuth direct publishing, save `client_secret.json` in the root folder and run:

```bash
python auth/auth_youtube.py
```

## Usage

### 1. Run the Studio Dashboard

Start the FastAPI backend:

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Start the Next.js frontend:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000` to manage broadcasts, trigger 24/7 live streaming, or render custom topics on demand.

### 2. Live Streaming via CLI

Start the 24/7 continuous live stream directly from the command line:

```bash
python scripts/continuous_live_stream.py
```

### 3. Automated 15-Minute News Publisher

Run the background publisher to generate and broadcast new stories every 15 minutes:

```bash
python scripts/run_realtime_news_autopublisher.py
```

## Deployment

### Linux Server (Systemd / Background)

```bash
# Start backend API
nohup python -m uvicorn app:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &

# Start automated background publisher
nohup python scripts/run_realtime_news_autopublisher.py > logs/publisher.log 2>&1 &
```

### Docker

```bash
docker compose up -d --build
```

## License

MIT
