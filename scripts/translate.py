#!/usr/bin/env python3
"""
Meteor Client - Chinese Translation Script

1. Loads hardcoded translations from scripts/translations.json
2. Falls back to Google Translate API for any untranslated strings
3. Generates zh_cn_full.json for runtime loading

Usage:
    python scripts/translate.py
"""

import json
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src" / "main" / "java"
OUTPUT_DIR = REPO_ROOT / "src" / "main" / "resources" / "assets" / "meteor-client" / "lang"
OUTPUT_FILE = OUTPUT_DIR / "zh_cn_full.json"
TRANSLATIONS_FILE = REPO_ROOT / "scripts" / "translations.json"


PAT_MODULE = re.compile(r'super\(\s*Categories\.\w+\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"')
PAT_COMMAND = re.compile(r'super\(\s*"([^"]+)"\s*,\s*"([^"]+)"')
PAT_SETTING_NAME = re.compile(r'\.name\(\s*"([a-z][a-z0-9-]*)"\s*\)')
PAT_DESCRIPTION = re.compile(r'\.description\(\s*"([^"]+)"\s*\)')
PAT_GROUP = re.compile(r'createGroup\(\s*"([^"]+)"\s*\)')
PAT_CATEGORY = re.compile(r'new\s+Category\(\s*"([^"]+)"\s*,')
PAT_GUI_THEME = re.compile(r'theme\.(?:label|button|window|section|horizontalSeparator|tooltip)\(\s*"([^"]+)"\s*\)')
PAT_GUI_THEME2 = re.compile(r'theme\.label\(\s*"([^"]+)"\s*,\s*(?:true|false)\s*\)')
PAT_CHAT_MSG = re.compile(r'\.(?:info|warning|error)\(\s*"([^"]+)"')
PAT_COLOR_NAME = re.compile(r'color\(\s*[\w.]+,\s*"([^"]*)",\s*"([^"]+)"')
PAT_THREESTATE = re.compile(r'new\s+ThreeStateColorSetting\(\s*[\w.]+,\s*"([^"]+)",')


def name_to_title(name):
    return " ".join(w.capitalize() for w in name.split("-"))


def extract_strings(java_files):
    strings = set()
    for filepath in java_files:
        text = filepath.read_text("utf-8", errors="ignore")
        for m in PAT_MODULE.finditer(text):
            strings.add(name_to_title(m.group(1)))
            desc = m.group(2).strip()
            if desc:
                strings.add(desc)
        if "commands" in str(filepath):
            for m in PAT_COMMAND.finditer(text):
                strings.add(name_to_title(m.group(1)))
                desc = m.group(2).strip()
                if desc:
                    strings.add(desc)
        for m in PAT_SETTING_NAME.finditer(text):
            n = m.group(1)
            if n and n != "undefined":
                strings.add(name_to_title(n))
        for m in PAT_DESCRIPTION.finditer(text):
            desc = m.group(1).strip()
            if desc:
                strings.add(desc)
        for m in PAT_GROUP.finditer(text):
            g = m.group(1).strip()
            if g:
                strings.add(g)
        for m in PAT_CATEGORY.finditer(text):
            c = m.group(1).strip()
            if c:
                strings.add(c)
        for m in PAT_GUI_THEME.finditer(text):
            t = m.group(1).strip()
            if t:
                strings.add(t)
        for m in PAT_GUI_THEME2.finditer(text):
            t = m.group(1).strip()
            if t:
                strings.add(t)
        for m in PAT_CHAT_MSG.finditer(text):
            msg = m.group(1).strip()
            if msg:
                strings.add(msg)
        for m in PAT_COLOR_NAME.finditer(text):
            desc = m.group(2).strip()
            if desc:
                strings.add(desc)
        for m in PAT_THREESTATE.finditer(text):
            n = m.group(1).strip()
            if n:
                strings.add(n)
    return strings


def translate_via_google(texts, retries=3):
    from deep_translator import GoogleTranslator
    translator = GoogleTranslator(source="en", target="zh-CN")
    results = {}
    batch_size = 50
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
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
                print(f"  [retry {attempt + 1}/{retries}] batch {i // batch_size} failed: {e}", file=sys.stderr)
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    for t in filtered:
                        for sa in range(retries):
                            try:
                                results[t] = translator.translate(t)
                                break
                            except Exception:
                                if sa < retries - 1:
                                    time.sleep(2 ** sa)
                                else:
                                    print(f"  FAILED: {t[:60]}", file=sys.stderr)
                                    results[t] = t
        time.sleep(0.5)
        done = min(i + batch_size, len(texts))
        print(f"  Translated {done}/{len(texts)} via Google", file=sys.stderr)
    return results


def main():
    print("Step 1: Scanning Java source files...", file=sys.stderr)
    java_files = sorted(SRC_DIR.rglob("*.java"))
    print(f"  Found {len(java_files)} Java files", file=sys.stderr)

    english_strings = extract_strings(java_files)
    english_strings = sorted(english_strings, key=lambda s: s.lower())
    print(f"  Extracted {len(english_strings)} unique English strings", file=sys.stderr)

    filtered = []
    for s in english_strings:
        s_stripped = s.strip()
        if not s_stripped:
            continue
        if re.match(r'^[\s%()_,.<>]+$', s_stripped):
            continue
        if re.search(r'[\u4e00-\u9fff]', s_stripped):
            continue
        filtered.append(s_stripped)
    print(f"  {len(filtered)} strings need translation", file=sys.stderr)

    print("Step 2: Loading translations table...", file=sys.stderr)
    if TRANSLATIONS_FILE.exists():
        translations = json.loads(TRANSLATIONS_FILE.read_text("utf-8"))
        print(f"  Loaded {len(translations)} entries from {TRANSLATIONS_FILE}", file=sys.stderr)
    else:
        translations = {}

    missing = [s for s in filtered if s not in translations or not translations[s] or translations[s] == s]
    if missing:
        print(f"Step 3: Translating {len(missing)} missing strings via Google...", file=sys.stderr)
        google_results = translate_via_google(missing)
        translations.update(google_results)
        TRANSLATIONS_FILE.write_text(
            json.dumps(dict(sorted(translations.items())), ensure_ascii=False, indent=2),
            "utf-8"
        )
        print(f"  Saved {len(google_results)} new translations to {TRANSLATIONS_FILE}", file=sys.stderr)
    else:
        print("Step 3: All strings have translations, skipping API", file=sys.stderr)

    final_map = {}
    for s in filtered:
        if s in translations and translations[s] and translations[s] != s:
            final_map[s] = translations[s]
        else:
            final_map[s] = s

    print(f"Step 4: Writing {len(final_map)} entries to {OUTPUT_FILE}", file=sys.stderr)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(final_map, ensure_ascii=False, indent=2),
        "utf-8"
    )

    translated_count = sum(1 for k, v in final_map.items() if k != v)
    print(f"  Translated: {translated_count}/{len(final_map)}", file=sys.stderr)
    print("Done!", file=sys.stderr)


if __name__ == "__main__":
    main()
