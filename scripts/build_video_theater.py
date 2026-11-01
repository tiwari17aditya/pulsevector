#!/usr/bin/env python3
"""
Builds an interactive Video Theater HTML application for the 10 famous YouTube channel
end-credit video scenes, embedding base64 MP4 videos and poster previews.
"""

import json
import base64
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT_DIR / "samples" / "End_Credits_Videos"
BRAIN_DIR = Path(r"C:\Users\Admin\.gemini\antigravity\brain\273fb3c7-db9f-4dd2-8fc1-c5e8928665dc")
ARTIFACT_PATH = BRAIN_DIR / "outro_video_theater.html"

CHANNELS_DATA = [
    {
        "id": "mrbeast",
        "number": 1,
        "channel": "MrBeast",
        "title": "Hype Studio & Bell Shockwave",
        "duration": "8.5s",
        "audio": "Electro Cabello + 1760Hz Chime",
        "fps": "30 fps",
        "mechanics": "Maximum urgency. High-impact Bangers typography, neon pulse borders, massive Subscribe slam button, and oversized golden bell tower with radiating soundwave shockwaves.",
        "bestFor": "Daily Briefings, Viral Milestones, Brain Teasers",
        "mp4": "outro_mrbeast.mp4",
        "poster": "outro_mrbeast_poster.jpeg",
    },
    {
        "id": "vox",
        "number": 2,
        "channel": "Vox",
        "title": "Kinetic Motion Graphics Split",
        "duration": "8.0s",
        "audio": "Clean Soul (Minimalist Grooves)",
        "fps": "30 fps",
        "mechanics": "Editorial sophistication. Sliding interactive card containers ('Watch Next' + 'Series Playlist'), clean Roboto typography, smooth tech cursor glide, and central avatar.",
        "bestFor": "Weekly Masterclasses, Topic Deep-Dives, Documentary Briefs",
        "mp4": "outro_vox.mp4",
        "poster": "outro_vox_poster.jpeg",
    },
    {
        "id": "veritasium",
        "number": 3,
        "channel": "Veritasium",
        "title": "Curiosity Question Loop Magnet",
        "duration": "8.5s",
        "audio": "Decisions (Reflective Acoustic)",
        "fps": "30 fps",
        "mechanics": "Algorithm comment loop. Poses a high-yield 'Question of the Day' with a 24-hour pinned comment community spotlight challenge.",
        "bestFor": "Daily Current Affairs, Analytical Debates, Brain Teasers",
        "mp4": "outro_veritasium.mp4",
        "poster": "outro_veritasium_poster.jpeg",
    },
    {
        "id": "kurzgesagt",
        "number": 4,
        "channel": "Kurzgesagt (In a Nutshell)",
        "title": "Stellar Cosmic Space Flat-Art",
        "duration": "8.0s",
        "audio": "Carefree (Upbeat Cosmic Strings)",
        "fps": "30 fps",
        "mechanics": "Playful aesthetic wonder. Twinkling vector starfield, wobbling ringed planet, candy squash-and-stretch buttons, and existential curiosity hook.",
        "bestFor": "Science, Defense, Space Technology, Environment Specials",
        "mp4": "outro_kurzgesagt.mp4",
        "poster": "outro_kurzgesagt_poster.jpeg",
    },
    {
        "id": "mkbhd",
        "number": 5,
        "channel": "MKBHD",
        "title": "Matte Obsidian Tech Studio",
        "duration": "7.5s",
        "audio": "Urban Gauntlet (Crisp Hip-Hop Beats)",
        "fps": "30 fps",
        "mechanics": "Uncompromising tech authority. Matte black cyber backdrop, horizontal speed lines, crisp red pill button, and subtle mechanical cursor recoil.",
        "bestFor": "Science & Tech Briefings, AI/Cybersecurity dossiers",
        "mp4": "outro_mkbhd.mp4",
        "poster": "outro_mkbhd_poster.jpeg",
    },
    {
        "id": "aliabdaal",
        "number": 6,
        "channel": "Ali Abdaal",
        "title": "Productivity Ecosystem Glassmorphism",
        "duration": "8.0s",
        "audio": "Bossa Antigua (Chill Lo-Fi Jazz)",
        "fps": "30 fps",
        "mechanics": "Multi-channel funnel conversion. Three balanced glass cards directing aspirants to YouTube Masterclasses, Telegram 1-Page PDFs, and 24/7 Discord Study Rooms.",
        "bestFor": "Exam Preparation series, Weekend Compilations, Capsule Guides",
        "mp4": "outro_aliabdaal.mp4",
        "poster": "outro_aliabdaal_poster.jpeg",
    },
    {
        "id": "thinkschool",
        "number": 7,
        "channel": "Think School",
        "title": "Indian Masterclass Resource Hub",
        "duration": "8.5s",
        "audio": "Clear Waters (Acoustic Clarity)",
        "fps": "30 fps",
        "mechanics": "Educational structure. Prominent top study capsule banner, syllabus lecture card with play button, and Telegram community counter (35,000+ aspirants).",
        "bestFor": "UPSC / State PSC Civil Services, High-Yield Daily Current Affairs",
        "mp4": "outro_thinkschool.mp4",
        "poster": "outro_thinkschool_poster.jpeg",
    },
    {
        "id": "oversimplified",
        "number": 8,
        "channel": "OverSimplified",
        "title": "Cartoon Dialogue & Hall of Fame",
        "duration": "8.0s",
        "audio": "Monkeys Spinning Monkeys (Comedic Pizzicato)",
        "fps": "30 fps",
        "mechanics": "Extreme humor & gamification. Animated cartoon glove cursor, comic speech bubbles, yesterday's challenge winner spotlight, and community tab poll callout.",
        "bestFor": "Daily Brain Teasers, Weekend History & Current Affairs Quizzes",
        "mp4": "outro_oversimplified.mp4",
        "poster": "outro_oversimplified_poster.jpeg",
    },
    {
        "id": "caspian",
        "number": 9,
        "channel": "CaspianReport",
        "title": "Tactical Geopolitical Radar HUD",
        "duration": "8.0s",
        "audio": "Constance (Suspenseful Tactical Ambient)",
        "fps": "30 fps",
        "mechanics": "Intelligence gravitas. Glowing green tactical HUD grid, 360-degree rotating radar sweep line targeting global energy corridors, and tactical video container.",
        "bestFor": "Geopolitics, International Treaties, Maritime Corridors",
        "mp4": "outro_caspian.mp4",
        "poster": "outro_caspian_poster.jpeg",
    },
    {
        "id": "lemmino",
        "number": 10,
        "channel": "Lemmino",
        "title": "Cinematic Ambient Waveform",
        "duration": "9.0s",
        "audio": "Shores of Avalon (Deep Synth Drone)",
        "fps": "30 fps",
        "mechanics": "Hypnotic visual immersion. Undulating audio frequency spectrum bars, minimal chapter progression portals ('Previous Chapter' / 'Next Chapter'), and atmospheric fade-out.",
        "bestFor": "Documentary Mini-Series, Chronological Case Studies",
        "mp4": "outro_lemmino.mp4",
        "poster": "outro_lemmino_poster.jpeg",
    },
]

