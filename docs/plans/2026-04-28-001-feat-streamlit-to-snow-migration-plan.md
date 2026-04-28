---
title: Migrate Playlist Sequencer from Streamlit to Snow SPA
type: feat
status: active
date: 2026-04-28
deepened: 2026-04-28
origin: docs/brainstorms/2026-04-28-streamlit-to-snow-migration-requirements.md
---

# Migrate Playlist Sequencer from Streamlit to Snow SPA

> **Target repos:** Most units land in a **new GHE repo** at `ghe.spotify.net/see-music/playlist-sequencer`. Units U5 and U6 modify the **existing personal-GitHub repo** at `github.com/andres-monge/playlist-sequencer` (cutover redirect + old README update). All file paths in this plan are repo-relative to whichever repo a unit targets — the unit headers state which.

---

## Overview

Port the Playlist Sequencer (CSV-in / sorted-CSV-out playlist optimizer) from a personal-GitHub Streamlit app to a Spotify-internal static SPA on Snow, with bit-for-bit feature parity, then cut over by adding an auto-redirect on the old Streamlit URL only after the new Snow app is verified working on real input.

The migration is a **deployment-platform pivot**, not a refactor: the algorithm (sum + divide + clamp + sort over ~5 fields) is identical; only the runtime moves from server-side Python to client-side JS. The reference implementation is [`see-music/podcast-dashboard`](../../../podcast-dashboard) (Snow + Tingle + GHE), but with a deliberate stack inversion — vanilla HTML/JS/CSS instead of React+Vite+TS, justified by the app's complexity ceiling.

---

## Problem Frame

The current app lives at `github.com/andres-monge/playlist-sequencer` (personal GitHub) and auto-deploys to Streamlit Community Cloud. Both endpoints are outside Spotify's perimeter, with personal rather than team ownership. The internal Streamlit-on-Spotify path (Edge Proxy + Okta + websocket sidecar + Declarative Infra) is rejected as too heavy for a tool with no server-side requirements.

The migration target is a static SPA on Snow at `snow.spotify.net/spa/playlist-sequencer/`, with the source on GHE at `ghe.spotify.net/see-music/playlist-sequencer`. The current "Copy All Track URIs" button is already raw HTML+JS embedded in [app.py:53-119](../../app.py:53), so the most user-visible interaction is already in the target language.

(See origin: [docs/brainstorms/2026-04-28-streamlit-to-snow-migration-requirements.md](../brainstorms/2026-04-28-streamlit-to-snow-migration-requirements.md))

---

## Requirements Trace

- R1. Browser file picker for CSV upload (no server upload).
- R2. Score formula bit-for-bit: `track_score = (likeRate + saveRate) / clamp(skipRate, 0.01, 1)`.
- R3. Sorted by `track_score` desc; `track_score_percentage` formatted `XX.YY%` and placed immediately after `track_uri`.
- R4. "Copy All Track URIs" button via `navigator.clipboard.writeText`, with the same success/failure label-flip UX.
- R5. "Download Optimized Playlist" button via Blob URL.
- R6. Graceful warning when CSV lacks `track_uri`; Copy button hidden in that case.
- R7. Deploys to `snow.spotify.net/spa/playlist-sequencer/`.
- R8. Tingle auto-deploys on push to `master` via `build-info.yaml`. Default branch is `master` (Tingle does not support `main`).
- R9. PR builds deploy to `snow.spotify.net/spa/playlist-sequencer-$PR_NUMBER/` with auto-comment on the PR.
- R10. Forwarding redirect on the old Streamlit URL is **only** activated after end-to-end verification on real CSV input.
- R11. Personal-GitHub `app.py` becomes a minimal "This tool has moved" page that auto-redirects to the new Snow URL within 2-3 seconds.
- R12. Redirect page remains live indefinitely in v1 (no archival of personal repo, no Streamlit Cloud shutdown).
- R13. New GHE repo at `ghe.spotify.net/see-music/playlist-sequencer`, owned by appropriate `see-music` IAM/Bandmanager group.
- R14. New repo's `README.md` describes app, links to live Snow URL, notes Tingle deploy. Legacy personal-GitHub `README.md` updated to point at new GHE repo + Snow URL.
- R15. New repo contains no `package.json`, `node_modules`, or JS build toolchain. Files limited to `index.html`, `app.css`, `app.js`, `build-info.yaml`, `README.md`, and minimal repo-config.

---

## Scope Boundaries

- No server-side execution. No API endpoints, no auth integration, no database, no BigQuery. All math runs in the browser on user-uploaded data.
- No Edge Proxy, no Okta, no websocket-proxy sidecar, no Backstage cookiecutter, no Declarative Infra onboarding, no production-lifecycle promotion.
- No charts, no multi-page navigation, no routing library. Single page, one form, one table.
- No JS build toolchain (no Vite, no TypeScript, no React, no `package.json`) — deliberate inversion of the podcast-dashboard pattern.
- No formal Backstage `service-info.yaml` registration (resolved during planning — see Open Questions).
- No archival of the personal GitHub repo and no shutdown of the Streamlit Community Cloud deployment in v1.
- No visual redesign in v1.
- No analytics, telemetry, or usage tracking on the new app.

---

## Context & Research

### Relevant Code and Patterns

- [`podcast-dashboard/build-info.yaml`](../../../podcast-dashboard/build-info.yaml) — canonical Tingle pipeline for Snow SPAs. Provides the master pipeline, PR review pipeline, `--review` flag pattern, and `ghe-pr-comment:1.1.0` auto-comment step. Direct template for U3.
- [`podcast-dashboard/index.html`](../../../podcast-dashboard/index.html) — CSP `default-src 'self'` lockdown pattern. Self-only is sufficient for our app (clipboard write is a same-origin browser API, not a network call).
- [`podcast-dashboard/.gitignore`](../../../podcast-dashboard/.gitignore) — baseline `.gitignore` for Snow SPA repos (`.DS_Store`, `*.swp`, OS noise). Strip the JS-toolchain entries since we don't have any.
- [`app.py:11-39`](../../app.py:11) — current `optimize_playlist()` function. Direct algorithmic reference for U2's port.
- [`app.py:53-119`](../../app.py:53) — current Copy URIs HTML+JS embed. The button styling (teal `rgb(33, 128, 141)`, `Source Sans Pro`, 0.5rem border-radius), SVG icon, and clipboard logic port directly into `app.css` and `app.js`.

### Institutional Learnings

