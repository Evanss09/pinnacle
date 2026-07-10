#!/usr/bin/env python3
"""Resolve YouTube @handles to raw UC... channel IDs into channels.yaml.

The live_stream embed on the dashboard needs the raw channel ID
(youtube.com/embed/live_stream?channel=UC...), which YouTube doesn't expose
via the handle. This scrapes each handle's channel page for it — no API key.
(Approach ported from automation-challenge/day1-newsletter/tools/youtube_rss.py,
swapped to stdlib urllib so this repo stays pyyaml+stdlib only.)

Usage:
    python3 resolve_channels.py          # resolve every null id in channels.yaml
    python3 resolve_channels.py --all    # re-verify already-resolved ids too

Also scans events.yaml for youtube_channel handles missing from channels.yaml
and adds them. Exits non-zero if anything is left unresolved.
"""

import re
import sys
import time
import urllib.request

import yaml

from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
# Ordered by reliability. The page's own channel appears as externalId /
# itemprop identifier exactly once; a bare "channelId" also matches featured
# channels and gives false positives, so it's deliberately NOT used.
ID_RES = [
    re.compile(r'"externalId":"(UC[A-Za-z0-9_-]{22})"'),
    re.compile(r'itemprop="identifier" content="(UC[A-Za-z0-9_-]{22})"'),
    re.compile(r'rel="canonical" href="https://www\.youtube\.com/channel/(UC[A-Za-z0-9_-]{22})"'),
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def resolve(handle):
    html = fetch(f"https://www.youtube.com/{handle}")
    for pattern in ID_RES:
        m = pattern.search(html)
        if m:
            return m.group(1)
    return None


def main():
    reverify = "--all" in sys.argv
    channels_path = ROOT / "channels.yaml"
    channels = yaml.safe_load(channels_path.read_text(encoding="utf-8")) or {}

    events = yaml.safe_load((ROOT / "events.yaml").read_text(encoding="utf-8")) or []
    for ev in events:
        handle = (ev.get("watch") or {}).get("youtube_channel")
        if handle and handle not in channels:
            print(f"  + {handle} (referenced by {ev['id']}, added)")
            channels[handle] = None

    failures = []
    for handle in sorted(channels):
        if channels[handle] and not reverify:
            continue
        try:
            cid = resolve(handle)
        except Exception as e:
            cid = None
            print(f"  ! {handle}: fetch failed ({e})")
        if cid:
            status = "ok" if channels[handle] in (None, cid) else f"CHANGED from {channels[handle]}"
            print(f"  ✓ {handle} → {cid} ({status})")
            channels[handle] = cid
        else:
            failures.append(handle)
            print(f"  ✗ {handle}: no channel id found — check the handle spelling")
        time.sleep(1)

    with open(channels_path, "w", encoding="utf-8") as f:
        f.write("# YouTube @handle → raw UC... channel id (needed for live_stream embeds).\n"
                "# Maintained by resolve_channels.py — run it after adding a new handle.\n")
        yaml.safe_dump(channels, f, allow_unicode=True, sort_keys=True, default_flow_style=False)

    if failures:
        sys.exit(f"{len(failures)} unresolved handle(s): {', '.join(failures)}")
    print(f"All {len(channels)} handles resolved.")


if __name__ == "__main__":
    main()
