"""
Instagram Publisher — Meta Graph API
Supports: Reels (9:16 video), Photo Posts, Story-style content
Requires: Instagram Business/Creator account linked to a Facebook Page
"""
import os
import json
import time
import requests
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent


def upload_instagram_reel(
    video_path: str,
    caption: str,
    access_token: str,
    instagram_business_id: str,
    cover_image_path: Optional[str] = None
) -> dict:
    """
    Upload a 9:16 Reel video to Instagram via Media Container API.
    """
    if not access_token or not instagram_business_id:
        return {"success": False, "error": "Instagram access_token or page_id not configured"}

    video_url = None  # Must be a publicly accessible URL for the video
    # For local videos, you'd need to upload to a temporary CDN or S3 first.
    # We generate a signed URL via EC2 static file server on port 8080 (or direct path for testing)

    # Step 1: Create media container
    container_url = f"https://graph.facebook.com/v19.0/{instagram_business_id}/media"
    params = {
        "media_type": "REELS",
        "video_url": video_url or f"file://{video_path}",  # Must be public URL in production
        "caption": caption,
        "access_token": access_token
    }
    if cover_image_path:
        params["thumb_offset"] = "0"

    resp = requests.post(container_url, data=params, timeout=60)
    container_data = resp.json()

    if "error" in container_data:
        return {"success": False, "error": container_data["error"].get("message", str(container_data["error"]))}

    container_id = container_data.get("id")
    if not container_id:
        return {"success": False, "error": "No container ID returned"}

    # Step 2: Poll until video is ready
    for _ in range(20):
        status_url = f"https://graph.facebook.com/v19.0/{container_id}?fields=status_code&access_token={access_token}"
        sr = requests.get(status_url, timeout=15).json()
        status = sr.get("status_code", "")
        if status == "FINISHED":
            break
        elif status == "ERROR":
            return {"success": False, "error": "Video processing failed on Instagram servers"}
        time.sleep(6)

    # Step 3: Publish
    publish_url = f"https://graph.facebook.com/v19.0/{instagram_business_id}/media_publish"
    pub_resp = requests.post(publish_url, data={
        "creation_id": container_id,
        "access_token": access_token
    }, timeout=30).json()

    if "id" in pub_resp:
        return {"success": True, "media_id": pub_resp["id"], "platform": "instagram"}
    return {"success": False, "error": pub_resp.get("error", {}).get("message", "Unknown publish error")}


def post_instagram_photo(
    image_path: str,
    caption: str,
    access_token: str,
    instagram_business_id: str,
    image_url: Optional[str] = None
) -> dict:
    """
    Post a photo to Instagram feed.
    """
    if not access_token or not instagram_business_id:
        return {"success": False, "error": "Not configured"}

    container_url = f"https://graph.facebook.com/v19.0/{instagram_business_id}/media"
    params = {
        "image_url": image_url or "",
        "caption": caption,
        "access_token": access_token
    }

    resp = requests.post(container_url, data=params, timeout=30).json()
    if "error" in resp:
        return {"success": False, "error": resp["error"].get("message", "Error")}

    container_id = resp.get("id")
    pub_url = f"https://graph.facebook.com/v19.0/{instagram_business_id}/media_publish"
    pub = requests.post(pub_url, data={"creation_id": container_id, "access_token": access_token}, timeout=30).json()

    if "id" in pub:
        return {"success": True, "media_id": pub["id"], "platform": "instagram"}
    return {"success": False, "error": pub.get("error", {}).get("message", "Publish failed")}
