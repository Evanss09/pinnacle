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
- **Event lifecycle:** a locked event stays in `events.yaml` for 7 days after it ends (feeding the dashboard's *Just Ended* section); the daily intake fills its `result:`, appends its highlight to `vault.yaml` (linked via `event_id:`), and prunes it once it's more than 7 days past — unless it is being *held* (a `⚠️ HOLD` comment, or a `result:` with no vault entry and no `✅ NO HIGHLIGHT` note), in which case it stays until a session can verify a highlight.
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

> ### ⚠️ PROMPTS EDITED 2026-08-25 — the stored copies in the two cloud routines are now STALE
> The scheduled routines run **stored prompt text pasted into the Claude Code web scheduler**, not the copies in this repo. Editing this file does **not** reach them. **Brad: re-paste both prompts (daily intake + weekly refresh) into the scheduler before 2026-08-30**, or the Aug 30 intake runs the old text — which lacks the duration check, the no-highlight escape hatch, and the durable hold comment. Delete this banner once both are re-pasted.

**Daily vault intake (~2 min most days, runs as a scheduled cloud routine at 09:00 UTC):**

> Run the Pinnacle daily vault intake. (1) Scan events.yaml for three lists: (a) locked events whose end_utc is between 36 and 12 hours ago and that have no vault.yaml entry with a matching event_id; (b) locked events that ended within the last 7 days and still lack a result field; (c) events whose end_utc is more than 7 days ago. If all three lists are empty, reply "Nothing ended — no changes" and stop. (2) For each (a) event: web-search the final result and set result: on the event (short form, e.g. "Spain 1-0 Argentina"), keeping the # source: comment convention; then find the single best highlight video (official channel preferred), verify it via YouTube oEmbed (a JSON body with a matching title) — using `curl "https://www.youtube.com/oembed?url=<VIDEO_URL>&format=json"` both locally and in cloud routines (NOT `WebFetch`: it routes through a separate egress layer that stays blocked on youtube even after the environment allows it; `curl` uses the session egress proxy. If `curl` returns 403/EGRESS_BLOCKED the egress policy has regressed — hold the event, report ⚠️ VERIFICATION BLOCKED, do not prune) — then ALSO check the duration, because oEmbed returns no length and a 45-second teaser passes a title match (`curl -s "https://www.youtube.com/watch?v=<ID>" | grep -o '"lengthSeconds":"[0-9]*"' | head -1`). Always record the observed duration in the entry's `# oembed title:` comment. Under ~4 minutes is a JUDGMENT TRIGGER, not an automatic reject: ask whether this is the complete moment or a teaser for it — a single-effort moment (a goal, a vault, a launch catch) is legitimately short and the vault already holds 10 s, 51 s and 208 s entries, and IFSC/Diamond League official uploads often run 60-180 s; but a multi-hour event summarized in under 4 minutes IS a teaser — reject that and keep looking — and append a vault.yaml entry with id, title, subject, date (the event date), category copied from the event, video_url, one_liner, event_id set to the event's id, and verified stamped with today's date. If no verifiable highlight exists yet, skip that event without a vault entry — the next run or the weekly audit will catch it. But if a good candidate exists and the *verification itself* failed (network block, tool error), do not skip silently: report it under "⚠️ VERIFICATION BLOCKED" at the top of the summary AND write a `# ⚠️ HOLD <date>:` comment above the event in events.yaml (what failed, the candidate URL, "do not prune") and commit it — the run summary is ephemeral, the committed comment is what a later local session finds and sweeps. If a `⚠️ HOLD` comment already exists on that event, update it in place — never add a second. Conversely, if verification WORKED and there is genuinely no official free highlight (PPV-gated card, rights-locked event), write `# ✅ NO HIGHLIGHT <date>: searched with working egress, no official free highlight exists — free to prune` instead: that marker is the only escape from the unprunable "result, no vault entry" state, and it may ONLY be written when the oEmbed check actually ran. Blocked = hold; searched-and-empty = no-highlight. (3) Fill result: for each (b) event via web search. (4) Delete each (c) event, together with its leading comment block — EXCEPT any that carries a `⚠️ HOLD` comment, or that has a result with no matching vault entry, except one carrying a `✅ NO HIGHLIGHT` note: those stay, held, until a session can verify a highlight or mark it no-highlight. (5) Run build.py; fix any validation errors; commit ("daily vault intake: ...") and push. Summarize in up to 5 bullets.

**Weekly (~10 min, runs as a scheduled cloud routine Thursdays 11:00 UTC):**

> Run the Pinnacle weekly refresh: (1) Verify every locked event in events.yaml in the next 21 days — confirm date/time/UTC and watch links via web search; fix drift. (2) Check active playoff/knockout series in tracked leagues; add newly-confirmed elimination games per the rules in PINNACLE.md §5; remove events that were cancelled or can no longer occur — but keep events that already finished in the last 7 days (the daily intake prunes those on schedule). (3) Promote any radar items that now have confirmed dates. (4) Audit the past week: every locked event that ended should carry a result and have a vault.yaml entry with a matching event_id — backfill anything the daily intake missed, and sweep held events — `grep -niE "⚠|\b(hold|held)\b" events.yaml` (tolerant on purpose: the 08-17 routine wrote "HELD", which a plain "⚠️ HOLD" or "-i hold" search misses; lines carrying ✅ are already handled) — and for each real one verify the held candidate → vault it → REPLACE the whole ⚠️ HOLD block with a ✅ HOLD RESOLVED note. If verification is still blocked, say so loudly and leave the hold in place: this sweep normally FAILS while egress is down, and that failure report IS the regression alarm — the local sweep is what actually clears holds. (5) Run build.py, commit, push. Summarize changes in 5 bullets.

**Monthly deep scan (~20 min):**

> Run the Pinnacle monthly scan: everything in the weekly refresh, plus (1) search for newly announced one-off feats and specials — free solo projects, record attempts (marathon, altitude, depth, speed), first-of-kind rocket missions, big-wave green lights, exhibition matches between world #1s; add qualifying items to radar. (2) Verify next-quarter dates for all recurring events in PINNACLE.md §5's master list. (3) Sanity-check all YouTube channel IDs in channels.yaml still resolve. (4) Ask Brad (in the summary) about any borderline new event before adding it.
