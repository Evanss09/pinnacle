# PINNACLE — Project Brief for Claude Code

A one-stop system for tracking and watching the highest level of human competition and skill.
Owner: Brad. This file is the complete spec — read it fully before building anything.

---

## 1. Mission & principles

- **Only the pinnacle.** Finals, elimination games, world championships, and world-class one-off feats. No round robins, no regular season, no group stages.
- **Not 24/7.** Most days nothing qualifies. That's correct behavior, not a bug.
- **Silent by design.** The calendar is the only alert mechanism. No emails, no push notifications, ever.
- **Traveler-first.** Brad travels constantly. All times UTC-anchored (calendar clients auto-convert). Prefer globally accessible YouTube/free sources; he also holds premium subs for the paywalled leagues, so paywalled ≠ excluded, just labeled.
- **One source of truth.** Everything (calendar feeds + dashboard) generates from a single `events.yaml`. Refresh runs edit that one file; a build script regenerates all outputs.

## 2. Deliverables

1. **Two .ics calendar feeds** (subscribable URLs via GitHub Pages):
   - `pinnacle-locked.ics` — confirmed finals/elimination games with dates & times.
   - `pinnacle-radar.ics` — announced but unscheduled or tentative (Honnold-type projects, Starship windows, conditions-dependent big-wave events, "final series starts ~June").
2. **Dashboard** — single static page (GitHub Pages), three sections:
   - 🔴 **ON NOW** — live YouTube embed when a tracked event is live.
   - **UP NEXT** — 7-day strip + countdown to next marquee event.
   - **THE VAULT** — curated shelf of greatest performances (see §7).
3. **Refresh workflow** — weekly + monthly Claude Code sessions using the verbatim prompts in §8.

## 3. Repo structure

```
pinnacle/
├── events.yaml          # single source of truth
├── vault.yaml           # curated greatest-performances entries
├── channels.yaml        # YouTube channel handles → resolved channel IDs
├── build.py             # generates docs/ outputs from the yaml files
├── docs/                # GitHub Pages root
│   ├── index.html       # dashboard
│   ├── pinnacle-locked.ics
│   ├── pinnacle-radar.ics
│   └── manifest.json    # minimal PWA manifest (add-to-homescreen)
├── PINNACLE.md          # this brief (copy it in)
└── README.md            # how to subscribe to calendars + run refreshes
```

