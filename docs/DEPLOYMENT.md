# Deployment & Workflow

## Workflow

```
Brew in KBH2
    ↓
Edit enrichment/{n}.json          # taste profile, Untappd ID, label color
    ↓
deploy/deploy.ps1                 # Windows: runs export.py, uploads everything
deploy/deploy.sh                  # Mac/Linux equivalent
```

Labels are generated and uploaded separately (takes longer):

```powershell
python web/generate_labels.py     # generate SVG labels
deploy/deploy.ps1 -Labels         # export + upload everything including labels/
```

For frontend-only changes (HTML/CSS/i18n, no data changes):

```powershell
deploy/deploy.ps1 -SkipData       # skip export.py and data/ upload
deploy/deploy.ps1 -SkipData -Labels
```

## Deploy Commands

One-time setup: copy `.env.example` → `.env` and fill in all values (see [Configuration](CONFIGURATION.md)).

**Windows (PowerShell):**
```powershell
deploy/deploy.ps1                    # export + upload everything
deploy/deploy.ps1 -Labels            # same + generate and upload labels/
deploy/deploy.ps1 -SkipData          # upload index.html + favicon + i18n/ + logo/ only
deploy/deploy.ps1 -SkipData -Labels  # frontend + labels only
```

**Mac/Linux (bash):**
```bash
bash deploy/deploy.sh                    # export + upload everything
bash deploy/deploy.sh --labels           # same + generate and upload labels/
bash deploy/deploy.sh --skip-data        # upload index.html + favicon + i18n/ + logo/ only
bash deploy/deploy.sh --skip-data --labels
```

Each file upload retries up to 3 times (3 s pause between attempts) before the script aborts. To retry just the labels after a partial failure: add `-SkipData -Labels` / `--skip-data --labels`.

## Local Development

```powershell
pip install -r requirements.txt  # optional, one-time
cd web
python export.py             # generates web/data/
python -m http.server 8080   # local HTTP server
# → http://localhost:8080
```

> `index.html` uses `fetch()` — opening as `file://` does not work.

## Label Generator

```powershell
cd web
pip install qrcode            # one-time – for real QR codes
python generate_labels.py          # all brews
python generate_labels.py 31 45    # specific brews
```

Output: `web/labels/{n}_label.svg` and `{n}_a4.svg` (9 labels on DIN A4).  
**Printing:** Print the A4 SVG at actual size — no "fit to page". Each label = 210mm × 33mm.

### Label layout

```
[EBC stripe] [QR codes + date] [radar chart] [name / style / stats] [logo] [EBC stripe]
```

- **Background:** parchment centre (`#F5F1EB`) with EBC beer-color stripes on the left and right ends
- **Left area:** two QR codes side by side (beer detail page + Untappd); bottling date centred below
- **Centre:** radar chart (8-axis Catmull-Rom spline, two series — taste profile + physical measurements)
- **Right area:** beer name (bold small-caps, dynamic font size), style (EBC color), combined `ABV · IBU · EBC` stat line, bottling date; brewery logo to the right of the text, fully within the parchment area
- **Logo:** opaque, sized to label height, vertically centred with a small downward offset to account for visual weight

The label color (`label_color` in enrichment JSON) is no longer used for the background — the EBC color derived from the actual measured beer color drives the stripe color automatically, so labels self-color to the beer they represent.