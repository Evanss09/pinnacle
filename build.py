#!/usr/bin/env python3
"""PINNACLE build script.

Reads events.yaml + vault.yaml + channels.yaml and regenerates everything in
docs/: pinnacle-locked.ics, pinnacle-radar.ics, index.html.

Design constraints (see PINNACLE.md):
- pyyaml + stdlib only; ICS written by hand.
- Truly silent calendars: TRANSP:TRANSPARENT, zero VALARM.
- Deterministic ICS output: DTSTAMP mirrors DTSTART so an unchanged data file
  produces a byte-identical .ics (clean git diffs, no spurious client resyncs).

Usage:
    python3 build.py            # validate + write docs/ outputs
    python3 build.py --check    # validate only (schema + a dry-run ICS lint)
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"

CATEGORIES = {"team", "mind", "adventure", "endurance", "motor", "strength", "space"}
TIERS = {"locked", "radar"}
WATCHABILITY = {"green", "yellow", "red"}
WATCH_ICON = {"green": "\U0001f7e2", "yellow": "\U0001f7e1", "red": "\U0001f534"}

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}

VIDEO_ID_RE = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/live/)"
    r"([A-Za-z0-9_-]{11})")


# ---------------------------------------------------------------- data loading

def load_yaml(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        sys.exit(f"FATAL: {path.name} failed to parse: {e}")
    return data if data is not None else []


def parse_utc(value, ctx):
    if not isinstance(value, str) or not value.endswith("Z"):
        sys.exit(f"FATAL: {ctx}: timestamp {value!r} must be an ISO string ending in Z")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        sys.exit(f"FATAL: {ctx}: timestamp {value!r} not YYYY-MM-DDTHH:MM:SSZ")


def parse_window(window, ctx):
    """Extract (year, month) from a radar window string like 'Oct 2026 (conditions-dependent)'."""
    if not isinstance(window, str):
        sys.exit(f"FATAL: {ctx}: radar item needs a window string containing a month + year")
    # First month + first year found anywhere, so "Sep-Dec 2026" pins to Sep (early warning).
    month = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", window.lower())
    year = re.search(r"\b(20\d{2})\b", window)
    if not (month and year):
        sys.exit(f"FATAL: {ctx}: window {window!r} has no parseable month + year")
    return int(year.group(1)), MONTHS[month.group(1)]


def validate(events, vault, channels):
    problems, warnings = [], []
    seen = set()
    today = datetime.now(timezone.utc)
    for ev in events:
        eid = ev.get("id")
        ctx = f"events.yaml [{eid}]"
        if not eid or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(eid)):
            problems.append(f"{ctx}: id must be a kebab-case slug")
            continue
        if eid in seen:
            problems.append(f"{ctx}: duplicate id")
        seen.add(eid)
        if not ev.get("name"):
            problems.append(f"{ctx}: missing name")
        if ev.get("category") not in CATEGORIES:
            problems.append(f"{ctx}: bad category {ev.get('category')!r}")
        if ev.get("tier") not in TIERS:
            problems.append(f"{ctx}: bad tier {ev.get('tier')!r}")
        if ev.get("watchability") not in WATCHABILITY:
            problems.append(f"{ctx}: bad watchability {ev.get('watchability')!r}")
        if not ev.get("why"):
            problems.append(f"{ctx}: missing why")
        watch = ev.get("watch") or {}
        if not isinstance(watch, dict):
            problems.append(f"{ctx}: watch must be a mapping")
            watch = {}
        if not watch.get("link"):
            warnings.append(f"{ctx}: no watch.link — calendar entry won't be self-sufficient")
        handle = watch.get("youtube_channel")
        if handle and handle not in channels:
            problems.append(f"{ctx}: youtube_channel {handle!r} not in channels.yaml")
        elif handle and not str(channels.get(handle) or "").startswith("UC"):
            problems.append(f"{ctx}: channels.yaml has no resolved UC... id for {handle!r}")

        if "result" in ev:
            if not isinstance(ev["result"], str) or not ev["result"].strip():
                problems.append(f"{ctx}: result must be a non-empty string")
            elif ev.get("tier") != "locked":
                warnings.append(f"{ctx}: result on a non-locked event")
            elif ev.get("end_utc") and parse_utc(ev["end_utc"], ctx) > today:
                warnings.append(f"{ctx}: result set but end_utc is in the future")

        has_start, has_end = "start_utc" in ev, "end_utc" in ev
        if ev.get("tier") == "locked":
            if not (has_start and has_end):
                problems.append(f"{ctx}: locked events need start_utc and end_utc")
            else:
                s, e = parse_utc(ev["start_utc"], ctx), parse_utc(ev["end_utc"], ctx)
                if e <= s:
                    problems.append(f"{ctx}: end_utc must be after start_utc")
        else:  # radar
            if has_start != has_end:
                problems.append(f"{ctx}: radar item has only one of start_utc/end_utc")
            elif has_start:
                s, e = parse_utc(ev["start_utc"], ctx), parse_utc(ev["end_utc"], ctx)
                if e <= s:
                    problems.append(f"{ctx}: end_utc must be after start_utc")
            else:
                y, mo = parse_window(ev.get("window"), ctx)
                if (y, mo) < (today.year, today.month):
                    warnings.append(f"{ctx}: window {ev.get('window')!r} is in the past")

    vseen = set()
    for v in vault:
        vid = v.get("id")
        ctx = f"vault.yaml [{vid}]"
        if not vid or vid in vseen:
            problems.append(f"{ctx}: missing or duplicate id")
        vseen.add(vid)
        for key in ("title", "one_liner", "video_url", "date"):
            if not v.get(key):
                problems.append(f"{ctx}: missing {key}")
        if v.get("video_url") and not VIDEO_ID_RE.search(v["video_url"]):
            problems.append(f"{ctx}: cannot extract a YouTube video id from {v.get('video_url')!r}")
        if not v.get("verified"):
            warnings.append(f"{ctx}: missing verified date — NEW badge and freshness need it")
        veid = v.get("event_id")
        if veid:
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(veid)):
                problems.append(f"{ctx}: event_id must be a kebab-case slug")
            elif veid not in seen and _is_recent(v.get("verified"), today, days=7):
                warnings.append(f"{ctx}: event_id {veid!r} matches no event "
                                "(fresh entry — possible typo; pruned events are expected to age out)")

    return problems, warnings


def _is_recent(verified, today, days):
    """True if a vault 'verified' date (date or str) is within the last N days."""
    try:
        d = datetime.strptime(str(verified), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return False
    return (today - d).days <= days


# ---------------------------------------------------------------- ICS engine

def ics_escape(text):
    return (str(text).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n"))


def fold(line):
    """RFC 5545 folding: lines max 75 octets; continuations = CRLF + single space.
    Operates on UTF-8 bytes and never splits inside a multi-byte sequence."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return [line]
    out, prefix = [], b""
    while len(prefix) + len(raw) > 75:
        cut = 75 - len(prefix)
        while cut > 1 and (raw[cut] & 0xC0) == 0x80:
            cut -= 1
        out.append((prefix + raw[:cut]).decode("utf-8"))
        raw = raw[cut:]
        prefix = b" "
    out.append((prefix + raw).decode("utf-8"))
    return out


