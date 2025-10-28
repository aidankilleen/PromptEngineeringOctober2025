#!/usr/bin/env python3
"""
Count *prose* words from Wikipedia for all 32 counties on the island of Ireland
using the XTools 'prose' API:
  https://xtools.wmcloud.org/api/page/prose/en.wikipedia.org/<TITLE>

Outputs:
- Pretty table to stdout
- irish_county_wikipedia_prose_wordcounts.csv in the working directory
"""

import csv
import time
import json
import re
import requests
from typing import Optional, Tuple, Dict, Any, List

BASE = "https://xtools.wmcloud.org/api/page/prose/en.wikipedia.org/"
USER_AGENT = "IrishCountyWordCountXTools/1.0 (contact: youremail@example.com)"
TIMEOUT = 25
SLEEP_BETWEEN = 0.5
RETRIES = 3

# 32 counties on the island of Ireland (26 + 6)
COUNTIES_32 = [
    # Northern Ireland
    "County Antrim", "County Armagh", "County Down", "County Fermanagh",
    "County Londonderry", "County Tyrone",
    # Republic of Ireland
    "County Carlow","County Cavan","County Clare","County Cork","County Donegal",
    "County Dublin","County Galway","County Kerry","County Kildare","County Kilkenny",
    "County Laois","County Leitrim","County Limerick","County Longford","County Louth",
    "County Mayo","County Meath","County Monaghan","County Offaly","County Roscommon",
    "County Sligo","County Tipperary","County Waterford","County Westmeath",
    "County Wexford","County Wicklow",
]

def fetch_prose_json(title: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Call XTools prose API for a single page title. Returns (json, error_message)."""
    url = BASE + requests.utils.quote(title, safe="")
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, headers=headers, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json(), None
            elif r.status_code == 404:
                return None, "404 Not Found"
            else:
                last_err = f"HTTP {r.status_code}: {r.text[:200]}"
        except requests.RequestException as e:
            last_err = f"Request error: {e}"
        time.sleep(SLEEP_BETWEEN * attempt)
    return None, last_err or "Unknown error"

def extract_prose_words(payload: Dict[str, Any]) -> Optional[int]:
    """
    XTools 'prose' endpoint commonly returns a top-level 'words' field.
    Be defensive: try a few shapes and fall back to summing section stats.
    """
    # Most common shape
    if isinstance(payload, dict):
        if "words" in payload and isinstance(payload["words"], int):
            return payload["words"]

        # Sometimes nested (just in case)
        if "prose" in payload and isinstance(payload["prose"], dict):
            if "words" in payload["prose"] and isinstance(payload["prose"]["words"], int):
                return payload["prose"]["words"]

        # section_statistics may exist; sum any 'words' values we find
        if "section_statistics" in payload and isinstance(payload["section_statistics"], list):
            total = 0
            found_any = False
            for sec in payload["section_statistics"]:
                if isinstance(sec, dict) and isinstance(sec.get("words"), int):
                    total += sec["words"]
                    found_any = True
            if found_any:
                return total

    return None

def main():
    rows: List[Dict[str, Any]] = []

    for title in COUNTIES_32:
        time.sleep(SLEEP_BETWEEN)
        data, err = fetch_prose_json(title)
        county_name = title.replace("County ", "")
        if err or data is None:
            rows.append({"county": county_name, "words": "", "page_title": title, "error": err or "No data"})
            continue

        words = extract_prose_words(data)
        if words is None:
            # Keep a tiny breadcrumb of what keys we saw to help diagnose
            keys_hint = ",".join(sorted(list(data.keys())[:8]))
            rows.append({"county": county_name, "words": "", "page_title": title,
                         "error": f"Could not find 'words' in payload (keys: {keys_hint})"})
        else:
            rows.append({"county": county_name, "words": words, "page_title": title, "error": ""})

    # Sort by county name
    rows.sort(key=lambda r: r["county"].lower())

    # Print a table
    name_w = max(len("County"), max(len(r["county"]) for r in rows))
    print(f"{'County'.ljust(name_w)}  ProseWords  Page Title")
    print(f"{'-'*name_w}  ----------  ----------")
    for r in rows:
        w = str(r["words"]) if r["words"] != "" else "ERROR"
        print(f"{r['county'].ljust(name_w)}  {w:>10}  {r['page_title']}")

    # Write CSV
    out = "irish_county_wikipedia_prose_wordcounts.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["County", "ProseWords", "PageTitle", "Error"])
        for r in rows:
            writer.writerow([r["county"], r["words"], r["page_title"], r["error"]])

    ok = sum(1 for r in rows if not r["error"])
    fail = len(rows) - ok
    print(f"\nSaved CSV to {out} — {ok} succeeded, {fail} failed.")

if __name__ == "__main__":
    main()
