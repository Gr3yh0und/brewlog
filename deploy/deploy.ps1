# deploy.ps1 – KBH2 Web Frontend → local + FTP publish (Windows / PowerShell)
# Requires: .env in the project root (see .env.example)
# Usage: deploy.ps1 [-Target local|public|both] [other params]
#   -Target defaults to "public" (unchanged historical behavior — FTP only).
#   "local" publishes to WWW_ROOT/brewlog/releases/<VERSION>/ and flips the
#   `current` symlink (WEBAPP_PROJECT_STANDARD.md §14B) — WWW_ROOT defaults to
#   the server's /samba/server/www; override via a WWW_ROOT entry in .env if
#   this machine reaches that tree through a different (e.g. mapped-drive) path.
# Optional parameters:
#   -Labels       → also run generate_labels.py and upload web/labels/
#                   (public target only — local never serves labels/)
#   -SkipData     → skip export.py and skip uploading web/data/ and web/images/
#   -Rollback [N] → roll back N releases (default 1) instead of publishing.
#                   public: re-upload a previously snapshotted release
#                   verbatim, no export/upload. local: flip `current` back, no
#                   re-copy. -Target both isn't valid with -Rollback — the two
#                   targets don't share a release history, so pick one.
param(
    [ValidateSet('local', 'public', 'both')][string]$Target = 'public',
    [switch]$Labels, [switch]$SkipData, [switch]$Rollback, [int]$RollbackN = 1
)

if ($Rollback -and $Target -eq 'both') {
    Write-Error "-Rollback needs a single target (local or public), not 'both' — the two targets don't share a release history."
    exit 1
}

$RootDir = "$PSScriptRoot\.."
$EnvFile = "$RootDir\.env"
if (-not (Test-Path $EnvFile)) {
    Write-Error "No .env found: $EnvFile`nPlease copy .env.example to .env and fill in credentials."
    exit 1
}

Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#=\s]+)\s*=\s*(.*)\s*$') {
        Set-Variable -Name $Matches[1] -Value $Matches[2] -Scope Script
    }
}

if ($Rollback) {
    if ($Target -eq 'local') {
        Write-Host "==> Rolling back local release $RollbackN step(s)..."
        python "$RootDir\deploy\rollback.py" rollback-local $RollbackN
    } else {
        Write-Host "==> Rolling back $RollbackN release(s)..."
        python "$RootDir\deploy\rollback.py" rollback $RollbackN
    }
    exit $LASTEXITCODE
}

$WebDir = "$PSScriptRoot\..\web"

function Send-File($Local, $Remote) {
    for ($try = 1; $try -le 3; $try++) {
        curl -s -T $Local $Remote --user "${FTP_USER}:${FTP_PASS}" --ftp-create-dirs
        if ($LASTEXITCODE -eq 0) { return }
        if ($try -lt 3) { Start-Sleep -Seconds 3 }
    }
    Write-Error "Upload failed after 3 attempts: $Remote"
    exit 1
}

# 1. Export data (skipped with -SkipData)
if ($SkipData) {
    Write-Host "==> Skipping data export (-SkipData)"
} else {
    Write-Host "==> Exporting BeerJSON data..."
    python "$WebDir\export.py"
    if ($LASTEXITCODE -ne 0) { Write-Error "export.py failed."; exit 1 }
}

# 2. Generate labels (only with -Labels flag)
if ($Labels) {
    Write-Host "==> Generating SVG labels..."
    python "$WebDir\generate_labels.py"
    if ($LASTEXITCODE -ne 0) { Write-Error "generate_labels.py failed."; exit 1 }
}

