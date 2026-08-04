# Memory

- `scripts/continuous_live_stream.py` is the 24/7 YouTube live entry point.
- The live engine now keeps one persistent RTMP FFmpeg process and feeds normalized MPEG-TS story segments through stdin to avoid per-clip reconnect cuts.
- If fresh rendering falls behind, the consumer loops the last valid clip instead of leaving dead air.
- README documents `python scripts/continuous_live_stream.py` for 24/7 YouTube live streaming with `YOUTUBE_STREAM_KEY` from `.env`.
- `services/rss_service.py` writes `seen_news.json` through unique process/thread temp files to avoid Windows collisions during overlapping live starts.
- Live encoder defaults are tuned for YouTube 720p health: 30fps, 4500k target bitrate, 5000k maxrate, 9000k buffer. `main_fixed()` now uses a raw-frame feeder into one persistent RTMP FFmpeg process to avoid MPEG-TS timestamp discontinuities between clips.
- **Hindi font fix**: `assets/fonts/NotoSansDevanagari-Bold.ttf` and `NotoSansDevanagari-Regular.ttf` downloaded. `_load_font()` in `agents/video_agent.py` updated to include `.ttc` fallback (`Nirmala.ttc`) and proper bold/regular variant selection. All text rendering is now Hindi/Devanagari compatible.
