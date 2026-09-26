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
echo "dist/ ready: $(find dist -type f | wc -l) files"
