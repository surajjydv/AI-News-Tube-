import sys
from services.youtube_upload_service import get_authenticated_service

youtube = get_authenticated_service(interactive=False)

# Check audit details of the channel / video
res = youtube.videos().list(
    part='status,snippet,processingDetails',
    id='QMLN7RsVaBI',
    onBehalfOfContentOwner=None
).execute()

print("Details:", res)
