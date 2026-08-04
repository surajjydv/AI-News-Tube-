# Memory

- `scripts/continuous_live_stream.py` is the 24/7 YouTube live entry point.
- The live engine now keeps one persistent RTMP FFmpeg process and feeds normalized MPEG-TS story segments through stdin to avoid per-clip reconnect cuts.
- If fresh rendering falls behind, the consumer loops the last valid clip instead of leaving dead air.
- README documents `python scripts/continuous_live_stream.py` for 24/7 YouTube live streaming with `YOUTUBE_STREAM_KEY` from `.env`.
