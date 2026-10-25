# -*- coding: utf-8 -*-
import json
import os
import re
import sys
import requests

def clean_json_response(raw_text: str) -> dict:
    raw_text = raw_text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
    if match:
        raw_text = match.group(1).strip()
    return json.loads(raw_text)

def call_gemini(api_key: str, prompt: str, system_prompt: str) -> str:
    api_key = api_key.strip()
    models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-2.0-flash", "gemini-pro"]
    last_err = None
    for model in models:
        for ver in ["v1beta", "v1"]:
            url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {"parts": [{"text": f"{system_prompt}\n\nTask:\n{prompt}"}]}
                ],
                "generationConfig": {
                    "temperature": 0.7
                }
            }
            try:
                r = requests.post(url, json=payload, timeout=40)
                if r.status_code == 200:
                    data = r.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                last_err = f"HTTP {r.status_code}: {r.text[:250]}"
            except Exception as e:
                last_err = str(e)
    raise Exception(f"Gemini API failed on all models: {last_err}")

def call_grok(api_key: str, prompt: str, system_prompt: str) -> str:
    api_key = api_key.strip()
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    models = ["grok-beta", "grok-2", "grok-2-1212"]
    last_err = None
    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt + "\nRespond ONLY with a valid JSON object."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=40)
            if r.status_code == 200:
                data = r.json()
                return data["choices"][0]["message"]["content"]
            last_err = f"HTTP {r.status_code}: {r.text[:250]}"
        except Exception as e:
            last_err = str(e)
    raise Exception(f"Grok API failed on all models: {last_err}")

def call_claude(api_key: str, prompt: str, system_prompt: str) -> str:
    api_key = api_key.strip()
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    models = ["claude-3-5-haiku-20241022", "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"]
    last_err = None
    for model in models:
        payload = {
            "model": model,
            "max_tokens": 1500,
            "system": system_prompt + "\nRespond ONLY with valid JSON, no markdown backticks.",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=40)
            if r.status_code == 200:
                data = r.json()
                return data["content"][0]["text"]
            last_err = f"HTTP {r.status_code}: {r.text[:250]}"
        except Exception as e:
            last_err = str(e)
    raise Exception(f"Claude API failed on all models: {last_err}")

def build_fallback_kisan_script(topic_info: str) -> dict:
    """Smart fallback generator if AI providers have network/key issues."""
    print("[AI Writer] Using smart Kisan Badlega script fallback...")
    clean_topic = re.sub(r"Title:\s*", "", topic_info).split("\n")[0][:80]
    return {
        "title": f"किसान भाइयों के लिए बड़ी खबर | #KisanBadlega #Shorts",
        "description": f"{clean_topic}\n\nखेती-किसानी की ताजा जानकारी और मुनाफे के लिए सब्सक्राइब करें किसान बदलेगा। #KisanBadlega #KhetiBadi #Shorts #Kisan",
        "tags": ["Kisan Badlega", "kisan", "kheti", "pm kisan", "agriculture", "shorts"],
        "script": (
            f"राम-राम किसान भाइयों! आज की सबसे बड़ी अपडेट खेती-किसानी से जुड़ी है। "
            f"{clean_topic}। "
            f"किसान साथियों, सही समय पर सही तकनीक और सरकारी योजनाओं का लाभ लेकर आप अपनी आमदनी को दोगुना कर सकते हैं। "
            f"खेती में ज्यादा मुनाफे और नई तकनीकों के लिए किसान बदलेगा को अभी सब्सक्राइब करें। जय जवान, जय किसान!"
        )
    }

