import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus
import feedparser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
    cfg = json.load(f)

query = cfg.get("google_news_query") or cfg.get("domain", "technology")
region = cfg.get("region", "IN")
lang = "hi" if cfg.get("language", "").lower().startswith("hindi") else "en"
url = (
    "https://news.google.com/rss/search?q=" + quote_plus(query)
    + "&hl=" + lang + "&gl=" + region + "&ceid=" + region + ":" + lang
)
feed = feedparser.parse(url)
entries = feed.entries[:int(cfg.get("max_items", 15))]

today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
out_dir = os.path.join(ROOT, "output")
os.makedirs(out_dir, exist_ok=True)
path = os.path.join(out_dir, f"research_brief_{today}.md")

lines = [
    f"# Topic research brief — {cfg.get('domain', query)}",
    "",
    f"- Generated (UTC): {datetime.now(timezone.utc).isoformat(timespec='minutes')}",
    f"- Domain: {cfg.get('domain', query)}",
    f"- Language preference: {cfg.get('language', 'English')}",
    "- Note: these are candidate stories from an RSS search, not independently fact-checked conclusions.",
    "",
    "## Candidate topics",
    ""
]
if not entries:
    lines += ["No RSS results were returned. Try a broader `google_news_query` in `config.json`.", ""]
for i, item in enumerate(entries, 1):
    title = re.sub(r"\s+", " ", item.get("title", "Untitled")).strip()
    link = item.get("link", "")
    published = item.get("published", "Date unavailable")
    summary = re.sub(r"<[^>]+>", " ", item.get("summary", ""))
    summary = re.sub(r"\s+", " ", summary).strip()
    lines += [
        f"### {i}. {title}",
        f"- Published: {published}",
        f"- Source: {link}",
        f"- RSS snippet: {summary[:500] if summary else 'No snippet provided.'}",
        ""
    ]

lines += [
    "## Research checklist before using NotebookLM",
    "- Open original articles and verify the source, date, author, and underlying evidence.",
    "- Prefer primary sources, official documentation, peer-reviewed papers, and original data.",
    "- Check whether multiple outlets are repeating the same original report.",
    "- Note conflicting claims, uncertainty, and what is not known.",
    "- Do not copy another creator's script or use unlicensed video/music.",
    "",
    "## NotebookLM handoff",
    "1. Choose one topic from the list.",
    "2. Add the verified source URLs/documents to a NotebookLM notebook.",
    "3. Generate a Video Overview using the UI if available for your account.",
    "4. Review names, numbers, claims, and visuals, then export/download the video.",
    "",
    "## Suggested structure",
    "1. Hook / question",
    "2. Background and why it matters",
    "3. Three evidence-backed findings",
    "4. Limitations or counterpoint",
    "5. Summary and source list",
    ""
]
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Created: {path}")
print(f"Feed entries found: {len(entries)}")
