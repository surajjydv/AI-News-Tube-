import sys, os
sys.path.insert(0, '.')
os.chdir('.')
from dotenv import load_dotenv
load_dotenv()
from services.youtube_upload_service import get_authenticated_service
try:
    yt = get_authenticated_service(interactive=False)
    ch = yt.channels().list(part='snippet', mine=True).execute()
    items = ch.get('items', [])
    if items:
        name = items[0]['snippet']['title']
        print(f'Connected to channel: {name}')
    else:
        print('Auth OK but no channel found')
except Exception as e:
    print(f'ERROR: {e}')
