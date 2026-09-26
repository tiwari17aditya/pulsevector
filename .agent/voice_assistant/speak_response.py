"""
Pulse Vector / Antigravity Voice Assistant (v1.1.0)
Automatically speaks AI responses as soon as output completes.
Triggered by Antigravity's native Lifecycle Hook ('Stop' event).
Supports Windows SAPI and Edge-TTS with configurable speed, volume, and voice selection.
"""

import os
import sys
import re
import json
import pathlib
import subprocess
import logging

# Ensure UTF-8 console output safety
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
LOG_FILE = SCRIPT_DIR / "voice.log"
CONFIG_FILE = SCRIPT_DIR / "voice_config.json"
LAST_SPOKEN_FILE = SCRIPT_DIR / ".last_spoken_hash"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

def load_config() -> dict:
    defaults = {
        "enabled": True,
        "rate": 1,
        "volume": 100,
        "max_words": 40,
        "engine": "sapi",
        "voice_name": "",
        "edge_voice": "en-US-ChristopherNeural"
    }
    if CONFIG_FILE.exists():
        try:
            defaults.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception as e:
            logging.warning(f"Error loading config: {e}")
    return defaults

def clean_markdown_for_speech(raw_text: str, max_words: int = 40) -> str:
    """Cleans code blocks, markdown symbols, and emojis for natural speech."""
    if not raw_text:
        return ""
    
    # 1. Strip fenced code blocks completely
    cleaned = re.sub(r"```[\s\S]*?```", "", raw_text)
    
    # 2. Strip inline code
    cleaned = re.sub(r"`[^`\n]+`", "", cleaned)
    
    # 3. Strip image embeds ![alt](url)
    cleaned = re.sub(r"!\[.*?\]\(.*?\)", "", cleaned)
    
    # 4. Strip markdown links [text](url) -> text
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
    
    # 5. Strip table lines
    lines = []
    for line in cleaned.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("|") and trimmed.endswith("|"):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    
    # 6. Strip emojis and high unicode symbols
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
    cleaned = re.sub(r'[•►▪■★☆✦✓✔✗✘🎙️🚀⚡⚙️📝🔊🔇🗣️🔍🧪✅📦🎛️]', '', cleaned)
    
    # 7. Strip bullet symbols, header hashes, blockquotes
    cleaned = re.sub(r"^[\s#*\-+=>]+", "", cleaned, flags=re.MULTILINE)
    
    # 8. Strip bold/italic markers and decorations
    cleaned = re.sub(r"[*_~`]", "", cleaned)
    
    # 9. Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    # 10. Cap length if excessively long
    words = cleaned.split()
    if len(words) > max_words:
        cleaned = " ".join(words[:max_words]) + "."
        
    return cleaned

def speak_sapi(text: str, rate: int = 1, volume: int = 100, voice_name: str = ""):
    """Speaks text using Windows SAPI (instant, 100% offline)."""
    import win32com.client
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Rate = max(-10, min(10, int(rate)))
    speaker.Volume = max(0, min(100, int(volume)))
    
    if voice_name:
        voices = speaker.GetVoices()
        for i in range(voices.Count):
            v = voices.Item(i)
            if voice_name.lower() in v.GetDescription().lower():
                speaker.Voice = v
                break
                
    speaker.Speak(text)

def speak_edge(text: str, voice: str = "en-US-ChristopherNeural", rate_pct: int = 15):
    """Speaks text using Microsoft Edge Neural TTS."""
    rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"
    temp_mp3 = SCRIPT_DIR / "temp_response.mp3"
    
    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", voice,
        "--rate", rate_str,
        "--text", text,
        "--write-media", str(temp_mp3)
    ]
    subprocess.run(cmd, capture_output=True)
    
    if temp_mp3.exists():
        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(temp_mp3)], check=True)
        except Exception:
            subprocess.run(["powershell", "-c", f"$w = New-Object -ComObject wmplayer.ocx; $w.URL = '{str(temp_mp3)}'; while($w.playState -ne 1) {{ Start-Sleep -Milliseconds 100 }}"], capture_output=True)
        try:
            temp_mp3.unlink()
        except Exception:
            pass

def find_last_model_message(transcript_path: pathlib.Path) -> str:
    """Finds the last user-facing text response from the model in transcript.jsonl."""
    if not transcript_path or not transcript_path.exists():
        return ""
        
    try:
        lines = transcript_path.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
        for line in reversed(lines):
            try:
                obj = json.loads(line)
                src = obj.get("source")
                stype = obj.get("type")
                has_tools = bool(obj.get("tool_calls"))
                content = obj.get("content", "")
                
                # Check for model conversational response
                if src == "MODEL" and stype == "PLANNER_RESPONSE" and not has_tools and content:
                    return content
            except Exception:
                continue
    except Exception as e:
        logging.warning(f"Error reading transcript: {e}")
        
    return ""

def main():
    # 1. Antigravity Hook contract: Immediately acknowledge with {} on stdout
    print("{}", flush=True)

    # 2. Check configuration
    config = load_config()
    if not config.get("enabled", True):
        logging.info("Voice assistant disabled in voice_config.json; skipping.")
        return

    # 3. Locate active transcript from newest brain log
    transcript_path = None
    brain_dir = pathlib.Path(os.path.expanduser(r"~\.gemini\antigravity-ide\brain"))
    if brain_dir.exists():
        transcripts = list(brain_dir.rglob("transcript.jsonl"))
        if transcripts:
            transcripts.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            transcript_path = transcripts[0]

    if not transcript_path or not transcript_path.exists():
        logging.warning("Could not find active transcript.jsonl.")
        return

    # 4. Extract latest response
    raw_response = find_last_model_message(transcript_path)
    if not raw_response:
        logging.info("No new model response text found to speak.")
        return

    # 5. Check deduplication to prevent speaking identical response twice
    import hashlib
    content_hash = hashlib.sha256(raw_response.encode("utf-8")).hexdigest()
    if LAST_SPOKEN_FILE.exists():
        try:
            if LAST_SPOKEN_FILE.read_text(encoding="utf-8").strip() == content_hash:
                logging.info("Response already spoken previously; skipping duplicate.")
                return
        except Exception:
            pass

    # 6. Clean text for natural speech
    max_words = int(config.get("max_words", 40))
    spoken_text = clean_markdown_for_speech(raw_response, max_words=max_words)
    if not spoken_text:
        return

    logging.info(f"Speaking response ({len(spoken_text)} chars, ~{len(spoken_text.split())} words)...")

    # 7. Speak using chosen engine
    engine = config.get("engine", "sapi").lower()
    try:
        if engine == "edge-tts":
            edge_voice = config.get("edge_voice", "en-US-ChristopherNeural")
            rate_pct = int(config.get("rate", 1)) * 15
            speak_edge(spoken_text, voice=edge_voice, rate_pct=rate_pct)
        else:
            rate = int(config.get("rate", 1))
            vol = int(config.get("volume", 100))
            voice_name = config.get("voice_name", "")
            speak_sapi(spoken_text, rate=rate, volume=vol, voice_name=voice_name)
        
        # Record spoken hash on successful playback
        try:
            LAST_SPOKEN_FILE.write_text(content_hash, encoding="utf-8")
        except Exception:
            pass
        logging.info("Speech playback completed successfully.")
    except Exception as e:
        logging.error(f"Speech error: {e}")

if __name__ == "__main__":
    main()
