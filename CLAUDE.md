# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal, mobile-first web app that presents a family road trip through the US Northeast
(10/9/26 – 1/10/26) as a day-by-day itinerary paired with an interactive map. The whole app —
markup, styles, data, and logic — currently lives in [index.html](index.html).

The trip is 22 days: days 1–17 are the driving route (NYC → Mystic → Newport → Cape Cod → Boston →
Maine/Acadia → White Mountains → Vermont → Albany → Manhattan), and days 18–22 are the closing stay
in Manhattan — car returned 27/9, flight home 1/10.

`Hotels.pdf` and `Trip Plan - Daily.pdf` are the source material the itinerary was transcribed from;
they are reference documents, not build inputs.

**Keep it simple.** This is a family trip app, not a product. Prefer the smallest change that works
over the general solution, and add features one at a time rather than building frameworks for them.

## Direction

Goal: land a few small features, then publish to GitHub Pages or Vercel (host not yet chosen — both
are static and HTTPS-only, so nothing should depend on which one wins).

Decisions already made, in rough order of when they matter:

1. **Days 18–22 are missing from `itineraryData`.** The array stops at day 17 (26/9/26). The closing
   Manhattan days need to be added from the source PDFs. This is a data-only change.
2. **Map tiles must move to `https://`** before publishing. Keep Google's `{s}.google.com/vt`
   endpoint and both layers (street + satellite) — just change the scheme. It's an undocumented
   endpoint that could break without notice; that risk is accepted for a private family app.
3. **The app must work offline.** It does not today — Tailwind, Leaflet, Font Awesome, and the Heebo
   font all load from CDNs, so no signal means a blank page. Roaming abroad makes this a real
   requirement, not a nicety. Delivering it means vendoring those dependencies into the repo and
   adding a service worker plus a web app manifest.

   **This retires the single-file constraint.** Do not treat "everything in one HTML file" as a rule
   to defend once this work starts; the app becomes a small handful of files (HTML, vendored assets,
   `sw.js`, `manifest.json`). Until then, keep new work inside `index.html`. Note that map
   tiles will still not be available offline without a separate caching strategy — worth flagging
   rather than silently half-solving.

Not a repository yet: there is no git history here. GitHub Pages will need `git init` and an initial
commit; check with the user before creating one.

## Running

There is no build step, package manager, test suite, or linter, but the app must be **served** —
`file://` no longer works. Run `python -m http.server 8000` in this directory and open
`http://localhost:8000/index.html`. The sign-in gate needs a real origin (Google Identity
Services rejects `file://`, and the allowlist is fetched over HTTP), as does the geolocation
"my location" control, and a service worker will too once that lands.

## Deploying

Host is **Vercel**, deploying from a private GitHub repo. No build step — Vercel serves the repo
root as static files, so `index.html` is the site root.

**Anything committed is fetchable at the public URL**, private repo or not. `.gitignore` therefore
excludes the source documents (`Hotels.pdf`, `Trip Plan - Daily.pdf`, `trip.txt`, `hotels.txt`) and
`users.plain.txt`. Check `git status --porcelain` before committing anything new.

**Changing who can sign in:** edit `users.plain.txt` (real addresses, one per line, never committed),
run `python hash-users.py` to regenerate `users.txt` (SHA-256 hashes, committed and deployed), then
commit and push. The normalisation in that script — strip, lowercase — must match `isAllowed()` in
`index.html`, or a valid account gets rejected. A plain address left in `users.txt` still works.

**Every origin needs registering** as an Authorized JavaScript origin on the OAuth client in Google
Cloud Console: `http://localhost:8000` for local work, plus the Vercel production URL. Google treats
`localhost` and `127.0.0.1` as different origins. Preview deployments get their own random URLs,
which will *not* be registered — sign-in only works on production and localhost.

Vercel's free Hobby plan cannot password-protect a production URL (that needs Pro/Enterprise), so
the Google gate is the only access control. `CLAUDE.md` is served at `/CLAUDE.md`; it reveals
nothing that reading `index.html` would not.

## Architecture

