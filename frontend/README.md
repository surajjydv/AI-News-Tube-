# AutoInsta Studio

Automated B2B Instagram content generation and publishing platform. Generates complete media packs (4K visuals, vertical video reels, neural voiceover, and thumbnails) from a single prompt and publishes directly via the Instagram Graph API.

---

## Features

- **Multi-Account Switching**: Manage multiple business profiles and client accounts from one unified dashboard.
- **Single-Prompt Generation**: Generates 4K images, 9:16 vertical video reels, neural voiceover, cover frames, captions, and hashtag sets from one creative brief.
- **Multi-Format Output**: Tailored rendering for Reels (9:16), Feed Posts (4:5 or 1:1), Stories, and Carousels.
- **Smart Scheduling & Queue**: Custom date/time picker, recurring cadence (Daily, Weekly, Monthly), and automated Graph API queue.
- **Brand Kit Configuration**: Save brand colors, typography, tone of voice, and standard call-to-actions per client.
- **Performance Analytics**: View engagement, impressions, format distribution, and top-performing posts.

---

## Backend & Database Integration

- **FastAPI Backend**: `http://127.0.0.1:8000` (`/api/studio/*`)
- **Neon Database**: Relational tables for accounts, media packs, schedule queues, and brand kits.
- **Neon S3 Storage**: Object storage connected via `neon-storage.env` targeting the `uploads` bucket for images, audio tracks, and video clips.

---

## Architecture

```text
Prompt Studio (Next.js 16 + Zustand)
  ?
  ??? Media Generation Pipeline
  ?     ??? Flux 1.1 (4K Visual Rendering)
  ?     ??? Edge-TTS (Neural Voice Synthesis)
  ?     ??? FFmpeg (9:16 Vertical Video Reel Assembly)
  ?
  ??? Publishing & Scheduling Layer
        ??? Auto-Pilot Calendar Queue
        ??? Meta Instagram Graph API
```

---

## Setup

### Prerequisites

- Node.js 18.x or later
- npm or pnpm

### Installation

```bash
git clone https://github.com/your-org/instagram-ai-studio.git
cd frontend
npm install
```

### Environment Variables

Create a `.env.local` file in the project root:

```env
NEXT_PUBLIC_APP_URL=http://localhost:3000
INSTAGRAM_CLIENT_ID=your_facebook_app_id
INSTAGRAM_CLIENT_SECRET=your_facebook_app_secret
```

---

## Usage

### Development Server

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm run start
```

---

## Deployment

Deploy directly to Vercel or any containerized Node.js environment:

```bash
npx vercel
```
