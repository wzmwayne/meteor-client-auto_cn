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
import os
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

PREFIX_RULES = [
    ("Whether or not to render ", "是否渲染"),
    ("Whether to render ", "是否渲染"),
    ("Whether or not ", "是否"),
    ("Whether ", "是否"),
    ("Automatically ", "自动"),
    ("Disables ", "禁用"),
    ("Disable ", "禁用"),
    ("Enables ", "启用"),
    ("Enable ", "启用"),
    ("Allows you to ", "允许你"),
    ("Allows ", "允许"),
    ("Prevents you from ", "防止你"),
    ("Prevents ", "防止"),
    ("The maximum ", "最大"),
    ("The minimum ", "最小"),
    ("Doesn", "不"),
    ("Don", "不要"),
    ("Cannot ", "无法"),
    ("Could not ", "无法"),
    ("Failed to ", "失败"),
    ("Only when ", "仅当"),
    ("Only if ", "仅当"),
    ("Only ", "仅"),
    ("If enabled, ", "若启用，"),
    ("If enabled ", "若启用"),
    ("If ", "若"),
    ("Will ", "将"),
    ("Sends a ", "发送"),
    ("Sends ", "发送"),
    ("Swaps ", "切换"),
    ("Swap ", "切换"),
    ("Shows ", "显示"),
    ("Show ", "显示"),
    ("Renders ", "渲染"),
    ("Render ", "渲染"),
    ("Displays ", "显示"),
    ("Display ", "显示"),
    ("Places ", "放置"),
    ("Place ", "放置"),
    ("Blocks ", "阻止"),
    ("Block ", "阻止"),
    ("Ignores ", "忽略"),
    ("Ignore ", "忽略"),
    ("Pauses ", "暂停"),
    ("Pause ", "暂停"),
    ("Hides ", "隐藏"),
    ("Hide ", "隐藏"),
    ("Select ", "选择"),
    ("Changes ", "更改"),
    ("Uses ", "使用"),
    ("Use ", "使用"),
    ("Adds ", "添加"),
    ("Add ", "添加"),
    ("Sets ", "设置"),
    ("Set ", "设置"),
    ("Removes ", "移除"),
    ("Remove ", "移除"),
    ("Opens ", "打开"),
    ("Open ", "打开"),
    ("Copies ", "复制"),
    ("Copy ", "复制"),
    ("Saves ", "保存"),
    ("Save ", "保存"),
    ("Resets ", "重置"),
    ("Reset ", "重置"),
    ("Clears ", "清除"),
    ("Clear ", "清除"),
    ("Closes ", "关闭"),
    ("Close ", "关闭"),
    ("Starts ", "启动"),
    ("Start ", "启动"),
    ("Stops ", "停止"),
    ("Stop ", "停止"),
    ("Cancels ", "取消"),
    ("Cancel ", "取消"),
    ("Creates ", "创建"),
    ("Create ", "创建"),
    ("Deletes ", "删除"),
    ("Delete ", "删除"),
    ("Takes ", "获取"),
    ("Take ", "获取"),
    ("Loads ", "加载"),
    ("Load ", "加载"),
    ("Exports ", "导出"),
    ("Export ", "导出"),
    ("Imports ", "导入"),
    ("Import ", "导入"),
    ("Generates ", "生成"),
    ("Generate ", "生成"),
    ("Searches ", "搜索"),
    ("Search ", "搜索"),
    ("Spoofs ", "伪装"),
    ("Limits ", "限制"),
    ("Prints ", "打印"),
    ("Provides ", "提供"),
    ("Stacks ", "堆叠"),
    ("Highlights ", "高亮"),
    ("Restarts ", "重启"),
    ("Has ", "有"),
    ("Holds ", "持有"),
    ("Modifies ", "修改"),
    ("Attempts to ", "尝试"),
    ("Determines ", "确定"),
    ("Tries to ", "尝试"),
    ("Works ", "工作"),
    ("Specify ", "指定"),
    ("Expands ", "扩大"),
    ("Reduces ", "减少"),
    ("Improves ", "改善"),
    ("Controls ", "控制"),
    ("Calculates ", "计算"),
    ("Finds ", "寻找"),
    ("Predicts ", "预测"),
    ("Predict ", "预测"),
    ("Rotates ", "旋转"),
    ("Boosts ", "增强"),
    ("Spins ", "旋转"),
    ("Replaces ", "替换"),
    ("Replace ", "替换"),
    ("Replenish ", "补充"),
    ("Helps you ", "帮助你"),
    ("Gives you ", "为你"),
    ("Tweaks ", "调整"),
    ("Decide ", "决定"),
    ("Require ", "需要"),
    ("Performs ", "执行"),
    ("No ", "无"),
    ("Yes ", "是"),
    ("Color of ", ""),
    ("Color for ", ""),
    ("Color when ", ""),
    ("Color Color", ""),
    ("Modifiers ", "修饰"),
    ("Error while ", "写入"),
    ("Error ", "错误"),
    ("How many ", "多少个"),
    ("How much ", "多少"),
    ("How long ", "多长时间"),
    ("How fast ", "速度"),
    ("How far ", "多远"),
    ("How close ", "多近"),
    ("How often ", "频率"),
]