def load_media_base64():
    media = {}
    for ch in CHANNELS_DATA:
        media[ch["id"]] = {}
        # Video
        vpath = VIDEOS_DIR / ch["mp4"]
        if vpath.exists():
            with open(vpath, "rb") as f:
                media[ch["id"]]["video"] = f"data:video/mp4;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        # Poster
        ppath = VIDEOS_DIR / ch["poster"]
        if ppath.exists():
            with open(ppath, "rb") as f:
                media[ch["id"]]["poster"] = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    return media

def build():
    media = load_media_base64()
    channels_json = json.dumps(CHANNELS_DATA)
    media_json = json.dumps(media)

    html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pulse Vector — Famous Channels Outro Video Theater</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    .theater-shadow {{
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.9), 0 0 0 1px rgba(255, 255, 255, 0.08);
    }}
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: rgba(15, 23, 42, 0.6);
    }}
    ::-webkit-scrollbar-thumb {{
      background: rgba(56, 189, 248, 0.4);
      border-radius: 9999px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: rgba(56, 189, 248, 0.8);
    }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased overflow-x-hidden selection:bg-cyan-500 selection:text-slate-950">

  <!-- Header -->
  <header class="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 py-3 shadow-lg">
    <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center font-black text-white text-base shadow-md shadow-cyan-500/20">
          PV
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <h1 class="text-base font-bold tracking-tight text-white">PULSE VECTOR</h1>
            <span class="px-2 py-0.5 text-[11px] font-semibold bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 rounded-full">Video Theater v2.9</span>
          </div>
          <p class="text-xs text-slate-400">10 Animated YouTube End-Credit Videos (LDoE Engine Reference)</p>
        </div>
      </div>
      <div class="flex items-center space-x-3 text-xs font-mono text-slate-400">
        <span class="px-2.5 py-1 bg-slate-800 text-slate-300 rounded-lg border border-slate-700">1080p60 • Native Audio + SFX</span>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 py-6 space-y-6">

    <!-- Cinema Stage Arena -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      
      <!-- Video Player Viewport (8 Cols) -->
      <div class="lg:col-span-8 flex flex-col items-center bg-slate-900/60 p-4 md:p-6 rounded-3xl border border-slate-800/80 relative overflow-hidden">
        
        <!-- Ambience -->
        <div class="absolute -top-20 -left-20 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -bottom-20 -right-20 w-72 h-72 bg-red-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <!-- The Video Screen Container -->
        <div class="w-full bg-black rounded-2xl overflow-hidden theater-shadow border border-slate-700/60 relative aspect-video flex items-center justify-center">
          <video id="player-video" controls autoplay loop class="w-full h-full object-contain">
            <source id="video-source" src="" type="video/mp4">
            Your browser does not support HTML5 video.
          </video>
        </div>

        <!-- Video Player Quick Controls Bar -->
        <div class="w-full mt-4 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
          <div class="flex items-center space-x-2">
            <button onclick="navVideo(-1)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-200 rounded-lg font-medium transition">← Prev Video</button>
            <span id="player-indicator" class="font-mono text-cyan-400 px-2">Video 1 of 10</span>
            <button onclick="navVideo(1)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-200 rounded-lg font-medium transition">Next Video →</button>
          </div>
          <div class="flex items-center space-x-3">
            <span id="player-audio-badge" class="px-2.5 py-1 bg-slate-800/80 text-yellow-300 font-mono text-[11px] rounded border border-slate-700">Audio: Electro Cabello</span>
            <button onclick="restartVideo()" class="px-3 py-1.5 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 rounded-lg font-medium">Replay ↺</button>
          </div>
        </div>

      </div>

      <!-- Specification Dossier (4 Cols) -->
      <div class="lg:col-span-4 space-y-4">
        <div class="bg-slate-900/80 rounded-2xl p-5 border border-slate-800 shadow-md">
          <div class="flex items-center justify-between mb-2">
            <span id="card-badge" class="px-2 py-0.5 rounded bg-red-950 text-red-400 font-mono text-xs font-bold border border-red-800">MRBEAST ARCHETYPE</span>
            <span id="card-duration" class="px-2 py-0.5 rounded text-xs font-mono bg-slate-800 text-slate-300">8.5 Seconds</span>
          </div>

          <h2 id="card-title" class="text-xl font-bold text-white tracking-tight leading-snug">MrBeast Hype Studio</h2>
          <p id="card-sub" class="text-xs text-cyan-400 font-medium mb-3">Giant Bell Shockwave & Button Pops</p>

          <div class="space-y-3 text-xs border-t border-slate-800/80 pt-3">
            <div>
              <span class="text-slate-400 font-semibold block mb-0.5">Algorithm Conversion Mechanics:</span>
              <p id="card-mech" class="text-slate-300 leading-relaxed">Maximum urgency. High-impact Bangers typography, neon pulse borders, massive Subscribe slam button, and oversized golden bell tower with radiating soundwave shockwaves.</p>
            </div>
            <div>
              <span class="text-slate-400 font-semibold block mb-0.5">Best Format For Pulse Vector:</span>
              <p id="card-best" class="text-slate-200">Daily Briefings, Viral Milestones, Brain Teasers</p>
            </div>
            <div>
              <span class="text-slate-400 font-semibold block mb-0.5">Sound Design & Chimes:</span>
              <p id="card-sound" class="font-mono text-yellow-300">Electro Cabello + 1760Hz Chime</p>
            </div>
          </div>

          <div class="mt-5 pt-4 border-t border-slate-800">
            <button onclick="selectWinner()" class="w-full py-2.5 px-4 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-bold rounded-xl shadow-md transition flex items-center justify-center space-x-2">
              <span>⭐ Select This Channel As Primary Outro</span>
            </button>
          </div>
        </div>

        <!-- LDoE Architecture Verification -->
        <div class="bg-gradient-to-br from-slate-900 to-slate-950 rounded-2xl p-4 border border-slate-800/80 text-xs space-y-2">
          <h3 class="font-bold text-slate-300 flex items-center space-x-1.5">
            <span>🛡️</span><span>LastDayOnEarth Reference Mechanics</span>
          </h3>
          <ul class="text-slate-400 space-y-1.5 leading-relaxed">
            <li class="flex items-start space-x-1.5">
              <span class="text-emerald-400 font-bold">✓</span>
              <span>Dynamic button squash/stretch scaling (<code class="text-cyan-400">scale = 1.0 + 0.18 * sin(...)</code>).</span>
            </li>
            <li class="flex items-start space-x-1.5">
              <span class="text-emerald-400 font-bold">✓</span>
              <span>Smooth sinusoidal cursor & cartoon glove movement trajectory.</span>
            </li>
            <li class="flex items-start space-x-1.5">
              <span class="text-emerald-400 font-bold">✓</span>
              <span>Synchronized high-pitch bell chime SFX mixed seamlessly with background audio.</span>
            </li>
          </ul>
        </div>

      </div>

    </div>

    <!-- 10 Channel Video Selector Grid -->
    <section class="space-y-3">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400">Select Channel Archetype (10 Video Clips)</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3" id="channel-grid">
        <!-- Rendered dynamically -->
      </div>
    </section>

  </main>

  <script>
    const CHANNELS = {channels_json};
    const MEDIA = {media_json};
    let currentIdx = 0;

    function init() {{
      renderGrid();
      playVideo(0);
    }}

    function renderGrid() {{
      const container = document.getElementById('channel-grid');
      container.innerHTML = '';
      CHANNELS.forEach((ch, idx) => {{
        const card = document.createElement('div');
        card.id = `grid-card-${{idx}}`;
        card.className = `p-2.5 rounded-xl border cursor-pointer transition-all flex flex-col justify-between group ${{
          idx === 0 ? 'bg-slate-800 border-cyan-500 shadow-md ring-1 ring-cyan-500' : 'bg-slate-900/70 border-slate-800 hover:bg-slate-800'
        }}`;
        card.onclick = () => playVideo(idx);

        const posterSrc = MEDIA[ch.id] ? MEDIA[ch.id].poster : '';
        card.innerHTML = `
          <div class="relative w-full aspect-video rounded-lg overflow-hidden bg-black mb-2">
            <img src="${{posterSrc}}" alt="${{ch.channel}}" class="w-full h-full object-cover group-hover:scale-105 transition-transform">
            <span class="absolute bottom-1 right-1 px-1.5 py-0.5 bg-black/80 text-[10px] font-mono text-white rounded">${{ch.duration}}</span>
          </div>
          <div>
            <div class="flex items-center justify-between text-[11px] font-semibold text-white">
              <span class="truncate">${{ch.channel}}</span>
              <span class="text-cyan-400 font-mono">#${{ch.number}}</span>
            </div>
            <p class="text-[10px] text-slate-400 truncate mt-0.5">${{ch.title}}</p>
          </div>
        `;
        container.appendChild(card);
      }});
    }}

    function playVideo(idx) {{
      currentIdx = idx;
      const ch = CHANNELS[idx];
      const videoEl = document.getElementById('player-video');
      const videoSrc = MEDIA[ch.id] ? MEDIA[ch.id].video : '';

      videoEl.src = videoSrc;
      videoEl.load();
      videoEl.play().catch(e => console.log('Autoplay deferred', e));

      // Update grid selection highlights
      CHANNELS.forEach((_, i) => {{
        const c = document.getElementById(`grid-card-${{i}}`);
        if (c) {{
          if (i === idx) {{
            c.className = 'p-2.5 rounded-xl border cursor-pointer transition-all flex flex-col justify-between group bg-slate-800 border-cyan-500 shadow-md ring-1 ring-cyan-500';
          }} else {{
            c.className = 'p-2.5 rounded-xl border cursor-pointer transition-all flex flex-col justify-between group bg-slate-900/70 border-slate-800 hover:bg-slate-800';
          }}
        }}
      }});

      // Update Dossier
      document.getElementById('card-badge').textContent = `${{ch.channel.toUpperCase()}} ARCHETYPE`;
      document.getElementById('card-duration').textContent = `${{ch.duration}} @ ${{ch.fps}}`;
      document.getElementById('card-title').textContent = `${{ch.channel}}: ${{ch.title}}`;
      document.getElementById('card-sub').textContent = ch.mechanics.split('.')[0] + '.';
      document.getElementById('card-mech').textContent = ch.mechanics;
      document.getElementById('card-best').textContent = ch.bestFor;
      document.getElementById('card-sound').textContent = ch.audio;
      document.getElementById('player-indicator').textContent = `Video ${{ch.number}} of 10 (${{ch.channel}})`;
      document.getElementById('player-audio-badge').textContent = `Audio: ${{ch.audio.split('(')[0]}}`;
    }}

    function navVideo(dir) {{
      let n = currentIdx + dir;
      if (n < 0) n = CHANNELS.length - 1;
      if (n >= CHANNELS.length) n = 0;
      playVideo(n);
    }}

    function restartVideo() {{
      const v = document.getElementById('player-video');
      v.currentTime = 0;
      v.play();
    }}

    function selectWinner() {{
      const ch = CHANNELS[currentIdx];
      alert(`Selected Style: ${{ch.channel}} (${{ch.title}})! Tell the AI assistant you choose #${{ch.number}} ${{ch.channel}} to set it as the default video outro.`);
    }}

    window.onload = init;
  </script>
</body>
</html>
"""

    with open(ARTIFACT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Wrote video theater to: {ARTIFACT_PATH}")

if __name__ == "__main__":
    build()
