# PINNACLE — Project Instructions

## What This Project Does

Tracks only the pinnacle of human competition (finals, elimination games, world championships, one-off feats) and publishes two silent .ics calendar feeds + a static dashboard via GitHub Pages. Everything generates from `events.yaml` — the full spec, schema, and elimination-only filter rules are in **PINNACLE.md**; read it before changing anything.

## Credentials & APIs Used

None. No API keys, no paid services. YouTube channel IDs are scraped keylessly (`resolve_channels.py`); vault links are verified via YouTube's public oEmbed endpoint; event dates via web search. Deploy is a plain `git push` (GitHub Pages serves `/docs` on `main`).

## Project-Specific Workflows

- **Weekly refresh / monthly scan** — verbatim prompts in README.md (§Refresh workflow). They edit `events.yaml`/`vault.yaml`, then `build.py`, commit, push.
- **Any data change** → run `.venv/bin/python build.py` (validates + regenerates `docs/`). Never hand-edit files in `docs/` — they're all generated except `manifest.json` and `icon.svg`.
- **New YouTube handle in events.yaml** → run `.venv/bin/python resolve_channels.py` (build fails if a referenced handle has no resolved UC id).
- **Vault additions** → verify the link first: `curl "https://www.youtube.com/oembed?url=<VIDEO_URL>&format=json"` must return 200 with a matching title; stamp `verified:` with today's date.

## Notes & Quirks

- Tier rule: `locked` only when the full start **time** is officially confirmed; date-known-but-time-TBD stays `radar` with the date in `why`. Radar `window` strings must contain a month + year ("Oct 2026") — the ICS all-day marker lands on the 1st of the first month found.
- Timezone math is the #1 error class (US evening events cross midnight UTC). Every entry carries a `# source:` comment showing the conversion — keep that convention.
- ICS output is deterministic (DTSTAMP mirrors DTSTART): rebuilding without data changes must produce a zero diff on the .ics files.
- The dashboard live embed (`youtube.com/embed/live_stream?channel=UC…`) shows an error inside the iframe if the channel isn't actively live — that's undetectable cross-origin and expected; the static "watch on official page" button is the fallback.
- Silent by design: no VALARMs ever, `TRANSP:TRANSPARENT`, no emails/push. Don't add them.
- Test the dashboard at any point in time with `?now=2026-07-19T19:30:00Z`.
