#!/usr/bin/env python3
"""
Meteor Client - Automatic Chinese Translation Script

Extracts all user-facing English strings from Java source files,
translates them to Chinese using a free translation API,
and generates zh_cn_full.json for runtime loading.

Usage:
    python scripts/translate.py [--api {google,deepl,libre}]
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src" / "main" / "java"
OUTPUT_DIR = REPO_ROOT / "src" / "main" / "resources" / "assets" / "meteor-client" / "lang"
OUTPUT_FILE = OUTPUT_DIR / "zh_cn_full.json"
CACHE_FILE = REPO_ROOT / "scripts" / "translation_cache.json"


# ---------------------------------------------------------------------------
# 1. String extraction patterns
# ---------------------------------------------------------------------------

# Module/Command: super(Categories.X, "name", "description", ...)
PAT_MODULE = re.compile(
    r'super\(\s*Categories\.\w+\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"'
)
# Command: super("name", "description", ...)
PAT_COMMAND = re.compile(
    r'super\(\s*"([^"]+)"\s*,\s*"([^"]+)"'
)
# Setting .name("kebab-name")
PAT_SETTING_NAME = re.compile(
    r'\.name\(\s*"([a-z][a-z0-9-]*)"\s*\)'
)
# Setting .description("text")
PAT_DESCRIPTION = re.compile(
    r'\.description\(\s*"([^"]+)"\s*\)'
)
# Setting group: createGroup("text")
PAT_GROUP = re.compile(
    r'createGroup\(\s*"([^"]+)"\s*\)'
)
# Category: new Category("text", ...)
PAT_CATEGORY = re.compile(
    r'new\s+Category\(\s*"([^"]+)"\s*,'
)
# GUI text in theme calls
PAT_GUI_THEME = re.compile(
    r'theme\.(?:label|button|window|section|horizontalSeparator|tooltip)\(\s*"([^"]+)"\s*\)'
)
# GUI text with two args where one might be a string
PAT_GUI_THEME2 = re.compile(
    r'theme\.label\(\s*"([^"]+)"\s*,\s*(?:true|false)\s*\)'
)
# Chat info/warning/error messages
PAT_CHAT_MSG = re.compile(
    r'\.(?:info|warning|error)\(\s*"([^"]+)"'
)
# Color setting helper in MeteorGuiTheme
PAT_COLOR_NAME = re.compile(
    r'color\(\s*[\w.]+,\s*"([^"]*)",\s*"([^"]+)"'
)
# ThreeStateColorSetting names
PAT_THREESTATE = re.compile(
    r'new\s+ThreeStateColorSetting\(\s*[\w.]+,\s*"([^"]+)",'
)


def name_to_title(name):
    """Match Java Utils.nameToTitle()."""
    return " ".join(w.capitalize() for w in name.split("-"))


def extract_strings(java_files):
    """Scan Java files and return a set of English strings to translate."""
    strings = set()

    for filepath in java_files:
        text = filepath.read_text("utf-8", errors="ignore")

        # Module names + descriptions
        for m in PAT_MODULE.finditer(text):
            # Module name -> title
            strings.add(name_to_title(m.group(1)))
            # Module description
            desc = m.group(2).strip()
            if desc:
                strings.add(desc)

        # Command names + descriptions (only in Command subclasses under commands/)
        if "commands" in str(filepath):
            for m in PAT_COMMAND.finditer(text):
                strings.add(name_to_title(m.group(1)))
                desc = m.group(2).strip()
                if desc:
                    strings.add(desc)

        # Setting names -> titles
        for m in PAT_SETTING_NAME.finditer(text):
            n = m.group(1)
            if n and n != "undefined":
                strings.add(name_to_title(n))

        # Setting descriptions
        for m in PAT_DESCRIPTION.finditer(text):
            desc = m.group(1).strip()
            if desc:
                strings.add(desc)

        # Setting group names
        for m in PAT_GROUP.finditer(text):
            g = m.group(1).strip()
            if g:
                strings.add(g)

        # Category names
        for m in PAT_CATEGORY.finditer(text):
            c = m.group(1).strip()
            if c:
                strings.add(c)

        # GUI theme text (single arg)
        for m in PAT_GUI_THEME.finditer(text):
            t = m.group(1).strip()
            if t:
                strings.add(t)

        # GUI theme text (label with boolean arg)
        for m in PAT_GUI_THEME2.finditer(text):
            t = m.group(1).strip()
            if t:
                strings.add(t)

        # Chat messages
        for m in PAT_CHAT_MSG.finditer(text):
            msg = m.group(1).strip()
            if msg:
                strings.add(msg)

        # Color setting helper descriptions
        for m in PAT_COLOR_NAME.finditer(text):
            desc = m.group(2).strip()
            if desc:
                strings.add(desc)

        # ThreeStateColorSetting names
        for m in PAT_THREESTATE.finditer(text):
            n = m.group(1).strip()
            if n:
                strings.add(n)

    return strings


# ---------------------------------------------------------------------------
# 2. Translation
# ---------------------------------------------------------------------------

def translate_batch(texts, api="google", src="en", target="zh-CN", retries=3):
    """Translate a list of texts using deep-translator."""
    from deep_translator import GoogleTranslator, DeeplTranslator, LibreTranslator

    if api == "google":
        translator = GoogleTranslator(source=src, target=target)
    elif api == "deepl":
        api_key = os.environ.get("DEEPL_API_KEY", "")
        translator = DeeplTranslator(api_key=api_key, source=src, target=target)
    elif api == "libre":
        url = os.environ.get("LIBRETRANSLATE_URL", "https://libretranslate.com")
        translator = LibreTranslator(url, source=src, target=target)
    else:
        raise ValueError(f"Unknown API: {api}")

    # Batch in groups to avoid rate limits
    batch_size = 50 if api == "google" else 20
    results = {}

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        # Filter out strings that would break translation (empty, too short, etc.)
        filtered = [t for t in batch if len(t) >= 1]
        if not filtered:
            continue

        for attempt in range(retries):
            try:
                translated = translator.translate_batch(filtered)
                for orig, trans in zip(filtered, translated):
                    results[orig] = trans
                break
            except Exception as e:
                print(f"  [retry {attempt + 1}/{retries}] Batch {i // batch_size} failed: {e}", file=sys.stderr)
                if attempt < retries - 1:
                    wait = 2 ** attempt
                    print(f"  Waiting {wait}s...", file=sys.stderr)
                    time.sleep(wait)
                else:
                    # Fall back to single translation for each text
                    print(f"  Falling back to single translation for batch", file=sys.stderr)
                    for t in filtered:
                        for single_attempt in range(retries):
                            try:
                                results[t] = translator.translate(t)
                                break
                            except Exception as e2:
                                if single_attempt < retries - 1:
                                    time.sleep(2 ** single_attempt)
                                else:
                                    print(f"  FAILED to translate: {t[:50]}...", file=sys.stderr)
                                    results[t] = t

        # Rate limiting pause
        if api == "google":
            time.sleep(0.5)
        else:
            time.sleep(1.0)

        # Progress
        done = min(i + batch_size, len(texts))
        print(f"  Translated {done}/{len(texts)}", file=sys.stderr)

    return results


# ---------------------------------------------------------------------------
# 3. Main
# ---------------------------------------------------------------------------

def collect_java_files():
    """Return all Java files in src/main/java."""
    return sorted(SRC_DIR.rglob("*.java"))


def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text("utf-8"))
    return {}


def save_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), "utf-8")


def main():
    parser = argparse.ArgumentParser(description="Translate Meteor Client to Chinese")
    parser.add_argument("--api", choices=["google", "deepl", "libre"], default="google",
                        help="Translation API to use (default: google, no API key needed)")
    parser.add_argument("--force", action="store_true",
                        help="Force re-translation, ignore cache")
    args = parser.parse_args()

    print("Step 1: Scanning Java source files...", file=sys.stderr)
    java_files = collect_java_files()
    print(f"  Found {len(java_files)} Java files", file=sys.stderr)

    english_strings = extract_strings(java_files)
    # Sort for deterministic output
    english_strings = sorted(english_strings, key=lambda s: s.lower())
    print(f"  Extracted {len(english_strings)} unique English strings", file=sys.stderr)

    # Filter out strings that don't need translation
    # Skip pure numbers, very short strings, format-placeholder-only strings
    filtered = []
    for s in english_strings:
        s_stripped = s.strip()
        if not s_stripped:
            continue
        # Skip strings that are purely format tags or placeholders
        if re.match(r'^[\s%()_,.<>]+$', s_stripped):
            continue
        # Skip if already looks like Chinese
        if re.search(r'[\u4e00-\u9fff]', s_stripped):
            continue
        filtered.append(s_stripped)

    print(f"  {len(filtered)} strings need translation (after filtering)", file=sys.stderr)

    # Load translation cache
    cache = load_cache()
    uncached = [s for s in filtered if s not in cache or args.force]

    if uncached:
        print(f"Step 2: Translating {len(uncached)} strings via {args.api}...", file=sys.stderr)
        translations = translate_batch(uncached, api=args.api)
        cache.update(translations)
        save_cache(cache)
    else:
        print("Step 2: All strings cached, skipping translation", file=sys.stderr)

    # Build final map (ensure all filtered strings have entries, falling back to original)
    final_map = {}
    for s in filtered:
        if s in cache and cache[s]:
            final_map[s] = cache[s]
        else:
            final_map[s] = s  # fallback to English

    print(f"Step 3: Writing {len(final_map)} entries to {OUTPUT_FILE}", file=sys.stderr)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(final_map, ensure_ascii=False, indent=2),
        "utf-8"
    )
    print("Done!", file=sys.stderr)


if __name__ == "__main__":
    main()
