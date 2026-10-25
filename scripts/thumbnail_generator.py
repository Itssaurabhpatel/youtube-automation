# -*- coding: utf-8 -*-
import base64
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Curated High-Definition Agricultural Assets
DEFAULT_BG_URLS = [
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1280&q=80",
    "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1280&q=80",
    "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?w=1280&q=80",
]

CROP_PHOTOS = {
    "wheat": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600&q=80",
    "green_wheat": "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=600&q=80",
    "seeds": "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?w=600&q=80",
    "mustard": "https://images.unsplash.com/photo-1527842891421-42eec6e703ea?w=600&q=80",
    "tomato": "https://images.unsplash.com/photo-1592841200221-a6898f307baa?w=600&q=80",
    "tractor": "https://images.unsplash.com/photo-1592982537447-7440770cbfc9?w=600&q=80",
    "fertilizer": "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?w=600&q=80"
}

def get_crop_images(crop_name: str) -> tuple:
    cn = (crop_name or "").lower()
    if any(k in cn for k in ["टमाटर", "tomato"]):
        return (
            CROP_PHOTOS["tomato"],
            CROP_PHOTOS["seeds"],
            CROP_PHOTOS["tractor"]
        )
    elif any(k in cn for k in ["सरसों", "mustard"]):
        return (
            CROP_PHOTOS["mustard"],
            CROP_PHOTOS["seeds"],
            CROP_PHOTOS["tractor"]
        )
    else: # Default Wheat / general crops
        return (
            CROP_PHOTOS["wheat"],
            CROP_PHOTOS["green_wheat"],
            CROP_PHOTOS["seeds"]
        )

