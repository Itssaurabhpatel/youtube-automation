# -*- coding: utf-8 -*-
import json
import math
import os
import re
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_BG_URLS = [
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1280&q=80",
    "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1280&q=80",
    "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?w=1280&q=80",
]

CROP_PHOTOS = {
    "wheat": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600&q=80",
    "seeds": "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?w=600&q=80",
    "tractor": "https://images.unsplash.com/photo-1592982537447-7440770cbfc9?w=600&q=80"
}

def get_devanagari_font(size: int, bold: bool = True):
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/mangalb.ttf",
        "C:/Windows/Fonts/NirmalaB.ttf",
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

def fetch_image_cached(url: str, local_path: str) -> Image.Image:
    if os.path.exists(local_path) and os.path.getsize(local_path) > 5000:
        try:
            return Image.open(local_path).convert("RGB")
        except Exception:
            pass
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            with open(local_path, "wb") as f:
                f.write(r.read())
        return Image.open(local_path).convert("RGB")
    except Exception:
        return None

def get_enhanced_farm_bg(cache_dir: str) -> Image.Image:
    bg_local = os.path.join(cache_dir, "farm_bg_vibrant.jpg")
    for url in DEFAULT_BG_URLS:
        im = fetch_image_cached(url, bg_local)
        if im:
            im = im.resize((1280, 720))
            enhancer = ImageEnhance.Color(im)
            im = enhancer.enhance(1.4)
            contrast = ImageEnhance.Contrast(im)
            im = contrast.enhance(1.2)
            return im
    return Image.new("RGB", (1280, 720), color=(25, 60, 35))

