# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ This is the legacy Streamlit repo. Active code lives elsewhere.

The playlist-sequencer was migrated from this Streamlit app to a pure-static Snow SPA in early 2026. **`app.py` is now a redirect stub** that points users at the Snow SPA URL.

**Active code:** `~/Documents/Cursor Projects/playlist-sequencer-snow/`
**Production URL:** https://snow.spotify.net/spa/playlist-sequencer
**Why we migrated:** Streamlit's Edge Proxy + Okta + DI path was too bureaucratic for a small internal tool. See `docs/2026-04-28-migrate-to-snow-spa-plan.md` for the migration plan.

Almost all changes belong in the Snow SPA repo, not here. This repo exists only because:

- It hosts the redirect stub at the original Streamlit URL until that link is eradicated from internal docs/bookmarks.
- It preserves git history of the pre-migration Streamlit implementation.

## When you might still touch this repo

- The Streamlit-cloud deployment of the redirect breaks (rare).
- You want to reference the pre-migration scoring algorithm or UI in `git log`.
- You're wiring up something that needs the original URL to stay functional during a transition.

## What it contains today

- `app.py` — the redirect stub (a few lines: shows a deprecation notice, links to Snow URL).
- `requirements.txt` — minimal Streamlit deps for the redirect stub only.
- `.devcontainer/` — legacy dev container config (probably stale).
- `docs/` — pre-migration design docs and the migration plan.

## What changed in the migration

The actual scoring logic and UI now live in the Snow SPA. Key differences:

- **No Python, no Streamlit, no server-side processing.** The Snow SPA is vanilla HTML/CSS/JS; CSV parsing happens client-side via `FileReader`.
- **No Okta/Edge Proxy plumbing.** Snow ships with IAP for free.
- **Deploy is `git push origin master`**, not a Streamlit-cloud upload.

For everything else, go to the Snow SPA repo at `~/Documents/Cursor Projects/playlist-sequencer-snow/`.
