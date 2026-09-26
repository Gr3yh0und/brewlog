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

## Deploy on the server: `/deploy`

On the home-lab server, deploy with the shared `/deploy` skill (`WEBAPP_PROJECT_STANDARD.md` §9).
It runs the tests, bumps `VERSION`, updates `CHANGELOG.md`, tags and pushes, runs
`deploy/build.sh` (export + assemble `dist/`), then publishes:

```bash
/deploy local     # WWW_ROOT/brewlog/releases/<VERSION>/, flips `current`
/deploy public    # FTP, via PUBLIC_PUBLISH_CMD="bash deploy/deploy.sh public"
/deploy           # both targets (deploy.config: TARGETS="local public")
```

Needs a gitignored `deploy.config` — copy `deploy.config.example`. Secrets are read from
`/etc/homelab/brewlog.env` when readable, else the repo `.env` (`BREWLOG_ENV` overrides both).
Only `deploy.sh` knows this order; `deploy.ps1` always reads `.env`.

## Deploy Commands (direct)

One-time setup: copy `.env.example` → `.env` and fill in all values (see [Configuration](CONFIGURATION.md)).

Two targets (WEBAPP_PROJECT_STANDARD.md §13B): **`public`** (FTP, the load-bearing one — printed
bottle QR codes point at it) and **`local`** (WWW_ROOT/brewlog, served by the proxy — server-side
only, since it writes directly to a local filesystem path). Target defaults to `public` if omitted,
matching this repo's original FTP-only behavior; pass `local` or `both` explicitly.

**Windows (PowerShell):**
```powershell
deploy/deploy.ps1                    # public: export + upload everything
deploy/deploy.ps1 -Target both       # public + local, same build
deploy/deploy.ps1 -Labels            # same + generate and upload labels/ (public only)
deploy/deploy.ps1 -SkipData          # upload index.html + favicon + i18n/ + logo/ only
deploy/deploy.ps1 -SkipData -Labels  # frontend + labels only
```

**Mac/Linux (bash):**
```bash
bash deploy/deploy.sh                    # public: export + upload everything
bash deploy/deploy.sh both               # public + local, same build
bash deploy/deploy.sh local              # local only — publishes to WWW_ROOT/brewlog
bash deploy/deploy.sh --labels           # same + generate and upload labels/ (public only)
bash deploy/deploy.sh --skip-data        # upload index.html + favicon + i18n/ + logo/ only
bash deploy/deploy.sh --skip-data --labels
```

Each file upload retries up to 3 times (3 s pause between attempts) before the script aborts. To retry just the labels after a partial failure: add `-SkipData -Labels` / `--skip-data --labels`.

## Rollback

The two targets use different rollback mechanisms, so `--rollback`/`-Rollback` needs a single target
— not `both` — to know which one to reverse.

**`public`**: every deploy snapshots the exact bytes it's about to upload (`web/index.html`, `favicon.svg`, `logo/`, `i18n/`, `data/`, `images/` — not `labels/`, which is a separate printable artifact) to `deploy/releases/` before uploading, and keeps the last 5. Rollback re-uploads an earlier snapshot verbatim — no re-export, no rebuild, so it still works even if the KBH2 database has since changed in a way that would make a fresh export different from what was actually live.

```powershell
deploy/deploy.ps1 -Rollback              # re-publish the release before the current one
deploy/deploy.ps1 -Rollback -RollbackN 2 # go back 2 releases instead of 1
```

```bash
bash deploy/deploy.sh --rollback         # re-publish the release before the current one
bash deploy/deploy.sh --rollback=2       # go back 2 releases instead of 1
```

`python3 deploy/rollback.py list` shows what's saved locally, newest first (`[0]` is what's live now, assuming nothing was published outside these scripts). The public URL is load-bearing (printed bottle QR codes point at it — see [main README](../README.md)), so a bad publish is worth rolling back rather than leaving live while you investigate.

**`local`**: no snapshot needed — every published version already lives under
`WWW_ROOT/brewlog/releases/<VERSION>/` (WEBAPP_PROJECT_STANDARD.md §14B). Rollback just flips the
`current` symlink back; instant, no re-copy.

```powershell
deploy/deploy.ps1 -Target local -Rollback              # flip back one release
deploy/deploy.ps1 -Target local -Rollback -RollbackN 2 # flip back two releases
```

```bash
bash deploy/deploy.sh local --rollback     # flip back one release
bash deploy/deploy.sh local --rollback=2   # flip back two releases
```

`python3 deploy/rollback.py list-local` shows what's saved under `WWW_ROOT/brewlog/releases`, newest version first, with `(live)` marking whatever `current` points at.

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