"""
Twitter / X Publisher — API v2
Supports: Tweets, Threads, Media Tweets (images/videos)
Requires: Twitter Developer App with read/write permissions
"""
import requests
import json
import os
from pathlib import Path
from typing import Optional, List
from requests_oauthlib import OAuth1

BASE_DIR = Path(__file__).resolve().parent.parent


def _get_oauth(api_key, api_secret, access_token, access_token_secret):
    return OAuth1(api_key, api_secret, access_token, access_token_secret)


def post_tweet(
    text: str,
    api_key: str,
    api_secret: str,
    access_token: str,
    access_token_secret: str,
    media_path: Optional[str] = None
) -> dict:
    """
    Post a single tweet with optional media attachment.
    """
    if not all([api_key, api_secret, access_token, access_token_secret]):
        return {"success": False, "error": "Twitter API credentials not configured"}

    auth = _get_oauth(api_key, api_secret, access_token, access_token_secret)
    media_id = None

    # Upload media if provided
    if media_path and os.path.exists(media_path):
        media_id = _upload_media(media_path, auth)

    payload = {"text": text[:280]}
    if media_id:
        payload["media"] = {"media_ids": [str(media_id)]}

    resp = requests.post(
        "https://api.twitter.com/2/tweets",
        auth=auth,
        json=payload,
        timeout=30
    )

    if resp.status_code in (200, 201):
        data = resp.json()
        tweet_id = data.get("data", {}).get("id", "")
        return {"success": True, "tweet_id": tweet_id, "platform": "twitter",
                "url": f"https://twitter.com/i/web/status/{tweet_id}"}
    return {"success": False, "error": resp.text}


def post_thread(
    texts: List[str],
    api_key: str,
    api_secret: str,
    access_token: str,
    access_token_secret: str
) -> dict:
    """
    Post a Twitter thread (chain of replies).
    """
    if not all([api_key, api_secret, access_token, access_token_secret]):
        return {"success": False, "error": "Twitter API credentials not configured"}

    auth = _get_oauth(api_key, api_secret, access_token, access_token_secret)
    reply_to_id = None
    tweet_ids = []

    for chunk in texts[:10]:  # Max 10 tweets in thread
        payload = {"text": str(chunk)[:280]}
        if reply_to_id:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}

        resp = requests.post("https://api.twitter.com/2/tweets", auth=auth, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            tid = resp.json().get("data", {}).get("id", "")
            tweet_ids.append(tid)
            reply_to_id = tid
        else:
            break

    if tweet_ids:
        return {"success": True, "tweet_ids": tweet_ids, "platform": "twitter",
                "url": f"https://twitter.com/i/web/status/{tweet_ids[0]}"}
    return {"success": False, "error": "Failed to post thread"}


def _upload_media(media_path: str, auth) -> Optional[str]:
    """Upload media to Twitter and return media_id."""
    try:
        with open(media_path, "rb") as f:
            data = f.read()
        ext = Path(media_path).suffix.lower()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png" if ext == ".png" else "video/mp4"

        resp = requests.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            auth=auth,
            files={"media": (Path(media_path).name, data, mime)},
            timeout=60
        )
        if resp.status_code == 200:
            return resp.json().get("media_id_string")
    except Exception as e:
        print(f"[TWITTER] Media upload error: {e}")
    return None
