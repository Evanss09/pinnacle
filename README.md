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
- **Event lifecycle:** a locked event stays in `events.yaml` for 7 days after it ends (feeding the dashboard's *Just Ended* section); the daily intake fills its `result:`, appends its highlight to `vault.yaml` (linked via `event_id:`), and prunes it once it's more than 7 days past.
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

**Daily vault intake (~2 min most days, runs as a scheduled cloud routine at 09:00 UTC):**

> Run the Pinnacle daily vault intake. (1) Scan events.yaml for three lists: (a) locked events whose end_utc is between 36 and 12 hours ago and that have no vault.yaml entry with a matching event_id; (b) locked events that ended within the last 7 days and still lack a result field; (c) events whose end_utc is more than 7 days ago. If all three lists are empty, reply "Nothing ended — no changes" and stop. (2) For each (a) event: web-search the final result and set result: on the event (short form, e.g. "Spain 1-0 Argentina"), keeping the # source: comment convention; then find the single best highlight video (official channel preferred), verify it via YouTube oEmbed (HTTP 200 with matching title), and append a vault.yaml entry with id, title, subject, date (the event date), category copied from the event, video_url, one_liner, event_id set to the event's id, and verified stamped with today's date. If no verifiable highlight exists yet, skip that event without a vault entry — the next run or the weekly audit will catch it. (3) Fill result: for each (b) event via web search. (4) Delete each (c) event. (5) Run build.py; fix any validation errors; commit ("daily vault intake: ...") and push. Summarize in up to 5 bullets.

**Weekly (~10 min, runs as a scheduled cloud routine Thursdays 11:00 UTC):**

> Run the Pinnacle weekly refresh: (1) Verify every locked event in events.yaml in the next 21 days — confirm date/time/UTC and watch links via web search; fix drift. (2) Check active playoff/knockout series in tracked leagues; add newly-confirmed elimination games per the rules in PINNACLE.md §5; remove events that were cancelled or can no longer occur — but keep events that already finished in the last 7 days (the daily intake prunes those on schedule). (3) Promote any radar items that now have confirmed dates. (4) Audit the past week: every locked event that ended should carry a result and have a vault.yaml entry with a matching event_id — backfill anything the daily intake missed. (5) Run build.py, commit, push. Summarize changes in 5 bullets.

**Monthly deep scan (~20 min):**

> Run the Pinnacle monthly scan: everything in the weekly refresh, plus (1) search for newly announced one-off feats and specials — free solo projects, record attempts (marathon, altitude, depth, speed), first-of-kind rocket missions, big-wave green lights, exhibition matches between world #1s; add qualifying items to radar. (2) Verify next-quarter dates for all recurring events in PINNACLE.md §5's master list. (3) Sanity-check all YouTube channel IDs in channels.yaml still resolve. (4) Ask Brad (in the summary) about any borderline new event before adding it.
