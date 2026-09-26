"""
Pulse Vector / Antigravity Voice Assistant CLI
Quick management of speech speed, voice engine, and toggle state.
Usage:
  python .agent/voice_assistant/voice_cli.py --status
  python .agent/voice_assistant/voice_cli.py --speed 2      # (-10 to 10)
  python .agent/voice_assistant/voice_cli.py --voice Zira   # (David, Zira, etc.)
  python .agent/voice_assistant/voice_cli.py --engine sapi  # (sapi or edge-tts)
  python .agent/voice_assistant/voice_cli.py --on
  python .agent/voice_assistant/voice_cli.py --off
  python .agent/voice_assistant/voice_cli.py --test "Hello! Antigravity voice is active."
"""

import sys
import json
import argparse
import pathlib

# Reconfigure stdout/stderr for Windows console unicode safety
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "voice_config.json"

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"enabled": True, "rate": 1, "volume": 100, "max_words": 150, "engine": "sapi", "voice_name": ""}

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Antigravity Voice Assistant Configuration")
    parser.add_argument("--status", action="store_true", help="Show current voice configuration")
    parser.add_argument("--on", action="store_true", help="Enable voice assistant")
    parser.add_argument("--off", action="store_true", help="Disable voice assistant")
    parser.add_argument("--speed", type=int, help="Set speech rate (-10 slowest, 0 normal, 1-3 fast)")
    parser.add_argument("--max-words", type=int, help="Maximum spoken words per turn")
    parser.add_argument("--voice", type=str, help="Voice name keyword (e.g. David, Zira)")
    parser.add_argument("--engine", choices=["sapi", "edge-tts"], help="Speech engine")
    parser.add_argument("--test", type=str, nargs="?", const="Hello! Antigravity text-to-speech is active and working.", help="Test speech output")

    args = parser.parse_args()
    cfg = load_config()

    updated = False
    if args.on:
        cfg["enabled"] = True
        updated = True
        print("🔊 Voice Assistant: ENABLED")
    elif args.off:
        cfg["enabled"] = False
        updated = True
        print("🔇 Voice Assistant: DISABLED")

    if args.speed is not None:
        cfg["rate"] = max(-10, min(10, args.speed))
        updated = True
        print(f"⚡ Speech Speed set to: {cfg['rate']}")

    if args.max_words is not None:
        cfg["max_words"] = args.max_words
        updated = True
        print(f"📝 Max spoken words set to: {cfg['max_words']}")

    if args.voice is not None:
        cfg["voice_name"] = args.voice
        updated = True
        print(f"🗣️ Voice set to: '{cfg['voice_name']}'")

    if args.engine is not None:
        cfg["engine"] = args.engine
        updated = True
        print(f"⚙️ Engine set to: {cfg['engine']}")

    if updated:
        save_config(cfg)

    if args.status or (not updated and not args.test):
        print("\n=== Antigravity Voice Assistant Status ===")
        print(f"  Enabled:     {cfg.get('enabled')}")
        print(f"  Engine:      {cfg.get('engine')}")
        print(f"  Speed (Rate):{cfg.get('rate')} (-10 to 10)")
        print(f"  Volume:      {cfg.get('volume')}%")
        print(f"  Max Words:   {cfg.get('max_words')}")
        print(f"  Voice:       {cfg.get('voice_name') or 'Default'}")
        print("==========================================\n")

    if args.test:
        from speak_response import speak_sapi, speak_edge
        print(f"🔊 Testing speech: '{args.test}'")
        if cfg.get("engine") == "edge-tts":
            speak_edge(args.test, rate_pct=cfg.get("rate", 1) * 15)
        else:
            speak_sapi(args.test, rate=cfg.get("rate", 1), volume=cfg.get("volume", 100), voice_name=cfg.get("voice_name", ""))
        print("✅ Test playback complete.")

if __name__ == "__main__":
    main()
