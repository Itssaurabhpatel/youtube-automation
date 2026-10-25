# -*- coding: utf-8 -*-
import json
import math
import os
import re
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Royalty-free agriculture field background URLs
DEFAULT_BG_URLS = [
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1280&q=80", # golden farm
    "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1280&q=80", # green farm field
    "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?w=1280&q=80", # agriculture crop
]

def get_devanagari_font(size: int, bold: bool = True):
    """Finds available Hindi Devanagari font on Windows and Linux."""
    candidates = [
        # Linux (Ubuntu GitHub Actions runner)
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        # Windows
        "C:/Windows/Fonts/NirmalaB.ttf",
        "C:/Windows/Fonts/Nirmala.ttc",
        "C:/Windows/Fonts/mangalb.ttf",
        "C:/Windows/Fonts/mangal.ttf",
        "C:/Windows/Fonts/aparajb.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

def ensure_background_image(cache_dir: str) -> str:
    """Gets or downloads a high-res farm background image."""
    bg_local = os.path.join(cache_dir, "farm_bg.jpg")
    if os.path.exists(bg_local) and os.path.getsize(bg_local) > 10000:
        return bg_local

    for url in DEFAULT_BG_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r, open(bg_local, "wb") as f:
                f.write(r.read())
            if os.path.exists(bg_local) and os.path.getsize(bg_local) > 10000:
                return bg_local
        except Exception:
            continue

    # Procedural farm landscape fallback (earthy greens & golden sky)
    img = Image.new("RGB", (1280, 720), color=(34, 75, 45))
    draw = ImageDraw.Draw(img)
    # Sky gradient
    for y in range(300):
        c = (int(135 + y * 0.2), int(190 - y * 0.1), int(220 - y * 0.3))
        draw.line([(0, y), (1280, y)], fill=c)
    # Field
    for y in range(300, 720):
        factor = (y - 300) / 420
        c = (int(30 + factor * 20), int(90 - factor * 30), int(35 + factor * 10))
        draw.line([(0, y), (1280, y)], fill=c)
    img.save(bg_local)
    return bg_local

def draw_curved_arrow(draw: ImageDraw.ImageDraw, start: tuple, end: tuple, color=(255, 212, 0), outline=(0, 0, 0)):
    """Draws a bold curved arrow with outline."""
    sx, sy = start
    ex, ey = end
    # Draw thick line
    draw.line([(sx, sy), (sx + 80, sy + 40), (ex, ey)], fill=outline, width=14)
    draw.line([(sx, sy), (sx + 80, sy + 40), (ex, ey)], fill=color, width=8)
    # Arrow head
    draw.polygon([(ex, ey - 20), (ex + 30, ey), (ex, ey + 20)], fill=color, outline=outline)

def generate_style1_news(
    headline: str,
    subheadline: str,
    points: list,
    output_path: str,
    bg_image_path: str
):
    """
    STYLE 1: Bold Hindi agriculture news thumbnail (16:9, 1280x720).
    - Deep maroon-red top banner (#800000) with bold white Devanagari headline.
    - White subheadline banner with dark-red text.
    - 3 visual panels on lower half with white borders.
    """
    # 1. Base Farm Background
    if os.path.exists(bg_image_path):
        base = Image.open(bg_image_path).convert("RGB").resize((1280, 720))
    else:
        base = Image.new("RGB", (1280, 720), color=(30, 60, 40))

    # Darken lower portion slightly for high-contrast panels
    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    ov_draw.rectangle([0, 220, 1280, 720], fill=(0, 0, 0, 80))
    base = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(base)

    # 2. TOP BANNER: Deep Maroon-Red (#800000)
    maroon = (128, 0, 0)
    banner_height = 145
    draw.rectangle([0, 0, 1280, banner_height], fill=maroon)

    # Main Hindi Headline (Bold White)
    font_main = get_devanagari_font(48, bold=True)
    # Center text
    bbox = draw.textbbox((0, 0), headline, font=font_main)
    w_text = bbox[2] - bbox[0]
    tx = max(30, (1280 - w_text) // 2)
    ty = 30
    # Shadow + Text
    draw.text((tx + 2, ty + 2), headline, fill=(40, 0, 0), font=font_main)
    draw.text((tx, ty), headline, fill=(255, 255, 255), font=font_main)

    # 3. SUBHEADLINE BANNER: White Rectangle directly below main headline
    sub_y1 = 125
    sub_y2 = 185
    sub_font = get_devanagari_font(32, bold=True)
    sub_bbox = draw.textbbox((0, 0), subheadline, font=sub_font)
    sub_w = sub_bbox[2] - sub_bbox[0] + 60
    sub_x1 = max(40, (1280 - sub_w) // 2)
    sub_x2 = sub_x1 + sub_w
    draw.rectangle([sub_x1, sub_y1, sub_x2, sub_y2], fill=(255, 255, 255), outline=(128, 0, 0), width=2)
    draw.text((sub_x1 + 30, sub_y1 + 10), subheadline, fill=(128, 0, 0), font=sub_font)

    # 4. THREE VISUAL PANELS across the lower half
    panel_y = 235
    panel_w = 360
    panel_h = 440
    gap = 40
    start_x = (1280 - (3 * panel_w + 2 * gap)) // 2

    clean_points = (points + ["महत्वपूर्ण जानकारी", "विशेष सावधानियां", "सरकारी लाभ"])[:3]

    for i in range(3):
        px = start_x + i * (panel_w + gap)
        # Panel background card with blur/semi-dark
        draw.rounded_rectangle([px, panel_y, px + panel_w, panel_y + panel_h], radius=16, fill=(15, 30, 20, 220), outline=(255, 255, 255), width=4)

        # Big Question Mark or Number Badge
        qm_font = get_devanagari_font(120, bold=True)
        draw.text((px + panel_w // 2 - 35, panel_y + 110), "?", fill=(255, 255, 255, 230), font=qm_font)

        # Bottom Point Label Bar
        draw.rounded_rectangle([px + 10, panel_y + panel_h - 90, px + panel_w - 10, panel_y + panel_h - 15], radius=10, fill=(128, 0, 0))
        pt_font = get_devanagari_font(26, bold=True)
        pt_text = clean_points[i]
        pt_bbox = draw.textbbox((0, 0), pt_text, font=pt_font)
        pw = pt_bbox[2] - pt_bbox[0]
        draw.text((px + (panel_w - pw) // 2, panel_y + panel_h - 75), pt_text, fill=(255, 255, 255), font=pt_font)

    base.save(output_path, quality=95)
    print(f"[Thumbnail] Style 1 (News) generated: {output_path}")
    return output_path

def generate_style2_education(
    headline: str,
    secondary_headline: str,
    key_benefit: str,
    crop_name: str,
    output_path: str,
    bg_image_path: str
):
    """
    STYLE 2: High-contrast Hindi agriculture education & tips thumbnail (16:9, 1280x720).
    - Top banner: Bright yellow (#FFD400) with bold black Hindi headline.
    - Full-frame photorealistic lush green field background.
    - Curved yellow arrow pointing toward featured crop.
    - Inset crop photo on right with white border.
    - Bottom before/after comparison info cards.
    """
    # 1. Base Field Background
    if os.path.exists(bg_image_path):
        base = Image.open(bg_image_path).convert("RGB").resize((1280, 720))
    else:
        base = Image.new("RGB", (1280, 720), color=(25, 65, 35))

    draw = ImageDraw.Draw(base)

    # 2. TOP BANNER: Bright Yellow (#FFD400)
    yellow = (255, 212, 0)
    black = (0, 0, 0)
    banner_height = 145
    draw.rectangle([0, 0, 1280, banner_height], fill=yellow)

    # Headline text with separator: "[HEADLINE] | [SECONDARY]"
    combined_headline = f"{headline}  |  {secondary_headline}" if secondary_headline else headline
    font_main = get_devanagari_font(44, bold=True)
    bbox = draw.textbbox((0, 0), combined_headline, font=font_main)
    w_text = bbox[2] - bbox[0]
    tx = max(30, (1280 - w_text) // 2)
    draw.text((tx, 35), combined_headline, fill=black, font=font_main)

    # 3. RIGHT INSET CROP PHOTOGRAPH (with clean white border 5px)
    inset_x1, inset_y1 = 760, 185
    inset_x2, inset_y2 = 1220, 680
    # Crop closeup card
    draw.rounded_rectangle([inset_x1, inset_y1, inset_x2, inset_y2], radius=16, fill=(20, 50, 30), outline=(255, 255, 255), width=6)
    
    # Inner crop label
    crop_label = f"फसल: {crop_name or 'आधुनिक खेती'}"
    lbl_font = get_devanagari_font(32, bold=True)
    lbl_box = draw.textbbox((0, 0), crop_label, font=lbl_font)
    lw = lbl_box[2] - lbl_box[0]
    draw.rounded_rectangle([inset_x1 + 30, inset_y2 - 80, inset_x2 - 30, inset_y2 - 20], radius=10, fill=yellow, outline=black, width=2)
    draw.text((inset_x1 + (inset_x2 - inset_x1 - lw) // 2, inset_y2 - 70), crop_label, fill=black, font=lbl_font)

    # 4. LARGE CURVED YELLOW ARROW with black outline pointing toward crop
    draw_curved_arrow(draw, start=(560, 360), end=(740, 340), color=yellow, outline=black)

    # 5. KEY BENEFIT HIGHLIGHT BADGE (Left center)
    badge_x1, badge_y1 = 50, 190
    badge_x2, badge_y2 = 540, 320
    draw.rounded_rectangle([badge_x1, badge_y1, badge_x2, badge_y2], radius=16, fill=(0, 0, 0, 210), outline=yellow, width=4)
    ben_font = get_devanagari_font(34, bold=True)
    draw.text((badge_x1 + 25, badge_y1 + 20), "बड़ा फायदा / पैदावार:", fill=yellow, font=get_devanagari_font(24, bold=True))
    draw.text((badge_x1 + 25, badge_y1 + 65), key_benefit or "बंपर मुनाफा व कम लागत", fill=(255, 255, 255), font=ben_font)

    # 6. BOTTOM BEFORE/AFTER COMPARISON CARDS
    c1_x1, c1_y1, c1_x2, c1_y2 = 50, 370, 270, 680
    c2_x1, c2_y1, c2_x2, c2_y2 = 330, 370, 550, 680
    
    # Card 1: साधारण तरीका (Untreated)
    draw.rounded_rectangle([c1_x1, c1_y1, c1_x2, c1_y2], radius=14, fill=(245, 245, 245), outline=(150, 150, 150), width=3)
    draw.rectangle([c1_x1, c1_y1, c1_x2, c1_y1 + 50], fill=(180, 50, 50))
    draw.text((c1_x1 + 25, c1_y1 + 12), "पुराना तरीका", fill=(255, 255, 255), font=get_devanagari_font(24, bold=True))
    draw.text((c1_x1 + 25, c1_y1 + 140), "कम पैदावार\nज्यादा लागत", fill=(80, 80, 80), font=get_devanagari_font(26, bold=True))

    # Connecting Arrow between cards
    draw.line([(c1_x2 + 5, 520), (c2_x1 - 10, 520)], fill=black, width=8)
    draw.polygon([(c2_x1 - 10, 505), (c2_x1 + 5, 520), (c2_x1 - 10, 535)], fill=yellow, outline=black)

    # Card 2: नया तरीका (Treated / High yield)
    draw.rounded_rectangle([c2_x1, c2_y1, c2_x2, c2_y2], radius=14, fill=(255, 255, 255), outline=yellow, width=4)
    draw.rectangle([c2_x1, c2_y1, c2_x2, c2_y1 + 50], fill=(20, 120, 40))
    draw.text((c2_x1 + 30, c2_y1 + 12), "नया तरीका", fill=(255, 255, 255), font=get_devanagari_font(24, bold=True))
    draw.text((c2_x1 + 25, c2_y1 + 140), "बंपर पैदावार\n3 गुना मुनाफा", fill=(20, 100, 30), font=get_devanagari_font(26, bold=True))

    base.save(output_path, quality=95)
    print(f"[Thumbnail] Style 2 (Education) generated: {output_path}")
    return output_path

def generate_thumbnail_content_with_ai(topic_info: str) -> dict:
    """Uses Gemini / Grok / Claude to parse topic into structured thumbnail headlines."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                "You are an expert YouTube Thumbnail copywriter for Hindi Agriculture channel 'Kisan Badlega'. "
                f"Topic: {topic_info}\n\n"
                "Create high-CTR Hindi thumbnail text components. Return ONLY a JSON object:\n"
                "{\n"
                '  "style": "1 or 2 (choose 1 for news/government scheme/alert; choose 2 for farming tips/crop/variety/yield)",\n'
                '  "headline": "Bold punchy Hindi headline (max 5-6 words, e.g. गेहूं की ये 3 किस्में)",\n'
                '  "subheadline": "Urgent Hindi subheadline (max 6-8 words, e.g. 40 क्विंटल पैदावार गारंटी!)",\n'
                '  "points": ["पॉइंट 1", "पॉइंट 2", "पॉइंट 3"],\n'
                '  "crop_name": "Name of crop in Hindi (e.g. गेहूं, टमाटर, सरसों, धान)",\n'
                '  "key_benefit": "Key fact/benefit in Hindi (e.g. 80% तक सब्सिडी)"\n'
                "}"
            )
            resp = model.generate_content(prompt)
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", resp.text)
            raw = match.group(1).strip() if match else resp.text.strip()
            data = json.loads(raw)
            if "headline" in data:
                return data
        except Exception as e:
            print(f"[Thumbnail AI] AI error: {e}. Using smart fallback.")

    # Smart Rule-Based Fallback
    clean_topic = re.sub(r"Title:\s*", "", topic_info).split("\n")[0][:70]
    is_news = any(k in clean_topic.lower() for k in ["pm kisan", "योजना", "सब्सिडी", "तारीख", "किस्त", "सरकार", "न्यूज़"])
    return {
        "style": "1" if is_news else "2",
        "headline": clean_topic[:35] if clean_topic else "किसान भाइयों के लिए बड़ी खबर",
        "subheadline": "सीधे बैंक खाते में आएंगे पैसे!" if is_news else "कम लागत में बंपर मुनाफा!",
        "points": ["बड़ा फैसला", "सीधे खाते में", "आज ही करें"],
        "crop_name": "खेती-किसानी",
        "key_benefit": "दोगुना मुनाफा व सब्सिडी"
    }

def create_video_thumbnail(
    topic_or_title: str,
    output_path: str,
    preferred_style: str = "auto"
) -> str:
    """Master function to generate 1280x720 thumbnail based on the user's two exact styles."""
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    bg_image = ensure_background_image(out_dir)

    content = generate_thumbnail_content_with_ai(topic_or_title)
    style = preferred_style if preferred_style in ("1", "2") else str(content.get("style", "1"))

    print(f"[Thumbnail] Generating Thumbnail Style {style} for: '{content.get('headline')}'")

    if style == "2":
        return generate_style2_education(
            headline=content.get("headline", "आधुनिक खेती के गुर"),
            secondary_headline=content.get("subheadline", "3 गुना मुनाफा"),
            key_benefit=content.get("key_benefit", "कम लागत ज्यादा पैदावार"),
            crop_name=content.get("crop_name", "खेती"),
            output_path=output_path,
            bg_image_path=bg_image
        )
    else:
        return generate_style1_news(
            headline=content.get("headline", "किसान भाइयों के लिए बड़ी खबर"),
            subheadline=content.get("subheadline", "आज ही देखें पूरी जानकारी!"),
            points=content.get("points", ["महत्वपूर्ण फैसला", "सीधे खाते में", "तुरंत देखें"]),
            output_path=output_path,
            bg_image_path=bg_image
        )

if __name__ == "__main__":
    test_topic = "PM Kisan 24th installment release date and beneficiary list update"
    out1 = os.path.join(ROOT, "output", "test_thumb_style1.jpg")
    out2 = os.path.join(ROOT, "output", "test_thumb_style2.jpg")
    create_video_thumbnail(test_topic, out1, preferred_style="1")
    create_video_thumbnail(test_topic, out2, preferred_style="2")