if ($Target -eq 'public' -or $Target -eq 'both') {
    # 2.5 Snapshot this release before uploading, for -Rollback (WEBAPP_PROJECT_STANDARD.md §14B)
    Write-Host "==> Snapshotting release..."
    python "$RootDir\deploy\rollback.py" snapshot
    if ($LASTEXITCODE -ne 0) { Write-Error "Snapshot failed."; exit 1 }

    # 3. Upload index.html
    Write-Host "==> Uploading to ftp://${FTP_HOST}${FTP_DIR}/ ..."
    Write-Host "  index.html"
    Send-File "$WebDir\index.html" "ftp://${FTP_HOST}${FTP_DIR}/index.html"

    # 4. Upload favicon.svg
    Write-Host "  favicon.svg"
    Send-File "$WebDir\favicon.svg" "ftp://${FTP_HOST}${FTP_DIR}/favicon.svg"

    # 5. Upload logo/
    Write-Host "  logo/..."
    $LogoEncoded = [Uri]::EscapeDataString($LOGO_PNG)
    Send-File "$WebDir\logo\$LOGO_PNG" "ftp://${FTP_HOST}${FTP_DIR}/logo/$LogoEncoded"
    # Upload SVG logo (ASCII filename – no encoding needed)
    Send-File "$WebDir\logo\logo.svg" "ftp://${FTP_HOST}${FTP_DIR}/logo/logo.svg"

    # 6. Upload i18n/ folder (translation files)
    $I18nDir = "$WebDir\i18n"
    $I18nFiles = Get-ChildItem $I18nDir -File
    Write-Host "  i18n/ ($($I18nFiles.Count) files)..."
    foreach ($f in $I18nFiles) {
        Send-File $f.FullName "ftp://${FTP_HOST}${FTP_DIR}/i18n/$($f.Name)"
    }

    # 7. Upload data/ folder (index.json + all *_beerjson.json) — skipped with -SkipData
    if ($SkipData) {
        Write-Host "  data/ skipped (-SkipData)"
    } else {
        $DataDir = "$WebDir\data"
        $DataFiles = Get-ChildItem $DataDir -File
        Write-Host "  data/ ($($DataFiles.Count) files)..."
        foreach ($f in $DataFiles) {
            Send-File $f.FullName "ftp://${FTP_HOST}${FTP_DIR}/data/$($f.Name)"
        }
    }

    # 8. Upload images/ folder — skipped with -SkipData
    if ($SkipData) {
        Write-Host "  images/ skipped (-SkipData)"
    } else {
        $ImagesDir = "$WebDir\images"
        if (Test-Path $ImagesDir) {
            $ImageFiles = Get-ChildItem $ImagesDir -File
            Write-Host "  images/ ($($ImageFiles.Count) files)..."
            foreach ($f in $ImageFiles) {
                $encoded = [Uri]::EscapeDataString($f.Name)
                Send-File $f.FullName "ftp://${FTP_HOST}${FTP_DIR}/images/${encoded}"
            }
        } else {
            Write-Host "  images/ not found, skipping"
        }
    }

    # 9. Upload labels/ folder (only with -Labels flag)
    if ($Labels) {
        $LabelsDir = "$WebDir\labels"
        if (Test-Path $LabelsDir) {
            $LabelFiles = Get-ChildItem $LabelsDir -File
            Write-Host "  labels/ ($($LabelFiles.Count) files)..."
            foreach ($f in $LabelFiles) {
                Send-File $f.FullName "ftp://${FTP_HOST}${FTP_DIR}/labels/$($f.Name)"
            }
        }
    } else {
        Write-Host "  labels/ skipped (no -Labels flag)"
    }

    Write-Host "`nPublic deploy complete: ${SITE_URL}"
}

if ($Target -eq 'local' -or $Target -eq 'both') {
    # local: publish into WWW_ROOT/brewlog/releases/<VERSION>/ and flip
    # `current` (WEBAPP_PROJECT_STANDARD.md §14B). No -Labels equivalent —
    # printed label sheets aren't part of the served site either target ships.
    $Version = (Get-Content "$RootDir\VERSION").Trim()
    Write-Host "==> Publishing local release $Version..."
    python "$RootDir\deploy\rollback.py" publish-local
    if ($LASTEXITCODE -ne 0) { Write-Error "Local publish failed."; exit 1 }
}
