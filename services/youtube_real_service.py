import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.youtube_upload_service import get_authenticated_service
from utils.logger import logger
from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

class YouTubeRealService:
    def __init__(self):
        self._yt = None

    def _get_client(self):
        if not self._yt:
            try:
                self._yt = get_authenticated_service(interactive=False)
            except Exception as e:
                logger.error(f"[YouTubeService] Authentication failed: {e}")
                raise
        return self._yt

    def get_channel_info(self) -> Dict[str, Any]:
        """Fetches real YouTube channel profile and statistics."""
        yt = self._get_client()
        resp = yt.channels().list(part="snippet,statistics,contentDetails", mine=True).execute()
        if not resp.get("items"):
            return {}
        
        item = resp["items"][0]
        snip = item["snippet"]
        stats = item["statistics"]
        
        return {
            "id": item["id"],
            "title": snip.get("title", "SRJ UNDERRATED"),
            "description": snip.get("description", ""),
            "customUrl": snip.get("customUrl", "@SRJUNDERRATED"),
            "avatarUrl": snip.get("thumbnails", {}).get("high", {}).get("url") or snip.get("thumbnails", {}).get("default", {}).get("url"),
            "subscriberCount": int(stats.get("subscriberCount", 0)),
            "viewCount": int(stats.get("viewCount", 0)),
            "videoCount": int(stats.get("videoCount", 0)),
            "publishedAt": snip.get("publishedAt", ""),
            "country": snip.get("country", "IN"),
            "uploadsPlaylistId": item["contentDetails"]["relatedPlaylists"]["uploads"],
        }

    def get_channel_videos(self, max_results: int = 24) -> List[Dict[str, Any]]:
        """Fetches real videos uploaded to the channel with metrics."""
        yt = self._get_client()
        ch_resp = yt.channels().list(part="contentDetails", mine=True).execute()
        uploads_playlist_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        pl_resp = yt.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=max_results
        ).execute()

        video_items = pl_resp.get("items", [])
        if not video_items:
            return []

        vid_ids = [item["snippet"]["resourceId"]["videoId"] for item in video_items]
        
        # Batch query detailed video statistics & duration
        stats_resp = yt.videos().list(
            part="statistics,snippet,contentDetails",
            id=",".join(vid_ids)
        ).execute()

        stats_map = {v["id"]: v for v in stats_resp.get("items", [])}

        videos = []
        for item in video_items:
            vid_id = item["snippet"]["resourceId"]["videoId"]
            snip = item["snippet"]
            detailed = stats_map.get(vid_id, {})
            st = detailed.get("statistics", {})
            cd = detailed.get("contentDetails", {})
            thumbs = snip.get("thumbnails", {})

            thumb_url = (
                thumbs.get("maxres", {}).get("url") or
                thumbs.get("high", {}).get("url") or
                thumbs.get("medium", {}).get("url") or
                f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
            )

            is_short = "#Shorts" in snip.get("title", "") or "#shorts" in snip.get("title", "")
            
            videos.append({
                "id": vid_id,
                "title": snip.get("title", ""),
                "description": snip.get("description", ""),
                "publishedAt": snip.get("publishedAt", ""),
                "thumbnailUrl": thumb_url,
                "viewCount": int(st.get("viewCount", 0)),
                "likeCount": int(st.get("likeCount", 0)),
                "commentCount": int(st.get("commentCount", 0)),
                "duration": cd.get("duration", ""),
                "youtubeUrl": f"https://youtu.be/{vid_id}",
                "embedUrl": f"https://www.youtube.com/embed/{vid_id}",
                "isShort": is_short,
            })

        return videos

    def get_stream_details(self) -> Dict[str, Any]:
        """Returns RTMP Live Stream credentials from environment."""
        stream_key = os.getenv("YOUTUBE_STREAM_KEY", "")
        masked_key = stream_key[:4] + "-****-****-" + stream_key[-4:] if len(stream_key) > 8 else "****"
        return {
            "rtmpUrl": "rtmp://a.rtmp.youtube.com/live2",
            "streamKeyMasked": masked_key,
            "hasKey": bool(stream_key),
            "targetResolution": "1080p 60fps / 720p 30fps",
            "audioCodec": "AAC stereo 128kbps 44.1kHz",
            "videoCodec": "H.264 / x264 NVENC/Software",
            "activeStreamEntry": "scripts/continuous_live_stream.py",
        }


youtube_real_service = YouTubeRealService()

def upload_to_channel(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list = None,
        thumbnail_path: str = None,
        is_short: bool = True,
        privacy_status: str = "public"
    ) -> Dict[str, Any]:
        """Uploads a generated video directly to SRJ UNDERRATED channel."""
        from services.youtube_upload_service import upload_video_to_youtube
        video_id = upload_video_to_youtube(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            thumbnail_path=thumbnail_path,
            is_short=is_short,
            privacy_status=privacy_status
        )
        return {
            "status": "success",
            "videoId": video_id,
            "youtubeUrl": f"https://youtu.be/{video_id}",
            "title": title
        }
