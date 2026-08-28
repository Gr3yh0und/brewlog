"""
Snapshot + rollback for brewlog's FTP-only publish target
(WEBAPP_PROJECT_STANDARD.md SS14B).

deploy.sh/deploy.ps1 call `snapshot` right after export.py/generate_labels.py
and before any upload begins, so the snapshot captures the exact bytes about
to go live -- not the inputs that produced them. brewlog's site bakes in
exported data, so re-running export.py months later against a changed KBH2
database would not reproduce what was actually live; only a byte snapshot
can. `rollback [N]` re-uploads an earlier snapshot verbatim, no rebuild.

This target has no symlink to flip (WEBAPP_PROJECT_STANDARD.md SS14B is
written for a target with one) -- it's a single directory on a remote FTP
host, overwritten in place, the same shape housebuycomparison's deploy.py
solved this for. releases[0] is what's live right now, assuming nothing was
published outside these two scripts.

Usage:
    python3 deploy/rollback.py snapshot        # called by deploy.sh/.ps1
    python3 deploy/rollback.py list            # show saved releases
    python3 deploy/rollback.py rollback [N]    # re-upload releases[N], default 1
"""
import ftplib
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / 'web'
RELEASES_DIR = ROOT / 'deploy' / 'releases'
KEEP_RELEASES = 5

sys.path.insert(0, str(WEB_DIR))
from utils import load_env  # noqa: E402


class RollbackError(Exception):
    pass


def _release_files():
    """{relative remote path: local Path} for everything a full deploy uploads.

    Fixed regardless of --skip-data/--labels -- a snapshot always captures
    the complete site (brewlog is small; don't over-engineer this), not just
    whatever a partial deploy happened to send. labels/ is excluded: printed
    label sheets are a separate artifact, not part of the served site the
    bottle QR codes point at.
    """
    files = {}

    for name in ('index.html', 'favicon.svg'):
        p = WEB_DIR / name
        if p.is_file():
            files[name] = p

    logo_dir = WEB_DIR / 'logo'
    if logo_dir.is_dir():
        for p in sorted(logo_dir.iterdir()):
            if p.is_file():
                files[f'logo/{p.name}'] = p

    for sub in ('i18n', 'data', 'images'):
        d = WEB_DIR / sub
        if d.is_dir():
            for p in sorted(d.iterdir()):
                if p.is_file():
                    files[f'{sub}/{p.name}'] = p

    return files


_SEQ_RE = re.compile(r'^(\d{6})-')


def list_releases():
    """Saved releases, newest first. Every release dir is prefixed with a
    zero-padded monotonic sequence number (f"{seq:06d}-..."), so lexicographic
    order always matches creation order -- unlike a bare timestamp, a
    sequence number freed by pruning is never reused, so a later release can
    never sort as older than an earlier one that already got pruned."""
    if not RELEASES_DIR.exists():
        return []
    return sorted((d for d in RELEASES_DIR.iterdir() if d.is_dir()), reverse=True)


def _next_sequence():
    """max(existing sequence numbers) + 1. No counter file needed -- pruning
    only ever removes the lowest-numbered releases, so the highest surviving
    sequence number is always the true running max."""
    if not RELEASES_DIR.exists():
        return 0
    seqs = [int(m.group(1)) for d in RELEASES_DIR.iterdir()
            if d.is_dir() and (m := _SEQ_RE.match(d.name))]
    return max(seqs, default=-1) + 1


def snapshot_release(files=None):
    """Save `files` ({relative path: local Path}) as a new release, prune to KEEP_RELEASES."""
    if files is None:
        files = _release_files()

    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    seq = _next_sequence()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    release_dir = RELEASES_DIR / f'{seq:06d}-{stamp}'
    while release_dir.exists():
        seq += 1
        release_dir = RELEASES_DIR / f'{seq:06d}-{stamp}'
    release_dir.mkdir(parents=True)

    for rel_path, local_path in files.items():
        dest = release_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(Path(local_path).read_bytes())

    for old in list_releases()[KEEP_RELEASES:]:
        shutil.rmtree(old)

    return release_dir


def _ftp_mkdirs(ftp, remote_dir):
    """mkdir -p equivalent for FTP; 'already exists' is not an error here."""
    path = ''
    for part in remote_dir.strip('/').split('/'):
        if not part:
            continue
        path += f'/{part}'
        try:
            ftp.mkd(path)
        except ftplib.error_perm:
            pass


def _ftp_upload_all(target, files, env):
    host = env['FTP_HOST']
    remote_base = env['FTP_DIR'].rstrip('/')
    ftp = ftplib.FTP(host)
    try:
        ftp.login(env['FTP_USER'], env['FTP_PASS'])
        ftp.set_pasv(True)
        for f in files:
            rel_path = f.relative_to(target).as_posix()
            remote_path = f'{remote_base}/{rel_path}'
            _ftp_mkdirs(ftp, os.path.dirname(remote_path))
            with open(f, 'rb') as fh:
                ftp.storbinary(f'STOR {remote_path}', fh)
    finally:
        ftp.quit()


def do_rollback(steps_back=1, uploader=None, env=None):
    """Re-upload releases[steps_back] verbatim -- no export.py re-run.

    releases[0] is the most recently deployed version; steps_back=1 (the
    default) re-publishes the release before it.
    """
    releases = list_releases()
    if len(releases) <= steps_back:
        raise RollbackError(
            f'Only {len(releases)} release(s) saved locally under {RELEASES_DIR} '
            f'-- cannot go back {steps_back}.'
        )
    target = releases[steps_back]
    files = sorted(p for p in target.rglob('*') if p.is_file())
    if not files:
        raise RollbackError(f'{target} has no saved files -- nothing to roll back to.')

    if env is None:
        env = load_env()
    if uploader is None:
        uploader = _ftp_upload_all

    uploader(target, files, env)
    return target, files


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'snapshot':
        release_dir = snapshot_release()
        n = sum(1 for _ in release_dir.rglob('*') if _.is_file())
        print(f'Snapshot saved: {release_dir.name} ({n} files)')
    elif cmd == 'list':
        releases = list_releases()
        if not releases:
            print('No releases saved yet.')
        for i, r in enumerate(releases):
            print(f'  [{i}] {r.name}' + (' (live)' if i == 0 else ''))
    elif cmd == 'rollback':
        steps_back = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        try:
            target, files = do_rollback(steps_back)
        except RollbackError as e:
            print(f'Error: {e}', file=sys.stderr)
            sys.exit(1)
        print(f'Rolled back to release {target.name} ({len(files)} file(s)).')
        print('Live site now serving this release.')
    else:
        print(f'Unknown command: {cmd}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
