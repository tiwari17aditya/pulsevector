import os
import pathlib
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes for YouTube Data API
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.force-ssl']

def get_authenticated_service(client_secrets_file='credentials/client_secrets.json'):
    if not pathlib.Path(client_secrets_file).exists() and os.path.exists('client_secrets.json'):
        client_secrets_file = 'client_secrets.json'
    creds = None
    token_path = pathlib.Path('credentials/token.json')
    if not token_path.exists() and os.path.exists('token.json'):
        token_path = pathlib.Path('token.json')
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        save_path = pathlib.Path('credentials/token.json') if pathlib.Path('credentials').exists() else pathlib.Path('token.json')
        with open(save_path, 'w') as token:
            token.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)

def get_quarter_info(date_obj):
    month = date_obj.month
    year_str = date_obj.strftime("%Y")
    
    if month in [1, 2, 3]:
        quarter_name = "Q1"
        q_months = "Jan to March"
    elif month in [4, 5, 6]:
        quarter_name = "Q2"
        q_months = "Apr to June"
    elif month in [7, 8, 9]:
        quarter_name = "Q3"
        q_months = "July to Sep"
    else:
        quarter_name = "Q4"
        q_months = "Oct to Dec"
        
    playlist_title = f"Daily Current Affairs - ( {q_months} )- {year_str}"
    return quarter_name, playlist_title

def create_playlist(youtube, title, description=""):
    try:
        request = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description
                },
                "status": {
                    "privacyStatus": "public"
                }
            }
        )
        response = request.execute()
        return response['id']
    except Exception as e:
        logging.error(f"Error creating playlist '{title}': {e}")
        return None

def add_video_to_playlist(youtube, video_id, playlist_title):
    try:
        request = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50
        )
        response = request.execute()
        playlist_id = None
        for item in response.get('items', []):
            if item['snippet']['title'] == playlist_title:
                playlist_id = item['id']
                break
                
        if not playlist_id:
            print(f"Playlist '{playlist_title}' not found. Creating it...")
            playlist_id = create_playlist(youtube, playlist_title, f"Collection of {playlist_title}")
            if playlist_id:
                print(f"✅ Created new YouTube Playlist: '{playlist_title}'")
            else:
                return False
                
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        )
        request.execute()
        print(f"✅ Video successfully added to playlist: '{playlist_title}'")
        return True
    except Exception as e:
        logging.error(f"Error adding video {video_id} to playlist {playlist_title}: {e}")
        print(f"❌ Failed to add video to playlist: {e}")
        return False

def upload_video_to_youtube(youtube, file_path, title, description, tags, category_id="27", privacy_status=None):
    if not privacy_status:
        privacy_status = os.getenv("YOUTUBE_PRIVACY_STATUS", "public")
    try:
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
        )
        
        response = None
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                print(f"Uploading... {int(status.progress() * 100)}%")
                
        if 'id' in response:
            video_id = response['id']
            return video_id
        else:
            raise RuntimeError(f"Unexpected upload response: {response}")
    except Exception as e:
        logging.error(f"YouTube upload failed: {e}")
        raise

STANDARD_PINNED_COMMENT_TEMPLATE = (
    "🧠 Master your exam prep with daily 60-second Current Affairs updates! \n"
    "📚 Watch our full Weekly Masterclass: {masterclass_link}\n"
    "🔔 Subscribe to Pulse Vector & turn on notifications so you never miss a day!\n"
    "Which question should we feature in tomorrow's quiz? Drop it below! 👇"
)

def get_pinned_comment(masterclass_link="https://www.youtube.com/@PulseVector"):
    """Returns the formatted pinned comment text with the real link substituted."""
    return STANDARD_PINNED_COMMENT_TEMPLATE.format(masterclass_link=masterclass_link)

STANDARD_PINNED_COMMENT = get_pinned_comment()

def log_upload_details(title, category_name="Education (27)", video_type="Short (9:16)", related_video_setting="Linked to Latest Weekly Masterclass", pinned_comment_status="Pinned", video_id="N/A"):
    """Logs uploaded video details into Research/youtube_upload_details.md"""
    import datetime
    details_file = pathlib.Path("Research/youtube_upload_details.md")
    if not details_file.exists():
        details_file = pathlib.Path("youtube_upload_details.md")
    if not details_file.exists():
        return
        
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M IST")
    entry = f"| {date_str} | {title} | {category_name} | {video_type} | {related_video_setting} | {pinned_comment_status} | {video_id} |\n"
    
    try:
        content = details_file.read_text(encoding="utf-8")
        if "| Date (IST) | Video Title |" in content:
            content += entry
            details_file.write_text(content, encoding="utf-8")
            print(f"✅ Upload details logged to {details_file.name}")
    except Exception as e:
        logging.error(f"Failed to log upload details: {e}")

