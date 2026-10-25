import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import quote_plus
import feedparser

# Add scripts directory to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, "scripts"))

from ai_writer import generate_hindi_script
from create_video import build_short_video
from youtube_upload import upload_local_file

def load_config() -> dict:
    cfg_path = os.path.join(ROOT, "config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def fetch_trending_hindi_topic(cfg: dict) -> str:
    query = cfg.get("google_news_query", "AI tools OR artificial intelligence OR तकनीक")
    region = cfg.get("region", "IN")
    lang = "hi" if cfg.get("language", "Hindi").lower().startswith("hindi") else "en"
    
    url = (
        "https://news.google.com/rss/search?q=" + quote_plus(query)
        + "&hl=" + lang + "&gl=" + region + "&ceid=" + region + ":" + lang
    )
    print(f"[Pipeline] Fetching top Hindi news from: {url}")
    feed = feedparser.parse(url)
    if not feed.entries:
        return "आर्टिफिशियल इंटेलिजेंस और नए टेक टूल्स के फायदे और लेटेस्ट फीचर्स"

    # Take the first entry
    first = feed.entries[0]
    title = re.sub(r"\s+", " ", first.get("title", "")).strip()
    summary = re.sub(r"<[^>]+>", " ", first.get("summary", "")).strip()
    topic = f"Title: {title}\nSummary: {summary}"
    print(f"[Pipeline] Selected topic: {title}")
    return topic

def run_pipeline(
    custom_topic: str = "",
    preferred_provider: str = "auto",
    privacy: str = "private",
    skip_upload: bool = False
):
    cfg = load_config()
    print("=" * 60)
    print("🚀 STARTING AUTOMATED HINDI YOUTUBE SHORTS PIPELINE")
    print("=" * 60)

    # 1. Topic Selection
    if custom_topic.strip():
        topic_info = custom_topic.strip()
        print(f"[1/4] Using custom topic:\n{topic_info}")
    else:
        print("[1/4] Researching trending Hindi topic...")
        topic_info = fetch_trending_hindi_topic(cfg)

    # 2. AI Hindi Script Generation
    provider = preferred_provider if preferred_provider != "auto" else cfg.get("ai_provider", "auto")
    print(f"\n[2/4] Generating Hindi Short script with AI (Provider: {provider})...")
    script_data = generate_hindi_script(topic_info, preferred_provider=provider)
    
    print("\n--- GENERATED SCRIPT DETAILS ---")
    print(f"Title: {script_data.get('title')}")
    print(f"Tags: {', '.join(script_data.get('tags', []))}")
    print(f"Script: {script_data.get('script')}")
    print("--------------------------------\n")

    # 3. Voiceover, Subtitles & Video Generation
    voice = cfg.get("voice", "hi-IN-MadhurNeural")
    out_dir = os.path.join(ROOT, "output")
    os.makedirs(out_dir, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    video_path = os.path.join(out_dir, f"short_{today}.mp4")

    print(f"[3/4] Synthesizing Hindi voice ({voice}) and building 9:16 Short...")
    build_short_video(
        script_text=script_data["script"],
        output_path=video_path,
        voice=voice
    )

    # 4. Upload to YouTube
    if skip_upload:
        print(f"\n[4/4] Video generated successfully at: {video_path} (Upload skipped)")
        return video_path

    print(f"\n[4/4] Uploading video to YouTube (Privacy: {privacy})...")
    upload_privacy = privacy or cfg.get("upload_privacy", "private")
    category = cfg.get("category_id", "27")
    tags = script_data.get("tags", []) + cfg.get("default_tags", [])

    vid = upload_local_file(
        video_path=video_path,
        title=script_data.get("title", "Hindi Tech Short #Shorts"),
        description=script_data.get("description", "Hindi AI Tech Short #Shorts"),
        tags=tags,
        privacy=upload_privacy,
        category=category
    )
    print("=" * 60)
    print(f"🎉 PIPELINE COMPLETED! Video live: https://www.youtube.com/watch?v={vid}")
    print("=" * 60)
    return video_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="", help="Custom topic to override RSS research")
    parser.add_argument("--provider", default="auto", choices=["auto", "gemini", "claude", "grok"], help="Preferred AI provider")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"], help="YouTube privacy")
    parser.add_argument("--skip-upload", action="store_true", help="Generate video without uploading")
    args = parser.parse_args()

    run_pipeline(
        custom_topic=args.topic,
        preferred_provider=args.provider,
        privacy=args.privacy,
        skip_upload=args.skip_upload
    )
