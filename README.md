# PINNACLE

A one-stop system for tracking and watching the highest level of human competition.
Finals, elimination games, world championships, one-off world-class feats — nothing else.
Most days nothing qualifies. That's correct behavior, not a bug.

**Dashboard:** https://evanss09.github.io/pinnacle/

## Subscribe to the calendars

Both feeds are silent by design: no alarms, no busy-blocking, all times UTC (your calendar client converts automatically).

| Feed | What's in it | URL |
|---|---|---|
| 🔒 Locked | Confirmed finals/eliminations with dates & times | `https://evanss09.github.io/pinnacle/pinnacle-locked.ics` |
| 🟡 Radar | Announced but unscheduled/tentative | `https://evanss09.github.io/pinnacle/pinnacle-radar.ics` |

- **Google Calendar:** Settings → *Add calendar* → *From URL* → paste a URL above.
- **Apple Calendar (Mac/iPhone):** File → *New Calendar Subscription* (or just open `webcal://evanss09.github.io/pinnacle/pinnacle-locked.ics`).

> Google refreshes subscribed feeds on its own schedule (typically every 12–48 h). A just-pushed change not appearing yet is latency, not a bug.

## How it works

```
events.yaml  ──┐
vault.yaml   ──┼──▶  python3 build.py  ──▶  docs/ (index.html + both .ics)
channels.yaml ─┘
```

- `events.yaml` is the single source of truth. Schema + the elimination-only filter rules live in [PINNACLE.md](PINNACLE.md).
- `build.py` validates everything, hand-writes the two ICS feeds (RFC 5545 folding, CRLF, zero VALARMs), and bakes the event data into `docs/index.html`.
- `channels.yaml` maps YouTube `@handles` to raw `UC…` channel IDs for the dashboard's live embeds — run `python3 resolve_channels.py` after adding a new handle.

```bash
# setup (once)
python3 -m venv .venv && .venv/bin/pip install pyyaml

# rebuild outputs
.venv/bin/python build.py          # or build.py --check to validate only
```

Dashboard tip: append `?now=2026-07-19T19:30:00Z` to the URL to preview what the page looks like at any moment (e.g. mid-final).

## Refresh workflow

**Weekly (~10 min, run in Claude Code from this directory):**

> Run the Pinnacle weekly refresh: (1) Verify every locked event in events.yaml in the next 21 days — confirm date/time/UTC and watch links via web search; fix drift. (2) Check active playoff/knockout series in tracked leagues; add newly-confirmed elimination games per the rules in PINNACLE.md §5; remove events that can no longer occur. (3) Promote any radar items that now have confirmed dates. (4) Add the best moment from any tracked event that finished this week to vault.yaml. (5) Run build.py, commit, push. Summarize changes in 5 bullets.

**Monthly deep scan (~20 min):**

> Run the Pinnacle monthly scan: everything in the weekly refresh, plus (1) search for newly announced one-off feats and specials — free solo projects, record attempts (marathon, altitude, depth, speed), first-of-kind rocket missions, big-wave green lights, exhibition matches between world #1s; add qualifying items to radar. (2) Verify next-quarter dates for all recurring events in PINNACLE.md §5's master list. (3) Sanity-check all YouTube channel IDs in channels.yaml still resolve. (4) Ask Brad (in the summary) about any borderline new event before adding it.
