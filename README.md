# AI Social Media & Video Publishing Engine

An end-to-end automation platform for news curation, multi-format video production, and scheduled multi-platform publishing (YouTube, Telegram, Twitter/X, Facebook, and Instagram).

## Features

- **Automated News Discovery**: Ingests breaking stories from verified RSS feeds and press wires with semantic deduplication.
- **Editorial Media Verification**: Filters imagery for quality, resolution, and safe presentation standards.
- **Neural Voice & Script Engine**: Generates journalistic scripts and natural text-to-speech narration in multiple voices and languages.
- **Multi-Format Video Rendering**: Builds 1080p landscape documentaries (16:9), TV broadcast bulletins with glassmorphic lower-thirds and live news tickers, and vertical shorts/reels (9:16) via an optimized FFmpeg pipeline.
- **Cross-Platform Distribution**: Automated and manual publishing pipelines for YouTube (VOD & Shorts), Telegram channels, Twitter/X, Facebook Pages, and Instagram.
- **Centralized Control Studio**: Browser-based dashboard (FastAPI) for one-click publishing, channel switching, scheduling, platform credential management, and live log streaming.
- **Configurable Scheduling**: Supports custom posting intervals (1h, 3h, 6h) and quiet hours (e.g., 12:00 AM - 06:00 AM IST).

## Architecture

```
[News Feeds & Press Wires]
         │
         ▼
[Content Curation & Verification]
         │
         ▼
[Script Generation & Neural TTS]
         │
         ▼
[FFmpeg Video Synthesis (16:9 / 9:16)]
         │
         ▼
[Multi-Platform Publishing Engine]
 ├── YouTube (API v3 / OAuth2)
 ├── Telegram (Bot API)
 ├── Twitter / X (v2 API)
 ├── Facebook (Graph API)
 └── Instagram (Content Publishing API)
```

## Setup

### Prerequisites

- Python 3.10+
- FFmpeg installed and available in system `PATH`

### Installation

```bash
git clone https://github.com/your-org/AI-NewsTube.git
cd AI-NewsTube
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key
CHANNEL_NAME="SRJ UNDERRATED"
DEFAULT_TTS_VOICE="hi-IN-MadhurNeural"
PORT=80
```

To configure platform credentials (Telegram, Twitter/X, Facebook, Instagram), add them via the **Platforms** tab in the Web Studio or update `data/platforms.json`.

For YouTube publishing, place your `client_secret.json` in the root folder and authenticate:

```bash
python auth_youtube.py
```

## Usage

### Web Control Studio

Start the dashboard:

```bash
python app.py
```

Access the UI at `http://localhost/` (or your server's public IP).

### Autonomous Publishing Daemon

Launch the autonomous background publisher:

```bash
python scripts/trending_documentary_autopublisher.py
```

### Manual CLI Publishing

Generate and publish a video for a single topic:

```bash
python test_generate_one_video.py --topic "Your Topic or Headline Here"
```

## Deployment

### Linux / AWS EC2 (systemd or tmux)

```bash
# Web Dashboard
tmux new-session -d -s studio_app 'sudo PYTHONPATH=. python3 -m uvicorn app:app --host 0.0.0.0 --port 80'

# Autonomous Publishing Daemon
tmux new-session -d -s autopublisher 'python3 -u scripts/trending_documentary_autopublisher.py >> logs/publisher.log 2>&1'
```

### Docker

```bash
docker compose up -d --build
```

## License

MIT License.