def generate_style1_news(
    headline: str,
    subheadline: str,
    points: list,
    output_path: str,
    cache_dir: str
):
    bg = get_enhanced_farm_bg(cache_dir)
    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    ov_draw.rectangle([0, 180, 1280, 720], fill=(0, 0, 0, 90))
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(bg)

    font_main = get_devanagari_font(54, bold=True)
    sub_font = get_devanagari_font(32, bold=True)
    pt_font = get_devanagari_font(26, bold=True)
    b_font = get_devanagari_font(20, bold=True)

    maroon = (128, 0, 0)
    gold = (255, 215, 0)
    draw.rectangle([0, 0, 1280, 145], fill=maroon)
    draw.line([(0, 145), (1280, 145)], fill=gold, width=5)

    draw.rounded_rectangle([1060, 12, 1260, 42], radius=6, fill=(20, 20, 20), outline=gold, width=2)
    draw.text((1075, 16), "🌾 KISAN BADLEGA", font=b_font, fill=gold)

    # Main Headline with 6px black stroke
    bbox = draw.textbbox((0, 0), headline, font=font_main)
    tx = (1280 - (bbox[2] - bbox[0])) // 2
    draw.text((tx + 3, 23), headline, font=font_main, fill=(0, 0, 0))
    draw.text((tx, 20), headline, font=font_main, fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0))

    # Subheadline white banner
    sub_bbox = draw.textbbox((0, 0), subheadline, font=sub_font)
    sw = sub_bbox[2] - sub_bbox[0] + 60
    sx1 = max(30, (1280 - sw) // 2)
    sx2 = sx1 + sw
    draw.rounded_rectangle([sx1 + 3, 103, sx2 + 3, 163], radius=10, fill=(0, 0, 0))
    draw.rounded_rectangle([sx1, 100, sx2, 160], radius=10, fill=(255, 255, 255), outline=maroon, width=3)
    draw.text((sx1 + 30, 110), subheadline, font=sub_font, fill=maroon, stroke_width=1, stroke_fill=maroon)

    # 3 Visual Panels with Real Photos
    panel_w = 360
    panel_h = 475
    gap = 40
    start_x = (1280 - (3 * panel_w + 2 * gap)) // 2
    panel_y = 210

    crop_keys = ["wheat", "seeds", "tractor"]
    clean_points = (points + ["बड़ा फैसला", "सीधे खाते में", "100% पक्का लाभ"])[:3]

    for i in range(3):
        px = start_x + i * (panel_w + gap)
        # Fetch crop photo
        p_img = fetch_image_cached(CROP_PHOTOS[crop_keys[i]], os.path.join(cache_dir, f"panel_{crop_keys[i]}.jpg"))
        if p_img:
            p_img = p_img.resize((panel_w, panel_h))
            mask = Image.new("L", (panel_w, panel_h), 0)
            m_draw = ImageDraw.Draw(mask)
            m_draw.rounded_rectangle([0, 0, panel_w, panel_h], radius=18, fill=255)
            bg.paste(p_img, (px, panel_y), mask)

        p_draw = ImageDraw.Draw(bg)
        # White border 5px
        p_draw.rounded_rectangle([px, panel_y, px + panel_w, panel_y + panel_h], radius=18, outline=(255, 255, 255), width=5)

        # Top pill
        p_draw.rounded_rectangle([px + 15, panel_y + 15, px + 120, panel_y + 48], radius=8, fill=maroon, outline=gold, width=2)
        p_draw.text((px + 25, panel_y + 18), f"अपडेट {i+1}", font=b_font, fill=(255, 255, 255))

        # Bottom label strip
        p_draw.rounded_rectangle([px + 12, panel_y + panel_h - 90, px + panel_w - 12, panel_y + panel_h - 15], radius=12, fill=maroon, outline=(255, 255, 255), width=3)
        lbl = clean_points[i]
        l_box = p_draw.textbbox((0, 0), lbl, font=pt_font)
        lw = l_box[2] - l_box[0]
        p_draw.text((px + (panel_w - lw) // 2, panel_y + panel_h - 75), lbl, font=pt_font, fill=(255, 235, 59), stroke_width=4, stroke_fill=(0, 0, 0))

    bg.save(output_path, quality=95)
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
    bg = get_enhanced_farm_bg(cache_dir)
    draw = ImageDraw.Draw(bg)

    font_main = get_devanagari_font(48, bold=True)
    sub_font = get_devanagari_font(30, bold=True)
    b_font = get_devanagari_font(22, bold=True)

    yellow = (255, 212, 0)
    draw.rectangle([0, 0, 1280, 150], fill=yellow)
    draw.line([(0, 150), (1280, 150)], fill=(0, 0, 0), width=5)

    draw.rounded_rectangle([1060, 12, 1260, 42], radius=6, fill=(0, 0, 0))
    draw.text((1075, 16), "🌾 KISAN BADLEGA", font=b_font, fill=yellow)

    combined = f"{headline}  |  {secondary_headline}" if secondary_headline else headline
    bbox = draw.textbbox((0, 0), combined, font=font_main)
    tx = (1280 - (bbox[2] - bbox[0])) // 2
    draw.text((tx, 35), combined, font=font_main, fill=(0, 0, 0))

    # Right Inset Real Crop Photo
    inset_x1, inset_y1 = 740, 180
    inset_x2, inset_y2 = 1240, 680
    crop_w, crop_h = inset_x2 - inset_x1, inset_y2 - inset_y1

    crop_img = fetch_image_cached(CROP_PHOTOS["wheat"], os.path.join(cache_dir, "inset_wheat.jpg"))
    if crop_img:
        crop_img = crop_img.resize((crop_w, crop_h))
        mask = Image.new("L", (crop_w, crop_h), 0)
        m_draw = ImageDraw.Draw(mask)
        m_draw.rounded_rectangle([0, 0, crop_w, crop_h], radius=20, fill=255)
        bg.paste(crop_img, (inset_x1, inset_y1), mask)

    draw = ImageDraw.Draw(bg)
    draw.rounded_rectangle([inset_x1, inset_y1, inset_x2, inset_y2], radius=20, outline=(255, 255, 255), width=6)

    # Crop Tag Badge
    draw.rounded_rectangle([inset_x1 + 30, inset_y2 - 85, inset_x2 - 30, inset_y2 - 20], radius=12, fill=yellow, outline=(0, 0, 0), width=3)
    cr_title = f"फसल: {crop_name or 'उन्नत खेती'}"
    c_bbox = draw.textbbox((0, 0), cr_title, font=sub_font)
    cw = c_bbox[2] - c_bbox[0]
    draw.text((inset_x1 + (crop_w - cw) // 2, inset_y2 - 70), cr_title, font=sub_font, fill=(0, 0, 0))

    # 3D Curved Arrow
    arrow_pts = [(540, 390), (620, 360), (710, 380)]
    draw.line(arrow_pts, fill=(0, 0, 0), width=18)
    draw.line(arrow_pts, fill=yellow, width=12)
    draw.polygon([(700, 355), (735, 380), (700, 405)], fill=yellow, outline=(0, 0, 0))

    # Benefit Badge
    draw.rounded_rectangle([40, 185, 530, 320], radius=16, fill=(180, 0, 0), outline=yellow, width=4)
    draw.text((65, 200), "बड़ा फायदा / बंपर पैदावार:", font=b_font, fill=yellow)
    draw.text((65, 245), key_benefit or "3 गुना पैदावार गारंटी!", font=get_devanagari_font(38, bold=True), fill=(255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0))

    # Comparison Cards
    c1 = [40, 350, 260, 680]
    c2 = [310, 350, 530, 680]
    # Card 1
    draw.rounded_rectangle([c1[0], c1[1], c1[2], c1[3]], radius=16, fill=(240, 240, 240), outline=(139, 0, 0), width=4)
    draw.rectangle([c1[0], c1[1], c1[2], c1[1] + 55], fill=(180, 30, 30))
    draw.text((c1[0] + 25, c1[1] + 12), "पुराना तरीका", font=b_font, fill=(255, 255, 255))
    draw.text((c1[0] + 20, c1[1] + 130), "कम पैदावार\n\nज्यादा लागत\n\nनुकसान!", font=get_devanagari_font(26, bold=True), fill=(120, 20, 20))

    # Arrow
    draw.line([(c1[2] + 5, 515), (c2[0] - 10, 515)], fill=(0, 0, 0), width=10)
    draw.polygon([(c2[0] - 12, 500), (c2[0] + 5, 515), (c2[0] - 12, 530)], fill=yellow, outline=(0, 0, 0))

    # Card 2
    draw.rounded_rectangle([c2[0], c2[1], c2[2], c2[3]], radius=16, fill=(255, 255, 255), outline=(0, 150, 40), width=5)
    draw.rectangle([c2[0], c2[1], c2[2], c2[1] + 55], fill=(0, 130, 40))
    draw.text((c2[0] + 30, c2[1] + 12), "नया तरीका", font=b_font, fill=(255, 255, 255))
    draw.text((c2[0] + 20, c2[1] + 130), "3x बंपर उपज\n\nकम लागत\n\nलाखों मुनाफा!", font=get_devanagari_font(26, bold=True), fill=(0, 110, 30))

    bg.save(output_path, quality=95)
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

    meta = ai_metadata or {}
    headline = meta.get("thumb_headline") or meta.get("title", "")
    subheadline = meta.get("thumb_subheadline") or "3 गुना मुनाफे का नया तरीका!"
    points = meta.get("thumb_points") or ["बड़ा फैसला", "सीधे खाते में", "100% पक्का लाभ"]
    crop_name = meta.get("crop_name") or "खेती"
    benefit = meta.get("key_benefit") or "3 गुना पैदावार गारंटी!"

    clean_h = re.sub(r"[#\|].*", "", headline).strip()
    words = clean_h.split()
    if len(words) > 6:
        clean_h = " ".join(words[:6]) + "!"

    style = preferred_style
    if style not in ("1", "2"):
        is_news = any(k in (headline + subheadline).lower() for k in ["pm kisan", "योजना", "सब्सिडी", "किस्त", "सरकार", "न्यूज़", "तारीख", "फैसला"])
        style = "1" if is_news else "2"

    print(f"[Thumbnail Engine] Rendering Style {style}...")
    if style == "2":
        return generate_style2_education(clean_h, subheadline, benefit, crop_name, output_path, out_dir)
    else:
        return generate_style1_news(clean_h, subheadline, points, output_path, out_dir)