def dt_stamp(dt):
    return dt.strftime("%Y%m%dT%H%M%SZ")


def event_description(ev):
    watch = ev.get("watch") or {}
    parts = [f"{WATCH_ICON[ev['watchability']]} {ev['why']}"]
    if ev.get("result"):
        parts.append(f"Result: {ev['result']}")
    if watch.get("free"):
        parts.append(f"Free: {watch['free']}")
    if watch.get("premium"):
        parts.append(f"Premium: {watch['premium']}")
    if watch.get("link"):
        parts.append(watch["link"])
    if ev.get("tier") == "radar" and ev.get("window"):
        parts.append(f"Window: {ev['window']}")
    if ev.get("recurrence_note"):
        parts.append(ev["recurrence_note"])
    return "\n".join(parts)


def make_vevent(ev):
    lines = ["BEGIN:VEVENT", f"UID:{ev['id']}@pinnacle"]
    if "start_utc" in ev:
        start = parse_utc(ev["start_utc"], ev["id"])
        end = parse_utc(ev["end_utc"], ev["id"])
        lines += [f"DTSTAMP:{dt_stamp(start)}",
                  f"DTSTART:{dt_stamp(start)}",
                  f"DTEND:{dt_stamp(end)}"]
        summary = ev["name"]
    else:
        y, mo = parse_window(ev["window"], ev["id"])
        day = f"{y:04d}{mo:02d}01"
        lines += [f"DTSTAMP:{day}T000000Z",
                  f"DTSTART;VALUE=DATE:{day}",
                  f"DTEND;VALUE=DATE:{day[:6]}02"]  # DTEND exclusive → one-day event
        summary = f"\U0001f7e1 RADAR: {ev['name']}"
    lines.append(f"SUMMARY:{ics_escape(summary)}")
    lines.append(f"DESCRIPTION:{ics_escape(event_description(ev))}")
    lines.append("STATUS:CONFIRMED" if ev["tier"] == "locked" else "STATUS:TENTATIVE")
    lines.append("TRANSP:TRANSPARENT")
    lines.append(f"CATEGORIES:{ev['category'].upper()}")
    link = (ev.get("watch") or {}).get("link")
    if link:
        lines.append(f"URL:{link}")
    lines.append("END:VEVENT")
    return lines


def sort_key(ev):
    if "start_utc" in ev:
        return (ev["start_utc"], ev["id"])
    y, mo = parse_window(ev["window"], ev["id"])
    return (f"{y:04d}-{mo:02d}-01T00:00:00Z", ev["id"])


def make_calendar(events, cal_id, cal_name):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             f"PRODID:-//PINNACLE//{cal_id}//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:{ics_escape(cal_name)}",
             "X-WR-TIMEZONE:UTC", "X-PUBLISHED-TTL:PT6H"]
    for ev in sorted(events, key=sort_key):
        lines += make_vevent(ev)
    lines.append("END:VCALENDAR")
    folded = []
    for line in lines:
        folded += fold(line)
    return "\r\n".join(folded) + "\r\n"


