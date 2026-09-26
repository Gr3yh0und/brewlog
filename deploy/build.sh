#!/usr/bin/env bash
# build.sh – export data and assemble dist/, the exact tree the `local` and
# `public` targets serve (same file set as deploy/rollback.py _release_files():
# no .py files, no labels/). Used as BUILD_CMD by the shared /deploy script.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 web/export.py

rm -rf dist
mkdir dist
cp web/index.html web/favicon.svg dist/
for sub in logo i18n data images; do
    [[ -d "web/$sub" ]] && cp -r "web/$sub" "dist/$sub"
done
# Homepage widget status (WEBAPP_PROJECT_STANDARD.md §6a). last_update is the
# newest mtime under input/ (KBH2 database, enrichment, images, InfluxDB dumps):
# when the brew data last changed, not when this build ran.
python3 - <<'PY'
import json, pathlib, datetime
files = [p for p in pathlib.Path('input').rglob('*') if p.is_file()]
newest = max((p.stat().st_mtime for p in files), default=None)
last = (datetime.datetime.fromtimestamp(newest, datetime.timezone.utc)
        .strftime('%Y-%m-%dT%H:%M:%SZ') if newest else None)
health = {'version': pathlib.Path('VERSION').read_text().strip(),
          'status': 'ok' if last else 'unknown',
          'last_update': last, 'extra': {}}
pathlib.Path('dist/health.json').write_text(json.dumps(health) + '\n')
PY

echo "dist/ ready: $(find dist -type f | wc -l) files"
