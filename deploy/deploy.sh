#!/usr/bin/env bash
# deploy.sh – KBH2 Web Frontend → FTP upload (Mac/Linux / bash)
# Requires: .env in the project root (see .env.example), curl, python3
# Optional flags:
#   --labels     → also run generate_labels.py and upload web/labels/
#   --skip-data  → skip export.py and skip uploading web/data/ and web/images/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WEB_DIR="$ROOT/web"
ENV_FILE="$ROOT/.env"

LABELS=false
SKIP_DATA=false
for arg in "$@"; do
    case "$arg" in
        --labels)    LABELS=true ;;
        --skip-data) SKIP_DATA=true ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: No .env found: $ENV_FILE" >&2
    echo "Please copy .env.example to .env and fill in credentials." >&2
    exit 1
fi

while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# || -z "${line// /}" ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
        declare "${BASH_REMATCH[1]}=${BASH_REMATCH[2]}"
    fi
done < "$ENV_FILE"

urlencode() {
    python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$1"
}

send_file() {
    local local_path="$1" remote_url="$2"
    for try in 1 2 3; do
        curl -s -T "$local_path" "$remote_url" --user "${FTP_USER}:${FTP_PASS}" --ftp-create-dirs \
            && return
        if (( try < 3 )); then sleep 3; fi
    done
    echo "Error: Upload failed after 3 attempts: $remote_url" >&2
    exit 1
}

# 1. Export data (skipped with --skip-data)
if $SKIP_DATA; then
    echo "==> Skipping data export (--skip-data)"
else
    echo "==> Exporting BeerJSON data..."
    python3 "$WEB_DIR/export.py"
fi

# 2. Generate labels (only with --labels)
if $LABELS; then
    echo "==> Generating SVG labels..."
    python3 "$WEB_DIR/generate_labels.py"
fi

echo "==> Uploading to ftp://${FTP_HOST}${FTP_DIR}/ ..."

# 3. Upload index.html
echo "  index.html"
send_file "$WEB_DIR/index.html" "ftp://${FTP_HOST}${FTP_DIR}/index.html"

# 4. Upload favicon.svg
echo "  favicon.svg"
send_file "$WEB_DIR/favicon.svg" "ftp://${FTP_HOST}${FTP_DIR}/favicon.svg"

# 5. Upload logo/
echo "  logo/..."
LOGO_ENCODED="$(urlencode "$LOGO_PNG")"
send_file "$WEB_DIR/logo/$LOGO_PNG" "ftp://${FTP_HOST}${FTP_DIR}/logo/$LOGO_ENCODED"

# 6. Upload i18n/
I18N_FILES=("$WEB_DIR/i18n"/*.json)
echo "  i18n/ (${#I18N_FILES[@]} files)..."
for f in "${I18N_FILES[@]}"; do
    send_file "$f" "ftp://${FTP_HOST}${FTP_DIR}/i18n/$(basename "$f")"
done

# 7. Upload data/ (skipped with --skip-data)
if $SKIP_DATA; then
    echo "  data/ skipped (--skip-data)"
else
    DATA_FILES=("$WEB_DIR/data"/*.json)
    echo "  data/ (${#DATA_FILES[@]} files)..."
    for f in "${DATA_FILES[@]}"; do
        send_file "$f" "ftp://${FTP_HOST}${FTP_DIR}/data/$(basename "$f")"
    done
fi

# 8. Upload images/ (skipped with --skip-data)
if $SKIP_DATA; then
    echo "  images/ skipped (--skip-data)"
elif [[ -d "$WEB_DIR/images" ]]; then
    IMAGE_FILES=("$WEB_DIR/images"/*)
    echo "  images/ (${#IMAGE_FILES[@]} files)..."
    for f in "${IMAGE_FILES[@]}"; do
        ENCODED="$(urlencode "$(basename "$f")")"
        send_file "$f" "ftp://${FTP_HOST}${FTP_DIR}/images/$ENCODED"
    done
else
    echo "  images/ not found, skipping"
fi

# 9. Upload labels/ (only with --labels)
if $LABELS; then
    if [[ -d "$WEB_DIR/labels" ]]; then
        LABEL_FILES=("$WEB_DIR/labels"/*.svg)
        echo "  labels/ (${#LABEL_FILES[@]} files)..."
        for f in "${LABEL_FILES[@]}"; do
            send_file "$f" "ftp://${FTP_HOST}${FTP_DIR}/labels/$(basename "$f")"
        done
    fi
else
    echo "  labels/ skipped (no --labels flag)"
fi

echo ""
echo "Deploy complete: ${SITE_URL}"
