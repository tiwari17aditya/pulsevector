import os
import re
import pathlib
import logging
from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Google API Scopes
YOUTUBE_SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]
GDRIVE_SCOPES = [
    'https://www.googleapis.com/auth/drive.file'
]
ALL_GOOGLE_SCOPES = YOUTUBE_SCOPES + GDRIVE_SCOPES
SCOPES = YOUTUBE_SCOPES  # Default YouTube scopes for backwards compatibility


# YouTube API tag constraints
_YT_MAX_TAG_CHARS = 500   # total char budget across all tags
_YT_MAX_SINGLE_TAG = 100  # single tag length limit


def sanitize_youtube_tags(tags: List[str]) -> List[str]:
    """
    Cleans a list of tags so they pass YouTube Data API validation.

    YouTube rules for snippet.tags:
      - No leading '#' character (those are description hashtags, not API tags)
      - No angle-brackets, quotes, or other chars that fail YouTube validation
      - Each tag <= 100 chars
      - Total length of all tags (comma-separated) <= 500 chars
      - Duplicates removed (case-insensitive)

    Returns a list of clean, API-safe tag strings.
    """
    seen: set = set()
    clean: List[str] = []
    total_chars = 0

    for raw in (tags or []):
        if not isinstance(raw, str):
            continue
        # Strip leading # (description hashtag prefix)
        tag = raw.lstrip("#").strip()
        # Remove characters YouTube rejects: < > " ' & and leading/trailing whitespace
        tag = re.sub(r'[<>"\'\'\"&]', '', tag).strip()
        # Collapse internal whitespace
        tag = re.sub(r'\s+', ' ', tag)
        # Skip empty or oversized individual tags
        if not tag or len(tag) > _YT_MAX_SINGLE_TAG:
            continue
        # Deduplicate (case-insensitive)
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        # Enforce total 500-char budget (YouTube counts comma+space separators)
        budget_cost = len(tag) + (2 if clean else 0)  # ", " separator
        if total_chars + budget_cost > _YT_MAX_TAG_CHARS:
            break
        clean.append(tag)
        total_chars += budget_cost

    return clean

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

def generate_playlist_description(title: str) -> str:
    """Generates an engaging, SEO-optimized, structured description for a Pulse Vector playlist."""
    t_lower = title.lower()
    if "brain teaser" in t_lower or "puzzle" in t_lower:
        return (
            f"🧠 Welcome to the Official {title} by Pulse Vector!\n\n"
            "Challenge your mind with sharp, high-yield logical reasoning puzzles, math teasers, "
            "pattern recognition questions, and analytical thinking riddles engineered for competitive exam aspirants and curious minds.\n\n"
            "🎯 Key Highlights:\n"
            "• ⏱️ Fast-Paced Shorts: Interactive 60-second puzzle shorts testing quick deduction and cognitive reflex.\n"
            "• 💡 Step-by-Step Solutions: Full logic breakdown and reasoning revealed in every episode.\n"
            "• 🏆 Exam Relevance: Perfect practice for CSAT (UPSC), SSC CGL/CHSL Reasoning, Banking PO/Clerk, Railways (RRB), and Campus Placements.\n"
            "• 💬 Community Discussion: Drop your answers in the comments before the reveal and compete with fellow aspirants!\n\n"
            "🔔 Subscribe to @Pulse_vector and turn on notifications for your daily cognitive workout!\n"
            "🌐 Official Channel: https://www.youtube.com/@Pulse_vector\n\n"
            "#BrainTeasers #Puzzles #LogicalReasoning #Aptitude #UPSC #SSCCGL #PulseVector #Shorts"
        )
    elif "weekly" in t_lower:
        return (
            f"📅 Official {title} Masterclasses by Pulse Vector.\n\n"
            "Consolidate your entire week's preparation with Pulse Vector's in-depth Weekly Current Affairs Masterclasses. "
            "Released every Sunday, these structured long-form video lectures synthesize all major national and global news "
            "from the preceding 7 days into an organized, exam-ready format.\n\n"
            "🎯 Why Follow This Weekly Playlist?\n"
            "• 🔍 In-Depth Analytical Breakdown: Goes beyond headlines into background context, policy implications, and analytical takeaways.\n"
            "• 🗂️ Structured Category Walkthrough: Economy, International Relations, Polity, Science & Environment, Defense, and National Affairs.\n"
            "• ⏱️ Optimized Time Efficiency: Replace hours of scattered newspaper reading with a single high-impact weekly masterclass.\n"
            "• 🎯 Exam Standard: Directly aligned with the dynamic syllabus of UPSC CSE, State PSCs, SSC CGL/CHSL, and Banking examinations.\n\n"
            "🔔 Subscribe to @Pulse_vector and master your weekly revision every Sunday!\n"
            "🌐 Official Channel: https://www.youtube.com/@Pulse_vector\n\n"
            "#WeeklyCurrentAffairs #CurrentAffairs #UPSC #UPSCMains #SSCCGL #BankingExams #PulseVector"
        )
    elif "monthly" in t_lower:
        return (
            f"🗓️ Official {title} Masterclass Roundups by Pulse Vector.\n\n"
            "Your definitive, end-to-end Monthly Current Affairs Compilations. Each monthly masterclass delivers an exhaustive, "
            "category-by-category synthesis of the entire month's critical events, policy shifts, and global developments.\n\n"
            "🎯 Masterclass Features:\n"
            "• 🏛️ Exhaustive Coverage: Complete 360-degree review of National Affairs, International Geopolitics, Economy & Banking, Environment, Science & Tech, Defense, and Major Appointments.\n"
            "• 📑 Visual & Bulleted Synthesis: High-clarity visual infographics and structured bullet points designed for fast memory recall.\n"
            "• 🚀 Pre-Exam Power Revision: The ultimate resource for rapid monthly revision before UPSC Prelims/Mains, SSC, Banking, and PSC exams.\n\n"
            "🔔 Subscribe to @Pulse_vector for authoritative monthly masterclasses!\n"
            "🌐 Official Channel: https://www.youtube.com/@Pulse_vector\n\n"
            "#MonthlyCurrentAffairs #CurrentAffairsRoundup #UPSC #SSCCGL #BankingAwareness #PulseVector"
        )
    else:
        return (
            f"⚡ Official {title} Archive by Pulse Vector.\n\n"
            "Your comprehensive, chronological archive of high-retention Daily Current Affairs shorts covering all critical "
            "national, international, economic, defense, and science developments.\n\n"
            "🎯 What's Inside This Playlist:\n"
            "• 📰 High-Yield Daily Summaries: Concise 60-second daily news capsules covering exam-centric facts and figures.\n"
            "• 🏛️ Multi-Domain Coverage: National Policies, Global Geopolitics, Banking & Economy, Science & Tech, Defense Exercises, Appointments, and Awards.\n"
            "• 🎓 Tailored For: UPSC Civil Services (Prelims & Mains), SSC CGL, CHSL, Banking (IBPS, SBI PO), Railways (RRB NTPC), State PSCs, NDA, and CDS.\n"
            "• 🔄 Rapid Revision: Watch chronologically or binge-revise key quarters before your competitive examinations.\n\n"
            "🔔 Subscribe to @Pulse_vector for daily, weekly, and monthly current affairs updates!\n"
            "🌐 Official Channel: https://www.youtube.com/@Pulse_vector\n\n"
            "#CurrentAffairs #DailyCurrentAffairs #UPSC #SSCCGL #BankingExams #PulseVector #GeneralKnowledge"
        )