SUFFIX_RULES = [
    (" Mode", "模式"),
    (" mode", "模式"),
    (" Method", "方法"),
    (" Speed", "速度"),
    (" Delay", "延迟"),
    (" Range", "范围"),
    (" Color", "颜色"),
    (" Multiplier", "倍率"),
    (" Radius", "半径"),
    (" Distance", "距离"),
    (" Threshold", "阈值"),
    (" Type", "类型"),
    (" Amount", "数量"),
    (" Size", "大小"),
    (" Height", "高度"),
    (" Width", "宽度"),
    (" Length", "长度"),
    (" Depth", "深度"),
    (" Scale", "缩放"),
    (" Count", "计数"),
    (" Value", "值"),
    (" Opacity", "不透明度"),
    (" Priority", "优先级"),
    (" Interval", "间隔"),
    (" Limit", "限制"),
]


def matches_pattern(s):
    for p, repl in PREFIX_RULES:
        if s.startswith(p):
            return True, f"prefix({repl})"
    for suf, repl in SUFFIX_RULES:
        if s.endswith(suf) and len(s) > len(suf):
            return True, f"suffix({repl})"
    return False, None


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


def write_step_summary(summary_lines):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as f:
            f.write("\n".join(summary_lines) + "\n")


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

    # Classify each filtered string
    table_hit = []
    pattern_hit = []
    need_api = []

    for s in filtered:
        is_pattern, _ = matches_pattern(s)
        in_table = s in translations and translations[s] and translations[s] != s
        if in_table and not is_pattern:
            table_hit.append(s)
        elif in_table and is_pattern:
            pattern_hit.append(s)
        else:
            need_api.append(s)

    google_results = {}
    if need_api:
        print(f"Step 3: Translating {len(need_api)} missing strings via Google...", file=sys.stderr)
        google_results = translate_via_google(need_api)
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

    total = len(final_map)
    translated_count = sum(1 for k, v in final_map.items() if k != v)
    still_english = total - translated_count

    # Count API success vs fail
    api_ok = sum(1 for s in need_api if s in google_results and google_results[s] and google_results[s] != s)
    api_fail = len(need_api) - api_ok

    print(f"  Translated: {translated_count}/{total}", file=sys.stderr)
    print(f"  - From hardcoded table (direct): {len(table_hit)}", file=sys.stderr)
    print(f"  - From pattern-based rules:      {len(pattern_hit)}", file=sys.stderr)
    print(f"  - From Google API (ok/fail):     {api_ok}/{api_fail}", file=sys.stderr)
    print(f"  - Still English (fallback):      {still_english}", file=sys.stderr)
    print("Done!", file=sys.stderr)

    summary = [
        "## Translation Report",
        "",
        f"| Category | Count |",
        f"|----------|-------|",
        f"| Total strings | {total} |",
        f"| Translated (direct table) | {len(table_hit)} |",
        f"| Translated (pattern rules) | {len(pattern_hit)} |",
        f"| Translated (Google API) | {api_ok} |",
        f"| API failures | {api_fail} |",
        f"| Still English (fallback) | {still_english} |",
        f"| **Fully translated** | **{translated_count}** |",
        "",
    ]

    if still_english > 0:
        summary.append("### Still English (fallback)")
        summary.append("")
        for s in filtered:
            v = final_map.get(s, s)
            if v == s:
                summary.append(f"- `{s}`")
        summary.append("")

    if api_ok > 0:
        summary.append("### API Translated Strings (least safe)")
        summary.append("")
        for s in need_api:
            if s in google_results and google_results[s] and google_results[s] != s:
                summary.append(f"- `{s}` → {google_results[s]}")
        summary.append("")

    write_step_summary(summary)


if __name__ == "__main__":
    main()
