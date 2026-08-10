# PINNACLE — Project Instructions

## What This Project Does

Tracks only the pinnacle of human competition (finals, elimination games, world championships, one-off feats) and publishes two silent .ics calendar feeds + a static dashboard via GitHub Pages. Everything generates from `events.yaml` — the full spec, schema, and elimination-only filter rules are in **PINNACLE.md**; read it before changing anything.

## Credentials & APIs Used

None. No API keys, no paid services. YouTube channel IDs are scraped keylessly (`resolve_channels.py`); vault links are verified via YouTube's public oEmbed endpoint; event dates via web search. Deploy is a plain `git push` (GitHub Pages serves `/docs` on `main`).

## Project-Specific Workflows

- **Daily vault intake / weekly refresh / monthly scan** — verbatim prompts in README.md (§Refresh workflow). They edit `events.yaml`/`vault.yaml`, then `build.py`, commit, push. The daily intake (09:00 UTC cloud routine) fills `result:` on just-ended events, appends their highlights to `vault.yaml` with an `event_id:` back-link, and prunes events >7 days past `end_utc`.
- **Any data change** → run `.venv/bin/python build.py` locally, or plain `python3 build.py` in a cloud routine (the `.venv/` is gitignored, so it does not exist in a fresh checkout). Validates + regenerates `docs/`. Never hand-edit files in `docs/` — they're all generated except `manifest.json` and `icon.svg`.
- **New YouTube handle in events.yaml** → run `.venv/bin/python resolve_channels.py` (build fails if a referenced handle has no resolved UC id).
- **Vault additions** → verify the link first with **`curl`**, both locally and in cloud routines:
  - `curl "https://www.youtube.com/oembed?url=<VIDEO_URL>&format=json"` must return 200 with a JSON body whose `title`/`author_name` match the intended official video.
  - **Use `curl`, NOT `WebFetch`, in cloud routines.** `curl` goes through the session's egress proxy (`$HTTPS_PROXY`), which honors the environment's network policy; once that policy allows `youtube.com` (Aug 2026 fix — Custom/Full access level in Claude Code web → environment settings), `curl` reaches the oEmbed endpoint. **`WebFetch` routes through a *separate* egress layer that does NOT honor the environment allowlist and stays 403/EGRESS_BLOCKED on youtube even after the fix** — so it is the wrong tool here. (Both prior claims — "use WebFetch" and "both go through the same gateway" — were wrong; verified Aug 10 2026 that curl works while WebFetch is still blocked.)
  - If `curl` itself returns 403/EGRESS_BLOCKED, the egress policy has regressed. Diagnose with `curl -sS "$HTTPS_PROXY/__agentproxy/status"` (a `connect_rejected … 403` for `youtube.com` confirms it). That is an infra failure, not "no highlight exists" — hold the event (don't prune), report `⚠️ VERIFICATION BLOCKED`, and re-allow `youtube.com` in the environment's egress policy. `WebSearch` still works (server-side) to find candidates but can't do the oEmbed pass/fail check.
  - Either way, stamp `verified:` with today's date.

## Notes & Quirks

- **The cloud environment's egress policy blocks youtube.com (a 403 policy denial on all non-allowlisted hosts — youtube, espn, google; only Anthropic services, package registries, and GitHub are reachable).** From Jul 23–27 2026 the daily intake verified links with `curl`, got an error every morning, and — following "skip if unverifiable" — silently added **zero** vault entries for 5 days. Seven moments (TdF stages 19–21, CrossFit Games finals, Starship F13) were nearly lost. We *thought* `WebFetch` was the fix, but from ~Aug 6 2026 stage-20 verification failed via `WebFetch` too: the routine correctly held the event and escalated for days rather than pruning it — proof the "hold + ⚠️ VERIFICATION BLOCKED" reflex works even when the documented workaround doesn't. **Fixed Aug 10 2026:** Brad set the environment's network access to allow `youtube.com` (Claude Code web → environment selector → gear → Network access = Custom/Full). This unblocked **`curl`** (which uses the session egress proxy) — but **`WebFetch` stayed blocked** (it uses a separate egress layer that ignores the environment allowlist). So the standing verifier is **`curl`**, not WebFetch. A `build.py` warning fires when a locked event with a `result:` is within 3 days of being pruned with no matching vault `event_id`. **Never let "the verifier broke" collapse into "nothing qualified"** — those are different outcomes and only one of them is silent.
- Tier rule: `locked` only when the full start **time** is officially confirmed; date-known-but-time-TBD stays `radar` with the date in `why`. Radar `window` strings must contain a month + year ("Oct 2026") — the ICS all-day marker lands on the 1st of the first month found.
- Timezone math is the #1 error class (US evening events cross midnight UTC). Every entry carries a `# source:` comment showing the conversion — keep that convention.
- ICS output is deterministic (DTSTAMP mirrors DTSTART): rebuilding without data changes must produce a zero diff on the .ics files.
- The dashboard live embed (`youtube.com/embed/live_stream?channel=UC…`) shows an error inside the iframe if the channel isn't actively live — that's undetectable cross-origin and expected; the static "watch on official page" button is the fallback.
- Silent by design: no VALARMs ever, `TRANSP:TRANSPARENT`, no emails/push. Don't add them.
- Ended locked events **intentionally linger 7 days** in events.yaml — the Just Ended section depends on them. Don't hand-prune; the daily intake does it on schedule.
- A `result:` landing on an event changes that event's ICS DESCRIPTION — that diff is expected and data-driven. Determinism (byte-identical rebuild on *unchanged* data) still holds.
- The featured "From the Vault" pick must stay a **pure function of the UTC day number** (no Math.random) so every viewer sees the same pick. Freshness/NEW badges key off the vault entry's performance `date`, not `verified` (re-verifying a link must not re-flag it as new).
- Test the dashboard at any point in time with `?now=2026-07-19T19:30:00Z` — this also drives Just Ended, NEW badges, and the premiere rotation.
