"""Download Google Translate pronunciations for every card into audio/.

Reads the SECTIONS data straight from index.html, so after adding or editing
cards just run:  python generate_audio.py
Existing files are skipped; delete a file (or use --force) to re-download it.
"""
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
AUDIO = ROOT / "audio"
TTS_URL = "https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=en&q="


def slug(text):
    # Must match slug() in index.html
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def category_speech(category):
    # Must match categorySpeech() in index.html
    return re.sub(r"\s+", " ", re.sub(r"[/()]", " ", category)).strip()


def load_sections():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    src = re.search(r"const SECTIONS = (\[.*?\n\]);", html, re.S).group(1)
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"([{,]\s*)(\w+)\s*:", r'\1"\2":', src)  # quote object keys
    src = re.sub(r",\s*([\]}])", r"\1", src)              # drop trailing commas
    return json.loads(src)


def texts():
    out = set()
    for _group, category, items in load_sections():
        out.add(category_speech(category))
        for it in items:
            if isinstance(it, str):
                out.add(it)
            elif isinstance(it, list):
                out.add(it[0])
            else:
                out.add(it.get("say") or it["n"])
    return sorted(out)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Chinese Windows consoles default to GBK
    force = "--force" in sys.argv
    AUDIO.mkdir(exist_ok=True)
    all_texts = texts()
    done = skipped = failed = 0
    for text in all_texts:
        path = AUDIO / f"{slug(text)}.mp3"
        if path.exists() and not force:
            skipped += 1
            continue
        req = urllib.request.Request(TTS_URL + urllib.parse.quote(text), headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                path.write_bytes(r.read())
            done += 1
            print(f"ok    {text}")
        except Exception as e:
            failed += 1
            print(f"FAIL  {text}: {e}")
        time.sleep(0.4)
    print(f"\n{len(all_texts)} clips: {done} downloaded, {skipped} already present, {failed} failed")


if __name__ == "__main__":
    main()
