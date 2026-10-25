# -*- coding: utf-8 -*-
import json
import math
import os
import re
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_BG_URLS = [
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1280&q=80",
    "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1280&q=80",
    "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?w=1280&q=80",
]

def get_devanagari_font(size: int, bold: bool = True):
    """Finds highest quality Devanagari font available."""
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/mangalb.ttf",
        "C:/Windows/Fonts/NirmalaB.ttf",
        "C:/Windows/Fonts/Nirmala.ttc",
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

def get_enhanced_farm_bg(cache_dir: str) -> Image.Image:
    """Gets and color-enhances a photorealistic agricultural background (1280x720)."""
    bg_local = os.path.join(cache_dir, "farm_bg_vibrant.jpg")
    base_img = None
    
    if os.path.exists(bg_local) and os.path.getsize(bg_local) > 10000:
        base_img = Image.open(bg_local).convert("RGB")
    else:
        for url in DEFAULT_BG_URLS:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    raw_data = r.read()
                temp_p = os.path.join(cache_dir, "raw_bg.jpg")
                with open(temp_p, "wb") as f:
                    f.write(raw_data)
                base_img = Image.open(temp_p).convert("RGB")
                break
            except Exception:
                continue

    if not base_img:
        base_img = Image.new("RGB", (1280, 720), color=(25, 60, 35))

    base_img = base_img.resize((1280, 720))
    # Boost saturation and contrast for cinematic YouTube look
    enhancer = ImageEnhance.Color(base_img)
    base_img = enhancer.enhance(1.45)
    contrast = ImageEnhance.Contrast(base_img)
    base_img = contrast.enhance(1.2)
    base_img.save(bg_local, quality=95)
    return base_img

def draw_text_with_effects(
    draw: ImageDraw.ImageDraw,
    pos: tuple,
    text: str,
    font: ImageFont.ImageFont,
    fill_color: tuple = (255, 235, 59),
    stroke_color: tuple = (0, 0, 0),
    stroke_w: int = 6,
    shadow_offset: tuple = (4, 4),
    shadow_color: tuple = (0, 0, 0)
):
    """Draws high-impact 3D stroked text with drop shadow."""
    x, y = pos
    sx, sy = shadow_offset
    # Shadow
    draw.text((x + sx, y + sy), text, font=font, fill=shadow_color, stroke_width=stroke_w, stroke_fill=shadow_color)
    # Foreground with stroke
    draw.text((x, y), text, font=font, fill=fill_color, stroke_width=stroke_w, stroke_fill=stroke_color)

