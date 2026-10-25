# -*- coding: utf-8 -*-
"""
Complete Automation from Topic to Post (Kisan Badlega)
Steps:
1. Topic Discovery & Research (User provided or Auto-Trending from Agriculture Niche)
2. 16:9 Video Production (NotebookLM URL processing or 100% Autonomous AI generation)
3. SEO Generation (High-CTR Title, Rich Structured Description, 25+ Tags)
4. Attractive High-CTR 16:9 Thumbnail Generation
5. Automatic YouTube Publishing
"""

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from urllib.parse import quote_plus
import feedparser
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, "scripts"))

from youtube_upload import upload_local_file
from drive_upload import extract_audio, get_video_info, generate_metadata_from_audio, load_config
from watermark_handler import apply_watermark_removal
from thumbnail_generator import create_video_thumbnail
from create_video import build_landscape_video
from intro_trim_upload import download_file, trim_video, merge_intro_and_video

def fetch_trending_agriculture_topic() -> dict:
    """Discovers the top trending agricultural news topic in India."""
    cfg = load_config()
    query = cfg.get("google_news_query", "खेती OR किसान OR 'PM Kisan' OR 'कृषि योजना' OR 'फसल' OR 'कृषि'")
    region = cfg.get("region", "IN")
    lang = "hi" if cfg.get("language", "Hindi").lower().startswith("hindi") else "en"
    
    url = (
        "https://news.google.com/rss/search?q=" + quote_plus(query)
        + "&hl=" + lang + "&gl=" + region + "&ceid=" + region + ":" + lang
    )
    print(f"[Topic Discovery] Fetching latest Hindi agriculture news from RSS...")
    try:
        feed = feedparser.parse(url)
        if feed.entries:
            first = feed.entries[0]
            title = re.sub(r"\s+", " ", first.get("title", "")).strip()
            summary = re.sub(r"<[^>]+>", " ", first.get("summary", "")).strip()
            print(f"[Topic Discovery] Found trending story: {title}")
            return {"title": title, "summary": summary, "source": first.get("link", "")}
    except Exception as e:
        print(f"[Topic Discovery] RSS parsing error: {e}")

    # High-retention evergreen fallback
    return {
        "title": "गेहूं और सरसों में बंपर पैदावार की आधुनिक वैज्ञानिक तकनीक",
        "summary": "कम पानी में 40 क्विंटल पैदावार, सही खाद का समय, और ड्रिप सिंचाई पर सरकारी सब्सिडी।",
        "source": "https://agricoop.nic.in"
    }

