"""
Generates a standalone, responsive, interactive HTML branding showcase with embedded base64 graphics.
Features the new 2026 Cinematic & 3D Rendered Banner and Avatar assets.
"""

import base64
import json
import pathlib
import shutil

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
BRANDING_DIR = pathlib.Path(__file__).resolve().parent
BANNERS_DIR = BRANDING_DIR / "assets" / "banners"
ICONS_DIR = BRANDING_DIR / "assets" / "icons"
DETAILS_FILE = BRANDING_DIR / "channel_details.json"
ARTIFACT_DIR = pathlib.Path(r"C:\Users\Admin\.gemini\antigravity\brain\273fb3c7-db9f-4dd2-8fc1-c5e8928665dc")

def to_b64(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def main():
    with open(DETAILS_FILE, "r", encoding="utf-8") as f:
        details = json.load(f)

    b64_banner_multi = to_b64(BANNERS_DIR / "banner_cinematic_multigenre_master.png")
    b64_banner_editorial = to_b64(BANNERS_DIR / "banner_cinematic_editorial_master.png")
    b64_banner_safe = to_b64(BANNERS_DIR / "banner_safe_zone_preview.png")

    b64_icon_3d = to_b64(ICONS_DIR / "icon_pulse_vector_3d_master.png")
    b64_icon_crop = to_b64(ICONS_DIR / "icon_circle_crop_preview.png")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pulse Vector — Cinematic YouTube Branding Suite</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg-dark: #070A13;
    --card-bg: #0F172A;
    --card-border: #1E293B;
    --accent-cyan: #00F0FF;
    --accent-gold: #FFB800;
    --accent-green: #10B981;
    --text-main: #F8FAFC;
    --text-muted: #94A3B8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: var(--bg-dark);
    color: var(--text-main);
    padding: 32px 20px;
    line-height: 1.6;
  }}
  .container {{ max-width: 1300px; margin: 0 auto; }}
  
  header {{
    text-align: center;
    margin-bottom: 40px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--card-border);
  }}
  .badge-live {{
    display: inline-block;
    padding: 6px 14px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid var(--accent-green);
    color: var(--accent-green);
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 12px;
    letter-spacing: 0.5px;
  }}
  h1 {{
    font-size: 38px;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #FFF, var(--accent-cyan));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
  }}
  .tagline {{ font-size: 18px; color: var(--accent-gold); font-weight: 600; }}
  
  .links-row {{
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-top: 20px;
    flex-wrap: wrap;
  }}
  .btn {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 14px;
    text-decoration: none;
    transition: all 0.2s ease;
  }}
  .btn-primary {{
    background: var(--accent-cyan);
    color: #0A0E1A;
  }}
  .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 0 20px rgba(0, 240, 255, 0.4); }}
  .btn-secondary {{
    background: #1E293B;
    color: var(--text-main);
    border: 1px solid #334155;
  }}
  .btn-secondary:hover {{ background: #334155; }}

  /* Pillars Grid */
  .section-title {{
    font-size: 24px;
    font-weight: 700;
    margin: 40px 0 20px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .pillars-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
  }}
  .pillar-card {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 20px;
    transition: border-color 0.2s;
  }}
  .pillar-card:hover {{ border-color: var(--accent-cyan); }}
  .pillar-icon {{ font-size: 28px; margin-bottom: 10px; }}
  .pillar-name {{ font-size: 16px; font-weight: 700; color: #FFF; margin-bottom: 6px; }}
  .pillar-desc {{ font-size: 13px; color: var(--text-muted); line-height: 1.5; }}
  .pillar-cadence {{
    margin-top: 10px;
    font-size: 11px;
    font-weight: 700;
    color: var(--accent-gold);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  /* Visual Preview Cards */
  .preview-card {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 32px;
  }}
  .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    flex-wrap: wrap;
    gap: 10px;
  }}
  .card-title {{ font-size: 18px; font-weight: 700; color: #FFF; }}
  .card-badge {{
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    background: rgba(0, 240, 255, 0.1);
    color: var(--accent-cyan);
    border: 1px solid rgba(0, 240, 255, 0.3);
  }}
  .image-wrapper {{
    width: 100%;
    border-radius: 10px;
    overflow: hidden;
    background: #000;
    border: 1px solid #1E293B;
  }}
  .image-wrapper img {{
    width: 100%;
    height: auto;
    display: block;
  }}

  /* Icons Section */
  .icon-showcase-box {{
    display: flex;
    gap: 32px;
    align-items: center;
    flex-wrap: wrap;
    background: #090D1A;
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
  }}
  .icon-large-preview {{
    width: 220px;
    height: 220px;
    border-radius: 50%;
    border: 4px solid var(--accent-cyan);
    box-shadow: 0 0 32px rgba(0, 240, 255, 0.35);
    display: block;
  }}
  .icon-details {{
    flex: 1;
    min-width: 280px;
  }}
  .icon-details h3 {{ font-size: 22px; color: #FFF; margin-bottom: 8px; }}
  .icon-details p {{ font-size: 14px; color: var(--text-muted); margin-bottom: 12px; line-height: 1.6; }}
  .spec-tag {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    background: #1E293B;
    color: var(--accent-gold);
    margin-right: 8px;
    font-weight: 600;
  }}

  /* Metadata Box */
  .metadata-box {{
    background: #040711;
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: #E2E8F0;
    white-space: pre-wrap;
    max-height: 380px;
    overflow-y: auto;
  }}
</style>
</head>
<body>
<div class="container">

  <header>
    <div class="badge-live">● LIVE CHANNEL METADATA UPDATED</div>
    <h1>Pulse Vector — Unified Channel Branding Suite</h1>
    <p class="tagline">{details['tagline']}</p>
    <div class="links-row">
      <a href="https://youtube.com/@pulse_vector" target="_blank" class="btn btn-primary">
        ▶ View Live YouTube Channel
      </a>
      <a href="https://studio.youtube.com/channel/{details['channel_id']}/editing/profile" target="_blank" class="btn btn-secondary">
        ⚙️ YouTube Studio Profile Customizer
      </a>
    </div>
  </header>

  <!-- Core Content Pillars -->
  <div class="section-title">🔥 Multi-Genre Content Pillars (All Projects Unified)</div>
  <div class="pillars-grid">
"""
    for p in details["pillars"]:
        html_content += f"""
    <div class="pillar-card">
      <div class="pillar-icon">{p['emoji']}</div>
      <div class="pillar-name">{p['name']}</div>
      <div class="pillar-desc">{p['description']}</div>
      <div class="pillar-cadence">{p['cadence']}</div>
    </div>
"""

    html_content += f"""
  </div>

  <!-- Primary Banner Section -->
  <div class="section-title">🖼️ YouTube Channel Banners (2560 x 1440 px Cinematic Composites)</div>

  <!-- Banner 1: Cinematic Multi-Genre Master Banner -->
  <div class="preview-card">
    <div class="card-header">
      <div class="card-title">1. Master Multi-Genre Cinematic Banner (RECOMMENDED)</div>
      <div class="card-badge">2560 x 1440 • 1546x423 Safe Zone • Photorealistic Art</div>
    </div>
    <div class="image-wrapper">
      <img src="data:image/png;base64,{b64_banner_multi}" alt="Master Multi-Genre Cinematic Banner">
    </div>
  </div>

  <!-- Safe Zone Preview -->
  <div class="preview-card">
    <div class="card-header">
      <div class="card-title">Universal Safe-Zone Verification Overlay</div>
      <div class="card-badge">TV (2560x1440) • Desktop (2560x423) • Mobile (1546x423)</div>
    </div>
    <div class="image-wrapper">
      <img src="data:image/png;base64,{b64_banner_safe}" alt="Safe Zone Preview">
    </div>
  </div>

  <!-- Banner 2: Editorial Geopolitical Intelligence -->
  <div class="preview-card">
    <div class="card-header">
      <div class="card-title">2. Editorial Geopolitical Intelligence Banner (Alternative Concept)</div>
      <div class="card-badge">Holographic Map • Orbital Telemetry • Vox/Wendover Aesthetic</div>
    </div>
    <div class="image-wrapper">
      <img src="data:image/png;base64,{b64_banner_editorial}" alt="Editorial Geopolitical Banner">
    </div>
  </div>

  <!-- Channel Icons / Avatars -->
  <div class="section-title">👤 YouTube Profile Avatar / Channel Icon (3D Titanium & Gold)</div>
  <div class="icon-showcase-box">
    <img src="data:image/png;base64,{b64_icon_3d}" alt="3D Titanium Pulse Vector Emblem" class="icon-large-preview">
    <div class="icon-details">
      <h3>3D Titanium & Gold Pulse Vector Emblem</h3>
      <p>Precision 3D rendered beveled titanium-and-gold geometric 'V' symbol with a glowing neon-cyan cardiogram/pulse energy beam cutting through its center. Mounted on dark brushed carbon-fiber with ancient Dharma geometry and tactical hex grip markings.</p>
      <div>
        <span class="spec-tag">1024 x 1024 Master</span>
        <span class="spec-tag">800 x 800 YouTube Spec</span>
        <span class="spec-tag">Volumetric Lighting</span>
        <span class="spec-tag">Brushed Metal Texture</span>
      </div>
    </div>
  </div>

  <!-- Circular Crop Verification -->
  <div class="preview-card">
    <div class="card-header">
      <div class="card-title">Avatar Circular Crop Verification (Mobile App & Dark/Light Mode)</div>
      <div class="card-badge">100% Corner-Safe</div>
    </div>
    <div class="image-wrapper">
      <img src="data:image/png;base64,{b64_icon_crop}" alt="Circular Crop Preview">
    </div>
  </div>

  <!-- Live Metadata Section -->
  <div class="section-title">📝 Live Updated YouTube Description & Keywords</div>
  <div class="preview-card">
    <div class="card-header">
      <div class="card-title">Active Description (973 Characters — Live on YouTube)</div>
      <div class="card-badge">Max: 1000 chars</div>
    </div>
    <div class="metadata-box">{details['description']}</div>
  </div>

  <div class="preview-card">
    <div class="card-header">
      <div class="card-title">Active Channel Keywords (Live on YouTube)</div>
      <div class="card-badge">YouTube SEO Indexed</div>
    </div>
    <div class="metadata-box">{details['keywords_string']}</div>
  </div>

</div>
</body>
</html>
"""

    out_file = BRANDING_DIR / "preview_branding.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated standalone branding showcase: {out_file} ({out_file.stat().st_size // 1024} KB)")

    if ARTIFACT_DIR.exists():
        dest = ARTIFACT_DIR / "channel_branding_showcase.html"
        shutil.copy2(out_file, dest)
        print(f"Copied to artifact dir: {dest}")

if __name__ == "__main__":
    main()
