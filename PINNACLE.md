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
```

**ICS generation rules (both feeds):**
- `TRANSP:TRANSPARENT` (doesn't block free/busy), **no VALARM components** (truly silent).
- `DTSTART`/`DTEND` in UTC with `Z` suffix.
- `STATUS:CONFIRMED` for locked, `STATUS:TENTATIVE` for radar. Radar items without dates become all-day events on the first day of their window month, prefixed "🟡 RADAR:".
- `DESCRIPTION` = the `why` line + watch link + watchability icon. The calendar entry alone should be enough to start watching.
- `X-WR-CALNAME: Pinnacle — Locked` / `Pinnacle — Radar`.

## 5. Elimination-only rules (the filter)

| Domain | What enters the calendar |
|---|---|
| NHL / NBA | Championship series only. Potential clinching games + any Game 7 → **locked**. Series start → one radar note. |
| MLB | World Series: same clincher/Game 7 rule. |
| Soccer (annual: UCL etc.) | Semifinals + final only. |
| Soccer (World Cup) / Olympics | WC: quarterfinals onward. Olympics: medal finals only, in sports Brad tracks (athletics, swimming, climbing, gymnastics marquee finals). |
| Super Bowl | The game itself (+ conference championships → radar only). |
| Tennis slams | Finals only. |
| Chess WCC | Entire match (every game is the final). Candidates: last 3 rounds + any tiebreak. |
| Norway Chess / Tata Steel / Freestyle GS | Final round day + armageddon/playoffs. |
| Esports (TI, LoL Worlds, CS2 Majors) | Grand finals only; semis → radar. |
| F1 | Monaco + any race where the title can be clinched + season finale. |
| Le Mans / Isle of Man TT / UTMB / Kona / marathons majors / WSM / CrossFit Games finals | The event **is** the pinnacle — include whole (key sessions only for multi-day: e.g. Le Mans start + final 2 hours as separate entries). |
| IFSC | World Championships finals + World Cup finals rounds only (not qualis). |
| Red Bull Rampage / Cliff Diving finals / X-Alps / WSL Finals | Whole event (they're short). |
| Rocket launches | Starship integrated tests, crewed launches, first-of-kind missions only. Routine Starlink = excluded. |
| Big wave (Eddie, Nazaré) / one-off feats | Radar until greenlit, then locked. |
| Boxing / UFC | Undisputed/unification title fights and title fights between top-3 P4P only. |

**Master event list** (already culled by Brad — seed events.yaml from this):
Team: FIFA WC, UCL final, Stanley Cup Final, World Series, NBA Finals, Super Bowl, Rugby WC (2027), Cricket WC/T20 finals.
Mind: World Chess Championship, Candidates, Norway Chess, Tata Steel, Freestyle Chess GS, The International, LoL Worlds final, CS2 Major finals, WSOP Main Event final table.
Adventure: IFSC WCups+Worlds, Red Bull Rampage, Cliff Diving, X-Alps, UTMB, Ironman Worlds, Vendée Globe (2028), Eddie Aikau/Nazaré, WSL Finals, one-off specials.
Endurance/athletics: World Athletics Champs, Diamond League Final, Berlin + Boston marathons, Tour de France (mountain queen stages + final GC-decisive stage + Paris), cycling Worlds.
Motor/machines: F1 (per rule above), Le Mans, Isle of Man TT, rocket launches.
Strength/combat: World's Strongest Man, CrossFit Games, UFC/boxing per rule, Olympics 2028/2030.

**Currently live (July 2026), seed immediately:** World Cup semifinals July 14–15, final July 19 (MetLife, ~20:00 ET); Tour de France in progress (identify remaining queen stages + Paris finale); Wimbledon finals this weekend if not passed.

## 6. Dashboard spec (docs/index.html)

- Single self-contained HTML file (inline CSS/JS). Dark theme, fast, mobile-first (Brad is often on phone/hotel wifi).
- **ON NOW:** For events flagged live-now (computed from events.yaml times at page load) with a `youtube_channel`, embed `https://www.youtube.com/embed/live_stream?channel=<CHANNEL_ID>` — this auto-resolves to the channel's active live stream, no API key needed. Resolve handles → UC... channel IDs during first build session and store in channels.yaml (the embed requires the raw ID, not the handle). If nothing is live: show next event countdown + a Vault pick instead.
- **UP NEXT:** next 7 days from events.yaml, each row: date (viewer-local, JS-converted), name, watchability icon (🟢🟡🔴), watch link.
- **THE VAULT:** grid of embedded/linked videos from vault.yaml, newest first, one-line context each.
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

**Weekly (~10 min, run in Claude Code from repo root):**
> Run the Pinnacle weekly refresh: (1) Verify every locked event in events.yaml in the next 21 days — confirm date/time/UTC and watch links via web search; fix drift. (2) Check active playoff/knockout series in tracked leagues; add newly-confirmed elimination games per the rules in PINNACLE.md §5; remove events that can no longer occur. (3) Promote any radar items that now have confirmed dates. (4) Add the best moment from any tracked event that finished this week to vault.yaml. (5) Run build.py, commit, push. Summarize changes in 5 bullets.

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
