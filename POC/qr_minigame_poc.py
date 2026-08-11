import os
import sys
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.config import ARCHIVE_DIR
from src.core.image_utils import ensure_fonts
from src.core.video_utils import create_base_background_with_glow, draw_watermark_on_image

def generate_qr_code_image(data_url, size=150):
    print(f"Downloading QR Code from api.qrserver.com for: {data_url}...")
    api_url = f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={requests.utils.quote(data_url)}"
    try:
        response = requests.get(api_url, timeout=10)
        if response.ok:
            return Image.open(BytesIO(response.content)).convert("RGBA")
        else:
            print(f"❌ Failed to download QR code. HTTP status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching QR code from API: {e}")
        return None

def create_countdown_bell_ring(draw, cx, cy, radius, progress, text, font_timer):
    # Base circle
    draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], outline=(255, 255, 255, 30), width=8)
    # Animated arc
    angle = int(360 * progress)
    draw.arc([(cx - radius, cy - radius), (cx + radius, cy + radius)], start=-90, end=-90 + angle, fill=(56, 189, 248), width=8)

def draw_text_centered(draw, text, cx, cy, font, text_color=(255, 255, 255)):
    # Draw text centered on cx, cy
    w = font.getlength(text)
    # Get approximate height from font size
    h = font.size if hasattr(font, 'size') else 20
    draw.text((cx - w/2, cy - h/2), text, fill=text_color, font=font)

def main():
    scratch_dir = os.path.join(PROJECT_ROOT, "scratch")
    os.makedirs(scratch_dir, exist_ok=True)
    
    # 1. Setup paths and targets
    W_canvas, H_canvas = 1080, 1920
    challenge_id = "25jul26"
    game_url = f"https://tiwari17aditya.github.io/pulsevector/play/?challenge={challenge_id}"
    
    print("🚀 Starting QR Code Overlay POC...")
    
    # Get a sample brain teaser image card from July archive
    sample_card_path = os.path.join(
        ARCHIVE_DIR, "2026", "July", "Brain_Teasers", "Images", f"brainteaser-{challenge_id}_styled.png"
    )
    
    if not os.path.exists(sample_card_path):
        print(f"⚠️ Warning: Sample image card '{sample_card_path}' not found.")
        print("Creating a placeholder square card instead...")
        # Create a placeholder card
        card_img = Image.new("RGBA", (656, 656), (15, 23, 42, 230))
        card_draw = ImageDraw.Draw(card_img)
        card_draw.rectangle([(0,0), (655, 655)], outline=(255, 255, 255, 40), width=3)
        card_draw.text((100, 300), "[ MOCK PUZZLE CARD ]\n(Please run slide generation first)", fill=(255,255,255,180))
    else:
        print(f"📂 Found sample image card at: {sample_card_path}")
        card_img = Image.open(sample_card_path).convert("RGBA")

    # 2. Get the QR code
    qr_img = generate_qr_code_image(game_url, size=150)
    if not qr_img:
        print("Creating placeholder QR Code...")
        # Make a placeholder white square with black text
        qr_img = Image.new("RGBA", (150, 150), (255, 255, 255, 255))
        qr_draw = ImageDraw.Draw(qr_img)
        qr_draw.rectangle([(0,0),(149,149)], fill=None, outline=(0,0,0,255), width=4)
        qr_draw.text((25, 65), "[ MOCK QR ]", fill=(0,0,0,255))

    # 3. Create canvas and draw base background
    print("🎨 Rendering mock video frame...")
    frame_img = create_base_background_with_glow(W_canvas, H_canvas, t=0.5)
    
    # Draw Watermark
    font_regular_path, font_bold_path = ensure_fonts(ARCHIVE_DIR)
    draw_watermark_on_image(frame_img, font_bold_path)
    
    # Paste main puzzle card in the center
    card_x = (W_canvas - 656) // 2
    card_y = (H_canvas - 656) // 2
    frame_img.paste(card_img, (card_x, card_y), card_img)
    
    # 4. Draw texts and bottom elements
    draw = ImageDraw.Draw(frame_img)
    font_title = ImageFont.truetype(str(font_bold_path), 54)
    font_subtitle = ImageFont.truetype(str(font_regular_path), 32)
    font_timer = ImageFont.truetype(str(font_bold_path), 48)
    font_qr_label = ImageFont.truetype(str(font_bold_path), 20)
    
    # Title
    draw_text_centered(draw, "DAILY BRAIN TEASER", W_canvas/2, 450, font_title, text_color=(251, 191, 36))
    draw_text_centered(draw, "Can you solve this puzzle?", W_canvas/2, 530, font_subtitle, text_color=(229, 231, 235))
    
    # Bottom Layout: Timer in Center, QR Code on Right
    cx_timer, cy_timer = W_canvas/2, 1480
    create_countdown_bell_ring(draw, cx_timer, cy_timer, radius=65, progress=0.75, text="8", font_timer=font_timer)
    draw_text_centered(draw, "8", cx_timer, cy_timer, font_timer, text_color=(255, 255, 255))
    draw_text_centered(draw, "Seconds left to think...", W_canvas/2, 1610, font_subtitle, text_color=(156, 163, 175))
    
    # Paste QR Code on the right side
    qr_x, qr_y = 820, 1405
    frame_img.paste(qr_img, (qr_x, qr_y), qr_img)
    
    # Draw label above QR Code
    qr_label_cx = qr_x + 75
    qr_label_cy = qr_y - 25
    # Rounded badge behind the label for legibility
    draw.rounded_rectangle(
        [(qr_x - 10, qr_y - 40), (qr_x + 160, qr_y - 10)], 
        radius=8, 
        fill=(15, 23, 42, 220), 
        outline=(255, 255, 255, 30), 
        width=1
    )
    draw_text_centered(draw, "Scan to Play! 📲", qr_label_cx, qr_label_cy, font_qr_label, text_color=(56, 189, 248))
    
    # 5. Save the preview image
    preview_path = os.path.join(scratch_dir, "qr_timer_preview.png")
    frame_img.convert("RGB").save(preview_path, "PNG")
    
    print(f"✅ Success! Mock video frame saved to: {preview_path}")
    print("Scan the QR code in the image with your phone to test the routing!")

if __name__ == "__main__":
    main()