def generate_landscape_script_ai(topic_text: str) -> dict:
    """Uses Gemini to research the topic and write a full 16:9 Hindi video script."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    prompt = (
        "You are the chief scriptwriter for India's leading Hindi Agriculture YouTube channel 'Kisan Badlega' (किसान बदलेगा).\n"
        f"Topic to research and write about:\n{topic_text}\n\n"
        "Write an engaging, high-retention 16:9 video script in simple, conversational Hindi (शुद्ध एवं सरल हिन्दी भाषा).\n"
        "Requirements:\n"
        "1. Hook: Start with a powerful 5-second greeting and hook for Indian farmers.\n"
        "2. 3 Actionable Scientific Tips / Solutions (फसल सुरक्षा, सही खाद तकनीक, सिंचाई नियम).\n"
        "3. High profit potential and government scheme advice.\n"
        "4. Call to action: Subscribe to 'Kisan Badlega'.\n\n"
        "Return ONLY a valid JSON object with these EXACT keys:\n"
        "{\n"
        '  "title": "Punchy Hindi Title under 65 chars with emojis and #KisanBadlega",\n'
        '  "script": "Full spoken Hindi text (approx 200-250 words, natural speech, no bracketed stage directions)",\n'
        '  "crop_name": "Main crop name or topic (e.g. गेहूं, टमाटर, सरसों, PM किसान)",\n'
        '  "thumb_headline": "3-5 HUGE punchy Hindi words for thumbnail",\n'
        '  "thumb_subheadline": "Benefit subheadline for thumbnail",\n'
        '  "key_benefit": "3 गुना पैदावार गारंटी!",\n'
        '  "thumb_points": ["पॉइंट 1", "पॉइंट 2", "पॉइंट 3"],\n'
        '  "tags": ["Kisan Badlega", "kheti", "kisan", "...20+ tags..."],\n'
        '  "description": "Comprehensive Hindi description with Hook, 📌 मुख्य बिंदु, 💡 किसान सलाह, 🌾 चैनल परिचय, ⚠️ अस्वीकरण, 15+ Hashtags"\n'
        "}"
    )

    if gemini_key:
        models = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        for m in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.4}
            }
            try:
                r = requests.post(url, json=payload, timeout=60)
                if r.status_code == 200:
                    raw_text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
                    raw_json = match.group(1).strip() if match else raw_text
                    data = json.loads(raw_json)
                    if "script" in data and "title" in data:
                        print(f"[AI Writer] Successfully researched and generated script using {m}!")
                        return data
            except Exception as e:
                print(f"[AI Writer] Error with {m}: {e}")

    # Fallback script
    return {
        "title": "किसान भाई ध्यान दें: 1 स्प्रे से 3 गुना बंपर पैदावार! 🌾 #KisanBadlega",
        "script": (
            "राम-राम किसान भाइयों! किसान बदलेगा चैनल में आपका स्वागत है। आज हम बात करेंगे फसलों में बंपर पैदावार लेने के सबसे बड़े सीक्रेट के बारे में। "
            "अक्सर हमारे किसान भाई गलत समय पर महंगी खाद डाल देते हैं जिससे फसल को नुकसान होता है और लागत बढ़ जाती है। "
            "सबसे पहले: मिट्टी की जांच के अनुसार ही नाइट्रोजन और पोटाश का संतुलन बनाएं। दूसरा: सिंचाई हमेशा मौसम और फसल की क्रांतिक अवस्था पर ही करें। "
            "तीसरा: जैविक टॉनिक और सही कीटनाशक का स्प्रे सुबह या शाम के समय करें। अगर आप इन 3 बातों का ध्यान रखेंगे, तो आपकी फसल में 40 क्विंटल तक बंपर पैदावार होगी और मुनाफा 3 गुना बढ़ जाएगा। "
            "खेती-किसानी की हर सच्ची और वैज्ञानिक जानकारी के लिए किसान बदलेगा को अभी सब्सक्राइब करें। जय जवान, जय किसान!"
        ),
        "crop_name": "उन्नत खेती",
        "thumb_headline": "खेती में 3 गुना मुनाफा!",
        "thumb_subheadline": "कम पानी में 40 क्विंटल पैदावार की गारंटी",
        "key_benefit": "3 गुना पैदावार गारंटी!",
        "thumb_points": ["कम लागत", "3 गुना उपज", "लाखों मुनाफा"],
        "tags": [
            "Kisan Badlega", "kheti", "kisan", "agriculture in india", "farming tips",
            "gehu ki kheti", "kheti badi", "pm kisan", "modern farming", "organic farming",
            "drip irrigation", "kisan yojana", "sarso ki kheti", "tamatar ki kheti"
        ],
        "description": (
            "राम-राम किसान भाइयों! 🌾\n\n"
            "आज के इस वीडियो में फसलों में कम लागत में 3 गुना बंपर पैदावार लेने के वैज्ञानिक तरीके बताए गए हैं।\n\n"
            "📌 मुख्य बिंदु:\n"
            "1️⃣ सही समय पर सही खाद और पोषक तत्वों का चुनाव\n"
            "2️⃣ सिंचाई और स्प्रे की सबसे सही तकनीक\n"
            "3️⃣ कृषि लागत में 50% की भारी बचत\n\n"
            "💡 किसान सलाह: हमेशा प्रमाणित बीज और जैविक उर्वरक का उपयोग करें।\n\n"
            "🌾 खेती-किसानी के नए तौर-तरीकों के लिए 'किसान बदलेगा' चैनल को अभी सब्सक्राइब करें!\n"
            "जय जवान, जय किसान! 🚜\n\n"
            "#KisanBadlega #KhetiBadi #IndianAgriculture #FarmingTips #PMKisan #OrganicFarming #KrishiDarshan"
        )
    }

def run_complete_automation(
    topic: str = "",
    video_url: str = "",
    thumbnail_style: str = "auto",
    thumbnail_url: str = "",
    privacy: str = "private"
):
    print("=" * 65)
    print("🚀 COMPLETE AUTOMATION: FROM TOPIC TO YOUTUBE POST (KISAN BADLEGA)")
    print("=" * 65)

    out_dir = os.path.join(ROOT, "output")
    os.makedirs(out_dir, exist_ok=True)
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    with tempfile.TemporaryDirectory() as tmpdir:
        final_video_file = os.path.join(tmpdir, "final_published_video.mp4")
        metadata = {}

        # ----------------------------------------------------
        # STEP 1: Topic Discovery & Research
        # ----------------------------------------------------
        print("\n[STEP 1/5] Finding Topic & Conducting Research...")
        if topic.strip():
            selected_topic = topic.strip()
            print(f"[Topic] User specified custom topic: {selected_topic}")
        else:
            trending = fetch_trending_agriculture_topic()
            selected_topic = f"{trending['title']}. {trending['summary']}"
            print(f"[Topic] Auto-selected trending topic: {selected_topic}")

        # ----------------------------------------------------
        # STEP 2: 16:9 Video Production (NotebookLM or AI Engine)
        # ----------------------------------------------------
        print("\n[STEP 2/5] Producing 16:9 Landscape Video...")
        if video_url.strip():
            # Mode A: Process User's NotebookLM / External Video
            print(f"[Video Mode] Processing provided video link: {video_url}")
            raw_video = os.path.join(tmpdir, "raw_video.mp4")
            trimmed_video = os.path.join(tmpdir, "trimmed_video.mp4")
            intro_file = os.path.join(tmpdir, "intro.mp4")
            merged_video = os.path.join(tmpdir, "merged_video.mp4")

            download_file(video_url.strip(), raw_video)

            # Locate intro
            repo_intro = os.path.join(ROOT, "assets", "intro.mp4")
            if os.path.exists(repo_intro):
                shutil.copy(repo_intro, intro_file)
            else:
                sys.exit("Error: 'assets/intro.mp4' missing in repository!")

            # Trim last 2 seconds (NotebookLM watermark cut)
            trim_video(raw_video, cut_start_seconds=0.0, cut_end_seconds=2.0, output_path=trimmed_video)

            # Merge Intro + Video
            merge_intro_and_video(intro_file, trimmed_video, merged_video)

            # Cover bottom-right watermark with logo.png
            apply_watermark_removal(merged_video, final_video_file, mode="cover_badge")

            # Extract metadata from the video audio
            metadata = generate_metadata_from_audio(final_video_file, is_short=False)

        else:
            # Mode B: 100% Autonomous 16:9 Video Generation
            print("[Video Mode] Generating full 16:9 video from topic research...")
            script_data = generate_landscape_script_ai(selected_topic)
            metadata = script_data

            ai_raw_video = os.path.join(tmpdir, "ai_landscape_video.mp4")
            intro_file = os.path.join(tmpdir, "intro.mp4")
            merged_video = os.path.join(tmpdir, "merged_video.mp4")

            # Build 16:9 Landscape Video with Voice & Subtitles
            build_landscape_video(
                script_text=script_data["script"],
                output_path=ai_raw_video,
                voice="hi-IN-MadhurNeural"
            )

            # Prepend Intro
            repo_intro = os.path.join(ROOT, "assets", "intro.mp4")
            if os.path.exists(repo_intro):
                shutil.copy(repo_intro, intro_file)
                merge_intro_and_video(intro_file, ai_raw_video, merged_video)
            else:
                merged_video = ai_raw_video

            # Overlay channel logo
            apply_watermark_removal(merged_video, final_video_file, mode="cover_badge")

        # Copy final video to output for artifacts
        persisted_video = os.path.join(out_dir, f"video_kisan_badlega_{today_str}.mp4")
        shutil.copy(final_video_file, persisted_video)
        print(f"[Video Produced] Final video saved: {persisted_video}")

        # ----------------------------------------------------
        # STEP 3: High-SEO Metadata Preparation
        # ----------------------------------------------------
        print("\n[STEP 3/5] Finalizing SEO Package (Title, Description, Tags)...")
        if not metadata.get("title"):
            metadata = generate_landscape_script_ai(selected_topic)

        print(f"🎬 Title: {metadata['title']}")
        print(f"🏷️ Tags: {', '.join(metadata.get('tags', []))[:120]}...")
        print(f"📝 Description:\n{metadata['description'][:200]}...\n")

        # ----------------------------------------------------
        # STEP 4: 16:9 YouTube Thumbnail Creation
        # ----------------------------------------------------
        print("\n[STEP 4/5] Producing Attractive 16:9 YouTube Thumbnail...")
        thumb_path = os.path.join(out_dir, f"thumb_kisan_badlega_{today_str}.jpg")

        if thumbnail_url and thumbnail_url.strip():
            print(f"[Thumbnail] Using custom thumbnail from link: {thumbnail_url}")
            download_file(thumbnail_url.strip(), thumb_path)
        else:
            create_video_thumbnail(
                topic_or_title=f"{metadata.get('title', '')}\n{metadata.get('description', '')}",
                output_path=thumb_path,
                preferred_style=thumbnail_style,
                ai_metadata=metadata
            )
        print(f"[Thumbnail Ready] Thumbnail saved: {thumb_path}")

        # ----------------------------------------------------
        # STEP 5: Post on YouTube
        # ----------------------------------------------------
        print(f"\n[STEP 5/5] Publishing Video to YouTube (Privacy: {privacy})...")
        cfg = load_config()
        tags = metadata.get("tags", []) + cfg.get("default_tags", [])
        category = cfg.get("category_id", "27")

        video_id = upload_local_file(
            video_path=final_video_file,
            title=metadata["title"],
            description=metadata["description"],
            tags=tags,
            privacy=privacy,
            category=category,
            thumbnail_path=thumb_path
        )

        print("\n" + "=" * 65)
        print("🎉 COMPLETE AUTOMATION SUCCESSFUL!")
        print(f"📺 Live on YouTube: https://www.youtube.com/watch?v={video_id}")
        print("=" * 65)
        return video_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Complete Automation from Topic to Post (Kisan Badlega)")
    parser.add_argument("--topic", default="", help="Custom topic (leave empty to auto-find trending news)")
    parser.add_argument("--video-url", default="", help="NotebookLM / Drive Video URL (leave empty for auto 16:9 generation)")
    parser.add_argument("--thumbnail-style", default="auto", choices=["auto", "1", "2"], help="Thumbnail Style (1: News Maroon, 2: Tips Yellow)")
    parser.add_argument("--thumbnail-url", default="", help="Custom Thumbnail URL (optional)")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    args = parser.parse_args()

    run_complete_automation(
        topic=args.topic,
        video_url=args.video_url,
        thumbnail_style=args.thumbnail_style,
        thumbnail_url=args.thumbnail_url,
        privacy=args.privacy
    )