def get_devanagari_font(size: int, bold: bool = True):
    repo_font = os.path.join(ROOT, "assets", "fonts", "NotoSansDevanagari-Bold.ttf")
    candidates = [
        repo_font,
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/NirmalaB.ttf",
        "C:/Windows/Fonts/mangalb.ttf",
        "C:/Windows/Fonts/Nirmala.ttc",
        "C:/Windows/Fonts/mangal.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

def find_chrome_binary():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def render_html_to_image(html_content: str, output_image_path: str) -> bool:
    chrome_bin = find_chrome_binary()
    if not chrome_bin:
        print("[Thumbnail Engine] Chrome binary not found, falling back to Pillow.")
        return False

    temp_html = output_image_path + ".html"
    raw_temp = output_image_path + "_raw.jpg"
    try:
        with open(temp_html, "w", encoding="utf-8") as f:
            f.write(html_content)

        is_windows = os.name == "nt"
        w_size = "1295,815" if is_windows else "1280,720"

        cmd = [
            chrome_bin,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size={w_size}",
            f"--screenshot={raw_temp}",
            f"file:///{temp_html.replace(os.sep, '/')}"
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        if os.path.exists(raw_temp):
            im = Image.open(raw_temp)
            im = im.crop((0, 0, 1280, 720))
            im.save(output_image_path, quality=95)
            print(f"[Thumbnail Engine] Headless Chrome generated pixel-perfect thumbnail: {output_image_path}")
            return True
    except Exception as e:
        print(f"[Thumbnail Engine] Chrome headless error: {e}")
    finally:
        for p in (temp_html, raw_temp):
            if os.path.exists(p):
                try: os.remove(p)
                except Exception: pass
    return False

def get_style1_html(headline: str, subheadline: str, points: list, bg_url: str = None, p1_img: str = None, p2_img: str = None, p3_img: str = None) -> str:
    bg_url = bg_url or DEFAULT_BG_URLS[0]
    p1 = p1_img or CROP_PHOTOS["seeds"]
    p2 = p2_img or CROP_PHOTOS["green_wheat"]
    p3 = p3_img or CROP_PHOTOS["wheat"]
    pts = (points + ["बड़ा फैसला", "सीधे खाते में", "100% पक्का लाभ"])[:3]

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@800;900&family=Poppins:wght@900&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1280px; height: 720px; overflow: hidden;
    font-family: 'Noto Sans Devanagari', sans-serif;
    position: relative; background: #000;
  }}
  .bg {{
    position: absolute; top: 0; left: 0; width: 1280px; height: 720px;
    background-image: linear-gradient(rgba(0,0,0,0.15), rgba(0,0,0,0.65)), url('{bg_url}');
    background-size: cover; background-position: center;
  }}
  .header-maroon {{
    position: absolute; top: 0; left: 0; width: 100%; height: 130px;
    background: linear-gradient(180deg, #990000 0%, #680000 100%);
    border-bottom: 5px solid #FFD700;
    display: flex; justify-content: center; align-items: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.8); z-index: 10;
  }}
  .badge {{
    position: absolute; right: 25px; top: 12px;
    background: #000; color: #FFD700;
    font-family: 'Poppins', sans-serif; font-size: 15px; font-weight: 900;
    padding: 5px 14px; border-radius: 8px; border: 2px solid #FFD700;
    letter-spacing: 1px;
  }}
  .headline {{
    color: #FFFFFF; font-size: 48px; font-weight: 900;
    text-shadow: 3px 3px 0 #000, -3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000, 0 8px 20px rgba(0,0,0,0.9);
    margin-top: -6px; max-width: 960px; text-align: center;
  }}
  .subheadline-banner {{
    position: absolute; top: 105px; left: 50%; transform: translateX(-50%);
    background: #FFFFFF; color: #8B0000; font-size: 26px; font-weight: 900;
    padding: 7px 40px; border-radius: 10px; border: 4px solid #8B0000;
    box-shadow: 0 8px 25px rgba(0,0,0,0.85); z-index: 20; white-space: nowrap;
  }}
  .panels-container {{
    position: absolute; top: 168px; left: 35px; width: 1210px; height: 510px;
    display: flex; justify-content: space-between; z-index: 5;
  }}
  .panel {{
    width: 380px; height: 510px; border-radius: 18px; border: 6px solid #FFFFFF;
    overflow: hidden; position: relative; box-shadow: 0 12px 30px rgba(0,0,0,0.85);
    background-size: cover; background-position: center;
  }}
  .panel-tag {{
    position: absolute; top: 14px; left: 14px;
    background: #8B0000; color: #FFF; font-size: 19px; font-weight: 900;
    padding: 5px 14px; border-radius: 8px; border: 2px solid #FFD700;
    box-shadow: 0 4px 10px rgba(0,0,0,0.5);
  }}
  .panel-label {{
    position: absolute; bottom: 16px; left: 14px; right: 14px;
    background: linear-gradient(180deg, #8B0000 0%, #5a0000 100%);
    color: #FFEB3B; font-size: 24px; font-weight: 900;
    padding: 10px 8px; text-align: center; border-radius: 10px;
    border: 3px solid #FFFFFF; box-shadow: 0 6px 15px rgba(0,0,0,0.8);
    text-shadow: 2px 2px 4px #000;
  }}
</style>
</head>
<body>
  <div class="bg"></div>
  <div class="header-maroon">
    <div class="badge">🌾 KISAN BADLEGA</div>
    <div class="headline">{headline}</div>
  </div>
  <div class="subheadline-banner">{subheadline}</div>
  <div class="panels-container">
    <div class="panel" style="background-image: url('{p1}')">
      <div class="panel-tag">अपडेट 1</div>
      <div class="panel-label">{pts[0]}</div>
    </div>
    <div class="panel" style="background-image: url('{p2}')">
      <div class="panel-tag">अपडेट 2</div>
      <div class="panel-label">{pts[1]}</div>
    </div>
    <div class="panel" style="background-image: url('{p3}')">
      <div class="panel-tag">अपडेट 3</div>
      <div class="panel-label">{pts[2]}</div>
    </div>
  </div>
</body>
</html>
"""

def get_style2_html(headline: str, secondary_headline: str, key_benefit: str, crop_name: str, bg_url: str = None, crop_img: str = None) -> str:
    bg_url = bg_url or DEFAULT_BG_URLS[0]
    crop_img = crop_img or CROP_PHOTOS["wheat"]
    comb = f"{headline} &nbsp;|&nbsp; {secondary_headline}" if secondary_headline else headline

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@800;900&family=Poppins:wght@900&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1280px; height: 720px; overflow: hidden;
    font-family: 'Noto Sans Devanagari', sans-serif;
    position: relative; background: #000;
  }}
  .bg {{
    position: absolute; top: 0; left: 0; width: 1280px; height: 720px;
    background-image: linear-gradient(rgba(0,0,0,0.1), rgba(0,0,0,0.5)), url('{bg_url}');
    background-size: cover; background-position: center;
  }}
  .header-yellow {{
    position: absolute; top: 0; left: 0; width: 100%; height: 125px;
    background: #FFD400;
    border-bottom: 5px solid #000000;
    display: flex; justify-content: center; align-items: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.8); z-index: 10;
  }}
  .badge {{
    position: absolute; right: 25px; top: 12px;
    background: #000; color: #FFD400;
    font-family: 'Poppins', sans-serif; font-size: 15px; font-weight: 900;
    padding: 5px 14px; border-radius: 8px; border: 2px solid #000;
    letter-spacing: 1px;
  }}
  .headline {{
    color: #000000; font-size: 42px; font-weight: 900;
    margin-top: -4px; max-width: 900px; text-align: center;
    letter-spacing: -0.5px;
  }}
  .left-content {{
    position: absolute; top: 150px; left: 40px; width: 620px; height: 535px;
    display: flex; flex-direction: column; justify-content: space-between;
    z-index: 5;
  }}
  .benefit-card {{
    background: linear-gradient(180deg, #B71C1C 0%, #880E4F 100%);
    border: 4px solid #FFD400; border-radius: 16px;
    padding: 12px 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.7);
    color: #FFF;
  }}
  .benefit-card .sub-title {{
    color: #FFD400; font-size: 20px; font-weight: 900; margin-bottom: 4px;
  }}
  .benefit-card .main-val {{
    color: #FFF; font-size: 38px; font-weight: 900;
    text-shadow: 2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000;
  }}
  .comparison-row {{
    display: flex; align-items: center; justify-content: space-between;
    width: 100%; height: 360px; position: relative;
  }}
  .compare-card {{
    width: 280px; height: 360px; border-radius: 16px;
    overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.7);
    background: #FFF; display: flex; flex-direction: column;
  }}
  .compare-card.bad {{
    border: 4px solid #C62828;
  }}
  .compare-card.good {{
    border: 4px solid #2E7D32;
  }}
  .card-header-bad {{
    background: #C62828; color: #FFF; padding: 12px; text-align: center;
    font-size: 24px; font-weight: 900;
  }}
  .card-header-good {{
    background: #2E7D32; color: #FFF; padding: 12px; text-align: center;
    font-size: 24px; font-weight: 900;
  }}
  .card-body {{
    padding: 24px 18px; flex: 1; display: flex; flex-direction: column;
    justify-content: space-around;
  }}
  .card-body .item-bad {{
    color: #B71C1C; font-size: 25px; font-weight: 900; display: flex; align-items: center; gap: 8px;
  }}
  .card-body .item-good {{
    color: #1B5E20; font-size: 25px; font-weight: 900; display: flex; align-items: center; gap: 8px;
  }}
  .compare-arrow {{
    font-size: 34px; color: #000; font-weight: 900;
    background: #FFD400; border-radius: 50%; width: 50px; height: 50px;
    display: flex; align-items: center; justify-content: center;
    border: 3px solid #000; box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    z-index: 10;
  }}
  .right-inset {{
    position: absolute; top: 150px; right: 40px; width: 540px; height: 535px;
    border-radius: 20px; border: 6px solid #FFFFFF;
    overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.85);
    background-size: cover; background-position: center;
    background-image: url('{crop_img}');
    z-index: 5;
  }}
  .crop-pill {{
    position: absolute; bottom: 18px; left: 20px; right: 20px;
    background: #FFD400; color: #000;
    font-size: 26px; font-weight: 900; text-align: center;
    padding: 10px 18px; border-radius: 12px; border: 3px solid #000;
    box-shadow: 0 8px 20px rgba(0,0,0,0.7);
  }}
  .svg-arrow {{
    position: absolute;
    top: 320px;
    left: 565px;
    width: 200px;
    height: 120px;
    z-index: 15;
    filter: drop-shadow(0 6px 10px rgba(0,0,0,0.8));
    pointer-events: none;
  }}
</style>
</head>
<body>
  <div class="bg"></div>
  <div class="header-yellow">
    <div class="badge">🌾 KISAN BADLEGA</div>
    <div class="headline">{comb}</div>
  </div>
  <div class="left-content">
    <div class="benefit-card">
      <div class="sub-title">🔥 किसान भाइयों के लिए बड़ा फायदा:</div>
      <div class="main-val">{key_benefit}</div>
    </div>
    <div class="comparison-row">
      <div class="compare-card bad">
        <div class="card-header-bad">पुराना तरीका ❌</div>
        <div class="card-body">
          <div class="item-bad">❌ कम पैदावार</div>
          <div class="item-bad">❌ ज्यादा लागत</div>
          <div class="item-bad">❌ भारी नुकसान!</div>
        </div>
      </div>
      <div class="compare-arrow">➔</div>
      <div class="compare-card good">
        <div class="card-header-good">नया तरीका ✅</div>
        <div class="card-body">
          <div class="item-good">✅ 3x बंपर उपज</div>
          <div class="item-good">✅ 50% कम खर्च</div>
          <div class="item-good">✅ लाखों का मुनाफा!</div>
        </div>
      </div>
    </div>
  </div>
  <div class="right-inset">
    <div class="crop-pill">🌾 फसल: {crop_name}</div>
  </div>
  <svg class="svg-arrow" viewBox="0 0 200 120">
    <path d="M 20 100 Q 100 20 170 50" fill="none" stroke="#FFD400" stroke-width="16" stroke-linecap="round"/>
    <polygon points="195,58 160,35 165,70" fill="#FFD400" stroke="#000" stroke-width="2"/>
    <path d="M 20 100 Q 100 20 170 50" fill="none" stroke="#000" stroke-width="3" stroke-linecap="round"/>
  </svg>
</body>
</html>
"""

# Pillow Fallback Implementations
def generate_style1_pillow(headline: str, subheadline: str, points: list, output_path: str):
    im = Image.new("RGB", (1280, 720), (20, 50, 30))
    draw = ImageDraw.Draw(im)
    font_main = get_devanagari_font(50, bold=True)
    font_sub = get_devanagari_font(28, bold=True)
    font_pt = get_devanagari_font(24, bold=True)

    draw.rectangle([0, 0, 1280, 135], fill=(128, 0, 0))
    draw.line([(0, 135), (1280, 135)], fill=(255, 215, 0), width=5)
    
    # Headline
    draw.text((50, 30), headline, font=font_main, fill=(255, 255, 255))
    # Subheadline
    draw.rounded_rectangle([200, 105, 1080, 155], radius=10, fill=(255, 255, 255), outline=(128, 0, 0), width=3)
    draw.text((230, 112), subheadline, font=font_sub, fill=(128, 0, 0))

    # 3 Panels
    pts = (points + ["बड़ा फैसला", "सीधे खाते में", "100% पक्का लाभ"])[:3]
    for i in range(3):
        px = 40 + i * 410
        draw.rounded_rectangle([px, 175, px + 380, 680], radius=16, fill=(35, 75, 45), outline=(255, 255, 255), width=5)
        draw.rounded_rectangle([px + 15, 610, px + 365, 665], radius=10, fill=(128, 0, 0), outline=(255, 255, 255), width=3)
        draw.text((px + 25, 620), pts[i], font=font_pt, fill=(255, 235, 59))
    im.save(output_path, quality=95)
    return output_path

def generate_style2_pillow(headline: str, secondary_headline: str, key_benefit: str, crop_name: str, output_path: str):
    im = Image.new("RGB", (1280, 720), (20, 50, 30))
    draw = ImageDraw.Draw(im)
    font_main = get_devanagari_font(42, bold=True)
    font_sub = get_devanagari_font(26, bold=True)

    draw.rectangle([0, 0, 1280, 125], fill=(255, 212, 0))
    draw.line([(0, 125), (1280, 125)], fill=(0, 0, 0), width=5)
    comb = f"{headline} | {secondary_headline}" if secondary_headline else headline
    draw.text((40, 35), comb, font=font_main, fill=(0, 0, 0))

    draw.rounded_rectangle([40, 145, 650, 260], radius=14, fill=(180, 0, 0), outline=(255, 212, 0), width=4)
    draw.text((60, 160), "बड़ा फायदा:", font=font_sub, fill=(255, 212, 0))
    draw.text((60, 200), key_benefit, font=font_main, fill=(255, 255, 255))

    draw.rounded_rectangle([700, 145, 1240, 680], radius=18, fill=(30, 70, 40), outline=(255, 255, 255), width=5)
    draw.rounded_rectangle([720, 610, 1220, 665], radius=10, fill=(255, 212, 0), outline=(0, 0, 0), width=3)
    draw.text((740, 620), f"फसल: {crop_name}", font=font_sub, fill=(0, 0, 0))
    im.save(output_path, quality=95)
    return output_path

def generate_ai_thumbnail_with_imagen(prompt: str, output_path: str) -> bool:
    """Calls Google Imagen 3 API via GEMINI_API_KEY to generate photorealistic 16:9 YouTube thumbnails."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        return False

    models = ["imagen-3.0-generate-002", "imagegeneration@006", "imagegeneration@005"]
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "16:9",
                "outputMimeType": "image/jpeg"
            }
        }
        try:
            print(f"[Thumbnail AI] Requesting photorealistic thumbnail generation from {model}...")
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 200:
                data = r.json()
                predictions = data.get("predictions", [])
                if predictions and "bytesBase64Encoded" in predictions[0]:
                    with open(output_path, "wb") as f:
                        f.write(base64.b64decode(predictions[0]["bytesBase64Encoded"]))
                    print(f"[Thumbnail AI] Successfully generated 8K AI thumbnail with {model}: {output_path}")
                    return True
            else:
                print(f"[Thumbnail AI] {model} response: HTTP {r.status_code} ({r.text[:120]})")
        except Exception as e:
            print(f"[Thumbnail AI] Error with {model}: {e}")
    return False

def create_video_thumbnail(
    topic_or_title: str,
    output_path: str,
    preferred_style: str = "auto",
    ai_metadata: dict = None
) -> str:
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)

    meta = ai_metadata or {}
    headline = meta.get("thumb_headline") or meta.get("title", "") or topic_or_title or "किसान भाइयों के लिए बड़ी खुशखबरी!"
    subheadline = meta.get("thumb_subheadline") or "कम पानी में 40 क्विंटल पैदावार की गारंटी"
    points = meta.get("thumb_points") or ["किस्म 1: HD-3226", "किस्म 2: DBW-187", "किस्म 3: PBW-550"]
    crop_name = meta.get("crop_name") or "उन्नत गेहूं"
    benefit = meta.get("key_benefit") or "3 गुना पैदावार गारंटी!"

    clean_h = re.sub(r"[#\|].*", "", headline).strip()
    words = clean_h.split()
    if len(words) > 7:
        clean_h = " ".join(words[:7]) + "!"

    style = preferred_style
    if style not in ("1", "2"):
        is_news = any(k in (headline + subheadline).lower() for k in ["pm kisan", "योजना", "सब्सिडी", "किस्त", "सरकार", "न्यूज़", "तारीख", "फैसला", "अपडेट"])
        style = "1" if is_news else "2"

    print(f"[Thumbnail] Generating High-CTR Style {style} (Channel: Kisan Badlega)...")

    # 1. Primary: Try Google Imagen 3 API with GEMINI_API_KEY for 8K Photorealistic AI Image
    sec_h = meta.get("secondary_headline") or "1 गलती से 40% नुकसान!"
    if style == "1":
        pt_str = " | ".join(points[:3])
        imagen_prompt = (
            f"A professional, high-quality YouTube thumbnail in 16:9 aspect ratio (1280x720) for Indian agriculture channel 'Kisan Badlega'. "
            f"TOP HEADER: Deep maroon-red background (#800000) occupying top 25% with very large bold white Hindi Devanagari typography '{clean_h}'. "
            f"SUBHEADLINE: White rectangular banner directly below main headline with bold dark-red Hindi text '{subheadline}'. "
            f"BACKGROUND: Realistic high-resolution agricultural farm photograph of lush healthy {crop_name} field under natural warm sunlight with cinematic depth. "
            f"THREE VISUAL PANELS: Three equal-sized rectangular panels horizontally across the lower half with clean white borders showing {crop_name} seeds, healthy green plant, and modern farming equipment with red bottom labels. "
            f"VISUAL STYLE: Bold Hindi news-thumbnail aesthetic, high contrast, dramatic lighting, 16:9 aspect ratio, 1280x720, photorealistic."
        )
    else:
        imagen_prompt = (
            f"A visually striking, professional YouTube thumbnail in 16:9 aspect ratio (1280x720) for Indian agriculture channel 'Kisan Badlega'. "
            f"TOP BANNER: Bright yellow background (#FFD400) occupying top 25% with large bold black Hindi headline '{clean_h} | {sec_h}'. "
            f"MAIN BACKGROUND: Full-frame photorealistic image of healthy lush agricultural field of {crop_name} under bright morning sunlight with flowing water. "
            f"MAIN VISUAL: A photographic crop inset card on right side with clean thick white border showing macro close-up of healthy {crop_name} ears. "
            f"ARROW: Large curved 3D yellow arrow with black outline pointing toward the crop inset. "
            f"BOTTOM GRAPHIC: Two comparison cards near bottom left: 'पुराना तरीका (कम पैदावार)' with red border vs 'नया तरीका (3 गुना बंपर मुनाफा)' with green border connected by an arrow. "
            f"VISUAL STYLE: High-contrast Hindi farming tips YouTube thumbnail, photorealistic, 16:9 aspect ratio, 1280x720."
        )

    if generate_ai_thumbnail_with_imagen(imagen_prompt, output_path):
        return output_path

    # 2. Fallback: Pixel-perfect Headless Chrome Engine
    p1, p2, p3 = get_crop_images(crop_name)
    if style == "1":
        html_code = get_style1_html(clean_h, subheadline, points, p1_img=p1, p2_img=p2, p3_img=p3)
        if render_html_to_image(html_code, output_path):
            return output_path
        return generate_style1_pillow(clean_h, subheadline, points, output_path)
    else:
        html_code = get_style2_html(clean_h, sec_h, benefit, crop_name, crop_img=p1)
        if render_html_to_image(html_code, output_path):
            return output_path
        return generate_style2_pillow(clean_h, sec_h, benefit, crop_name, output_path)

if __name__ == "__main__":
    test_out = os.path.join(ROOT, "output_thumb_test.jpg")
    create_video_thumbnail("गेहूं की खेती", test_out, preferred_style="1")
    print("Generated:", test_out)
