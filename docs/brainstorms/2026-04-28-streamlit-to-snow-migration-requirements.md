---
date: 2026-04-28
topic: streamlit-to-snow-migration
---

# Migrate Playlist Sequencer from Streamlit Community Cloud to Spotify-Internal Snow

## Problem Frame

Playlist Sequencer is a CSV-in / CSV-out tool that reorders playlist tracks by a score derived from like, save, and skip rates. It currently lives in a personal GitHub repo (`github.com/andres-monge/playlist-sequencer`) and is auto-deployed to Streamlit Community Cloud, which is unsuitable for an internal Spotify tool: the repo is outside Spotify's GHE, the deployment is outside Spotify's hosting perimeter, and ownership/sharing semantics are personal rather than team-owned.

The migration target is a static SPA hosted on Snow (`snow.spotify.net/spa/playlist-sequencer/`) with the source on GHE (`ghe.spotify.net/see-music/playlist-sequencer`), modeled on the existing [`see-music/podcast-dashboard`](../../../podcast-dashboard) reference. The streamlit deployment path at Spotify (Edge Proxy + Okta + websocket sidecar + Declarative Infra) is deliberately rejected as too heavy for a tool with no server-side requirements.

The app's logic is fully client-side-portable: pandas does sum, divide, clamp, and sort — all trivially expressible in browser JS. The current Streamlit "Copy All Track URIs" button is already raw HTML+JS embedded in [app.py:53-119](../../app.py:53), so the most user-visible interaction is already in the target language.

---

## Requirements

**Functional behavior — port of current app**

- R1. The new app accepts a CSV upload via a browser file picker (no server upload).
- R2. The new app reproduces the existing score formula bit-for-bit: `track_score = (likeRate + saveRate) / clamp(skipRate, 0.01, 1)`. The clamp prevents division by zero and matches the existing skipRate boundary in [app.py:19-20](../../app.py:19).
- R3. The new app displays the resulting rows sorted by `track_score` descending in a tabular UI, with `track_score_percentage` formatted as `XX.YY%` and positioned immediately after `track_uri` when that column exists (matching current column-reordering in [app.py:25-36](../../app.py:25)).
- R4. The new app provides a "Copy All Track URIs" button that copies newline-joined track URIs to the clipboard via `navigator.clipboard.writeText`, with the same success/failure label-flip UX as the existing implementation in [app.py:101-119](../../app.py:101).
- R5. The new app provides a "Download Optimized Playlist" button that triggers a browser download of the sorted CSV using a Blob URL.
- R6. The new app shows a graceful warning ("No 'track_uri' column found...") when the uploaded CSV lacks a `track_uri` column, hiding the Copy button in that case (matches [app.py:135-137](../../app.py:135)).

**Hosting and CI/CD**