def generate_hindi_script(topic_info: str, preferred_provider: str = "auto") -> dict:
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    claude_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    grok_key = (os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY") or "").strip()

    providers = []
    preferred = preferred_provider.lower().strip()
    if preferred == "gemini" and gemini_key:
        providers = [("gemini", gemini_key, call_gemini)]
    elif preferred == "claude" and claude_key:
        providers = [("claude", claude_key, call_claude)]
    elif preferred in ("grok", "xai") and grok_key:
        providers = [("grok", grok_key, call_grok)]

    # Add available fallbacks
    all_available = []
    if grok_key:
        all_available.append(("grok", grok_key, call_grok))
    if gemini_key:
        all_available.append(("gemini", gemini_key, call_gemini))
    if claude_key:
        all_available.append(("claude", claude_key, call_claude))

    for p in all_available:
        if p not in providers:
            providers.append(p)

    if not providers:
        print("[AI Writer] Warning: No API keys configured, using high-retention fallback script.")
        return build_fallback_kisan_script(topic_info)

    system_prompt = (
        "You are an expert agricultural content creator and video scriptwriter for the popular Hindi YouTube channel 'Kisan Badlega' (किसान बदलेगा). "
        "Target Audience: Indian farmers (किसान भाई), agri-entrepreneurs, and rural youth interested in modern, profitable farming. "
        "Tone: Respectful, energetic, motivating, and practical (देसी और आदरपूर्ण लहज़ा, e.g., 'राम-राम किसान भाइयों!', 'किसान साथियों!'). "
        "Core Niches: Modern farming techniques (ड्रिप, पॉलीहाउस, जैविक खाद), high-profit crops (सब्जी, बागवानी, कम लागत ज्यादा मुनाफा), government subsidies (PM Kisan, सब्सिडी योजना), farm machinery, and Mandi updates. "
        "You must output ONLY a valid JSON object with the following keys:\n"
        "{\n"
        '  "title": "Catchy Hindi / Hinglish YouTube Shorts title with #Shorts (under 70 chars, e.g. किसान भाई इस तकनीक से कमाएं लाखों | #Shorts)",\n'
        '  "description": "Short Hindi description highlighting the tips, mentioning channel किसान बदलेगा, with hashtags #KisanBadlega #KhetiBadi #Shorts #Agriculture #Kisan",\n'
        '  "tags": ["Kisan Badlega", "kisan", "kheti badi", "agriculture", "modern farming", "pm kisan", "shorts"],\n'
        '  "script": "The narration in pure spoken Hindi (Devanagari script only). 85 to 110 words (about 40-45 seconds when spoken). Must start with a warm farmer greeting like \'राम-राम किसान भाइयों!\' or \'किसान साथियों!\' followed by an eye-opening hook. Explain 2-3 actionable, high-value farming tips or scheme details simply. End with: \'खेती में ज्यादा मुनाफे और नई तकनीकों के लिए किसान बदलेगा को अभी सब्सक्राइब करें। जय जवान, जय किसान!\' Absolutely NO emojis, NO brackets or sound effect cues [like music], NO English alphabet in the script - strictly spoken Hindi words only."\n'
        "}"
    )

    user_prompt = (
        f"Channel: Kisan Badlega (किसान बदलेगा)\n"
        f"Topic / Agriculture News:\n{topic_info}\n\n"
        f"Create an engaging, viral 40-50 second Hindi YouTube Short script tailored for Indian farmers."
    )

    for name, key, fn in providers:
        try:
            print(f"[AI Writer] Attempting generation with provider: {name}...")
            raw = fn(key, user_prompt, system_prompt)
            parsed = clean_json_response(raw)
            if "script" in parsed and "title" in parsed:
                print(f"[AI Writer] Successfully generated Hindi script using {name}!")
                return parsed
        except Exception as e:
            print(f"[AI Writer] Provider {name} failed: {e}")

    print("[AI Writer] All configured AI providers had errors. Engaging smart fallback...")
    return build_fallback_kisan_script(topic_info)

if __name__ == "__main__":
    test_topic = sys.argv[1] if len(sys.argv) > 1 else "PM Kisan 24th installment release date"
    result = generate_hindi_script(test_topic)
    print(json.dumps(result, ensure_ascii=False, indent=2))
