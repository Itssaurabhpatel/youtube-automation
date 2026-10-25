# -*- coding: utf-8 -*-
import os
import subprocess
import sys

def apply_watermark_removal(
    input_video: str,
    output_video: str,
    mode: str = "cover_badge",
    custom_image_path: str = ""
) -> str:
    """
    Handles NotebookLM watermark in bottom-right corner.
    Modes:
      - 'cover_badge': Overlays custom logo image or generated 'Kisan Badlega' badge. (BEST)
      - 'delogo': Blurs and blends the watermark area using FFmpeg delogo.
      - 'none': Leaves video as is.
    """
    if mode == "none":
        return input_video

    print(f"[Watermark] Applying NotebookLM watermark removal (Mode: {mode})...")

    # Check if user provided or committed an image (e.g. assets/logo.png)
    logo_path = ""
    if custom_image_path and os.path.exists(custom_image_path):
        logo_path = custom_image_path
    else:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for candidate in ["logo.png", "logo.jpg", "badge.png", "watermark_cover.png"]:
            p = os.path.join(root, "assets", candidate)
            if os.path.exists(p):
                logo_path = p
                break

    if mode == "cover_badge" and logo_path:
        print(f"[Watermark] Covering NotebookLM watermark with custom image: {logo_path}")
        # Scale logo to 180px width, clean overlay tucked into bottom-right corner (10px margin)
        filter_complex = (
            "[1:v]scale=180:-1,format=rgba[logo];"
            "[0:v][logo]overlay=main_w-overlay_w-10:main_h-overlay_h-10"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-i", logo_path,
            "-filter_complex", filter_complex,
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "copy",
            output_video
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print("[Watermark] Logo overlay applied successfully!")
            return output_video
        else:
            print(f"[Watermark] Logo overlay failed: {res.stderr[:200]}. Falling back to delogo.")

    # Fallback to FFmpeg delogo / blur on bottom-right corner
    # NotebookLM watermark is in bottom right (~260px wide, ~70px high)
    print("[Watermark] Blurring bottom-right NotebookLM watermark area...")
    delogo_filter = "delogo=x=main_w-270:y=main_h-85:w=250:h=70:show=0"
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", delogo_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "copy",
        output_video
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print("[Watermark] Delogo applied successfully!")
        return output_video

    # If delogo has bounds issue on smaller videos, gentle crop/scale fallback
    print("[Watermark] Delogo fallback: returning original video.")
    return input_video

if __name__ == "__main__":
    if len(sys.argv) > 2:
        apply_watermark_removal(sys.argv[1], sys.argv[2], mode=sys.argv[3] if len(sys.argv) > 3 else "cover_badge")
