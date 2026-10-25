# -*- coding: utf-8 -*-
"""
Helper script to preview logo alignment on a sample 9:16 frame.
Run: python scripts/preview_logo.py
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(ROOT, "assets", "logo.png")
OUTPUT_PATH = os.path.join(ROOT, "preview_alignment.png")

# 1. Create a 720x1280 vertical Short sample canvas
width, height = 720, 1280
base = Image.new("RGB", (width, height), color=(25, 45, 30))
draw = ImageDraw.Draw(base)

# Guide lines
draw.text((40, 60), "Kisan Badlega - Video Frame Preview", fill=(255, 255, 255))
draw.rectangle([width - 240, height - 70, width - 10, height - 15], outline=(100, 100, 100), width=1)
draw.text((width - 230, height - 60), "NotebookLM Area", fill=(120, 120, 120))

# 2. Resize logo (150px width)
if os.path.exists(LOGO_PATH):
    logo = Image.open(LOGO_PATH).convert("RGBA")
    target_w = 180
    target_h = int(logo.height * (target_w / logo.width))
    logo_resized = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # 3. Position at bottom-right corner (10px padding)
    pos_x = width - target_w - 10
    pos_y = height - target_h - 10
    base.paste(logo_resized, (pos_x, pos_y), logo_resized)
    base.save(OUTPUT_PATH)
    print(f"Preview generated successfully: {OUTPUT_PATH}")
    # Open preview image automatically on Windows
    try:
        os.startfile(OUTPUT_PATH)
    except Exception:
        pass
else:
    print(f"Logo not found at: {LOGO_PATH}")
