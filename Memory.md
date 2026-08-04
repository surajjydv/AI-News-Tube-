# Memory

- `scripts/continuous_live_stream.py` is the 24/7 YouTube live entry point.
- The live engine streams normalized MP4 clips (video + neural AAC audio) sequentially to YouTube RTMP FLV using `stream_clip_to_rtmp()`.
- If fresh rendering falls behind, the consumer loops the last valid clip instead of leaving dead air.
- README documents `python scripts/continuous_live_stream.py` for 24/7 YouTube live streaming with `YOUTUBE_STREAM_KEY` from `.env`.
- `services/rss_service.py` writes `seen_news.json` through unique process/thread temp files to avoid Windows collisions during overlapping live starts.
- Live encoder defaults are tuned for YouTube 720p health: 30fps, 4500k target bitrate, 5000k maxrate, 9000k buffer.
- **Hindi font fix**: `assets/fonts/NotoSansDevanagari-Bold.ttf` and `NotoSansDevanagari-Regular.ttf` downloaded. `_load_font()` in `agents/video_agent.py` updated to include `.ttc` fallback (`Nirmala.ttc`) and proper bold/regular variant selection. All text rendering is now Hindi/Devanagari compatible.
- **Live Stream Audio Fix**: Fixed `asyncio` event loop in bg threads. `stream_clip_to_rtmp()` now uses `aresample=async=1:first_pts=0` to fix growing audio lag (was causing YouTube to drop audio). Added `anullsrc` fallback + `-fflags +genpts+igndts` so clips with corrupt/delayed audio timestamps always stream with a valid AAC track. Old startup clip deleted and regenerated fresh.

