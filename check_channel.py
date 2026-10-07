import sys
from services.youtube_upload_service import get_authenticated_service

youtube = get_authenticated_service(interactive=False)
channels = youtube.channels().list(
    part='snippet,contentDetails,statistics',
    mine=True
).execute()

for ch in channels.get('items', []):
    print('CHANNEL TITLE:', ch['snippet']['title'])
    print('CHANNEL ID:', ch['id'])
    print('CUSTOM URL:', ch['snippet'].get('customUrl'))

uploads_playlist_id = channels['items'][0]['contentDetails']['relatedPlaylists']['uploads']
print('UPLOADS PLAYLIST ID:', uploads_playlist_id)

playlist_items = youtube.playlistItems().list(
    part='snippet,status',
    playlistId=uploads_playlist_id,
    maxResults=10
).execute()

print('=== RECENT UPLOADS ON CHANNEL ===')
for item in playlist_items.get('items', []):
    v_id = item['snippet']['resourceId']['videoId']
    v_title = item['snippet']['title']
    v_priv = item.get('status', {}).get('privacyStatus', 'unknown')
    print(f"ID: {v_id} | Title: {v_title} | Privacy: {v_priv}")