def lint_ics(text, name):
    """Self-lint the generated ICS bytes; returns a list of problems."""
    problems = []
    raw = text.encode("utf-8")
    if not raw.endswith(b"\r\n"):
        problems.append(f"{name}: does not end with CRLF")
    body = raw.replace(b"\r\n", b"")
    if b"\n" in body or b"\r" in body:
        problems.append(f"{name}: bare LF or CR outside CRLF pairs")
    if b"VALARM" in raw:
        problems.append(f"{name}: contains VALARM — calendars must be silent")
    lines = raw.split(b"\r\n")[:-1]
    uids = []
    depth = 0
    for i, line in enumerate(lines, 1):
        if len(line) > 75:
            problems.append(f"{name}:{i}: line exceeds 75 octets ({len(line)})")
        if line.startswith(b"BEGIN:"):
            depth += 1
        elif line.startswith(b"END:"):
            depth -= 1
        elif line.startswith(b"UID:"):
            uids.append(line)
    if depth != 0:
        problems.append(f"{name}: unbalanced BEGIN/END")
    if len(uids) != len(set(uids)):
        problems.append(f"{name}: duplicate UIDs")
    for req in (b"VERSION:2.0", b"PRODID:", b"X-WR-CALNAME:"):
        if not any(l.startswith(req) for l in lines):
            problems.append(f"{name}: missing {req.decode()}")
    return problems


# ---------------------------------------------------------------- dashboard

def render_html(events, vault, channels, template):
    payload_events = []
    for ev in sorted(events, key=sort_key):
        watch = ev.get("watch") or {}
        handle = watch.get("youtube_channel")
        payload_events.append({
            "id": ev["id"], "name": ev["name"], "category": ev["category"],
            "tier": ev["tier"],
            "start_utc": ev.get("start_utc"), "end_utc": ev.get("end_utc"),
            "window": ev.get("window"), "why": ev["why"],
            "free": watch.get("free"), "premium": watch.get("premium"),
            "link": watch.get("link"),
            "channel_id": channels.get(handle) if handle else None,
            "watchability": ev["watchability"],
            "result": ev.get("result"),
        })
    payload_vault = []
    for v in sorted(vault, key=lambda v: str(v.get("date")), reverse=True):
        payload_vault.append({
            "id": v["id"], "title": v["title"], "subject": v.get("subject"),
            "date": str(v["date"]), "category": v.get("category"),
            "video_id": VIDEO_ID_RE.search(v["video_url"]).group(1),
            "one_liner": v["one_liner"],
            "event_id": v.get("event_id"),
            "verified": str(v["verified"]) if v.get("verified") else None,
        })
    data = {"events": payload_events, "vault": payload_vault}
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if "__DATA__" not in template or "__BUILT__" not in template:
        sys.exit("FATAL: template.html is missing the __DATA__/__BUILT__ tokens")
    return template.replace("__DATA__", blob).replace("__BUILT__", built)


# ---------------------------------------------------------------- main

def main():
    check_only = "--check" in sys.argv

    events = load_yaml(ROOT / "events.yaml")
    vault = load_yaml(ROOT / "vault.yaml")
    channels = load_yaml(ROOT / "channels.yaml") or {}

    problems, warnings = validate(events, vault, channels)
    for w in warnings:
        print(f"  warn: {w}")
    if problems:
        for p in problems:
            print(f" ERROR: {p}", file=sys.stderr)
        sys.exit(f"FATAL: {len(problems)} validation error(s); nothing written")

    locked = [e for e in events if e["tier"] == "locked"]
    radar = [e for e in events if e["tier"] == "radar"]

    locked_ics = make_calendar(locked, "pinnacle-locked", "Pinnacle — Locked")
    radar_ics = make_calendar(radar, "pinnacle-radar", "Pinnacle — Radar")

    lint = lint_ics(locked_ics, "pinnacle-locked.ics") + lint_ics(radar_ics, "pinnacle-radar.ics")
    if lint:
        for p in lint:
            print(f" ERROR: {p}", file=sys.stderr)
        sys.exit(f"FATAL: {len(lint)} ICS lint error(s); nothing written")

    template = (ROOT / "template.html").read_text(encoding="utf-8")
    html = render_html(events, vault, channels, template)

    if check_only:
        print(f"OK (check): {len(locked)} locked, {len(radar)} radar, {len(vault)} vault entries")
        return

    DOCS.mkdir(exist_ok=True)
    with open(DOCS / "pinnacle-locked.ics", "w", encoding="utf-8", newline="") as f:
        f.write(locked_ics)
    with open(DOCS / "pinnacle-radar.ics", "w", encoding="utf-8", newline="") as f:
        f.write(radar_ics)
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print(f"OK: wrote docs/ — {len(locked)} locked, {len(radar)} radar, {len(vault)} vault entries")


if __name__ == "__main__":
    main()