Host on GitHub Pages (free). Keep build.py dependency-light: `pyyaml` + stdlib. Write ICS by hand (it's a simple text format) rather than pulling a heavy library.

## 4. events.yaml schema

```yaml
- id: fifa-wc-2026-final
  name: "FIFA World Cup Final"
  category: team          # team | mind | adventure | endurance | motor | strength | space
  tier: locked            # locked | radar
  start_utc: "2026-07-19T20:00:00Z"   # omit if radar/unscheduled
  end_utc:   "2026-07-19T23:00:00Z"
  window: null            # for radar items: "Oct 2026", "winter, conditions-dependent"
  why: "The single biggest match in sport. MetLife Stadium."
  watch:
    free: "FIFA+ app (region-varies); BBC/ITV in UK"
    premium: null
    youtube_channel: "@FIFA"          # for live_stream embed if applicable
    link: "https://www.fifa.com/..."  # direct watch/schedule link
  watchability: green     # green = free live | yellow = highlights only | red = premium sub
  recurrence_note: "Every 4 years"
  result: "Spain 1-0 Argentina (AET)"   # optional; filled by the daily intake after the event ends
```

**Event lifecycle:** a locked event stays in `events.yaml` for **7 days after `end_utc`** — it feeds the dashboard's *Just Ended* section. The daily intake fills `result:` ~24 h after the end, appends the highlight to `vault.yaml`, and deletes the event once it's more than 7 days past. Don't hand-prune ended events early. **The 7 days is not unconditional:** an event carrying a `⚠️ HOLD` comment, or one with a `result:` and no vault entry and no `✅ NO HIGHLIGHT` note, is held past the prune until a session can verify a highlight or mark it `✅ NO HIGHLIGHT` — losing the moment is worse than an event lingering.

**vault.yaml schema:**

```yaml
# oembed title: "<title>" | channel: <channel name> | duration <m:ss> (<n>s)   ← verification comment, required
- id: wc-2026-final-spain-argentina    # kebab-case slug
  title: "World Cup 2026 Final — Spain 1-0 Argentina"
  subject: "Spain"                     # person/team the moment belongs to
  date: "2026-07-19"                   # date of the performance (drives newest-first sort, NEW badges, fresh rotation)
  category: team                       # same taxonomy as events
  video_url: "https://www.youtube.com/watch?v=..."
  one_liner: "Why this moment matters, one sentence."
  event_id: fifa-wc-2026-final         # optional; links back to the events.yaml entry it came from (dedupe key for the daily intake)
  verified: "2026-07-22"               # date the link was oEmbed-verified (a link-check stamp, NOT an added-date)
```

**Link verification = two checks.** oEmbed HTTP 200 with a matching `title`/`author_name`, **and** a duration check — oEmbed returns no length, so a 45-second teaser passes a title match on its own (the `CODJnhDoYfY` near-miss on TdF stage 20, caught 2026-08-09). Read `lengthSeconds` off the watch page (`curl -s "https://www.youtube.com/watch?v=<ID>" | grep -o '"lengthSeconds":"[0-9]*"' | head -1`) or `yt-dlp --print duration`, and **always** record the duration in the verification comment. Under ~4 minutes is a **judgment trigger, not a reject**: a single-effort moment is legitimately short (`alvarez-wc-quarterfinal-goal` 10 s, `biles-yurchenko-double-pike` 51 s, `spacex-chopsticks-catch` 208 s are all correct entries), but a multi-hour event compressed into under 4 minutes is a teaser — reject that. Full details and the egress history are in CLAUDE.md §Vault additions.

**ICS generation rules (both feeds):**
- `TRANSP:TRANSPARENT` (doesn't block free/busy), **no VALARM components** (truly silent).
- `DTSTART`/`DTEND` in UTC with `Z` suffix.
- `STATUS:CONFIRMED` for locked, `STATUS:TENTATIVE` for radar. Radar items without dates become all-day events on the first day of their window month, prefixed "🟡 RADAR:".
- `DESCRIPTION` = the `why` line + watch link + watchability icon. The calendar entry alone should be enough to start watching.
- `X-WR-CALNAME: Pinnacle — Locked` / `Pinnacle — Radar`.

## 5. Elimination-only rules (the filter)

> **Taste recalibration (Brad, 2026-08-31):** the calendar was skewing toward combat sports and poker. Direction: boxing/UFC and poker are now *very-top-only* (a handful of era-defining events per year, not per month), while **space launches, chess/mind events, and intellectual feats get MORE weight**, along with endurance/hybrid events in the Hyrox/marathon mold. When a borderline call comes up, lean *in* for space/mind/endurance and lean *out* for combat/poker.

| Domain | What enters the calendar |
|---|---|
| NHL / NBA | Championship series only. Potential clinching games + any Game 7 → **locked**. Series start → one radar note. |
| MLB | World Series: same clincher/Game 7 rule. |
| Soccer (annual: UCL etc.) | Semifinals + final only. |
| Soccer (World Cup) / Olympics | WC: quarterfinals onward. Olympics: medal finals only, in sports Brad tracks (athletics, swimming, climbing, gymnastics marquee finals). |
| Super Bowl | The game itself (+ conference championships → radar only). |
| Tennis slams | Finals only. |
| Chess WCC | Entire match (every game is the final). Candidates: last 3 rounds + any tiebreak. |
| Norway Chess / Tata Steel / Freestyle GS / Sinquefield Cup / GCT Finals | Final round day + armageddon/playoffs/knockout finals. |
| FIDE World Rapid & Blitz | Final day of the Rapid + final day of the Blitz (two entries). |
| Poker | WSOP Main Event **final day only** (the day the champion is crowned). No other poker — no earlier final-table days, no Triton/high-roller series (tightened 2026-08-31). |
| Esports (TI, LoL Worlds, CS2 Majors) | Grand finals only; semis → radar. |
| F1 | Monaco + any race where the title can be clinched + season finale. |
| Le Mans / Isle of Man TT / UTMB / Kona / World Marathon Majors (all seven, elite races) / HYROX Elite Series + Worlds / WSM / CrossFit Games finals | The event **is** the pinnacle — include whole (key sessions only for multi-day: e.g. Le Mans start + final 2 hours as separate entries; marathons = elite-race window; HYROX = the Elite 15 Singles day of each Elite Series race — 5/season, the format that replaced Majors in 2026/27 — plus the World Championships Elite days). |
| IFSC | World Championships finals + World Cup finals rounds only (not qualis). |
| Red Bull Rampage / Cliff Diving finals / X-Alps / WSL Finals | Whole event (they're short). |
| Rocket launches / space | Weighted UP (2026-08-31): Starship flights, **all crewed launches** (ISS/Tiangong rotations and private missions count — crewed = pinnacle, drop the "borderline routine rotation" hedging), first-of-kind missions, lunar/planetary landing attempts, new-vehicle debut flights, and major mission milestones (sample returns, flagship first light). Routine Starlink/satellite ops still excluded. |
| Big wave (Eddie, Nazaré) / one-off feats | Radar until greenlit, then locked. |
| Boxing / UFC | **Era-defining fights only** (tightened 2026-08-31 — the old "undisputed/unification OR top-3 P4P" bar let in too many cards). An event qualifies only if it is an undisputed/title fight **AND** either headlined by a top-3 pound-for-pound fighter or the consensus biggest fight of the year. Expect a handful per year. When in doubt, leave it out. |

**Master event list** (culled by Brad; recalibrated 2026-08-31 — more mind/space/endurance, less combat/poker):
Team: FIFA WC, UCL final, Stanley Cup Final, World Series, NBA Finals, Super Bowl, Rugby WC (2027), Cricket WC/T20 finals.
Mind: World Chess Championship, Candidates, Norway Chess, Tata Steel, Freestyle Chess GS, Sinquefield Cup + GCT Finals, FIDE World Rapid & Blitz, The International, LoL Worlds final, CS2 Major finals, WSOP Main Event final day only.
Adventure: IFSC WCups+Worlds, Red Bull Rampage, Cliff Diving, X-Alps, UTMB, Ironman Worlds, Vendée Globe (2028), Eddie Aikau/Nazaré, WSL Finals, one-off specials.
Endurance/athletics: World Athletics Champs, Diamond League Final, all seven World Marathon Majors (Tokyo, Boston, London, Sydney, Berlin, Chicago, NYC — elite races), HYROX World Championships, Tour de France (mountain queen stages + final GC-decisive stage + Paris), cycling Worlds.
Motor/machines: F1 (per rule above), Le Mans, Isle of Man TT, rocket launches & space milestones (per rule above — weighted up).
Strength/combat: World's Strongest Man, CrossFit Games, UFC/boxing per (tightened) rule, Olympics 2028/2030.

**Currently live (July 2026), seed immediately:** World Cup semifinals July 14–15, final July 19 (MetLife, ~20:00 ET); Tour de France in progress (identify remaining queen stages + Paris finale); Wimbledon finals this weekend if not passed.

## 6. Dashboard spec (docs/index.html)

- Single self-contained HTML file (inline CSS/JS). Dark theme, fast, mobile-first (Brad is often on phone/hotel wifi).
- **ON NOW:** For events flagged live-now (computed from events.yaml times at page load) with a `youtube_channel`, embed `https://www.youtube.com/embed/live_stream?channel=<CHANNEL_ID>` — this auto-resolves to the channel's active live stream, no API key needed. Resolve handles → UC... channel IDs during first build session and store in channels.yaml (the embed requires the raw ID, not the handle). If nothing is live: show next event countdown + a Vault pick instead.
- **UP NEXT:** next 7 days from events.yaml, each row: date (viewer-local, JS-converted), name, watchability icon (🟢🟡🔴), watch link.
- **JUST ENDED:** locked events that finished within the last 7 days, newest first: end date + "Nd ago", name, `result` in accent, and — when a vault entry carries a matching `event_id` — a "Watch the highlight →" link that scrolls to, flashes, and plays the vault card.
- **FROM THE VAULT (hero):** when nothing is live, the countdown card is followed by a full-width *featured* vault pick with category badge. The pick is a **pure function of the UTC day number** (deterministic — every viewer sees the same pick): a moment dated within the last 4 days always premieres; otherwise moments dated within 14 days own even days and the classic full cycle runs on odd days.
- **THE VAULT:** grid of embedded/linked videos from vault.yaml, newest first, one-line context each. Entries whose performance `date` is within 14 days get a NEW badge (keyed off `date`, not `verified` — re-verifying a link must not re-flag it).
- PWA manifest so it can be added to home screen. No service worker complexity needed.
- No analytics, no cookies, no build framework. Boring and durable.

## 7. Vault seeds (vault.yaml starters — verify links during build)

- Kipchoge INEOS 1:59 Challenge (full + highlights)
- Alex Honnold — Free Solo El Cap footage
- Adam Ondra — Silence 9c first ascent
- Janja Garnbret — any recent Worlds final run
- Simone Biles — Yurchenko double pike
- Mondo Duplantis — latest world record vault
- SpaceX — first Starship booster catch
- Brandon Semenuk — Rampage winning run
- Magnus Carlsen — a signature blitz/banter session
- Isle of Man TT — onboard lap record (Peter Hickman)
- Marc Márquez save compilation
- Katie Ledecky — 1500m free dominance
Refresh runs append each finished tracked event's best moment.

## 8. Refresh workflow (verbatim prompts)

> **README.md §Refresh workflow is the canonical copy of these prompts** — it is what Brad pastes into the scheduled routines. The routines then run their own *stored* copy, so after any edit here or there the live routines are STALE until they are manually re-pasted. Edit README first; this section is a mirror. (It drifted once: this copy still told cloud routines to use `WebFetch`, months after that was proven wrong. Corrected 2026-08-25.)

**Daily vault intake (~2 min most days, scheduled cloud routine at 09:00 UTC):**
> Run the Pinnacle daily vault intake. (1) Scan events.yaml for three lists: (a) locked events whose end_utc is between 36 and 12 hours ago and that have no vault.yaml entry with a matching event_id; (b) locked events that ended within the last 7 days and still lack a result field; (c) events whose end_utc is more than 7 days ago. If all three lists are empty, reply "Nothing ended — no changes" and stop. (2) For each (a) event: web-search the final result and set result: on the event (short form, e.g. "Spain 1-0 Argentina"), keeping the # source: comment convention; then find the single best highlight video (official channel preferred), verify it via YouTube oEmbed (a JSON body with a matching title) — using `curl "https://www.youtube.com/oembed?url=<VIDEO_URL>&format=json"` both locally and in cloud routines (NOT `WebFetch`: it routes through a separate egress layer that stays blocked on youtube even after the environment allows it; `curl` uses the session egress proxy. If `curl` returns 403/EGRESS_BLOCKED the egress policy has regressed — hold the event, report ⚠️ VERIFICATION BLOCKED, do not prune) — then ALSO check the duration, because oEmbed returns no length and a 45-second teaser passes a title match (`curl -s "https://www.youtube.com/watch?v=<ID>" | grep -o '"lengthSeconds":"[0-9]*"' | head -1`). Always record the observed duration in the entry's `# oembed title:` comment. Under ~4 minutes is a JUDGMENT TRIGGER, not an automatic reject: ask whether this is the complete moment or a teaser for it — a single-effort moment (a goal, a vault, a launch catch) is legitimately short and the vault already holds 10 s, 51 s and 208 s entries, and IFSC/Diamond League official uploads often run 60-180 s; but a multi-hour event summarized in under 4 minutes IS a teaser — reject that and keep looking — and append a vault.yaml entry with id, title, subject, date (the event date), category copied from the event, video_url, one_liner, event_id set to the event's id, and verified stamped with today's date. If no verifiable highlight exists yet, skip that event without a vault entry — the next run or the weekly audit will catch it. But if a good candidate exists and the *verification itself* failed (network block, tool error), do not skip silently: report it under "⚠️ VERIFICATION BLOCKED" at the top of the summary AND write a `# ⚠️ HOLD <date>:` comment above the event in events.yaml (what failed, the candidate URL, "do not prune") and commit it — the run summary is ephemeral, the committed comment is what a later local session finds and sweeps. If a `⚠️ HOLD` comment already exists on that event, update it in place — never add a second. Conversely, if there is genuinely no official free highlight to verify (PPV-gated card, rights-locked event), you must still PROVE egress was working before calling it empty — with no candidate URL there is nothing to oEmbed, so run a CONTROL oEmbed against a known-good video already in vault.yaml (`curl -s -o /dev/null -w "%{http_code}" "https://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3Dk-XgKRJUEgQ&format=json"`, expect 200). If the control returns 200, write `# ✅ NO HIGHLIGHT <date>: searched with working egress (control oEmbed k-XgKRJUEgQ = 200), no official free highlight exists — free to prune`. If the control FAILS, egress is blocked: that is a HOLD, not a no-highlight. The control result must appear in the marker — a no-highlight claim without it is not trustworthy. Blocked = hold; searched-with-proven-egress-and-empty = no-highlight. (3) Fill result: for each (b) event via web search. (4) Delete each (c) event, together with its leading comment block — meaning ONLY the contiguous comment lines directly above its `- id:`, stopping at the first blank line; never delete a `# ==== category ====` banner (the first event under a banner is separated from it by a blank line, so the stop rule protects it) — EXCEPT any that carries a `⚠️ HOLD` comment, or that has a result with no matching vault entry, except one carrying a `✅ NO HIGHLIGHT` note: those stay, held, until a session can verify a highlight or mark it no-highlight. (5) Run build.py; fix any validation errors; commit ("daily vault intake: ...") and push. Summarize in up to 5 bullets.

**Weekly (~10 min, scheduled cloud routine Thursdays 11:00 UTC):**
> Run the Pinnacle weekly refresh: (1) Verify every locked event in events.yaml in the next 21 days — confirm date/time/UTC and watch links via web search; fix drift. (2) Check active playoff/knockout series in tracked leagues; add newly-confirmed elimination games per the rules in PINNACLE.md §5; remove events that were cancelled or can no longer occur — but keep events that already finished in the last 7 days (the daily intake prunes those on schedule). (3) Promote any radar items that now have confirmed dates. (4) Audit the past week: every locked event that ended should carry a result and have a vault.yaml entry with a matching event_id — backfill anything the daily intake missed — backfilled links get the SAME two checks as the daily intake (oEmbed 200 with matching title/channel, AND duration recorded in the `# oembed title:` comment, with under ~4 minutes as a judgment trigger: complete moment, or teaser for it?) — and sweep held events — `grep -niE "⚠|\b(hold|held)\b" events.yaml` (tolerant on purpose: the 08-17 routine wrote "HELD", which a plain "⚠️ HOLD" or "-i hold" search misses; lines carrying ✅ are already handled) — and for each real one verify the held candidate → vault it → REPLACE the whole ⚠️ HOLD block with a ✅ HOLD RESOLVED note. If verification is still blocked, say so loudly and leave the hold in place: this sweep normally FAILS while egress is down, and that failure report IS the regression alarm — the local sweep is what actually clears holds. (5) Run build.py, commit, push. Summarize changes in 5 bullets.

**Monthly deep scan (~20 min):**
> Run the Pinnacle monthly scan: everything in the weekly refresh, plus (1) search for newly announced one-off feats and specials — free solo projects, record attempts (marathon, altitude, depth, speed), first-of-kind rocket missions, big-wave green lights, exhibition matches between world #1s; add qualifying items to radar. (2) Verify next-quarter dates for all recurring events in PINNACLE.md §5's master list. (3) Sanity-check all YouTube channel IDs in channels.yaml still resolve. (4) Ask Brad (in the summary) about any borderline new event before adding it.

## 9. First build session checklist

1. Init repo, structure per §3, enable GitHub Pages on /docs.
2. Seed events.yaml: currently-live items (§5 bottom) first, then everything datable in the next 6 months via web search; rest of master list → radar with windows.
3. Resolve YouTube channel IDs into channels.yaml: @FIFA, @ifscclimbing (verify handle), @SpaceX, @NASA, @chess, @RedBull, @redbulltv if separate, @WSL, @UTMBMontBlanc, @IRONMANtri, @CrossFitGames, plus any others encountered.
4. Write build.py, generate both .ics files + index.html, verify the ICS imports cleanly into Google Calendar (test with a validator).
5. Seed vault.yaml from §7 with verified links.
6. Update README with the two calendar subscription URLs and the two refresh prompts.
7. Suggestion: use parallel subagents for step 2 (one per category) to speed up date verification.

## 10. Explicitly out of scope

Emails, push notifications, accounts/logins, paid APIs, aggregating paywalled streams (link out with 🔴 instead), regular-season anything, 24/7 programming.
