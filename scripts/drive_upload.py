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
from thumbnail_generator import create_video_thumbnail

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
    """Uses Gemini inline audio listening or Speech Recognition to create viral, high-SEO Hindi metadata for Kisan Badlega."""
    import base64
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    clean_filename = os.path.splitext(os.path.basename(video_path))[0]
    clean_filename = re.sub(r"[_\-]+", " ", clean_filename)

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = os.path.join(tmp, "audio_compressed.mp3")
        extract_audio(video_path, audio_path)

        short_instruction = "This is a YouTube Short (under 60s). Must add #Shorts in title and description." if is_short else "This is a full-length YouTube video."
        seo_prompt = (
            "You are India's top YouTube SEO strategist and content director for the Hindi Agriculture channel 'Kisan Badlega' (किसान बदलेगा).\n"
            "Listen to this audio track from our newly uploaded agriculture video. Understand the exact crops, diseases, fertilizers, government schemes, or techniques discussed.\n"
            f"Context: {short_instruction}\n\n"
            "Generate an elite, high-retention YouTube SEO package tailored for Indian farmers. Return ONLY a valid JSON object with these EXACT keys:\n"
            "{\n"
            '  "title": "Ultra high-CTR Hindi / Hinglish Title under 65 chars. Must create irresistible curiosity or promise big profit/warning, ending with #KisanBadlega #Shorts",\n'
            '  "description": "Comprehensive, highly formatted YouTube description in Hindi. Structure:\\n- Powerful Hook sentence\\n- 📌 प्रमुख बिंदु (3-4 bullet points from the video)\\n- 💡 किसान भाइयों के लिए विशेष सलाह\\n- 🌾 चैनल परिचय (किसान बदलेगा को सब्सक्राइब करें)\\n- ⚠️ अस्वीकरण (Disclaimer)\\n- 🏷️ 15+ trending hashtags including #KisanBadlega #KhetiBadi #IndianAgriculture",\n'
            '  "tags": ["Kisan Badlega", "kheti", "kisan", "agriculture", "...at least 20 highly searched farming keywords in Hindi and English..."],\n'
            '  "thumb_headline": "3 to 5 BIG PUNCHY Hindi words for the top thumbnail headline (e.g. गेहूं में ये 1 स्प्रे डालो!)",\n'
            '  "thumb_subheadline": "Shocking or high-benefit subheadline (e.g. 3 गुना पैदावार की पक्की गारंटी!)",\n'
            '  "crop_name": "Name of crop or topic (e.g. गेहूं, टमाटर, सरसों, PM किसान)",\n'
            '  "key_benefit": "Main promise/benefit (e.g. 3 गुना पैदावार गारंटी!)",\n'
            '  "thumb_points": ["पॉइंट 1", "पॉइंट 2", "पॉइंट 3"]\n'
            "}"
        )

        # 1. Primary: Direct Base64 inline audio to Gemini (with multi-model fallback)
        if gemini_key:
            try:
                print("[AI SEO Engine] Uploading audio directly to Gemini for Hindi listening...")
                with open(audio_path, "rb") as af:
                    audio_b64 = base64.b64encode(af.read()).decode("utf-8")

                candidate_models = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
                for model_name in candidate_models:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                    payload = {
                        "contents": [
                            {
                                "parts": [
                                    {"inlineData": {"mimeType": "audio/mp3", "data": audio_b64}},
                                    {"text": seo_prompt}
                                ]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.4
                        }
                    }
                    try:
                        r = requests.post(url, json=payload, timeout=90)
                        if r.status_code == 200:
                            resp_data = r.json()
                            raw_text = resp_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
                            raw_json = match.group(1).strip() if match else raw_text
                            data = json.loads(raw_json)
                            if "title" in data and "description" in data:
                                print(f"[AI SEO Engine] Successfully created viral Hindi metadata via {model_name}!")
                                return data
                        else:
                            print(f"[AI SEO Engine] {model_name} failed (HTTP {r.status_code}): {r.text[:150]}")
                    except Exception as me:
                        print(f"[AI SEO Engine] Error calling {model_name}: {me}")
            except Exception as e:
                print(f"[AI SEO Engine] Gemini inline audio error: {e}")

        # 2. Secondary: Speech Recognition to transcribe Hindi speech
        try:
            import speech_recognition as sr
            print("[AI SEO Engine] Attempting Hindi speech-to-text recognition...")
            wav_path = os.path.join(tmp, "speech.wav")
            cmd = ["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", wav_path]
            subprocess.run(cmd, capture_output=True, check=True)

            r_sr = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_rec = r_sr.record(source, duration=90)
                transcript = r_sr.recognize_google(audio_rec, language="hi-IN")
                print(f"[AI SEO Engine] Transcribed Hindi text: {transcript[:100]}...")

                # Ask AI to generate from transcript
                if gemini_key:
                    t_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                    t_payload = {
                        "contents": [{"parts": [{"text": f"{seo_prompt}\n\nSpoken Video Transcript:\n{transcript}"}]}],
                        "generationConfig": {"temperature": 0.4}
                    }
                    t_r = requests.post(t_url, json=t_payload, timeout=45)
                    if t_r.status_code == 200:
                        t_data = json.loads(re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", t_r.json()["candidates"][0]["content"]["parts"][0]["text"]).group(1).strip())
                        return t_data
        except Exception as e_sr:
            print(f"[AI SEO Engine] Speech recognition fallback: {e_sr}")

    # 3. High-Quality Brand Fallback (Never show 'drive_video')
    print("[AI SEO Engine] Using high-retention agricultural SEO template...")
    short_tag = " #Shorts" if is_short else ""
    return {
        "title": f"किसान भाई जरूर देखें: खेती में 3 गुना बंपर मुनाफा | #KisanBadlega{short_tag}",
        "description": (
            "राम-राम किसान भाइयों! 🌾\n\n"
            "आज के इस वीडियो में खेती-किसानी से जुड़ी बेहद महत्वपूर्ण जानकारी दी गई है। "
            "कम लागत में ज्यादा मुनाफा कैसे कमाएं और आधुनिक कृषि तकनीकों का सही इस्तेमाल कैसे करें।\n\n"
            "📌 मुख्य बिंदु:\n"
            "1️⃣ सही समय पर सही खाद और सिंचाई का चुनाव\n"
            "2️⃣ कम लागत में 3 गुना पैदावार की तकनीक\n"
            "3️⃣ सरकारी कृषि सब्सिडी योजनाओं का पूरा लाभ\n\n"
            "💡 किसान सलाह: हमेशा प्रमाणित बीज और जैविक उर्वरक का उपयोग करें।\n\n"
            "🌾 खेती-किसानी के नए तौर-तरीकों के लिए 'किसान बदलेगा' चैनल को अभी सब्सक्राइब करें!\n"
            "जय जवान, जय किसान! 🚜\n\n"
            "#KisanBadlega #KhetiBadi #IndianAgriculture #Kisan #ModernFarming #FarmingTips #PMKisan #KisanSammanNidhi #OrganicFarming #KrishiDarshan"
        ),
        "tags": [
            "Kisan Badlega", "kheti", "kisan", "agriculture", "kheti badi",
            "modern farming", "farming in india", "gehu ki kheti", "tamatar ki kheti",
            "kisan samman nidhi", "pm kisan", "organic farming", "drip irrigation",
            "krishi yojana", "mandi bhav today", "crop insurance", "smart farming"
        ],
        "thumb_headline": "खेती में 3 गुना मुनाफा!",
        "thumb_subheadline": "कम लागत में बंपर पैदावार की गारंटी!",
        "crop_name": "आधुनिक खेती",
        "key_benefit": "3 गुना पैदावार गारंटी!",
        "thumb_points": ["कम लागत", "3 गुना मुनाफा", "सरकारी सब्सिडी"]
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
        match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", drive_url) or re.search(r"id=([a-zA-Z0-9_-]+)", drive_url)
        if match:
            gdown.download(id=match.group(1), output=output_file, quiet=False)
        else:
            gdown.download(url=drive_url, output=output_file, quiet=False)

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

            # Generate Custom Hindi Thumbnail (16:9, 1280x720)
            out_dir = os.path.join(ROOT, "output")
            os.makedirs(out_dir, exist_ok=True)
            thumb_path = os.path.join(out_dir, f"thumb_{os.path.basename(video_path)}.jpg")
            create_video_thumbnail(
                topic_or_title=f"{metadata.get('title', '')}\n{metadata.get('description', '')}",
                output_path=thumb_path,
                preferred_style="auto"
            )

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
                category=category,
                thumbnail_path=thumb_path
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
