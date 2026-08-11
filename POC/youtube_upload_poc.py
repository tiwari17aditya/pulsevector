import os
import re
import sys
import cv2
import random
import glob
import urllib.request
import subprocess
from datetime import datetime
import imageio_ffmpeg
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    creds = None
    token_path = "token.json"
    secrets_path = "client_secrets.json"
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing access token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(secrets_path):
                print(f"Error: {secrets_path} not found in the project root folder.")
                print("Please download your desktop client credentials JSON and save it as client_secrets.json.")
                sys.exit(1)
            print("Initiating OAuth 2.0 flow. A browser window will open for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_path, "w") as token:
            token.write(creds.to_json())
            
    return build("youtube", "v3", credentials=creds)

def parse_daily_metadata(text_path):
    title = ""
    description = ""
    if not os.path.exists(text_path):
        return None, None
        
    with open(text_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    title_match = re.search(r'^Title:\s*(.+)$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        
    desc_match = re.search(r'^Reel Description:\s*(.+)$', content, re.MULTILINE)
    if desc_match:
        description = desc_match.group(1).strip()
    else:
        desc_match = re.search(r'^Description:\s*(.+)$', content, re.MULTILINE)
        if desc_match:
            description = desc_match.group(1).strip()
            
    return title, description

def download_audio_library():
    audio_dir = "samples/Audio"
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
        
    print("Checking background music assets (15 free tracks)...")
    for i in range(1, 16):
        file_name = f"track_{i:02d}.mp3"
        file_path = os.path.join(audio_dir, file_name)
        if not os.path.exists(file_path):
            url = f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{i}.mp3"
            print(f"Downloading background music track {i}/15: {url} ...")
            try:
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=15) as response, open(file_path, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"Saved: {file_name}")
            except Exception as e:
                print(f"Failed to download track {i}: {e}")

def get_random_audio_track():
    audio_dir = "samples/Audio"
    mp3_files = glob.glob(os.path.join(audio_dir, "*.mp3"))
    if not mp3_files:
        return None
    return random.choice(mp3_files)

def compile_images_to_video(image_paths, output_path, duration_per_image=3.0, fps=10):
    print("Compiling silent video from slide images...")
    if not image_paths:
        raise ValueError("No image paths provided for video compilation.")
    
    first_img = cv2.imread(image_paths[0])
    if first_img is None:
        raise FileNotFoundError(f"Failed to read image: {image_paths[0]}")
    h, w, c = first_img.shape
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    
    frames_per_image = int(duration_per_image * fps)
    
    for img_path in image_paths:
        img = cv2.imread(img_path)
        if img is None:
            print(f"Warning: Skipping unreadable image {img_path}")
            continue
        if img.shape[0] != h or img.shape[1] != w:
            img = cv2.resize(img, (w, h))
        
        for _ in range(frames_per_image):
            out.write(img)
            
    out.release()
    print(f"Silent video file generated: {output_path}")

def merge_audio_video(video_path, audio_path, output_path, video_duration=9.0):
    print(f"Muxing background audio '{os.path.basename(audio_path)}' into video...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    st_fade = max(0.0, video_duration - 1.0)
    
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-filter_complex", f"[1:a]volume=0.35,afade=t=out:st={st_fade}:d=1.0[a]",
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")
    print(f"Finalized video with audio generated: {output_path}")

def upload_video_to_youtube(youtube, video_path, title, description, privacy_status="private"):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["CurrentAffairs", "NewsUpdate", "PulseVector"],
            "categoryId": "27"  # Education
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024*1024
    )
    
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    response = None
    print(f"Starting upload of {video_path} to YouTube...")
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%...")
            
    video_id = response.get("id")
    print(f"Upload Complete! Video ID: {video_id}")
    print(f"Watch URL: https://www.youtube.com/watch?v={video_id}")
    return video_id

def main():
    # Target date: Today (16 June 2026)
    target_date = datetime(2026, 6, 16)
    date_str = target_date.strftime("%d%b-%Y").lower()  # e.g., "16jun-2026"
    
    text_path = f"pulse_archive/2026/June/Daily/daily-{date_str}_formatted.txt"
    images_dir = f"pulse_archive/2026/June/Daily_Images/daily-{date_str}_formatted"
    
    print(f"Processing content for {target_date.strftime('%d %B %Y')}")
    
    title, description = parse_daily_metadata(text_path)
    if not title or not description:
        print("Error: Could not parse Title or Description from the text file.")
        sys.exit(1)
        
    print(f"Parsed Title: {title}")
    
    # Locate images
    image_paths = [
        os.path.join(images_dir, f"daily-{date_str}_formatted_page-1.png"),
        os.path.join(images_dir, f"daily-{date_str}_formatted_page-2.png"),
        os.path.join(images_dir, f"daily-{date_str}_formatted_page-3.png")
    ]
    
    for img_path in image_paths:
        if not os.path.exists(img_path):
            print(f"Error: Required image not found: {img_path}")
            sys.exit(1)
            
    # Setup/update background audio library
    download_audio_library()
    
    # Choose random audio track
    audio_track = get_random_audio_track()
    
    silent_video_path = f"POC/daily-{date_str}_silent.mp4"
    final_video_path = f"POC/daily-{date_str}_formatted.mp4"
    
    # 1. Compile images into a silent video
    compile_images_to_video(image_paths, silent_video_path, duration_per_image=3.0, fps=10)
    
    # 2. Merge with random background audio (if available)
    if audio_track:
        print(f"Selected audio track: {audio_track}")
        try:
            merge_audio_video(silent_video_path, audio_track, final_video_path, video_duration=9.0)
            # Remove silent video temp file
            if os.path.exists(silent_video_path):
                os.remove(silent_video_path)
        except Exception as e:
            print(f"Warning: Failed to merge audio ({e}). Falling back to silent video.")
            if os.path.exists(silent_video_path):
                os.rename(silent_video_path, final_video_path)
    else:
        print("Warning: No audio tracks found in samples/Audio/. Using silent video.")
        if os.path.exists(silent_video_path):
            os.rename(silent_video_path, final_video_path)
            
    # 3. Authenticate and upload to YouTube
    try:
        youtube = get_authenticated_service()
        upload_video_to_youtube(
            youtube,
            video_path=final_video_path,
            title=title,
            description=description,
            privacy_status="unlisted"  # Default to unlisted for testing
        )
    except Exception as e:
        print(f"An error occurred during YouTube upload: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
