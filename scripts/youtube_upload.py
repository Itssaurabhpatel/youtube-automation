import argparse
import os
import sys
import tempfile
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default=os.getenv("VIDEO_URL", ""))
    p.add_argument("--title", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--tags", default="")
    p.add_argument("--privacy", choices=["private", "unlisted", "public"], default="private")
    p.add_argument("--category", default="27")
    args = p.parse_args()

    client_id = os.getenv("YT_CLIENT_ID")
    client_secret = os.getenv("YT_CLIENT_SECRET")
    refresh_token = os.getenv("YT_REFRESH_TOKEN")
    if not all([client_id, client_secret, refresh_token]):
        sys.exit("Missing YT_CLIENT_ID, YT_CLIENT_SECRET, or YT_REFRESH_TOKEN environment secret.")
    if not args.url:
        sys.exit("No video URL supplied. Provide --url or VIDEO_URL secret.")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    youtube = build("youtube", "v3", credentials=creds)

    # Download to runner temp storage. URL must serve the actual file, not an HTML preview.
    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, "video.mp4")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        with requests.get(args.url, headers=headers, stream=True, timeout=(30, 180)) as r:
            r.raise_for_status()
            content_type = r.headers.get("Content-Type", "").lower()
            if "text/html" in content_type:
                sys.exit("The supplied URL returned HTML, not a direct video download. Use a direct MP4 download URL.")
            with open(video_path, "wb") as out:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        out.write(chunk)
        if os.path.getsize(video_path) < 1024:
            sys.exit("Downloaded file is too small; verify the direct-download URL.")

        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        body = {
            "snippet": {
                "title": args.title[:100],
                "description": args.description[:5000],
                "categoryId": str(args.category),
                "tags": tags[:500],
            },
            "status": {
                "privacyStatus": args.privacy,
                "selfDeclaredMadeForKids": False
            }
        }
        media = MediaFileUpload(video_path, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
        vid = response["id"]
        print(f"UPLOAD_SUCCESS privacy={args.privacy}")
        print(f"VIDEO_URL=https://www.youtube.com/watch?v={vid}")

if __name__ == "__main__":
    main()