**`itineraryData` ([index.html:523](index.html#L523)) is the single source of truth.**
It is an array of day objects; everything visible is derived from it. Adding or editing a trip day
means editing this array and nothing else.

```js
{ dayId, date, dayName, title, driveTime, driveDistance,
  weather: { max, min, desc, aqi, icon, color },
  stops: [ { title, desc, lat, lng } ] }
```

`dayId` is displayed in the carousel; `currentDayIndex` is the array position. They happen to line up
today (`dayId === index + 1`) — don't rely on that when adding days.

**Rendering is a single full re-render.** `updateUI()` ([index.html:935](index.html#L935))
is the only render path: it repaints the carousel button states, header stats, weather, rebuilds
the whole timeline via `innerHTML`, clears and re-adds every Leaflet marker, then calls
`fitMapToCurrentDay()`. `currentDayIndex` is the only real state. Any new feature that changes what
is displayed should funnel through `updateUI()` rather than patching the DOM directly — that is the
main thing keeping this app simple, so preserve it.

**Two views, one container.** `switchView('list' | 'map')` toggles `hidden` on the two absolutely
positioned panes. The map pane is hidden at startup, so Leaflet renders into a zero-size container —
`switchView` compensates with `map.invalidateSize()` inside a 50 ms `setTimeout`. Keep that call if
you touch view switching. `focusOnMap()` passes `autoFit = false` so flying to one stop isn't
immediately overridden by a bounds fit.

**Boot order matters:** `DOMContentLoaded` → `initAuth()` → (once an allowlisted account is signed
in) `startApp()` → `initMap()`, which creates `markersGroup` before calling `buildDaysCarousel()`
and `updateUI()`. `updateUI()` dereferences `markersGroup`, so it cannot run before the map exists.
Nothing map-related may move ahead of `startApp()`: until then `.app-container` carries `hidden`,
and Leaflet would initialize into a display-none element.

**The sign-in gate** (top of the script block) hides the app behind a Google account chooser and an
allowlist read from `users.txt` at runtime. It is a lock, not a wall — client-side only, and
`users.txt` is publicly readable once deployed; that is accepted. `GOOGLE_CLIENT_ID` must be set for
it to work, and every origin the app is served from must be an authorized JavaScript origin on that
OAuth client. A successful sign-in is stored in `localStorage['tm_auth']` so later launches work
offline; when `users.txt` can't be fetched, a stored session is trusted rather than locking the
user out. The gate is styled with plain CSS, not Tailwind, so it survives a cold or offline CDN.

**Markers are stashed on the data.** `updateUI()` assigns `stop._marker` on each stop object so
`focusOnMap()` can open a popup by index. These references are stale after every re-render — never
cache them elsewhere.

## Conventions and constraints

- **RTL Hebrew UI** (`<html lang="he" dir="rtl">`). All user-facing strings are Hebrew — new ones
  should be too. Direction is mirrored: "previous day" uses `fa-chevron-right` and "next" uses
  `fa-chevron-left` — correct in RTL, do not "fix" it. Leaflet popups escape the document direction,
  so each popup body carries an inline `direction:rtl; text-align:right;` wrapper.
- **Tailwind classes are interpolated at runtime**: `bg-${day.weather.color}-100` in `updateUI()`.
  This works only because the Play CDN generates classes from live DOM. New `weather.color` values
  must be real Tailwind palette names. Vendoring Tailwind for offline support will break these
  unless the classes are safelisted or written out literally — handle it when that work happens.
- **Stop `title`/`desc` are injected unescaped** into timeline `innerHTML` and marker popups. The
  data is hand-authored, so keep it free of raw HTML and stray quotes rather than adding escaping
  for content you control.
- **Mobile-first, fixed viewport**: `body { overflow: hidden }`, `100dvh` app shell, no user zoom,
  `env(safe-area-inset-bottom)` on the bottom tab bar. Layout assumes a phone-sized portrait screen;
  new UI should stay inside the flex column (`shrink-0` chrome, `flex-1` content). This is the
  screen the app will actually be used on — check changes at phone width, not desktop.
- Handlers are global functions wired through inline `onclick` attributes. Follow that pattern for
  new controls instead of introducing a listener-registration layer.
