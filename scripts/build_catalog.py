#!/usr/bin/env python3
"""
build_catalog.py — Generates vox-feeds-catalog.json from all OPML files.
OPML files are the SOURCE OF TRUTH.
"""

import os, sys, json, glob
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

LANGUAGE_COUNTRY_MAP = {
    "arabic":      ("Arabic",      "Arabic Countries"),
    "bengali":     ("Bengali",     "Bangladesh / India"),
    "bulgarian":   ("Bulgarian",   "Bulgaria"),
    "catalan":     ("Catalan",     "Spain / Catalonia"),
    "chinese":     ("Chinese",     "China"),
    "croatian":    ("Croatian",    "Croatia"),
    "czech":       ("Czech",       "Czech Republic"),
    "danish":      ("Danish",      "Denmark"),
    "dutch":       ("Dutch",       "Netherlands / Belgium"),
    "english":     ("English",     "International"),
    "estonian":    ("Estonian",    "Estonia"),
    "filipino":    ("Filipino",    "Philippines"),
    "finnish":     ("Finnish",     "Finland"),
    "french":      ("French",      "France"),
    "german":      ("German",      "Germany / Austria / Switzerland"),
    "greek":       ("Greek",       "Greece"),
    "hebrew":      ("Hebrew",      "Israel"),
    "hindi":       ("Hindi",       "India"),
    "hungarian":   ("Hungarian",   "Hungary"),
    "icelandic":   ("Icelandic",   "Iceland"),
    "indonesian":  ("Indonesian",  "Indonesia"),
    "italian":     ("Italian",     "Italy"),
    "japanese":    ("Japanese",    "Japan"),
    "javanese":    ("Javanese",    "Indonesia"),
    "korean":      ("Korean",      "South Korea"),
    "latvian":     ("Latvian",     "Latvia"),
    "lithuanian":  ("Lithuanian",  "Lithuania"),
    "macedonian":  ("Macedonian",  "North Macedonia"),
    "malay":       ("Malay",       "Malaysia / Brunei"),
    "marathi":     ("Marathi",     "India"),
    "norwegian":   ("Norwegian",   "Norway"),
    "persian":     ("Persian",     "Iran"),
    "polish":      ("Polish",      "Poland"),
    "portuguese":  ("Portuguese",  "Portugal / Brazil"),
    "romanian":    ("Romanian",    "Romania"),
    "russian":     ("Russian",     "Russia"),
    "serbian":     ("Serbian",     "Serbia"),
    "slovak":      ("Slovak",      "Slovakia"),
    "slovenian":   ("Slovenian",   "Slovenia"),
    "spanish":     ("Spanish",     "Spain / Latin America"),
    "swahili":     ("Swahili",     "East Africa"),
    "swedish":     ("Swedish",     "Sweden"),
    "tamil":       ("Tamil",       "India / Sri Lanka"),
    "telugu":      ("Telugu",      "India"),
    "thai":        ("Thai",        "Thailand"),
    "turkish":     ("Turkish",     "Turkey"),
    "ukrainian":   ("Ukrainian",   "Ukraine"),
    "urdu":        ("Urdu",        "Pakistan / India"),
    "vietnamese":  ("Vietnamese",  "Vietnam"),
}

def extract_language_from_filename(filename):
    return os.path.basename(filename).replace("_feeds.opml.xml", "").lower()

def get_language_info(lang_key):
    return LANGUAGE_COUNTRY_MAP.get(lang_key, (lang_key.title(), lang_key.title()))

def parse_opml_file(filepath):
    lang_key = extract_language_from_filename(filepath)
    language_name, country = get_language_info(lang_key)
    feeds = []
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"  WARNING: Failed to parse {filepath}: {e}", file=sys.stderr)
        return []
    body = root.find("body")
    if body is None:
        return []
    for category_outline in body.findall("outline"):
        category_name = category_outline.get("text") or category_outline.get("title") or "Uncategorized"
        for feed_outline in category_outline.findall("outline"):
            xml_url = feed_outline.get("xmlUrl") or feed_outline.get("xmlurl")
            if not xml_url:
                continue
            name = feed_outline.get("text") or feed_outline.get("title") or "Unknown"
            html_url = feed_outline.get("htmlUrl") or feed_outline.get("htmlurl") or ""
            feeds.append({
                "name": name.strip(),
                "rssUrl": xml_url.strip(),
                "websiteUrl": html_url.strip(),
                "language": lang_key,
                "languageName": language_name,
                "country": country,
                "category": category_name.strip(),
            })
    return feeds

def build_catalog(repo_root):
    opml_files = sorted(glob.glob(os.path.join(repo_root, "*.opml.xml")))
    if not opml_files:
        print("No OPML files found", file=sys.stderr)
        sys.exit(1)
    print(f"Found {len(opml_files)} OPML files")
    all_feeds = []
    for f in opml_files:
        feeds = parse_opml_file(f)
        print(f"  {os.path.basename(f)}: {len(feeds)} feeds")
        all_feeds.extend(feeds)
    seen = set()
    unique = []
    for feed in all_feeds:
        if feed["rssUrl"] not in seen:
            seen.add(feed["rssUrl"])
            unique.append(feed)
    print(f"\nTotal: {len(all_feeds)} → {len(unique)} unique")
    unique.sort(key=lambda f: (f["language"], f["category"], f["name"].lower()))
    return {
        "version": 1,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "totalFeeds": len(unique),
        "totalLanguages": len(set(f["language"] for f in unique)),
        "feeds": unique,
    }

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    catalog = build_catalog(repo_root)
    output = os.path.join(repo_root, "vox-feeds-catalog.json")
    with open(output, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"\nWritten: {output}")
    print(f"  Feeds: {catalog['totalFeeds']}, Languages: {catalog['totalLanguages']}")

if __name__ == "__main__":
    main()
