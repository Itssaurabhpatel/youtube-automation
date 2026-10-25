# -*- coding: utf-8 -*-
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import gdown

# Add scripts directory to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, "scripts"))

from youtube_upload import upload_local_file

def load_config() -> dict:
    cfg_path = os.path.join(ROOT, "config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_video_info(video_path: str):
    """Returns (duration_seconds, width, height) using ffprobe."""
    try:
        cmd_dur = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        duration = float(subprocess.run(cmd_dur, capture_output=True, text=True, check=True).stdout.strip())

        cmd_dim = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            video_path
        ]
        dim_str = subprocess.run(cmd_dim, capture_output=True, text=True, check=True).stdout.strip()
        w, h = [int(x) for x in dim_str.split("x")]
        return duration, w, h
    except Exception as e:
        print(f"[Info] Could not read ffprobe metadata: {e}. Defaulting to standard video.")
        return 60.0, 1080, 1920

def extract_audio(video_path: str, audio_path: str):
    """Extracts lightweight mono audio track for AI transcription/analysis."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "64k",
        audio_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"[Audio] Extracted audio for AI analysis: {audio_path}")

def generate_metadata_from_audio(video_path: str, is_short: bool) -> dict:
    """Uses Gemini to listen to video audio and create viral Hindi metadata for Kisan Badlega."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    clean_filename = os.path.splitext(os.path.basename(video_path))[0]
    clean_filename = re.sub(r"[_\-]+", " ", clean_filename)

    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)

            with tempfile.TemporaryDirectory() as tmp:
                audio_path = os.path.join(tmp, "audio.mp3")
                extract_audio(video_path, audio_path)

                print("[AI] Uploading audio track to Gemini for Hindi content understanding...")
                audio_file = genai.upload_file(path=audio_path)
                
                model = genai.GenerativeModel("gemini-1.5-flash")
                short_instruction = "This is a YouTube Short (under 60s). Add #Shorts in title and tags." if is_short else "This is a full-length YouTube video."

                prompt = (
                    "You are a top YouTube SEO strategist and content director for the Indian Agriculture channel 'Kisan Badlega' (किसान बदलेगा). "
                    "Listen to this audio track from the uploaded video. Understand the crop names, farming techniques, government schemes, or advice discussed. "
                    f"Filename context: '{clean_filename}'. {short_instruction}\n\n"
                    "Generate a high-CTR, viral YouTube title, detailed SEO description, and search tags tailored for Indian farmers.\n"
                    "Output ONLY a valid JSON object:\n"
                    "{\n"
                    '  "title": "Engaging Hindi/Hinglish Title under 70 chars with #Shorts if short (e.g. किसान भाई इस फसल से कमाएं लाखों | #Shorts)",\n'
                    '  "description": "Comprehensive description in Hindi. Include video summary, 3 practical takeaways, channel mention (किसान बदलेगा), and hashtags #KisanBadlega #KhetiBadi #Kisan #Agriculture",\n'
                    '  "tags": ["Kisan Badlega", "kheti", "kheti badi", "agriculture in india", "kisan", "...10 more relevant tags..."]\n'
                    "}"
                )

                response = model.generate_content([audio_file, prompt])
                raw_text = response.text.strip()
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
                if match:
                    raw_text = match.group(1).strip()
                data = json.loads(raw_text)
                if "title" in data and "description" in data:
                    print(f"[AI] Successfully generated metadata with Gemini!")
                    return data
        except Exception as e:
            print(f"[AI] Gemini audio analysis error: {e}. Falling back to filename metadata.")

    # High quality fallback based on filename and channel brand
    print(f"[AI] Using smart metadata generator based on video: '{clean_filename}'")
    short_tag = " #Shorts" if is_short else ""
    return {
        "title": f"किसान भाई जरूर देखें: {clean_filename[:50]}{short_tag}",
        "description": (
            f"राम-राम किसान भाइयों! आज के इस वीडियो में {clean_filename} के बारे में महत्वपूर्ण जानकारी दी गई है।\n\n"
            f"खेती-किसानी के नए तौर-तरीकों, आधुनिक तकनीकों और सरकारी योजनाओं के लिए 'किसान बदलेगा' चैनल को अभी सब्सक्राइब करें!\n\n"
            f"#KisanBadlega #KhetiBadi #Kisan #FarmingInIndia #Agriculture{short_tag}"
        ),
        "tags": [
            "Kisan Badlega",
            "kheti",
            "kisan",
            "agriculture",
            "kheti badi",
            "modern farming",
            "pm kisan"
        ]
    }

def download_drive_video(drive_url: str, dest_dir: str) -> list:
    """Downloads a file or folder from Google Drive using gdown."""
    print(f"[Drive] Downloading from Google Drive: {drive_url}")
    
    # Check if folder link
    if "folders/" in drive_url:
        print("[Drive] Detected Google Drive folder link, downloading all videos...")
        gdown.download_folder(url=drive_url, output=dest_dir, quiet=False, use_cookies=False)
    else:
        output_file = os.path.join(dest_dir, "drive_video.mp4")
        gdown.download(url=drive_url, output=output_file, quiet=False, fuzzy=True)

    # Gather all video files found
    exts = ("*.mp4", "*.mkv", "*.mov", "*.webm", "*.avi")
    found_videos = []
    for ext in exts:
        found_videos.extend(glob.glob(os.path.join(dest_dir, "**", ext), recursive=True))

    if not found_videos:
        sys.exit("[Drive] Error: No video files (.mp4, .mov, etc.) were found in the Google Drive download.")
    return found_videos

def process_and_upload_drive_video(drive_url: str, privacy: str = "private"):
    cfg = load_config()
    print("=" * 60)
    print("🚜 GOOGLE DRIVE AUTO-METADATA & UPLOAD PIPELINE (KISAN BADLEGA)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        videos = download_drive_video(drive_url, tmpdir)
        print(f"[Drive] Found {len(videos)} video(s) to process.")

        for idx, video_path in enumerate(videos, 1):
            print(f"\n--- Processing Video [{idx}/{len(videos)}]: {os.path.basename(video_path)} ---")
            duration, w, h = get_video_info(video_path)
            is_short = (duration <= 60 or h > w)
            print(f"[Video Details] Duration: {duration:.1f}s | Resolution: {w}x{h} | Type: {'Shorts (9:16)' if is_short else 'Standard (16:9)'}")

            # AI Metadata Generation
            metadata = generate_metadata_from_audio(video_path, is_short=is_short)
            print(f"\n--- AUTO-GENERATED METADATA ---")
            print(f"Title: {metadata['title']}")
            print(f"Tags: {', '.join(metadata.get('tags', []))}")
            print(f"Description:\n{metadata['description'][:200]}...")
            print("-------------------------------\n")

            # Upload to YouTube
            tags = metadata.get("tags", []) + cfg.get("default_tags", [])
            category = cfg.get("category_id", "27")
            upload_privacy = privacy or cfg.get("upload_privacy", "private")

            vid = upload_local_file(
                video_path=video_path,
                title=metadata["title"],
                description=metadata["description"],
                tags=tags,
                privacy=upload_privacy,
                category=category
            )
            print(f"🎉 UPLOAD SUCCESS: https://www.youtube.com/watch?v={vid}")

    print("=" * 60)
    print("✅ All Google Drive videos processed and uploaded successfully!")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Google Drive File or Folder Share Link")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    args = parser.parse_args()

    process_and_upload_drive_video(args.url, args.privacy)
