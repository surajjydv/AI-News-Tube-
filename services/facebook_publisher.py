"""
Facebook Publisher — Meta Graph API
Supports: Text posts, link posts, photo posts, video uploads on Facebook Pages
"""
import requests
from pathlib import Path
from typing import Optional


def post_facebook_text(
    message: str,
    page_id: str,
    page_access_token: str,
    link: Optional[str] = None
) -> dict:
    """Post a text/link post on a Facebook Page."""
    if not page_id or not page_access_token:
        return {"success": False, "error": "Facebook credentials not configured"}

    payload = {
        "message": message,
        "access_token": page_access_token
    }
    if link:
        payload["link"] = link

    resp = requests.post(
        f"https://graph.facebook.com/v19.0/{page_id}/feed",
        data=payload,
        timeout=30
    ).json()

    if "id" in resp:
        return {"success": True, "post_id": resp["id"], "platform": "facebook"}
    return {"success": False, "error": resp.get("error", {}).get("message", "Post failed")}


def post_facebook_photo(
    image_path: str,
    caption: str,
    page_id: str,
    page_access_token: str,
    image_url: Optional[str] = None
) -> dict:
    """Post a photo to a Facebook Page."""
    if not page_id or not page_access_token:
        return {"success": False, "error": "Facebook credentials not configured"}

    if image_url:
        payload = {
            "url": image_url,
            "caption": caption,
            "access_token": page_access_token
        }
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{page_id}/photos",
            data=payload,
            timeout=30
        ).json()
    else:
        with open(image_path, "rb") as f:
            resp = requests.post(
                f"https://graph.facebook.com/v19.0/{page_id}/photos",
                data={"caption": caption, "access_token": page_access_token},
                files={"source": f},
                timeout=60
            ).json()

    if "id" in resp:
        return {"success": True, "post_id": resp["id"], "platform": "facebook"}
    return {"success": False, "error": resp.get("error", {}).get("message", "Photo post failed")}


def upload_facebook_video(
    video_path: str,
    title: str,
    description: str,
    page_id: str,
    page_access_token: str
) -> dict:
    """Upload a video to a Facebook Page."""
    if not page_id or not page_access_token:
        return {"success": False, "error": "Facebook credentials not configured"}

    with open(video_path, "rb") as f:
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{page_id}/videos",
            data={
                "title": title,
                "description": description,
                "access_token": page_access_token
            },
            files={"source": f},
            timeout=300
        ).json()

    if "id" in resp:
        return {"success": True, "video_id": resp["id"], "platform": "facebook"}
    return {"success": False, "error": resp.get("error", {}).get("message", "Video upload failed")}
