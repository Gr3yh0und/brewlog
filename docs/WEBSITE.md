# Website Features

## List view
- Beers grouped by brew year; recipes (no brew date) shown first
- Status filter tabs (All / Recipe / Brewed / Bottled / Finished) with counts
- Style filter bar with colored chips (color derived from style name, persists per style)
- Compact header KPIs: total brews, total litres brewed, avg. brewhouse efficiency, favourite style
- 8-language flag-picker dropdown; language persists in `localStorage`
- Light/dark mode toggle; defaults to system preference, persists in `localStorage`

## Cards
- EBC color bar on the left edge
- Brew number badge (pill) + beer name (leading `#N` stripped)
- Style chip (colored) + status badge
- Date line: shows "Brewed" for brewed beers, "Created" for status-0 recipes
- Key stats: OG, IBU, EBC, volume, fermentation time, ABV
- Radar chart thumbnail (two separate shapes — see below)

## Detail view
- Sticky header with back button and beer name (no brew number prefix)
- Hero section: brew number pill, status badge, style chip, key stats grid (OG, ABV, IBU, EBC), secondary row (volume, boil time, CO₂, brewhouse efficiency), visual timeline (Brewed → Fermentation → Bottled → Conditioning → Today)
- Download buttons at top (BeerJSON, SVG label, A4 label) — color-coded, colored in dark mode too
- Radar chart (full size, 220px, with labeled axes)
- Grain bill, hops, yeast, misc ingredients
- Mash plan: SVG step-profile diagram (proportional to duration, min. 8 % width per step) above a step list with icons (🌾 mash-in, ⏱️ rests, 🌡️ mash-out)
- Hop totals show g/L, split into brewing hops vs. dry hops when both are present
- **Brew Day** chart (if InfluxDB data available): SVG time-series of kettle and ambient temperature over the brew session; one colored line per sensor
- **Fermentation** charts (if InfluxDB data available): gravity (°P) and temperature (°C) over the fermentation window; one line per iSpindel source; hidden for brews without process data
- Notes, tasting ratings
- Photo gallery (thumbnail grid + lightbox, keyboard ← / → / Esc) — only shown when images exist

## Direct links
Every beer has a shareable URL: `{SITE_URL}?beer={sudnummer}`.  
Opening that URL navigates directly to the detail view. The QR code on each label points to this URL.  
The browser back button works correctly (URL updates on open/close via `history.pushState`).

## Radar chart
The radar has 8 axes rendered as smooth Catmull-Rom closed splines.  
Two **separate, non-overlapping** shapes are drawn:

1. **Taste profile** (solid fill, axes 0–4) — Bitterkeit, Frucht, Milde, Erde, Würze; zeros on physical axes
2. **Physical measurements** (dashed fill, axes 5–7) — Stammwürze, Alkohol, Farbe computed from OG/ABV/EBC; zeros on taste axes

Colors are derived from the beer's EBC hex color via D3-compatible Lab interpolation (`beer.darker(5)` → `beer.brighter(3)`), matching `generate_labels.py` exactly. Colored dots mark each axis point in the detail view.