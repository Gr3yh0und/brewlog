import shutil
import tempfile
import unittest
import unittest.mock
from datetime import datetime, timezone
from pathlib import Path

import helpers  # sets up sys.path; must come before deploy imports
import rollback


class TestRollback(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self._orig_releases_dir = rollback.RELEASES_DIR
        rollback.RELEASES_DIR = self.tmpdir / 'releases'

    def tearDown(self):
        rollback.RELEASES_DIR = self._orig_releases_dir
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_source(self, name, content):
        """A fake 'web/' output tree with one file, for snapshot_release()."""
        src_dir = self.tmpdir / f'src_{name}'
        src_dir.mkdir()
        f = src_dir / 'index.html'
        f.write_text(content, encoding='utf-8')
        return {'index.html': f}

    # -- Core scenario: deploy twice with different content, roll back,
    #    the FIRST content is what a rollback actually re-publishes. --
    def test_rollback_restores_previous_release_content_not_latest(self):
        rollback.snapshot_release(self._write_source('a', 'VERSION-A content'))
        rollback.snapshot_release(self._write_source('b', 'VERSION-B content'))

        uploaded = {}

        def stub_uploader(target, files, env):
            for f in files:
                uploaded[f.relative_to(target).as_posix()] = f.read_text(encoding='utf-8')

        target, files = rollback.do_rollback(steps_back=1, uploader=stub_uploader, env={})

        self.assertEqual(uploaded['index.html'], 'VERSION-A content')
        self.assertNotEqual(uploaded['index.html'], 'VERSION-B content')
        self.assertEqual(len(files), 1)

    def test_rollback_default_steps_back_is_previous_not_current(self):
        rollback.snapshot_release(self._write_source('a', 'first'))
        rollback.snapshot_release(self._write_source('b', 'second'))
        rollback.snapshot_release(self._write_source('c', 'third'))

        uploaded = {}
        rollback.do_rollback(
            uploader=lambda target, files, env: uploaded.update(
                {f.name: f.read_text(encoding='utf-8') for f in files}
            ),
            env={},
        )
        # steps_back defaults to 1: releases[0] is "third" (current live),
        # releases[1] is "second" -- the one before it.
        self.assertEqual(uploaded['index.html'], 'second')

    # -- Positive-state-change control, not an absence check: seed 7,
    #    confirm exactly 5 remain and it's the 5 newest. --
    def test_prune_keeps_last_5_newest(self):
        for i in range(7):
            rollback.snapshot_release(self._write_source(str(i), f'content-{i}'))

        releases = rollback.list_releases()
        self.assertEqual(len(releases), 5)

        contents = [
            (r / 'index.html').read_text(encoding='utf-8') for r in releases
        ]
        # Newest-first; content-6 was the last snapshot taken, so it's live.
        self.assertEqual(contents, [f'content-{i}' for i in (6, 5, 4, 3, 2)])

    def test_rollback_insufficient_releases_raises(self):
        rollback.snapshot_release(self._write_source('only', 'solo'))
        with self.assertRaises(rollback.RollbackError):
            rollback.do_rollback(steps_back=1, env={})

    def test_rollback_no_releases_raises(self):
        with self.assertRaises(rollback.RollbackError):
            rollback.do_rollback(steps_back=0, env={})

    # -- Timestamp collision: two snapshots in the same microsecond must not
    #    silently overwrite one another. --
    def test_timestamp_collision_disambiguates_without_data_loss(self):
        fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        with unittest.mock.patch.object(rollback, 'datetime') as mock_dt:
            mock_dt.now.return_value = fixed_now
            rollback.snapshot_release(self._write_source('x', 'collision-1'))
            rollback.snapshot_release(self._write_source('y', 'collision-2'))

        releases = rollback.list_releases()
        self.assertEqual(len(releases), 2)
        names = sorted(r.name for r in releases)
        self.assertNotEqual(names[0], names[1])
        self.assertTrue(all('20260101T000000.000000Z' in n for n in names))

        contents = {r.name: (r / 'index.html').read_text(encoding='utf-8') for r in releases}
        self.assertEqual(sorted(contents.values()), ['collision-1', 'collision-2'])

    # -- Regression: a freed release name must never be reused. Under a
    #    frozen clock (worst case -- every call returns the same timestamp,
    #    which coarse clock resolution or a tight retry loop can trigger for
    #    real), a bare/lowest-sorting name that gets pruned away must not be
    #    handed to a later deploy, which would delete that deploy's own
    #    snapshot in the same call that created it. --
    def test_frozen_clock_prune_never_deletes_the_release_just_created(self):
        fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        created = []
        with unittest.mock.patch.object(rollback, 'datetime') as mock_dt:
            mock_dt.now.return_value = fixed_now
            for i in range(12):
                release_dir = rollback.snapshot_release(self._write_source(str(i), f'content-{i}'))
                created.append(release_dir)
                self.assertTrue(
                    release_dir.exists(),
                    f'deploy {i}: release {release_dir.name!r} was deleted in the same '
                    f'call that created it -- its snapshot was never actually persisted',
                )

        releases = rollback.list_releases()
        self.assertEqual(len(releases), 5)
        # The 5 most recent deploys (7..11) must be exactly what survived.
        contents = sorted((r / 'index.html').read_text(encoding='utf-8') for r in releases)
        self.assertEqual(contents, sorted(f'content-{i}' for i in range(7, 12)))

    def test_release_files_matches_actual_web_dir_layout(self):
        # _release_files() reads the real web/ dir (no monkeypatching) --
        # sanity-checks it against files this repo actually ships, so a
        # rename in web/ that _release_files() misses shows up here.
        files = rollback._release_files()
        self.assertIn('index.html', files)
        self.assertIn('favicon.svg', files)
        self.assertTrue(any(k.startswith('i18n/') for k in files))


if __name__ == '__main__':
    unittest.main()
