import asyncio
import os
import re
import shutil
import subprocess
import sys
import tempfile
import edge_tts
import requests

# Default royalty-free vertical tech background loops
STOCK_VIDEO_URLS = [
    "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
]

async def create_speech_and_srt(text: str, voice: str, audio_path: str, srt_path: str):
    """Generates MP3 audio and timed SRT subtitles using edge-tts."""
    comm = edge_tts.Communicate(text, voice=voice)
    sub = edge_tts.SubMaker()
    
    with open(audio_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                sub.feed(chunk)
                
    srt_content = sub.get_srt()
    if not srt_content.strip():
        # Fallback simple subtitle if WordBoundary wasn't emitted
        srt_content = f"1\n00:00:00,000 --> 00:00:30,000\n{text[:100]}...\n"
        
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"[TTS] Generated audio: {audio_path} and subtitles: {srt_path}")

def get_audio_duration(audio_path: str) -> float:
    """Gets audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def generate_procedural_background(duration: float, output_bg: str):
    """
    Creates a sleek dark-mode vertical background (720x1280, 9:16) with FFmpeg.
    Runs 100% offline with zero network dependency.
    """
    print(f"[Video] Creating procedural animated tech background for {duration:.1f}s...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0a0f1d:s=720x1280:r=30:d={duration}",
        "-f", "lavfi",
        "-i", f"cellauto=s=720x1280:r=15:rule=30:seed=1234:d={duration}",
        "-filter_complex",
        "[1:v]format=rgba,colorchannelmixer=aa=0.08[noise];[0:v][noise]overlay=shortest=1",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        output_bg
    ]
    # Simple fallback if cellauto fails
    simple_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0d1117:s=720x1280:r=30:d={duration}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        output_bg
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception:
        subprocess.run(simple_cmd, check=True, capture_output=True)

def build_short_video(
    script_text: str,
    output_path: str,
    voice: str = "hi-IN-MadhurNeural"
) -> str:
    """
    Combines TTS audio, background, audio visualizer waveform, and Hindi subtitles into a 9:16 Short.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_file = os.path.join(tmpdir, "voice.mp3")
        srt_file = os.path.join(tmpdir, "subs.srt")
        bg_file = os.path.join(tmpdir, "bg.mp4")

        # 1. Generate Voice and Subtitles
        asyncio.run(create_speech_and_srt(script_text, voice, audio_file, srt_file))
        duration = get_audio_duration(audio_file) + 0.5

        # 2. Prepare Background
        generate_procedural_background(duration, bg_file)

        # 3. Assemble final video with subtitles and sound waveform
        print("[Video] Merging audio, background, visualizer, and subtitles...")
        
        # Relative path for srt works best across platforms inside tmpdir
        shutil.copy(srt_file, "current_subs.srt")

        # Subtitle styling: bold yellow font with black outline, centered, position slightly below center
        sub_filter = (
            "subtitles=current_subs.srt:force_style="
            "'FontName=Arial,FontSize=20,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,"
            "BorderStyle=3,Outline=2.5,Shadow=1,Alignment=2,MarginV=260'"
        )
        
        # Audio visualizer overlay
        filter_complex = (
            f"[0:v]{sub_filter}[subbed];"
            f"[1:a]showwaves=s=600x120:mode=line:colors=0x00f2fe|0x4facfe:r=30[waves];"
            f"[subbed][waves]overlay=(W-w)/2:H-200:shortest=1[outv]"
        )

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", bg_file,
            "-i", audio_file,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(duration),
            output_path
        ]

        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print("[Video] Advanced filter failed, trying clean fallback without wave overlay...")
            # Simpler fallback: background + audio + subtitles
            simple_ffmpeg = [
                "ffmpeg", "-y",
                "-i", bg_file,
                "-i", audio_file,
                "-vf", sub_filter,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-c:a", "aac",
                "-t", str(duration),
                output_path
            ]
            try:
                subprocess.run(simple_ffmpeg, check=True, capture_output=True)
            except subprocess.CalledProcessError as e2:
                print(f"[Video] Subtitle filter fallback: {e2.stderr.decode(errors='ignore') if e2.stderr else e2}")
                # Pure audio + bg fallback if subtitles filter encounters font issues
                pure_ffmpeg = [
                    "ffmpeg", "-y",
                    "-i", bg_file,
                    "-i", audio_file,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-t", str(duration),
                    output_path
                ]
                subprocess.run(pure_ffmpeg, check=True)
        finally:
            if os.path.exists("current_subs.srt"):
                os.remove("current_subs.srt")

    print(f"[Video] Successfully generated YouTube Short video: {output_path}")
    return output_path

if __name__ == "__main__":
    test_script = (
        "नमस्ते दोस्तों! क्या आप जानते हैं कि आर्टिफिशियल इंटेलिजेंस ने अब कोडिंग को पूरी तरह बदल दिया है? "
        "अब AI टूल्स की मदद से सेकंडों में ऐप्स और वीडियो बनाए जा सकते हैं। "
        "अगर आप भी ऐसी ही लेटेस्ट टेक अपडेट्स चाहते हैं, तो अभी सब्सक्राइब करें!"
    )
    out = os.path.abspath("test_short.mp4")
    build_short_video(test_script, out)