def generate_style1_news(
    headline: str,
    subheadline: str,
    points: list,
    output_path: str,
    cache_dir: str
):
    """
    STYLE 1: High-CTR Bold Hindi Agriculture News Thumbnail (16:9, 1280x720).
    - Deep Maroon-Red (#800000) top header with bold golden-yellow/white typography.
    - White subheadline banner with dark-red bold text.
    - 3 prominent visual cards on lower half with white borders (4px).
    - Channel branding badge.
    """
    base = get_enhanced_farm_bg(cache_dir)
    draw = ImageDraw.Draw(base)

    # 1. TOP HEADER: Deep Maroon-Red (#800000 / #8B0000)
    maroon = (139, 0, 0)
    gold = (255, 215, 0)
    header_h = 160
    draw.rectangle([0, 0, 1280, header_h], fill=maroon)
    # Glowing golden separator line
    draw.line([(0, header_h), (1280, header_h)], fill=gold, width=6)

    # Channel Stamp in top-right
    stamp_font = get_devanagari_font(20, bold=True)
    draw.rounded_rectangle([1060, 12, 1260, 42], radius=6, fill=(20, 20, 20), outline=gold, width=2)
    draw.text((1075, 16), "🌾 KISAN BADLEGA", font=stamp_font, fill=gold)

    # Main Headline (Massive, Bold White/Yellow)
    font_main = get_devanagari_font(56, bold=True)
    bbox = draw.textbbox((0, 0), headline, font=font_main)
    w_text = bbox[2] - bbox[0]
    tx = max(30, (1280 - w_text) // 2)
    draw_text_with_effects(draw, (tx, 22), headline, font_main, fill_color=(255, 255, 255), stroke_color=(0, 0, 0), stroke_w=6)

    # 2. SUBHEADLINE BANNER: High-contrast white box with dark-red text
    sub_font = get_devanagari_font(34, bold=True)
    sub_bbox = draw.textbbox((0, 0), subheadline, font=sub_font)
    sub_w = sub_bbox[2] - sub_bbox[0] + 70
    sub_x1 = max(40, (1280 - sub_w) // 2)
    sub_x2 = sub_x1 + sub_w
    sub_y1, sub_y2 = 108, 175
    # White card with drop shadow
    draw.rounded_rectangle([sub_x1 + 3, sub_y1 + 4, sub_x2 + 3, sub_y2 + 4], radius=12, fill=(0, 0, 0))
    draw.rounded_rectangle([sub_x1, sub_y1, sub_x2, sub_y2], radius=12, fill=(255, 255, 255), outline=maroon, width=3)
    draw.text((sub_x1 + 35, sub_y1 + 12), subheadline, font=sub_font, fill=maroon, stroke_width=1, stroke_fill=maroon)

    # 3. THREE EQUAL VISUAL PANELS ACROSS LOWER HALF
    panel_y = 215
    panel_w = 360
    panel_h = 475
    gap = 40
    start_x = (1280 - (3 * panel_w + 2 * gap)) // 2

    clean_points = (points + ["बड़ा फैसला", "सीधे खाते में", "100% पक्का लाभ"])[:3]

    for i in range(3):
        px = start_x + i * (panel_w + gap)
        # Drop shadow
        draw.rounded_rectangle([px + 5, panel_y + 5, px + panel_w + 5, panel_y + panel_h + 5], radius=18, fill=(0, 0, 0, 180))
        # Panel Background (semi-darkened glass card with 5px white border)
        draw.rounded_rectangle([px, panel_y, px + panel_w, panel_y + panel_h], radius=18, fill=(10, 30, 18), outline=(255, 255, 255), width=5)

        # Inner Top Badge
        badge_titles = ["अपडेट 1", "अपडेट 2", "अपडेट 3"]
        b_font = get_devanagari_font(22, bold=True)
        draw.rounded_rectangle([px + 20, panel_y + 15, px + 140, panel_y + 52], radius=8, fill=maroon, outline=gold, width=2)
        draw.text((px + 35, panel_y + 20), badge_titles[i], font=b_font, fill=(255, 255, 255))

        # Big Visual Focus (Icon / Question Mark with golden glow)
        qm_font = get_devanagari_font(130, bold=True)
        draw_text_with_effects(draw, (px + panel_w // 2 - 40, panel_y + 105), "?", qm_font, fill_color=gold, stroke_color=(0, 0, 0), stroke_w=7)

        # Bottom Point Label (Bold high-impact strip)
        draw.rounded_rectangle([px + 12, panel_y + panel_h - 105, px + panel_w - 12, panel_y + panel_h - 15], radius=12, fill=maroon, outline=(255, 255, 255), width=3)
        pt_font = get_devanagari_font(28, bold=True)
        pt_text = clean_points[i]
        pt_bbox = draw.textbbox((0, 0), pt_text, font=pt_font)
        pw = pt_bbox[2] - pt_bbox[0]
        draw_text_with_effects(draw, (px + (panel_w - pw) // 2, panel_y + panel_h - 85), pt_text, pt_font, fill_color=(255, 235, 59), stroke_color=(0, 0, 0), stroke_w=4)

    base.save(output_path, quality=95)
    print(f"[Thumbnail] Style 1 generated successfully: {output_path}")
    return output_path

def generate_style2_education(
    headline: str,
    secondary_headline: str,
    key_benefit: str,
    crop_name: str,
    output_path: str,
    cache_dir: str
):
    """
    STYLE 2: High-Contrast Agriculture Tips & Education Thumbnail (16:9, 1280x720).
    - Top Banner: Bright Electric Yellow (#FFD400) with bold black Hindi headline.
    - Full-frame lush green field background.
    - Inset Crop Photo card on right with 6px white border.
    - 3D Curved Yellow Arrow pointing toward crop.
    - Before & After comparison cards with connecting arrow.
    """
    base = get_enhanced_farm_bg(cache_dir)
    draw = ImageDraw.Draw(base)

    # 1. TOP BANNER: Bright Electric Yellow (#FFD400)
    yellow = (255, 212, 0)
    header_h = 160
    draw.rectangle([0, 0, 1280, header_h], fill=yellow)
    draw.line([(0, header_h), (1280, header_h)], fill=(0, 0, 0), width=6)

    # Channel Stamp
    stamp_font = get_devanagari_font(20, bold=True)
    draw.rounded_rectangle([1060, 12, 1260, 42], radius=6, fill=(0, 0, 0))
    draw.text((1075, 16), "🌾 KISAN BADLEGA", font=stamp_font, fill=yellow)

    # Main Headline with separator: "[HEADLINE] | [SECONDARY]"
    combined = f"{headline}  |  {secondary_headline}" if secondary_headline else headline
    font_main = get_devanagari_font(52, bold=True)
    bbox = draw.textbbox((0, 0), combined, font=font_main)
    w_text = bbox[2] - bbox[0]
    tx = max(30, (1280 - w_text) // 2)
    # High-impact black text with shadow
    draw.text((tx + 2, 42), combined, font=font_main, fill=(80, 60, 0))
    draw.text((tx, 40), combined, font=font_main, fill=(0, 0, 0))

    # 2. RIGHT INSET CROP PHOTOGRAPH CARD
    inset_x1, inset_y1 = 740, 185
    inset_x2, inset_y2 = 1240, 690
    # Shadow
    draw.rounded_rectangle([inset_x1 + 6, inset_y1 + 6, inset_x2 + 6, inset_y2 + 6], radius=20, fill=(0, 0, 0, 180))
    # Card with 6px white border
    draw.rounded_rectangle([inset_x1, inset_y1, inset_x2, inset_y2], radius=20, fill=(15, 45, 25), outline=(255, 255, 255), width=6)

    # Crop Tag / Badge on Inset Card
    crop_title = f"फसल: {crop_name or 'आधुनिक खेती'}"
    cr_font = get_devanagari_font(34, bold=True)
    draw.rounded_rectangle([inset_x1 + 25, inset_y2 - 95, inset_x2 - 25, inset_y2 - 25], radius=14, fill=yellow, outline=(0, 0, 0), width=3)
    c_bbox = draw.textbbox((0, 0), crop_title, font=cr_font)
    cw = c_bbox[2] - c_bbox[0]
    draw.text((inset_x1 + (inset_x2 - inset_x1 - cw) // 2, inset_y2 - 80), crop_title, font=cr_font, fill=(0, 0, 0))

    # 3. 3D CURVED YELLOW ARROW POINTING TO CROP
    # Line
    arrow_pts = [(540, 390), (620, 360), (720, 380)]
    draw.line(arrow_pts, fill=(0, 0, 0), width=18)
    draw.line(arrow_pts, fill=yellow, width=12)
    # Head
    draw.polygon([(710, 355), (745, 380), (710, 405)], fill=yellow, outline=(0, 0, 0))

    # 4. BIG BENEFIT BADGE (Top-Left under banner)
    ben_x1, ben_y1 = 40, 185
    ben_x2, ben_y2 = 530, 320
    draw.rounded_rectangle([ben_x1 + 4, ben_y1 + 4, ben_x2 + 4, ben_y2 + 4], radius=16, fill=(0, 0, 0))
    draw.rounded_rectangle([ben_x1, ben_y1, ben_x2, ben_y2], radius=16, fill=(180, 0, 0), outline=yellow, width=4)
    draw.text((ben_x1 + 25, ben_y1 + 18), "बड़ा फायदा / बंपर पैदावार:", font=get_devanagari_font(24, bold=True), fill=yellow)
    ben_font = get_devanagari_font(38, bold=True)
    draw_text_with_effects(draw, (ben_x1 + 25, ben_y1 + 60), key_benefit or "3 गुना पैदावार गारंटी!", ben_font, fill_color=(255, 255, 255), stroke_color=(0, 0, 0), stroke_w=5)

    # 5. BEFORE / AFTER COMPARISON CARDS (Bottom-Left)
    card1_pts = [40, 350, 260, 690]
    card2_pts = [310, 350, 530, 690]

    # Card 1: पुराना तरीका (Loss/Low yield)
    draw.rounded_rectangle([card1_pts[0], card1_pts[1], card1_pts[2], card1_pts[3]], radius=16, fill=(240, 240, 240), outline=(139, 0, 0), width=4)
    draw.rectangle([card1_pts[0], card1_pts[1], card1_pts[2], card1_pts[1] + 55], fill=(180, 30, 30))
    draw.text((card1_pts[0] + 25, card1_pts[1] + 12), "पुराना तरीका", font=get_devanagari_font(26, bold=True), fill=(255, 255, 255))
    draw.text((card1_pts[0] + 20, card1_pts[1] + 140), "कम पैदावार\n\nज्यादा लागत\n\nनुकसान!", font=get_devanagari_font(28, bold=True), fill=(100, 20, 20))

    # Arrow connecting cards
    draw.line([(card1_pts[2] + 5, 520), (card2_pts[0] - 10, 520)], fill=(0, 0, 0), width=10)
    draw.polygon([(card2_pts[0] - 12, 505), (card2_pts[0] + 5, 520), (card2_pts[0] - 12, 535)], fill=yellow, outline=(0, 0, 0))

    # Card 2: नया तरीका (Profit/High yield)
    draw.rounded_rectangle([card2_pts[0], card2_pts[1], card2_pts[2], card2_pts[3]], radius=16, fill=(255, 255, 255), outline=(0, 150, 40), width=5)
    draw.rectangle([card2_pts[0], card2_pts[1], card2_pts[2], card2_pts[1] + 55], fill=(0, 130, 40))
    draw.text((card2_pts[0] + 30, card2_pts[1] + 12), "नया तरीका", font=get_devanagari_font(26, bold=True), fill=(255, 255, 255))
    draw.text((card2_pts[0] + 20, card2_pts[1] + 140), "3x बंपर उपज\n\nकम लागत\n\nलाखों मुनाफा!", font=get_devanagari_font(28, bold=True), fill=(0, 110, 30))

    base.save(output_path, quality=95)
    print(f"[Thumbnail] Style 2 generated successfully: {output_path}")
    return output_path

def create_video_thumbnail(
    topic_or_title: str,
    output_path: str,
    preferred_style: str = "auto",
    ai_metadata: dict = None
) -> str:
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)

    # Use AI metadata fields directly if provided
    meta = ai_metadata or {}
    headline = meta.get("thumb_headline") or meta.get("title", "")
    subheadline = meta.get("thumb_subheadline") or "3 गुना मुनाफे का नया तरीका!"
    points = meta.get("thumb_points") or ["बड़ा फैसला", "सीधे खाते में", "100% पक्का लाभ"]
    crop_name = meta.get("crop_name") or "खेती"
    benefit = meta.get("key_benefit") or "3 गुना पैदावार गारंटी!"

    # Clean headline for thumbnail: keep to 4-6 big words
    clean_h = re.sub(r"[#\|].*", "", headline).strip()
    words = clean_h.split()
    if len(words) > 6:
        clean_h = " ".join(words[:6]) + "!"

    style = preferred_style
    if style not in ("1", "2"):
        # Auto: Style 1 for news/subsidy, Style 2 for crops/methods
        is_news = any(k in (headline + subheadline).lower() for k in ["pm kisan", "योजना", "सब्सिडी", "किस्त", "सरकार", "न्यूज़", "तारीख", "फैसला"])
        style = "1" if is_news else "2"

    print(f"[Thumbnail Engine] Rendering Style {style}...")
    if style == "2":
        return generate_style2_education(clean_h, subheadline, benefit, crop_name, output_path, out_dir)
    else:
        return generate_style1_news(clean_h, subheadline, points, output_path, out_dir)

if __name__ == "__main__":
    out1 = os.path.join(ROOT, "output", "pro_thumb_style1.jpg")
    out2 = os.path.join(ROOT, "output", "pro_thumb_style2.jpg")
    sample_meta = {
        "thumb_headline": "गेहूं में ये 1 स्प्रे डालो!",
        "thumb_subheadline": "3 गुना पैदावार की 100% गारंटी!",
        "thumb_points": ["सही समय", "स्प्रे की मात्रा", "रोगों से मुक्ति"],
        "crop_name": "गेहूं",
        "key_benefit": "3 गुना पैदावार गारंटी!"
    }
    create_video_thumbnail("गेहूं की खेती", out1, preferred_style="1", ai_metadata=sample_meta)
    create_video_thumbnail("गेहूं की खेती", out2, preferred_style="2", ai_metadata=sample_meta)