- R7. The new app deploys to `snow.spotify.net/spa/playlist-sequencer/` via Snow.
- R8. Tingle CI auto-deploys on every push to `master` via a `build-info.yaml` modeled on [podcast-dashboard's build-info.yaml](../../../podcast-dashboard/build-info.yaml). Default branch is `master` (Tingle does not support `main`).
- R9. PR builds deploy to a per-PR review URL at `snow.spotify.net/spa/playlist-sequencer-$PR_NUMBER/`, with an auto-comment on the PR pointing to the review URL.

**Cutover sequencing**

- R10. The forwarding redirect on the old Streamlit URL is **only** activated after the Snow app is verified working end-to-end. Verification means: a real CSV upload produces an identical sorted output to the current Streamlit app on the same input.
- R11. After verification, `app.py` in the personal GitHub repo (`github.com/andres-monge/playlist-sequencer`) is replaced with a minimal Streamlit page that displays a "This tool has moved" message and auto-redirects to the new Snow URL after 2-3 seconds via an HTML meta-refresh (or equivalent JS redirect). Streamlit Community Cloud auto-redeploys the redirect within ~30 seconds of the push.
- R12. The redirect page remains live indefinitely in v1. Archiving the personal repo and taking the Streamlit Cloud deployment offline is deferred (see Scope Boundaries).

**Repo and docs**

- R13. A new GHE repo is created at `ghe.spotify.net/see-music/playlist-sequencer`, owned by the appropriate `see-music` IAM/Bandmanager group (same ownership pattern as podcast-dashboard).
- R14. The new repo's `README.md` describes the app, links to the live Snow URL, and notes the deployment via Tingle. The legacy personal-GitHub `README.md` is updated to point at the new GHE repo and Snow URL.
- R15. The new repo does not include a `package.json`, `node_modules`, or any JS build toolchain. Contents are limited to `index.html`, `app.css`, `app.js`, `build-info.yaml`, `README.md`, and any necessary repo-config files (`.gitignore`, etc.).

---

## Success Criteria

- A Spotify employee on VPN can navigate to `snow.spotify.net/spa/playlist-sequencer/`, upload the same CSV they were previously uploading to Streamlit Community Cloud, and get an identical sorted output without any visible regression.
- After cutover, a user with the old Streamlit URL bookmarked is auto-redirected to the new Snow URL within 3 seconds, and reaches a working app.
- A future agent or implementer reading this doc can produce the new repo + Snow deployment without inventing scope, picking a stack, or guessing at cutover timing — every load-bearing decision is captured here or pointed at an authoritative reference.

---

## Scope Boundaries

- No server-side execution. No API endpoints, no auth integration, no database, no BigQuery. All math runs in the browser on user-uploaded data.
- No Edge Proxy, no Okta, no websocket-proxy sidecar, no Backstage cookiecutter, no Declarative Infra onboarding, no production-lifecycle promotion. Snow's default internal-only access is sufficient for a CSV transform tool.
- No charts, no multi-page navigation, no routing library. The UI is a single page with one form and one table.
- No JS build toolchain (no Vite, no TypeScript, no React, no `package.json`). This is a deliberate inversion of the podcast-dashboard pattern, justified by the app's complexity ceiling.
- No formal Backstage `service-info.yaml` component registration unless Snow requires it for static SPA — TBD during planning.
- No archival of the personal GitHub repo and no shutdown of the Streamlit Community Cloud deployment in v1. The redirect page stays live indefinitely; cleanup is deferred until traffic clearly migrates and stabilizes.
- No visual redesign in v1. The new app may look minimal/different from the current Streamlit chrome (since it isn't Streamlit), but no deliberate redesign work is in scope.
- No analytics, telemetry, or usage tracking on the new app.

---

## Key Decisions

- **Stack: vanilla HTML + JS, no build step.** Picked over Vite+TS and React+Vite+TS via decision-helper analysis (this conversation, 2026-04-28). The app's complexity ceiling — sum + divide + clamp + sort over ~5 fields — is too small for TypeScript or React to pay back, and a no-toolchain repo has zero ongoing maintenance (no `npm ci`, no Dependabot, no Vite version churn). The path from B → C is a mechanical 10-min migration if the app ever grows charts/tests/multiple pages, so the decision is reversible.
- **Snow site name has no `see-` prefix** (`playlist-sequencer`, not `see-playlist-sequencer`), explicitly chosen by the user against the podcast-dashboard convention. Shorter URL; minor inconsistency across the user's projects is acceptable.
- **Cutover is gated on verification.** The redirect is not pushed until the new Snow app is confirmed working on real input. This avoids the failure mode where users hit a half-broken new app via the redirect.
- **Auto-redirect with a brief countdown**, rather than a click-here notice or hard takedown. Smoothest UX for current users; old URL stays useful as a forwarding stub.
- **Personal GitHub repo stays alive (not archived) in v1.** Required to keep the Streamlit Community Cloud redirect active. Archival is deferred to a future cleanup pass.

---

## Dependencies / Assumptions

- **Verified:** The user's reference `see-music/podcast-dashboard` is React 19 + Vite + TS, deployed to Snow at `snow.spotify.net/spa/see-podcast-dashboard/`, default branch `master`, Tingle auto-deploys via `build-info.yaml`. PR-preview pattern is in [podcast-dashboard/build-info.yaml](../../../podcast-dashboard/build-info.yaml) and is the model for R9.
- **Verified:** Snow is static-only — confirmed by `backstage.spotify.net/docs/default/component/data-science-golden-path/web-app-dashboards`. This rules out Streamlit on Snow, but is fine because R1-R6 are all client-side.
- **Verified:** Streamlit Community Cloud auto-redeploys on push to the connected GitHub branch — standard Streamlit Cloud behavior; the cutover in R11 relies on this.
- **Unverified — needs planning research:** Whether Snow's deploy pipeline accepts a repo with no `package.json` (i.e., does `snow --yes` against a directory of static files work without `npm run build`?). The podcast-dashboard `build-info.yaml` uses `npm ci && npm run build && snow --no-build`; the unprefixed `snow` command may or may not handle pure-static repos out of the box. If it doesn't, the fallback is a trivial 3-line `package.json` with no real dependencies and a no-op `build` script.
- **Assumption:** The user has push access to the `see-music` GHE org (they own podcast-dashboard there).
- **Assumption:** The current `.devcontainer/devcontainer.json` and `requirements.txt` in the personal GitHub repo are deleted or ignored at cutover, since the redirect-only `app.py` no longer needs them. This is a planning detail.

---

## Outstanding Questions

### Deferred to Planning

- [Affects R7, R8][Needs research] Does Snow accept a no-`package.json` deployment via `snow --yes`, or does Tingle require a `npm run build` step even when there are no JS deps? Verify by reading `ghe.spotify.net/snow/snow-action-container` README or asking in `#streamlit-support` / Snow's support channel.
- [Affects R3, R4, R5][Technical] Visual styling: keep the existing Streamlit-default look (familiar) or design something cleaner from scratch? Default during planning is "minimal, similar to current — single column, native browser controls, one accent color matching the existing teal button." Revisit if the user wants a polish pass.
- [Affects R13][Technical] Does the new GHE repo need a `service-info.yaml` for Backstage component registration, or is a static SPA repo on Snow exempt? Verify against `backstage.spotify.net/docs/default/component/snow/`.
- [Affects R11][Technical] Exact redirect mechanism — `<meta http-equiv="refresh">` (works without JS) vs `<script>window.location = ...</script>` (works without HTML meta) vs `st.markdown` rendering both. Default is meta-refresh wrapped in `st.markdown(unsafe_allow_html=True)` for resilience against ad blockers and JS-disabled browsers.

---

## Next Steps

`-> /ce-plan` for structured implementation planning. The plan should sequence (1) new repo bootstrap, (2) static SPA implementation with feature parity, (3) Snow deployment and verification, (4) redirect cutover, in that order — never reorder (4) before (3).