def create_playlist(youtube, title, description=""):
    try:
        if not description:
            description = generate_playlist_description(title)
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
            playlist_desc = generate_playlist_description(playlist_title)
            playlist_id = create_playlist(youtube, playlist_title, playlist_desc)
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
    # Always sanitize tags before sending to YouTube API.
    # Raw tags from Gemini output often carry '#' prefixes or special chars
    # that cause HTTP 400 invalidTags errors.
    safe_tags = sanitize_youtube_tags(tags or [])
    logging.debug(f"YouTube upload tags (sanitized): {safe_tags}")
    try:
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': safe_tags,
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

def get_pinned_comment(masterclass_link="https://www.youtube.com/@Pulse_vector"):
    """Returns the formatted pinned comment text with the real link substituted."""
    return STANDARD_PINNED_COMMENT_TEMPLATE.format(masterclass_link=masterclass_link)

def format_daily_interactive_comment(headline_preview: str, date_str: str, masterclass_link: str = "https://www.youtube.com/@Pulse_vector") -> str:
    """Formats a high-engagement discussion comment for Daily Current Affairs Shorts."""
    # Clean headline preview
    clean_hl = re.sub(r'[\.\:\;\-\"\'\`]', '', headline_preview).strip()
    if len(clean_hl) > 60:
        clean_hl = clean_hl[:60].rsplit(' ', 1)[0] + "..."
    return (
        f"🔥 TODAY'S TOPIC DEBATE ({date_str}):\n"
        f"Regarding: \"{clean_hl}\"\n\n"
        "💬 Which of today's 5 stories do you believe will shape the coming month most?\n"
        "Drop your answer or perspective below — best analytical comments get pinned! 📌\n\n"
        f"📚 Full Weekly Masterclass breakdown: {masterclass_link}\n"
        "🔔 Subscribe to Pulse Vector for daily rapid updates!"
    )

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

def add_video_comment(youtube, video_id: str, comment_text: str) -> Optional[str]:
    """
    Inserts a top-level interactive comment directly onto an uploaded YouTube video/Short.
    Returns the comment ID if successful, or None on failure.
    """
    try:
        request = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": comment_text
                        }
                    }
                }
            }
        )
        response = request.execute()
        comment_id = response.get("id")
        print(f"✅ Posted interactive comment on video {video_id} (ID: {comment_id})")
        return comment_id
    except Exception as e:
        print(f"  > Warning: Could not post video comment: {e}")
        logging.warning(f"Could not post video comment on {video_id}: {e}")
        return None