- Memory: [reference_podcast_dashboard_snow_pattern.md](../../../../.claude/projects/-Users-andresm-Documents-Cursor-Projects-playlist-sequencer/memory/reference_podcast_dashboard_snow_pattern.md) — Snow SPAs use `master` branch (Tingle doesn't support `main`), `base: '/spa/<site-name>/'` is required when Vite is used, `snow --yes` is the manual deploy fallback.
- Memory: [feedback_avoid_streamlit_at_spotify.md](../../../../.claude/projects/-Users-andresm-Documents-Cursor-Projects-playlist-sequencer/memory/feedback_avoid_streamlit_at_spotify.md) — User explicitly prefers Snow over the internal Streamlit path. Reinforces R7-R9.

### External References

- Brainstorm verified: Snow is static-only (`backstage.spotify.net/docs/default/component/data-science-golden-path/web-app-dashboards`). This rules out Streamlit on Snow but is fine because R1-R6 are all client-side.
- Brainstorm verified: Streamlit Community Cloud auto-redeploys on push to the connected GitHub branch (~30 seconds). The cutover in R11 relies on this.

---

## Key Technical Decisions

- **Stack: vanilla HTML + JS + CSS, no build step.** Carried verbatim from origin. The app's complexity ceiling — sum + divide + clamp + sort over ~5 fields — is too small for TypeScript or React to pay back, and a no-toolchain repo has zero ongoing maintenance (no `npm ci`, no Dependabot, no Vite version churn). The path from this stack to React+Vite+TS is a mechanical 10-min migration if the app ever grows charts/tests/multiple pages, so the decision is reversible. (See origin.)
- **Snow site name `playlist-sequencer` (no `see-` prefix).** Carried verbatim from origin. Shorter URL; minor inconsistency with podcast-dashboard's `see-podcast-dashboard` is acceptable.
- **Verification is manual browser-based, not automated tests.** Direct consequence of R15 (no JS toolchain). Adding Jest/Vitest would require `package.json`, dev dependencies, and a `node_modules/` tree — explicitly excluded by R15. For an app this small, manual verification scenarios with specific input/output assertions provide adequate coverage. The identical-output gate in U4 is the load-bearing verification that protects R10.
- **CSV parsing: inline minimal parser, with Papa Parse via CDN (with SRI) as a documented fallback.** The default approach is a ~30-line inline parser handling the three RFC 4180 cases that matter for playlist CSVs: quoted fields containing commas, escaped quotes (`""` → `"`), and header rows. If real-world CSVs trigger parser bugs (most likely failure mode: embedded newlines inside a quoted field), swap to Papa Parse via jsDelivr CDN with these specifics — pin the exact version (e.g., `papaparse@5.4.1`, never the floating `papaparse@5`), include an SRI hash for supply-chain safety (`openssl dgst -sha384 -binary papaparse.min.js | base64`), and narrow the CSP relaxation to exactly `script-src 'self' https://cdn.jsdelivr.net`. The script tag becomes `<script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js" integrity="sha384-<hash>" crossorigin="anonymous"></script>`. The pinned-version + SRI combination addresses supply-chain risk fully; CDN loading is fine when used this way. **Vendoring** (committing `papaparse.min.js` next to `app.js`) is also a valid alternative if you'd rather avoid a CSP change at the cost of maintaining a committed file across version bumps; pick whichever feels less annoying. Document the chosen path in a top-of-file comment in `app.js`.
- **Percentage formatting uses fixed-2-decimal `toFixed(2)`, not pandas' variable-decimal output.** Pandas' `.round(2).astype(str)` produces `'6.0%'`, `'6.5%'`, `'6.12%'` (variable trailing zeros); JS's `toFixed(2)` produces `'6.00%'`, `'6.50%'`, `'6.12%'`. R3 specifies `XX.YY%` which favors the JS form. The numeric `track_score` values are bit-for-bit identical (R2); the display string differs in two ways: (a) trailing zeros, AND (b) banker's rounding — pandas uses half-to-even (so `0.125` → `0.12`), JS `toFixed` uses half-away-from-zero (so `(0.125).toFixed(2)` → `0.13` in V8/Chrome). For values exactly at `.x05` boundaries, the displayed percentage can differ by `0.01`. Treat this as a small UX improvement, not a regression. **U4's identical-output verification must compare the underlying numeric `track_score` column to ≥4 decimal places — never compare the `track_score_percentage` display string column directly, because both display formatting and rounding mode differ.**
- **`service-info.yaml` is NOT needed.** Resolved during planning by precedent: podcast-dashboard runs successfully on Snow with only `build-info.yaml` and no Backstage component registration. (See Open Questions.)
- **Try no-`package.json` first; fall back to a 3-line no-op `package.json` if Snow's pipeline rejects pure-static repos.** The brainstorm's Q1 is genuinely deploy-time-unknowable. The plan's default is the leaner path (no toolchain) per R15. If `npm ci && npm run build && snow --no-build` fails because there is no `package.json`, the implementer drops in:
  ```json
  { "name": "playlist-sequencer", "private": true, "version": "0.1.0", "scripts": { "build": "true" } }
  ```
  and re-pushes. This fallback is mechanical and documented in U3.
- **Cutover ordering is a hard invariant.** U5 (redirect on old Streamlit) is dependency-blocked by U4 (verify on Snow). Encoded explicitly in unit dependencies. A redirect to a half-broken target is worse than the status quo.

---

## Open Questions

### Resolved During Planning

- **Does the new GHE repo need `service-info.yaml` for Backstage component registration?** Resolved: **No.** Verified by precedent — `podcast-dashboard` has only `build-info.yaml` and runs successfully on Snow without Backstage component registration. (Origin Q3, [Affects R13].)
- **Visual styling: keep Streamlit-default look or design from scratch?** Resolved: **minimal, similar to current.** Single column, native browser controls, one accent color matching the existing teal button (`rgb(33, 128, 141)`), `Source Sans Pro` typography (or system-ui fallback). No deliberate redesign in v1, per Scope Boundaries. (Origin Q2, [Affects R3, R4, R5].)
- **Exact redirect mechanism on the old Streamlit URL?** Resolved: **HTML meta-refresh wrapped in `st.markdown(unsafe_allow_html=True)`**. Works without JS execution (resilient to ad blockers and JS-disabled browsers); supplemented with a `<script>window.location = ...</script>` belt-and-braces for the rare case where meta-refresh is blocked. (Origin Q4, [Affects R11].)

### Deferred to Implementation

- **Does Snow's deploy pipeline accept a no-`package.json` repo via `snow --yes`?** Genuinely deploy-time-unknowable; the answer comes from observing Tingle's first run on master. Plan defaults to the leaner path (R15-faithful) and documents the mechanical fallback in U3. (Origin Q1, [Affects R7, R8].)
- **Exact `see-music` GHE owning team / IAM group for the new repo.** The user owns `podcast-dashboard` under `see-music`, so push access exists. The specific Bandmanager group used to mirror podcast-dashboard's ownership is verified at repo-creation time in U1 (a 30-second `gh repo view ghe.spotify.net/see-music/podcast-dashboard --json owner` or equivalent).
- **Whether real-world playlist CSVs trigger inline-parser edge cases.** Default: minimal inline parser. Fallback: Papa Parse via CDN. Determined by U4's verification step on a real CSV.

---

## Output Structure

New GHE repo at `ghe.spotify.net/see-music/playlist-sequencer` (after U1 + U2 + U3):

    playlist-sequencer/
    ├── .gitignore
    ├── README.md
    ├── build-info.yaml
    ├── index.html
    ├── app.css
    └── app.js

Modified personal-GitHub repo at `github.com/andres-monge/playlist-sequencer` (after U5 + U6):

    playlist-sequencer/
    ├── README.md          # updated to point at new GHE repo + Snow URL
    ├── app.py             # replaced with redirect-only Streamlit page
    └── requirements.txt   # unchanged (Streamlit Cloud still needs streamlit)

> The implementer may adjust file structure if implementation reveals a better layout. Per-unit `**Files:**` sections remain authoritative.

---

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

**Cutover sequence (load-bearing — never reorder):**

```
┌──────────────────────────────────────────────────────────────────┐
│ NEW GHE repo: ghe.spotify.net/see-music/playlist-sequencer       │
│                                                                  │
│   U1. Bootstrap repo  ─→  U2. SPA  ─→  U3. build-info.yaml       │
│                                              │                   │
│                                              ▼                   │
│                                      U4. Deploy & verify         │
│                                      (R10 gate: real CSV)        │
│                                              │                   │
└──────────────────────────────────────────────┼───────────────────┘
                                               │
                                               ▼ (only after U4 passes)
┌──────────────────────────────────────────────────────────────────┐
│ EXISTING personal-GitHub repo: github.com/andres-monge/...       │
│                                                                  │
│   U5. Replace app.py with redirect ──→ U6. Update README         │
│       (Streamlit Cloud auto-deploys                              │
│        within ~30 seconds)                                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**SPA runtime data flow** (inside U2's `app.js`):

```
File picker change event
        │
        ▼
FileReader.readAsText()  ─────────────────────────┐
        │                                         │
        ▼                                         │
parseCSV(text)  →  rows: Array<{header: value}>   │
        │                                         │
        ▼                                         │
optimizePlaylist(rows):                           │
   for each row:                                  │
     likeRate  ← parseFloat or 0                  │
     saveRate  ← parseFloat or 0                  │
     skipRate  ← clamp(parseFloat or 0, 0.01, 1)  │
     discoveryRate ← likeRate + saveRate          │
     track_score   ← discoveryRate / skipRate     │
     track_score_percentage ← (track_score * 100).toFixed(2) + '%'
   sort rows desc by track_score                  │
        │                                         │
        ▼                                         │
renderTable(rows)  ──→  <table> in #output       │
        │                                         │
        ├──→ extractTrackURIs(rows)  ──→ Copy button enabled/hidden
        │                                         │
        └──→ buildCSVBlob(rows)  ────────────────→ Download button href
```

The shape mirrors the current `app.py` linearly: read → optimize → render → expose Copy/Download. No reactive framework, no virtual DOM, no async beyond the FileReader and Clipboard APIs. The whole `app.js` should fit comfortably in 150-200 lines.

---

## Implementation Units

> All units in U1–U4 target the **new GHE repo** (`ghe.spotify.net/see-music/playlist-sequencer`). Units U5–U6 target the **existing personal-GitHub repo** (`github.com/andres-monge/playlist-sequencer`). File paths are repo-relative to the unit's target repo.

---

- U1. **Bootstrap new GHE repo with baseline files**

**Goal:** Create the new GHE repo with default branch `master`, baseline `.gitignore`, and a placeholder `README.md`. This is the scaffolding unit that establishes the target for U2-U4.

**Requirements:** R13, R14 (first half — new repo's README), R15 (limit on file types).

**Dependencies:** None. (The user's `see-music` GHE access is verified by their existing ownership of `podcast-dashboard`.)

**Target repo:** `ghe.spotify.net/see-music/playlist-sequencer` (new).

**Files:**
- Create: `.gitignore`
- Create: `README.md`

**Approach:**
- **Pre-flight (gathered alongside repo creation, recorded in the plan/PR/commit):**
  - **Live Streamlit URL.** Capture the actually-deployed Streamlit Community Cloud URL for the current Playlist Sequencer (likely `https://playlist-sequencer.streamlit.app/` but the exact URL must be verified by visiting share.streamlit.io or the user's bookmark). U4's identical-output verification depends on this URL being correct. Record it in the plan's Sources section or in U4's Step A comment.
  - **Streamlit Cloud deploy branch.** Open `share.streamlit.io`, find the Playlist Sequencer app entry, note the configured deploy branch (commonly `main` for the personal repo). U5 must push to that branch — pushing to a different branch silently no-ops the cutover.
  - **`see-music` ownership reference.** Mirror podcast-dashboard's ownership (`gh repo view ghe.spotify.net/see-music/podcast-dashboard --json owner` or equivalent Bandmanager check). If the user's `see-music` access is via a personal-team membership rather than a group, surface that to the user before pushing U2.
- Create the GHE repo via `gh repo create ghe.spotify.net/see-music/playlist-sequencer` (or the GHE web UI), with default branch set to `master` from the start (Tingle does not support `main`).
- `.gitignore`: derive from podcast-dashboard's, **strip all JS-toolchain entries** (`node_modules/`, `build/`, `dist/`) since R15 forbids them. Keep `.DS_Store`, `*.swp`, `*.swo`, `.vscode/`, `.idea/`, `.env*`.
- `README.md`: short and Ankane-style — title, one-paragraph description ("CSV-in / sorted-CSV-out playlist optimizer"), live Snow URL placeholder (filled in after U4), deployment note ("Tingle auto-deploys to Snow on push to `master`"), no algorithm walkthrough (the algorithm is documented in `app.js` itself).
- Land as the initial commit on `master`.

**Patterns to follow:**
- [`podcast-dashboard/.gitignore`](../../../podcast-dashboard/.gitignore) — strip the JS-toolchain entries before copying.
- [`podcast-dashboard/README.md`](../../../podcast-dashboard/README.md) lines 1-15 — Stack/Repo/CI section structure, but trimmed because we have no charts/data pipeline.

**Test scenarios:**
- Verification (Happy path): `gh repo view ghe.spotify.net/see-music/playlist-sequencer` returns the repo with default branch `master`, owner = `see-music`-aligned IAM group.
- Verification (Edge case): `git ls-tree --name-only master` shows only `.gitignore` and `README.md` (no committed `node_modules/`, no stray Python artifacts from a wrong-repo push).
- Test expectation: scaffolding unit — primary verification is "files exist on `master`."

**Verification:**
- New GHE repo accessible at `ghe.spotify.net/see-music/playlist-sequencer` with default branch `master`.
- README renders correctly on GHE web UI.

---

- U2. **Implement static SPA with feature parity**

**Goal:** Build the entire client-side app — file upload, CSV parse, score computation, sorted-table render, Copy URIs button, Download button — as `index.html` + `app.css` + `app.js` with no build step. Achieves R1-R6.

**Requirements:** R1, R2, R3, R4, R5, R6, R15.

**Dependencies:** U1.

**Target repo:** `ghe.spotify.net/see-music/playlist-sequencer` (new).

**Files:**
- Create: `index.html`
- Create: `app.css`
- Create: `app.js`

**Approach:**
- **`index.html`** (~40 lines): `<!doctype html>`, `<head>` with `<meta charset>`, `<meta viewport>`, **CSP carried verbatim from [podcast-dashboard/index.html:7](../../../podcast-dashboard/index.html:7)**: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'self'; base-uri 'self'; form-action 'none';`. (Earlier drafts of this plan said "default-src 'self'" only — that was wrong; podcast-dashboard's policy is multi-directive and `style-src 'self' 'unsafe-inline'` and `img-src 'self' data:` are load-bearing for SVG-fill and stylesheet behavior.) `<title>Playlist Sequencer</title>`, `<link rel="stylesheet" href="app.css">`. `<body>` contains an `<h1>`, a `<form>` with `<input type="file" accept=".csv">`, a `<div id="output">` (initially empty), and `<script src="app.js"></script>` at the end. No `<script type="module">` — module imports require a bundler or a server with proper MIME types; classic scripts work cleanly on Snow.
- **`app.css`** (~50 lines): single column, max-width container (~960px), system-ui font with `Source Sans Pro` fallback. Teal accent color `rgb(33, 128, 141)` for buttons (carried from [app.py:73](../../app.py:73) for visual continuity). Table styling: bordered, alternating row backgrounds. Copy/Download buttons: 0.5rem border-radius, 0.4rem 1rem padding, white text, hover opacity 0.8, fixed `min-width: 180px` to prevent jump on label-flip (carried from [app.py:69-89](../../app.py:69)). Prefer external CSS for maintainability, but inline `style=` attributes are fine when concise (e.g., the SVG icon's `fill` attribute, one-off layout tweaks). The mirrored CSP includes `style-src 'self' 'unsafe-inline'`, so inline styles work without policy changes.
- **`app.js`** (~150-200 lines), structured as a small set of pure functions plus inline DOM glue. The original draft listed factory functions (`buildCopyButton`, `buildDownloadButton`, `buildWarning`) — each used exactly once. Per the plan's own complexity-ceiling argument, single-call factories don't earn their abstraction tax; the Copy and Download DOM construction lives directly in the change-event handler. The remaining functions are pure-data transforms that do benefit from isolation:
  - `parseCSV(text) → {headers, rows}` — minimal parser handling the three RFC 4180 cases that matter for playlist CSVs: quoted fields with commas, escaped quotes (`""`), and a header row. Embedded newlines inside quoted fields are NOT handled — see Risks for the vendoring fallback. Document the chosen-fallback decision in a top-of-file comment.
  - `optimizePlaylist(rows, headers) → {rows, headers}` — direct port of [app.py:11-39](../../app.py:11). Coerce numeric fields with `Number(value)` (NOT `parseFloat`) + `Number.isNaN` check. `Number()` rejects partial parses like `"1,234"` (returns `NaN` → coerced to 0), which is closer to pandas' `pd.to_numeric(errors='coerce')` behavior than `parseFloat("1,234") === 1`. Acknowledged parity gaps: pandas `pd.to_numeric` accepts a few formats `Number()` rejects (e.g., trailing whitespace is fine in both; embedded units are rejected by both; locale-comma `"1,234"` is rejected by both — actually full alignment for the formats playlist CSVs are likely to contain). Clamp `skipRate` to `[0.01, 1]` via `Math.max(0.01, Math.min(1, skipRate))`. Compute `discoveryRate`, `track_score`, `track_score_percentage` (using `toFixed(2)` per K.T.D.). Reorder columns so `track_score_percentage` follows `track_uri` when present (and is appended at the end when absent). Sort rows descending by `track_score` (no secondary key — match Streamlit's behavior; ties resolve by whatever order JS's stable `Array.prototype.sort` happens to produce, which on tied input is the input row order). Tied scores in real CSVs are rare since `likeRate` and `saveRate` are real-valued floats.
  - `renderTable(rows, headers) → HTMLTableElement` — build a `<table>` with `<thead>` and `<tbody>` via `document.createElement` + `textContent` (never `innerHTML` for row data — XSS-safe by default).
  - `extractTrackURIs(rows) → string | null` — newline-joined URIs, or `null` if no `track_uri` header. Direct port of [app.py:5-9](../../app.py:5).
  - `formatCSV(rows, headers) → string` — build the CSV string for the Download button. Quote any field containing comma, double-quote, or newline; escape inner quotes by doubling.
  - **DOM glue (inline at the bottom of the file, no factory wrappers):** attach a `change` listener on `#fileInput`. On change: clear `#output`, read the file via `FileReader.readAsText`, run `parseCSV → optimizePlaylist → renderTable`, append the resulting table to `#output`. Then build the Copy and Download buttons inline (each is ~10-15 lines: `document.createElement('button')`, `textContent`, attach `click` listener with the clipboard / blob-download logic, append to `#output`). The Copy button's `click` handler calls `navigator.clipboard.writeText(uris)`; success flips label to "Copied" for 2s; failure flips to "Copy failed - try again" for 3s (mirroring [app.py:101-119](../../app.py:101)). The Download button's handler builds a `Blob([formatCSV(rows, headers)], {type: 'text/csv'})`, creates an object URL via `URL.createObjectURL`, simulates click on a temporary `<a download="optimized_playlist.csv">`, then revokes the URL. If `extractTrackURIs(rows)` returns `null` (no `track_uri` column), skip the Copy button entirely and append a warning paragraph instead.
- **R6 specifically:** when `extractTrackURIs` returns `null`, hide (do not render) the Copy button and render the warning. Mirrors [app.py:135-137](../../app.py:135).
- **Interaction states — explicit enumeration so the implementer doesn't invent these:**
  - *Pre-upload (initial load):* `<input type="file">` is visible, `<h1>` and any short instructional sub-line are visible, `#output` is empty (no placeholder, no spinner — silent void is acceptable for v1, matches the "no visual redesign" scope boundary). No Copy/Download buttons rendered yet.
  - *Loading (file selected, parse in progress):* For typical playlist CSVs (<1 MB), `FileReader.readAsText` + `parseCSV` + render is essentially instant; no explicit loading indicator is needed. If a real CSV produces a perceptible delay (>250 ms), add a transient `<p>Loading…</p>` inside `#output` before the table replaces it. Treat this as a v1.1 polish, not v1 work.
  - *Parse-success:* `#output` contains, in order: an `<h2>Optimized Playlist:</h2>` heading, the rendered `<table>`, the Copy button (only if `track_uri` column is present), the Download button. The previous `#output` content is fully cleared before this render — no stale tables.
  - *Parse-error:* if `parseCSV` throws or returns 0 rows, `#output` contains a single `<p class="error">Could not parse this CSV: <reason></p>` element. NO table, NO Copy button, NO Download button. The file picker remains usable for retry. Reason strings are short ("missing header row", "no rows found", "malformed line at row N"); a generic catch-all "could not parse this CSV" is acceptable when the parser can't pinpoint a row.
  - *Missing-`track_uri` column (R6):* `#output` contains the heading, the rendered table, the warning paragraph, and the Download button. No Copy button is rendered (per R6). This is a successful parse; just one feature is unavailable.

**Patterns to follow:**
- [`app.py:11-39`](../../app.py:11) — algorithmic source of truth. The JS port should preserve operation order exactly (clamp before division, percentage after score, column reorder before sort).
- [`app.py:53-119`](../../app.py:53) — Copy button styling and label-flip UX. Lift the SVG icon and the 2s/3s timeout values verbatim.
- [`podcast-dashboard/index.html`](../../../podcast-dashboard/index.html) — CSP shape (`default-src 'self'`).

**Test scenarios:** *(All scenarios are manual browser verification per K.T.D. — open `index.html` directly via `file://` in Chrome/Firefox/Safari for local checks before deploying.)*
- Manual verification (Happy path): Upload a CSV with one row `likeRate=0.4, saveRate=0.2, skipRate=0.1, track_uri=spotify:track:abc` → table shows `track_score = 6.0`, `track_score_percentage = 600.00%`, columns ordered `[..., track_uri, track_score_percentage, ...]`.
- Manual verification (Happy path): Upload a CSV with three rows of varying scores → rows displayed in `track_score` descending order.
- Manual verification (Edge case): Upload a CSV row with `skipRate=0` → score uses clamped `0.01`; no `Infinity` or `NaN` in the rendered cell.
- Manual verification (Edge case): Upload a CSV row with `skipRate=2` → clamped to `1.0`; score equals `discoveryRate / 1.0`.
- Manual verification (Edge case): Upload a CSV row with `likeRate="not-a-number"` → coerced to `0` (parity with `pd.to_numeric(..., errors='coerce').fillna(0)`).
- Manual verification (Edge case — R6): Upload a CSV without a `track_uri` column → Copy button is NOT in the DOM; warning text "No 'track_uri' column found..." is visible.
- Manual verification (Happy path — R4): Click "Copy All Track URIs" with a valid CSV loaded → button text flips to "Copied" for ~2s, then back to "Copy All Track URIs"; clipboard contains newline-joined URIs in displayed order.
- Manual verification (Error path — R4): Click "Copy All Track URIs" in a context where Clipboard API rejects (e.g., open `index.html` from `file://` in some browsers) → button text flips to "Copy failed - try again" for ~3s, then back; error logged to console.
- Manual verification (Happy path — R5): Click "Download Optimized Playlist" → browser downloads `optimized_playlist.csv` whose content equals the rendered table (same columns, same row order, same values).
- Manual verification (Edge case — CSV parsing): Upload a CSV with a quoted field containing a comma (e.g., `track_name = "Hello, World"`) → field is parsed as a single column, not split.
- Manual verification (Edge case — CSV parsing): Upload a CSV with a quoted field containing escaped quotes (`"she said ""hi"""`) → unescaped to `she said "hi"`.

**Verification:**
- Loading `index.html` directly from disk in a modern browser produces a working file picker.
- All test scenarios above pass without console errors (except the deliberate `file://`-clipboard error case).
- Total code under ~250 lines across all three files (sanity check on R15's "no toolchain" spirit).

---

- U3. **Tingle `build-info.yaml` for master + PR review pipelines**

**Goal:** Configure CI/CD so push-to-master deploys to `snow.spotify.net/spa/playlist-sequencer/` and pull requests deploy to `snow.spotify.net/spa/playlist-sequencer-$PR_NUMBER/` with auto-PR-comment. Achieves R8 and R9.

**Requirements:** R7 (deploy target URL pattern), R8, R9.

**Dependencies:** U1, U2.

**Target repo:** `ghe.spotify.net/see-music/playlist-sequencer` (new).

**Files:**
- Create: `build-info.yaml`
- (Conditional fallback) Create: `package.json` — only if pure-static deploy fails on the first Tingle run.

**Approach:**
- Mirror [`podcast-dashboard/build-info.yaml`](../../../podcast-dashboard/build-info.yaml) structurally:
  - `version: 2`
  - `notifications.failure.email: [andresm]` on `refs/heads/master`
  - `pipelines: [Review build, Master build]`
  - Snow image: reuse `gcr.io/spotify-snow/snow:2.6.0_20251020T191414` (the version known-working in podcast-dashboard at planning time; bump only if Tingle reports the image is deprecated).
  - Comment-and-PR action: `gcr.io/action-containers/ghe-pr-comment:1.1.0`.
- **Site name `playlist-sequencer`** (not `see-playlist-sequencer`) — explicit user decision. This applies to both pipelines.
- **Default attempt — pure static, no `npm`:** Keep `--no-build` even though there's nothing to skip. In podcast-dashboard `--no-build` tells `snow` "don't run your own build, just publish what's here." Without it, `snow` may invoke an internal default builder against a static repo and fail in a confusing way (a different failure mode than "no `package.json`"). Two failure modes need different fallbacks; making `--no-build` explicit collapses the distinction.
  - Master pipeline command: `snow --no-build --site-name=playlist-sequencer --yes --verbose` (drop `npm ci && npm run build`, keep `--no-build`).
  - Review pipeline command: `snow --no-build --site-name=playlist-sequencer-$PR_NUMBER --yes --verbose --review`.
- **Fallback path (if first push to a feature branch fails because `snow` requires `package.json` to be present):**
  - Add a 3-line `package.json`:
    ```json
    { "name": "playlist-sequencer", "private": true, "version": "0.1.0", "scripts": { "build": "true" } }
    ```
  - Switch pipeline commands back to the podcast-dashboard chain: `npm ci && npm run build && snow --no-build --site-name=playlist-sequencer{,-$PR_NUMBER} --yes --verbose [--review]`.
  - This is mechanical and adds at most ~5 minutes to the unit. Document in a comment in `build-info.yaml` why the trivial `package.json` exists (so a future maintainer doesn't try to "clean it up").
- Initial validation happens on a feature branch with an open PR (i.e., the first push exercises the **Review build** pipeline, which is safer because it deploys to a per-PR URL, not the production URL).

**Patterns to follow:**
- [`podcast-dashboard/build-info.yaml`](../../../podcast-dashboard/build-info.yaml) — copy structure verbatim, change only the site name, the deploy command (per fallback decision), and the email recipient. Keep the `Available for review at: ...` echo + `ghe_pr_comment.md` redirection — this is what produces the auto-PR-comment per R9.

**Test scenarios:**
- Verification (R9 — PR review pipeline): Push U2 changes on a feature branch, open a PR. Tingle's "Review build" pipeline runs to green; an auto-comment appears on the PR with `https://snow.spotify.net/spa/playlist-sequencer-$PR_NUMBER`. Following that URL on VPN renders the working app.
- Verification (R8 — master pipeline): Merge the PR. Tingle's "Master build" pipeline runs to green. `https://snow.spotify.net/spa/playlist-sequencer/` renders the working app on VPN.
- Verification (Failure-mode handling): If the first feature-branch push fails with an error mentioning `package.json` or `npm`, apply the fallback (add `package.json`, update `build-info.yaml` commands), re-push. Confirm the next pipeline run goes green.
- Verification (Email failure notification): A deliberate broken push (e.g., a malformed `build-info.yaml`) on a feature branch should NOT email; only `master` failures should email per the `notifications` block.

**Verification:**
- Both pipelines run green on Tingle.
- The PR auto-comment lands within ~5 minutes of pushing to a feature branch.
- The deployed app on `snow.spotify.net/spa/playlist-sequencer/` is reachable from VPN and exhibits the U2 behavior.

---

- U4. **Snow deployment activation + end-to-end verification on real CSV (R10 GATE)**

**Goal:** Confirm the new Snow app produces output identical to the current Streamlit app on the same input. This is the **load-bearing gate** that controls whether U5 may proceed: until U4's verification passes, the redirect must not be activated. Achieves R10.

**Requirements:** R7, R10.

**Dependencies:** U3.

**Target repo:** `ghe.spotify.net/see-music/playlist-sequencer` (new) — **verification only**, no code changes here. Uses the artifacts deployed by U3.

**Files:**
- (None modified.) Verification artifacts may be staged in `docs/verification/` of the new GHE repo for traceability — optional.

**Approach:**
- Pick a real playlist CSV the user has previously processed via the current Streamlit app (e.g., a recent export from the Spotify-internal data source they normally feed into the tool). Sensitive data should remain local — do not commit the CSV.
- **Step A — capture Streamlit baseline:** Open the current Streamlit app (`https://playlist-sequencer.streamlit.app/` or wherever it is hosted). Upload the CSV. Click "Download Optimized Playlist". Save the result as `streamlit_output.csv`.
- **Step B — capture Snow output:** Open `https://snow.spotify.net/spa/playlist-sequencer/` on VPN. Upload the same CSV. Click "Download Optimized Playlist". Save the result as `snow_output.csv`.
- **Step C — diff and verify:**
  - Numeric `track_score`: identical to ≥4 decimal places. JS `toFixed(2)` and pandas `.round(2).astype(str)` differ in (a) trailing zeros (`'6.00%'` vs `'6.0%'`) AND (b) banker's rounding (pandas uses half-to-even; JS uses half-away-from-zero) at exact `.x05` boundaries — so always compare the underlying numeric `track_score` column, never the `track_score_percentage` display column. Compare via a quick `awk` / spreadsheet pivot, not a literal `diff`.
  - Sort order: row sequence should match for the vast majority of rows. If tied `track_score` values exist (rare with real-valued like/save/skip rates), the two outputs may diverge on the order of the tied rows, because pandas' default `sort_values` uses unstable quicksort while JS `Array.prototype.sort` is stable. This is acceptable — the divergence is purely on tied scores and does not indicate a bug. If tied rows are not present, the row sequences should match exactly.
  - Column ordering: `track_score_percentage` immediately after `track_uri` in both outputs.
- **Step D — interactive sanity check (Snow only):**
  - **Asset-path resolution check:** visit BOTH `https://snow.spotify.net/spa/playlist-sequencer/` (with trailing slash) AND `https://snow.spotify.net/spa/playlist-sequencer` (no trailing slash). Both should render the working app. With no Vite to rewrite paths to absolute, `app.css` and `app.js` are referenced as relative paths in `index.html`. The trailing-slash form is canonical (browser resolves `app.js` against `/spa/playlist-sequencer/`); the no-slash form depends on Snow's default redirect behavior. If the no-slash URL 404s on the assets, either configure Snow to canonicalize-with-slash or change the asset references in `index.html` to absolute paths (`/spa/playlist-sequencer/app.js`).
  - Click "Copy All Track URIs". Paste into a scratchpad. Confirm count matches sorted row count and first/last URIs match the table.
  - Re-upload a CSV missing the `track_uri` column. Confirm warning text appears and Copy button is hidden (R6).
  - **Off-VPN behavior is informational, not gating.** Snow's exact off-VPN response (timeout, Okta interstitial, 403, or pass-through) is not documented in the plan and varies by Snow site config. Try off-VPN access, observe what happens, and record the response shape — but do NOT block U5 cutover on a particular off-VPN response code. The R10 gate is the on-VPN identical-output check, not the off-VPN response check.

**Patterns to follow:**
- This is a verification-only unit — no patterns to mirror in code. Treat it like a release-checklist unit.

**Test scenarios:**
- Verification (Happy path — R10): Streamlit and Snow outputs on the same CSV produce identical row order and identical numeric `track_score` values to ≥4 decimal places.
- Verification (Edge case): A row with `skipRate=0` produces the same `track_score` value in both outputs (both clamp to 0.01).
- Verification (Edge case): A row with non-numeric `likeRate` produces the same `track_score` value in both outputs (both coerce to 0).
- Verification (R6 sanity): Re-upload missing-`track_uri` CSV → Snow shows warning + hides Copy button.
- Verification (Network/access sanity): Snow URL on VPN → app loads. Off VPN → Snow's internal-only-access response. (Documents that R10's verification is not just "does it run" but "does it run within Spotify's perimeter as expected.")
- Verification (Negative): If any of the above fail, U5 is blocked. Investigate, fix in U2/U3, redeploy, re-verify.

**Verification:**
- A short verification note (in any form — Slack message to self, GitHub PR comment, or `docs/verification/2026-04-28-cutover-gate.md`) records: CSV used (filename, hash), date, browser, Snow build version, and a "PASS" attestation.
- Until this attestation exists, U5 is dependency-blocked.

---

- U5. **Cutover redirect on personal-GitHub Streamlit repo**

**Goal:** Replace the personal-GitHub `app.py` with a minimal Streamlit page that auto-redirects to the new Snow URL within 2-3 seconds. Streamlit Community Cloud auto-redeploys the redirect within ~30 seconds. Achieves R11 and R12.

**Requirements:** R11, R12.

**Dependencies:** **U4 PASSED** (load-bearing gate — see U4's verification attestation).

**Target repo:** `github.com/andres-monge/playlist-sequencer` (existing personal GitHub).

**Files:**
- Modify: `app.py`
- (No changes to `requirements.txt`. Streamlit Cloud still needs `streamlit` to render the page. `pandas` is no longer used by `app.py` but removing it would cause a re-resolution that risks deploy disruption — leave it in v1; cleanup is deferred.)

**Approach:**
- Replace the entire body of `app.py` with a ~15-line Streamlit page that:
  1. Renders a centered "This tool has moved" headline.
  2. Renders a one-line explanation: "Playlist Sequencer is now hosted at `snow.spotify.net/spa/playlist-sequencer/`. Redirecting in 3 seconds…"
  3. Renders a manual link "Click here if you are not redirected automatically" pointing to the Snow URL — fallback for users on browsers that block meta-refresh.
  4. Embeds (via `st.markdown(unsafe_allow_html=True)`) an HTML `<meta http-equiv="refresh" content="3; url=https://snow.spotify.net/spa/playlist-sequencer/">` tag — primary redirect mechanism.
  5. Embeds a fallback `<script>setTimeout(() => window.location = 'https://snow.spotify.net/spa/playlist-sequencer/', 3000)</script>` — belt-and-braces if meta-refresh is blocked.
- Delete `extract_track_uris`, `optimize_playlist`, the file uploader, the dataframe rendering, the Copy button HTML, and the Download button — all redundant.
- Land as a single commit on the default branch the personal-GitHub repo is configured to auto-deploy from (per origin: Streamlit Community Cloud auto-redeploys on push to the connected branch within ~30 seconds).
- Do not delete `requirements.txt`, `.devcontainer/`, or other repo files in this unit. Cleanup is deferred per Scope Boundaries.

**Execution note:** Verify U4 PASSED before pushing this commit. The brainstorm explicitly says "the plan should sequence (1) bootstrap, (2) implementation, (3) deployment + verification, (4) redirect cutover, in that order — never reorder (4) before (3)." Pushing U5 before U4 passes risks redirecting users to a half-broken target.

**Patterns to follow:**
- N/A — this is a deliberate teardown of the existing app.py to a redirect stub. No internal patterns to follow.
- Standard HTML meta-refresh pattern; nothing exotic.

**Test scenarios:**
- Verification (Happy path — R11): After push and ~30 second auto-redeploy, visit the old Streamlit URL. Page loads showing "This tool has moved", then auto-navigates to the Snow URL within ~3 seconds.
- Verification (Edge case — meta-refresh blocked): With browser meta-refresh disabled (Firefox `accessibility.blockautorefresh = true`), the JS `setTimeout` redirect still fires. User reaches the Snow URL.
- Verification (Edge case — both meta-refresh and JS blocked): The visible "Click here if you are not redirected automatically" link is still functional; clicking it navigates to the Snow URL.
- Verification (Source review): View source of the deployed redirect page. Confirm no remnants of the algorithm code, no `pd.read_csv`, no Copy/Download buttons. Only the redirect message and the redirect mechanisms.

**Verification:**
- Within ~5 minutes of push (30s redeploy + buffer), the old Streamlit URL behaves as a redirect stub.
- A user with the old URL bookmarked reaches the working Snow app within ~3 seconds of clicking their bookmark.

---

- U6. **Update old personal-GitHub `README.md` to point at new repo + Snow URL**

**Goal:** Make discovery work: anyone landing on the personal-GitHub repo (e.g., via a stale link from an old Slack thread or browser bookmark) sees the new home prominently. Achieves the second half of R14.

**Requirements:** R14 (legacy README update).

**Dependencies:** U5 (so the README update is consistent with the deployed redirect).

**Target repo:** `github.com/andres-monge/playlist-sequencer` (existing personal GitHub).

**Files:**
- Modify: `README.md`

**Approach:**
- Replace the current 2-line `README.md` ("playlist-sequencer / Sequences tracks in a music playlist") with a short "this repo has moved" notice:
  1. Heading: `# Playlist Sequencer (moved)`.
  2. Paragraph: "This tool has been migrated to a Spotify-internal Snow SPA at [snow.spotify.net/spa/playlist-sequencer](https://snow.spotify.net/spa/playlist-sequencer/) (VPN required). The source now lives on GHE at `ghe.spotify.net/see-music/playlist-sequencer`."
  3. Paragraph: "This repo is preserved as a forwarding stub via Streamlit Community Cloud. Visiting the old Streamlit URL auto-redirects to the new home. Archival of this repo is deferred."
- Land on the same default branch as U5, in a separate commit so the diff is minimal and the cutover redirect commit (U5) stays atomic.

**Patterns to follow:**
- N/A — small documentation update.

**Test scenarios:**
- Verification (Happy path — R14): Old GitHub repo's main page renders the new README. Both the Snow URL and the GHE repo URL are present and correctly formatted as Markdown links.
- Verification (Happy path): The Snow URL link, if clicked from a Spotify-internal browser on VPN, lands on the new app.
- Verification (Edge case): The GHE URL link is plain text or a Markdown code-span (not a clickable link from public GitHub, since `ghe.spotify.net` is internal). This is intentional — clicking from outside Spotify would 404, so leaving it as a code-span avoids a confusing link.

**Verification:**
- Old personal-GitHub repo's main page shows the moved-notice on its first render, with no scroll required.

---

## System-Wide Impact

- **Two repos, two deployments:** The plan touches a new GHE repo (most units) and the existing personal-GitHub repo (U5, U6). The new Snow deployment becomes the primary endpoint; the existing Streamlit Community Cloud deployment is repurposed as a forwarding stub. There is no shared infrastructure between them.
- **Cutover invariant (load-bearing):** U5 must not run before U4's verification passes. This is encoded in U5's Dependencies (`U4 PASSED`). A redirect to a half-broken target is worse than the status quo.
- **Error propagation:** The new SPA handles all errors client-side (CSV parse error → render an error message in `#output`; Clipboard API rejection → label-flip; missing `track_uri` column → warning). No errors propagate to a server, because there is no server. This is an explicit simplification vs the Streamlit version, which served some error rendering through Streamlit's framework chrome.
- **State lifecycle risks:** Each upload fully replaces `#output` (clears prior table, prior buttons, prior warning). No partial-state cache, no `localStorage`, no service worker. The app is stateless across page reloads — closing the tab discards everything.
- **API surface parity:** "API surface" here means the user-facing URL, the CSV input contract, and the CSV output contract. The URL changes (Streamlit Cloud → Snow), but the redirect (U5) preserves bookmark continuity. The CSV input/output contracts are bit-for-bit unchanged for the score; the percentage display string changes from variable-decimal to fixed-2-decimal (see K.T.D.).
- **Integration coverage:** The R10 gate in U4 is the only true cross-system integration check (Streamlit-baseline-output vs Snow-output on the same input). It cannot be replicated by unit tests because it spans two deployments.
- **Unchanged invariants:** The score formula (R2), the column-order rule (R3), the missing-`track_uri` warning (R6), and the personal-GitHub repo's existence (R12) are all explicitly unchanged. The new app's behavior on edge cases (skipRate=0, non-numeric inputs) matches Streamlit's behavior.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Snow's pipeline rejects a no-`package.json` repo | U3 documents the 5-minute fallback (3-line `package.json` with no-op `build` script). Pipeline command pivots to podcast-dashboard's `npm ci && npm run build && snow --no-build` chain. Caught on the first feature-branch push to Tingle's Review build — never on production. |
| Inline CSV parser misses an edge case (most likely: embedded newlines in quoted fields, which the inline parser explicitly does NOT handle per U2) | If real CSVs trigger this, the **preferred fix is vendoring** Papa Parse (commit `papaparse.min.js` next to `app.js`, R15-faithful, no CSP change). CDN-with-SRI is a documented last resort but weakens `script-src` and is a real security delta — see K.T.D. for the full vendoring vs CDN rules. Caught during U4's identical-output check (row count mismatch reveals embedded-newline bugs). |
| Percentage display difference (`6.0%` vs `6.00%`) creates noise during the U4 identical-output check | K.T.D. spells out the difference up-front. U4's verification compares numeric `track_score` to ≥4 decimal places, not the display string. |
| User pushes U5 (redirect) before U4 (verify) passes | U5's Dependencies declares `U4 PASSED` explicitly; the Execution note repeats the warning. The cutover sequence appears in the brainstorm's Next Steps and in this plan's High-Level Technical Design diagram. |
| Streamlit Cloud fails to auto-redeploy after the U5 push (rare but possible — service outage, branch config drift) | U5's verification scenario is "within ~5 minutes of push, the old URL is a redirect stub." If that fails, manually trigger a redeploy from the Streamlit Cloud dashboard. If Streamlit Cloud is fully down, the old URL serves whatever Streamlit Cloud's outage page is — the new Snow URL is unaffected. |
| GHE repo creation lacks the right `see-music` IAM ownership, blocking team access | U1 verifies ownership by mirroring podcast-dashboard's owner via `gh repo view`. If the IAM group differs (e.g., the user's `see-music` access is via a personal-team membership), surface to the user before pushing U2. Worst case adds a 1-day Hive ticket to grant team ownership; tool itself works regardless. |
| Snow image version `2.6.0_20251020T191414` is deprecated by the time the implementer runs U3 | U3 says "bump only if Tingle reports the image is deprecated." Tingle's error message points at the current image tag; this is a 30-second `build-info.yaml` edit. |

---

## Documentation / Operational Notes

- **Memory update on completion:** After U6 lands, update [project_migration_to_snow.md](../../../../.claude/projects/-Users-andresm-Documents-Cursor-Projects-playlist-sequencer/memory/project_migration_to_snow.md) status from "in-flight" to "shipped" and record the live Snow URL.
- **Operational ownership:** Once the new GHE repo is owned by `see-music`, on-call patterns automatically apply (no separate runbook needed for a static tool). The personal-GitHub redirect stub is owner-of-record only.
- **No monitoring required for v1:** Snow handles uptime; the app itself has no server logs to monitor.
- **No cleanup / archival planned.** Per Scope Boundaries and R12, the personal-GitHub repo and Streamlit Cloud deployment stay alive indefinitely. After cutover, the redirect page no longer accepts CSV uploads — it just renders a "this tool has moved" message — so no internal Spotify data flows through the personal-infra path anymore. The remaining personal footprint is inert (a static "moved" page on a free hosting platform); there is no perimeter or data-flow concern that would warrant teardown work. The redirect stub is safe to keep alive without a deadline.

---

## Sources & References

- **Origin document:** [docs/brainstorms/2026-04-28-streamlit-to-snow-migration-requirements.md](../brainstorms/2026-04-28-streamlit-to-snow-migration-requirements.md)
- **Reference repo (canonical Snow SPA pattern):** [`see-music/podcast-dashboard`](../../../podcast-dashboard) — local sibling clone; live at `snow.spotify.net/spa/see-podcast-dashboard/`.
- **Current app source:** [app.py](../../app.py) — algorithmic source of truth; lines 11-39 (algorithm) and 53-119 (Copy button HTML+JS) port directly into U2.
- **Memory: Snow SPA pattern reference:** [reference_podcast_dashboard_snow_pattern.md](../../../../.claude/projects/-Users-andresm-Documents-Cursor-Projects-playlist-sequencer/memory/reference_podcast_dashboard_snow_pattern.md)
- **Memory: migration project state:** [project_migration_to_snow.md](../../../../.claude/projects/-Users-andresm-Documents-Cursor-Projects-playlist-sequencer/memory/project_migration_to_snow.md)
- **Memory: Spotify-Streamlit aversion rationale:** [feedback_avoid_streamlit_at_spotify.md](../../../../.claude/projects/-Users-andresm-Documents-Cursor-Projects-playlist-sequencer/memory/feedback_avoid_streamlit_at_spotify.md)
