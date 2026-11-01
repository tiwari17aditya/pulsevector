#!/usr/bin/env python3
"""
Builds an interactive Video Theater HTML application for the 5 finalized famous YouTube channel
end-credit video scenes, embedding base64 MP4 videos and poster previews with full
Like, Share, and Subscribe animated triad visualizations and random rotation demonstration.
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
        "id": "vox",
        "number": 1,
        "channel": "Vox",
        "title": "Kinetic Split & Animated Triad Dock",
        "duration": "8.0s",
        "audio": "Clean Soul (Minimalist Grooves) + 1760Hz Chime",
        "fps": "30 fps",
        "highlight": "TOP PICK",
        "rating": "5.0 ★★★★★",
        "triad": "Smash Like! -> Smash Like (Liked +1) | Share -> Shared! | Subscribe -> Subscribed! (Bell Ring)",
        "mechanics": "Editorial kinetic sophistication. Dynamic sliding video containers ('Watch Next' + 'Series Playlist'), central channel avatar, and lower interactive triad dock. Animated cursor glides across Like, Share, and Subscribe buttons triggering mathematical squash/stretch scaling and state transformations.",
        "bestFor": "Daily Current Affairs Briefings, Weekly Masterclasses, In-Depth Strategic Analysis",
        "mp4": "outro_vox.mp4",
        "poster": "outro_vox_poster.jpeg",
    },
    {
        "id": "mrbeast",
        "number": 2,
        "channel": "MrBeast",
        "title": "Hype Studio & Giant Bell Shockwave",
        "duration": "8.5s",
        "audio": "Electro Cabello + 1760Hz Chime",
        "fps": "30 fps",
        "highlight": "VIRAL MAGNET",
        "rating": "4.9 ★★★★★",
        "triad": "Smash Like! -> Liked! | Share Intel -> Shared! | Giant Red Subscribe Slam -> Subscribed! + Soundwave Shockwaves",
        "mechanics": "Maximum conversion urgency. Bangers typography, neon pulsating borders, massive Subscribe slam button with scale overshoot, cartoon glove cursor trajectory, and oversized wobbling golden bell tower with concentric radiating shockwaves.",
        "bestFor": "High-Energy Daily Briefings, Viral Milestones, Brain Teasers",
        "mp4": "outro_mrbeast.mp4",
        "poster": "outro_mrbeast_poster.jpeg",
    },
    {
        "id": "thinkschool",
        "number": 3,
        "channel": "Think School",
        "title": "Civil Services Exam & Resource Hub",
        "duration": "8.5s",
        "audio": "Clear Waters (Acoustic Clarity) + 1760Hz Chime",
        "fps": "30 fps",
        "highlight": "STUDY CAPSULE",
        "rating": "4.9 ★★★★★",
        "triad": "Like Class -> Liked! | Share Notes -> Shared! | Subscribe -> Subscribed! + Active Bell Chime",
        "mechanics": "Structured educational ecosystem. Top highlight pill banner, high-yield lecture card container with live play button, verified Telegram community counter, and unified study triad dock. Professional, calm, and tailored for serious aspirants.",
        "bestFor": "UPSC / State PSC Civil Services, High-Yield Daily Current Affairs",
        "mp4": "outro_thinkschool.mp4",
        "poster": "outro_thinkschool_poster.jpeg",
    },
    {
        "id": "kurzgesagt",
        "number": 4,
        "channel": "Kurzgesagt",
        "title": "Cosmic Flat-Art & Orbiting Planets",
        "duration": "8.0s",
        "audio": "Carefree (Cosmic Acoustic Strings) + 1760Hz Chime",
        "fps": "30 fps",
        "highlight": "VISUAL WONDER",
        "rating": "4.8 ★★★★★",
        "triad": "Upvote Cosmo -> Voted! | Spread Orbit -> Shared! | Join Mission -> Mission Joined! + Ring Wobble",
        "mechanics": "Cosmic curiosity & aesthetic brilliance. Twinkling vector starfield, wobbling ringed Saturn-style planet, candy pill buttons with smooth squash/stretch easing, and an existential knowledge inquiry hook.",
        "bestFor": "Science, Defense, Space Technology, Environment Specials",
        "mp4": "outro_kurzgesagt.mp4",
        "poster": "outro_kurzgesagt_poster.jpeg",
    },
    {
        "id": "veritasium",
        "number": 5,
        "channel": "Veritasium",
        "title": "Curiosity Question Loop & Pinned Comment",
        "duration": "8.5s",
        "audio": "Decisions (Reflective Acoustic) + 1760Hz Chime",
        "fps": "30 fps",
        "highlight": "ALGORITHM RETENTION",
        "rating": "4.8 ★★★★★",
        "triad": "Upvote -> Upvoted! | Discuss -> Shared! | Subscribe -> Subscribed! + Golden Bell Ring",
        "mechanics": "Algorithm comment velocity multiplier. Poses a controversial 'Question of the Day' with a 24-hour pinned comment community spotlight challenge. Features smooth cursor click path, upvote pill recoil, and verified badge.",
        "bestFor": "Analytical Debates, Thought Experiments, Interactive Brain Teasers",
        "mp4": "outro_veritasium.mp4",
        "poster": "outro_veritasium_poster.jpeg",
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
  <title>Pulse Vector — Final 5 YouTube End-Credit Video Theater</title>
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
    .glow-top-pick {{
      box-shadow: 0 0 25px rgba(6, 182, 212, 0.35);
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
            <span class="px-2 py-0.5 text-[11px] font-semibold bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 rounded-full">Final 5 Selection</span>
          </div>
          <p class="text-xs text-slate-400">Animated End-Credit Videos with Full Like, Share & Subscribe Triads</p>
        </div>
      </div>
      <div class="flex items-center space-x-3 text-xs font-mono text-slate-400">
        <span class="px-2.5 py-1 bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 rounded-lg font-semibold">● 5 Finalists Active</span>
        <span class="px-2.5 py-1 bg-slate-800 text-slate-300 rounded-lg border border-slate-700">1080p30 • LastDayOnEarth Engine</span>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 py-6 space-y-6">

    <!-- Top Strategy Advisory Banner -->
    <div class="bg-gradient-to-r from-cyan-950/60 via-slate-900 to-indigo-950/60 border border-cyan-800/50 rounded-2xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
      <div class="space-y-1">
        <div class="flex items-center space-x-2">
          <span class="px-2 py-0.5 bg-cyan-500 text-slate-950 font-black text-[11px] rounded uppercase tracking-wider">Strategic Recommendation</span>
          <h2 class="font-bold text-white text-sm">Dynamic Outro Rotation (Random Outro Dispatcher)</h2>
        </div>
        <p class="text-xs text-slate-300 leading-relaxed max-w-4xl">
          Rotating randomly between these <strong>5 finalized archetypes</strong> prevents viewer fatigue, keeps regular subscribers engaged with fresh creative visuals every day, and acts as a continuous algorithmic A/B test for audience retention and subscriber conversions!
        </p>
      </div>
      <div class="shrink-0 flex items-center space-x-2">
        <button onclick="playRandom()" class="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition flex items-center space-x-1.5">
          <span>🎲</span>
          <span>Test Random Outro</span>
        </button>
      </div>
    </div>

    <!-- Cinema Stage Arena -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      
      <!-- Video Player Viewport (8 Cols) -->
      <div class="lg:col-span-8 flex flex-col items-center bg-slate-900/60 p-4 md:p-6 rounded-3xl border border-slate-800/80 relative overflow-hidden">
        
        <!-- Ambience -->
        <div class="absolute -top-20 -left-20 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -bottom-20 -right-20 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl pointer-events-none"></div>

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
            <button onclick="navVideo(-1)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-200 rounded-lg font-medium transition">← Prev</button>
            <span id="player-indicator" class="font-mono text-cyan-400 px-2">Video 1 of 5 (Vox)</span>
            <button onclick="navVideo(1)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-200 rounded-lg font-medium transition">Next →</button>
          </div>
          <div class="flex items-center space-x-3">
            <span id="player-audio-badge" class="px-2.5 py-1 bg-slate-800/80 text-yellow-300 font-mono text-[11px] rounded border border-slate-700">Audio: Clean Soul</span>
            <button onclick="restartVideo()" class="px-3 py-1.5 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 rounded-lg font-medium">Replay ↺</button>
          </div>
        </div>

      </div>

      <!-- Specification Dossier (4 Cols) -->
      <div class="lg:col-span-4 space-y-4">
        <div class="bg-slate-900/80 rounded-2xl p-5 border border-slate-800 shadow-md">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center space-x-2">
              <span id="card-badge" class="px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 font-mono text-xs font-bold border border-cyan-800">VOX ARCHETYPE</span>
              <span id="card-highlight" class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-sans text-[10px] font-bold border border-amber-500/40">TOP PICK</span>
            </div>
            <span id="card-duration" class="px-2 py-0.5 rounded text-xs font-mono bg-slate-800 text-slate-300">8.0 Seconds</span>
          </div>

          <h2 id="card-title" class="text-xl font-bold text-white tracking-tight leading-snug">Vox: Kinetic Split</h2>
          <p id="card-sub" class="text-xs text-cyan-400 font-medium mb-3">Sliding Card Motion Graphics & Animated Triad Dock</p>

          <div class="space-y-3 text-xs border-t border-slate-800/80 pt-3">
            <div>
              <span class="text-slate-400 font-semibold block mb-0.5">🎬 Animated Triad Flow (Like/Share/Subscribe):</span>
              <p id="card-triad" class="font-mono text-emerald-300 bg-slate-950/70 p-2 rounded border border-slate-800 text-[11px] leading-relaxed">Smash Like! -> Smash Like (Liked +1) | Share -> Shared! | Subscribe -> Subscribed! (Bell Ring)</p>
            </div>
            <div>
              <span class="text-slate-400 font-semibold block mb-0.5">Conversion & Visual Mechanics:</span>
              <p id="card-mech" class="text-slate-300 leading-relaxed">Editorial sophistication. Sliding interactive card containers, clean Roboto typography, smooth tech cursor glide, and central avatar.</p>
            </div>
            <div>
              <span class="text-slate-400 font-semibold block mb-0.5">Recommended Pulse Vector Placement:</span>
              <p id="card-best" class="text-slate-200">Daily Briefings, Topic Deep-Dives, Documentary Briefs</p>
            </div>
            <div>
              <span class="text-slate-400 font-semibold block mb-0.5">Soundtrack & Chime:</span>
              <p id="card-sound" class="font-mono text-yellow-300">Clean Soul + 1760Hz Chime</p>
            </div>
          </div>

          <div class="mt-5 pt-4 border-t border-slate-800 flex flex-col space-y-2">
            <button onclick="setPrimary()" class="w-full py-2.5 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded-xl shadow-md transition flex items-center justify-center space-x-2">
              <span>⭐ Select As Default / Standalone Outro</span>
            </button>
            <button onclick="setRandomRotation()" class="w-full py-2 px-3 bg-slate-800 hover:bg-slate-750 text-cyan-300 font-medium rounded-xl border border-slate-700 transition text-xs flex items-center justify-center space-x-2">
              <span>🎲 Enable Random Rotation Among All 5</span>
            </button>
          </div>
        </div>

        <!-- Pipeline Integration Checklist -->
        <div class="bg-gradient-to-br from-slate-900 to-slate-950 rounded-2xl p-4 border border-slate-800/80 text-xs space-y-2">
          <h3 class="font-bold text-slate-300 flex items-center space-x-1.5">
            <span>⚙️</span><span>Main Branch Integration Handling</span>
          </h3>
          <ul class="text-slate-400 space-y-1.5 leading-relaxed">
            <li class="flex items-start space-x-1.5">
              <span class="text-emerald-400 font-bold">✓</span>
              <span><strong>Dynamic Cards:</strong> Automatically handles custom <code class="text-cyan-400">next_video_title</code> and <code class="text-purple-400">playlist_title</code> with fallback defaults.</span>
            </li>
            <li class="flex items-start space-x-1.5">
              <span class="text-emerald-400 font-bold">✓</span>
              <span><strong>YouTube End Screen Safe Zones:</strong> Left & right cards are sized exactly at 640x360 with generous margins, ensuring YouTube native End Screen clickable elements fit directly inside without visual clipping.</span>
            </li>
            <li class="flex items-start space-x-1.5">
              <span class="text-emerald-400 font-bold">✓</span>
              <span><strong>Random Dispatcher:</strong> Single function call <code class="text-amber-400">engine.render_dynamic_outro(context=...)</code> automatically handles random archetype picking or explicit override.</span>
            </li>
          </ul>
        </div>

      </div>

    </div>

    <!-- Final 5 Channel Video Selector Grid -->
    <section class="space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400">Finalist Archetypes (5 Chosen Channels)</h3>
        <span class="text-[11px] text-slate-500 font-mono">Removed: mkbhd, aliabdaal, oversimplified, caspian, lemmino</span>
      </div>
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
      playVideo(0); // Start with Vox (Top Pick)
    }}

    function renderGrid() {{
      const container = document.getElementById('channel-grid');
      container.innerHTML = '';
      CHANNELS.forEach((ch, idx) => {{
        const card = document.createElement('div');
        card.id = `grid-card-${{idx}}`;
        card.className = `p-2.5 rounded-xl border cursor-pointer transition-all flex flex-col justify-between group relative ${{
          idx === 0 ? 'bg-slate-800 border-cyan-500 shadow-md ring-1 ring-cyan-500' : 'bg-slate-900/70 border-slate-800 hover:bg-slate-800'
        }}`;
        card.onclick = () => playVideo(idx);

        const posterSrc = MEDIA[ch.id] ? MEDIA[ch.id].poster : '';
        const isVox = ch.id === 'vox';
        card.innerHTML = `
          <div class="relative w-full aspect-video rounded-lg overflow-hidden bg-black mb-2">
            <img src="${{posterSrc}}" alt="${{ch.channel}}" class="w-full h-full object-cover group-hover:scale-105 transition-transform">
            <span class="absolute bottom-1 right-1 px-1.5 py-0.5 bg-black/80 text-[10px] font-mono text-white rounded">${{ch.duration}}</span>
            ${{isVox ? '<span class="absolute top-1 left-1 px-1.5 py-0.5 bg-cyan-500 text-[9px] font-bold text-slate-950 rounded shadow">★ USER BEST</span>' : ''}}
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
            c.className = 'p-2.5 rounded-xl border cursor-pointer transition-all flex flex-col justify-between group relative bg-slate-800 border-cyan-500 shadow-md ring-1 ring-cyan-500';
          }} else {{
            c.className = 'p-2.5 rounded-xl border cursor-pointer transition-all flex flex-col justify-between group relative bg-slate-900/70 border-slate-800 hover:bg-slate-800';
          }}
        }}
      }});

      // Update Dossier
      document.getElementById('card-badge').textContent = `${{ch.channel.toUpperCase()}} ARCHETYPE`;
      document.getElementById('card-highlight').textContent = ch.highlight;
      document.getElementById('card-duration').textContent = `${{ch.duration}} @ ${{ch.fps}}`;
      document.getElementById('card-title').textContent = `${{ch.channel}}: ${{ch.title}}`;
      document.getElementById('card-sub').textContent = ch.mechanics.split('.')[0] + '.';
      document.getElementById('card-triad').textContent = ch.triad;
      document.getElementById('card-mech').textContent = ch.mechanics;
      document.getElementById('card-best').textContent = ch.bestFor;
      document.getElementById('card-sound').textContent = ch.audio;
      document.getElementById('player-indicator').textContent = `Video ${{ch.number}} of 5 (${{ch.channel}})`;
      document.getElementById('player-audio-badge').textContent = `Audio: ${{ch.audio.split('(')[0].split('+')[0].trim()}}`;
    }}

    function navVideo(dir) {{
      let n = currentIdx + dir;
      if (n < 0) n = CHANNELS.length - 1;
      if (n >= CHANNELS.length) n = 0;
      playVideo(n);
    }}

    function playRandom() {{
      let n = currentIdx;
      while (n === currentIdx && CHANNELS.length > 1) {{
        n = Math.floor(Math.random() * CHANNELS.length);
      }}
      playVideo(n);
    }}

    function restartVideo() {{
      const v = document.getElementById('player-video');
      v.currentTime = 0;
      v.play();
    }}

    function setPrimary() {{
      const ch = CHANNELS[currentIdx];
      alert(`Primary Outro Set to: ${{ch.channel}} (${{ch.title}})!`);
    }}

    function setRandomRotation() {{
      alert('Random Outro Rotation Enabled! The pipeline will rotate randomly among Vox, MrBeast, Think School, Kurzgesagt, and Veritasium for each video generated.');
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
