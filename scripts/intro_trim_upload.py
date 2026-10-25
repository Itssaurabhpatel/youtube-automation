# -*- coding: utf-8 -*-
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import gdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, "scripts"))

from youtube_upload import upload_local_file
from drive_upload import get_video_info, generate_metadata_from_audio, load_config
from watermark_handler import apply_watermark_removal

def has_audio_stream(file_path: str) -> bool:
    """Checks if video contains an audio stream using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0",
            file_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return bool(res.stdout.strip())
    except Exception:
        return True

def download_file(url_or_path: str, dest_path: str) -> str:
    """Downloads file from Google Drive, HTTP URL, or copies from local path."""
    if os.path.exists(url_or_path):
        import shutil
        shutil.copy(url_or_path, dest_path)
        return dest_path

    print(f"[Download] Fetching file from: {url_or_path}")
    if "drive.google.com" in url_or_path:
        gdown.download(url=url_or_path, output=dest_path, quiet=False, fuzzy=True)
    else:
        import requests
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        with requests.get(url_or_path, headers=headers, stream=True, timeout=(30, 300)) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
    if not os.path.exists(dest_path) or os.path.getsize(dest_path) < 1024:
        sys.exit(f"Error: Failed to download valid video file from {url_or_path}")
    return dest_path

def trim_video(input_path: str, cut_start_seconds: float, cut_end_seconds: float, output_path: str):
    """Trims start and/or end seconds from video."""
    duration, _, _ = get_video_info(input_path)
    start_time = max(0.0, cut_start_seconds)
    target_duration = duration - start_time - max(0.0, cut_end_seconds)

    if target_duration <= 0:
        print("[Edit] Warning: Target duration too short after trim, keeping original video.")
        import shutil
        shutil.copy(input_path, output_path)
        return

    print(f"[Edit] Trimming main video: Start cut = {start_time}s, End cut = {cut_end_seconds}s (Total duration: {target_duration:.1f}s)...")
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-i", input_path,
        "-t", str(target_duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"[Edit] Trimmed video created successfully: {output_path}")

def merge_intro_and_video(intro_path: str, main_trimmed_path: str, output_path: str):
    """Seamlessly joins intro.mp4 + trimmed main video with resolution & audio matching."""
    print("[Edit] Merging intro.mp4 and main video...")
    _, w, h = get_video_info(main_trimmed_path)

    intro_has_audio = has_audio_stream(intro_path)
    main_has_audio = has_audio_stream(main_trimmed_path)

    # Filter handles scaling to match main video dimensions, padding with black if ratio differs
    if intro_has_audio and main_has_audio:
        filter_complex = (
            f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v0];"
            f"[1:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v1];"
            f"[0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0];"
            f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo[a1];"
            f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[outv][outa]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", intro_path,
            "-i", main_trimmed_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            output_path
        ]
    else:
        # If one lacks audio, handle video concat and combine audio
        filter_complex = (
            f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v0];"
            f"[1:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v1];"
            f"[v0][v1]concat=n=2:v=1:a=0[outv]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", intro_path,
            "-i", main_trimmed_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-preset", "fast",
            output_path
        ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"[Edit] Successfully merged video: {output_path}")

def process_trim_intro_upload(
    video_url: str,
    cut_end_seconds: float = 2.0,
    cut_start_seconds: float = 0.0,
    intro_url: str = "",
    privacy: str = "private",
    watermark_mode: str = "cover_badge",
    logo_image_url: str = ""
):
    cfg = load_config()
    print("=" * 60)
    print("🎬 INTRO STITCH & TRIM AUTO-UPLOAD PIPELINE (KISAN BADLEGA)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        main_video_file = os.path.join(tmpdir, "main_raw.mp4")
        trimmed_video_file = os.path.join(tmpdir, "main_trimmed.mp4")
        intro_file = os.path.join(tmpdir, "intro.mp4")
        merged_video_file = os.path.join(tmpdir, "final_merged.mp4")

        # 1. Download Main Video
        download_file(video_url, main_video_file)

        # 2. Locate / Download Intro Video
        repo_intro = os.path.join(ROOT, "assets", "intro.mp4")
        if intro_url.strip():
            download_file(intro_url, intro_file)
        elif os.path.exists(repo_intro):
            import shutil
            shutil.copy(repo_intro, intro_file)
            print(f"[Intro] Using repository intro: {repo_intro}")
        else:
            sys.exit(
                "Error: No intro video found! Please provide 'intro_url' or commit 'intro.mp4' into 'assets/' folder in the repository."
            )

        # 3. Trim End / Start Seconds from Main Video
        if cut_end_seconds > 0 or cut_start_seconds > 0:
            trim_video(main_video_file, cut_start_seconds, cut_end_seconds, trimmed_video_file)
        else:
            import shutil
            shutil.copy(main_video_file, trimmed_video_file)

        # 4. Merge Intro + Trimmed Main Video
        merge_intro_and_video(intro_file, trimmed_video_file, merged_video_file)

        # 5. NotebookLM Watermark Removal / Logo Cover
        cleaned_video_file = os.path.join(tmpdir, "final_cleaned.mp4")
        final_video_file = apply_watermark_removal(
            merged_video_file,
            cleaned_video_file,
            mode=watermark_mode,
            custom_image_path=logo_image_url
        )

        # Save to output folder for artifact download
        out_dir = os.path.join(ROOT, "output")
        os.makedirs(out_dir, exist_ok=True)
        persisted_final = os.path.join(out_dir, f"merged_kisan_{os.path.basename(main_video_file)}")
        import shutil
        shutil.copy(final_video_file, persisted_final)

        # 6. AI Metadata Generation from the Final Video
        duration, w, h = get_video_info(final_video_file)
        is_short = (duration <= 60 or h > w)
        print(f"[Video Details] Duration: {duration:.1f}s | Resolution: {w}x{h} | Type: {'Shorts' if is_short else 'Long'}")

        metadata = generate_metadata_from_audio(final_video_file, is_short=is_short)
        print("\n--- AUTO-GENERATED METADATA ---")
        print(f"Title: {metadata['title']}")
        print(f"Tags: {', '.join(metadata.get('tags', []))}")
        print(f"Description:\n{metadata['description'][:200]}...")
        print("-------------------------------\n")

        # 7. Upload to YouTube
        tags = metadata.get("tags", []) + cfg.get("default_tags", [])
        category = cfg.get("category_id", "27")
        upload_privacy = privacy or cfg.get("upload_privacy", "private")

        vid = upload_local_file(
            video_path=final_video_file,
            title=metadata["title"],
            description=metadata["description"],
            tags=tags,
            privacy=upload_privacy,
            category=category
        )
        print("=" * 60)
        print(f"🎉 VIDEO LIVE ON YOUTUBE: https://www.youtube.com/watch?v={vid}")
        print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-url", required=True, help="Main video Google Drive or Direct Link")
    parser.add_argument("--cut-end-seconds", type=float, default=2.0, help="Seconds to trim from end of main video")
    parser.add_argument("--cut-start-seconds", type=float, default=0.0, help="Seconds to trim from start of main video")
    parser.add_argument("--intro-url", default="", help="Intro video Google Drive or Direct Link (optional if assets/intro.mp4 exists)")
    parser.add_argument("--watermark-mode", default="cover_badge", choices=["cover_badge", "delogo", "none"])
    parser.add_argument("--logo-url", default="", help="Custom logo/image URL to cover watermark")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    args = parser.parse_args()

    process_trim_intro_upload(
        video_url=args.video_url,
        cut_end_seconds=args.cut_end_seconds,
        cut_start_seconds=args.cut_start_seconds,
        intro_url=args.intro_url,
        privacy=args.privacy,
        watermark_mode=args.watermark_mode,
        logo_image_url=args.logo_url
    )
