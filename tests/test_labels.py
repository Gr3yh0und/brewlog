import base64
import os
import tempfile
import unittest
import unittest.mock

import helpers  # sets up sys.path; must come before web imports
import export as export_module
import generate_labels as labels_module


class TestLabels(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmpdir   = tempfile.mkdtemp()
        cls.db_path  = os.path.join(cls.tmpdir, 'test.sqlite')
        cls.data_dir = os.path.join(cls.tmpdir, 'data')
        cls.out_dir  = os.path.join(cls.tmpdir, 'labels')

        helpers.create_fixture_db(cls.db_path)

        # Run export first so BeerJSON files exist for label generation
        with unittest.mock.patch.multiple(
            export_module,
            DB_PATH      = cls.db_path,
            ENR_DIR      = helpers.ENRICHMENT_DIR,
            IMG_DIR      = '',
            DATA_DIR     = cls.data_dir,
            IMG_OUT      = os.path.join(cls.tmpdir, 'images'),
            LOGO_SRC     = '',
            LOGO_OUT     = os.path.join(cls.tmpdir, 'logo'),
            BREWERY_NAME = 'Test Brewery',
            SITE_URL     = 'https://test.example.com',
            LOGO_PNG     = 'test-logo.png',
        ):
            export_module.export()

        # Load test logo as base64
        with open(helpers.LOGO_SVG, 'rb') as f:
            cls.logo_b64 = base64.b64encode(f.read()).decode()

        # Generate labels for brew #1 (with logo) and brew #2 (without)
        with unittest.mock.patch.multiple(
            labels_module,
            DATA_DIR     = cls.data_dir,
            OUT_DIR      = cls.out_dir,
            LOGO_PATH    = helpers.LOGO_SVG,
            BREWERY_NAME = 'Test Brewery',
            SITE_URL     = 'https://test.example.com',
        ):
            labels_module.generate_label(1, cls.logo_b64)
            labels_module.generate_label(2, None)

    # ── output files ─────────────────────────────────────────────────

    def test_single_label_created(self):
        for n in (1, 2):
            path = os.path.join(self.out_dir, f'{n}_label.svg')
            self.assertTrue(os.path.exists(path), f'Missing: {n}_label.svg')

    def test_a4_label_created(self):
        for n in (1, 2):
            path = os.path.join(self.out_dir, f'{n}_a4.svg')
            self.assertTrue(os.path.exists(path), f'Missing: {n}_a4.svg')

    # ── SVG validity ─────────────────────────────────────────────────

    def test_single_label_is_svg(self):
        with open(os.path.join(self.out_dir, '1_label.svg'), encoding='utf-8') as f:
            content = f.read()
        self.assertIn('<svg ', content)
        self.assertIn('</svg>', content)

    def test_a4_label_is_svg(self):
        with open(os.path.join(self.out_dir, '1_a4.svg'), encoding='utf-8') as f:
            content = f.read()
        self.assertIn('<svg ', content)
        self.assertIn('</svg>', content)

    def test_label_contains_beer_name(self):
        with open(os.path.join(self.out_dir, '1_label.svg'), encoding='utf-8') as f:
            content = f.read()
        self.assertIn('Example Pale Ale', content)

    def test_label_without_logo_still_valid(self):
        """Brew #2 was generated without a logo — SVG must still be complete."""
        with open(os.path.join(self.out_dir, '2_label.svg'), encoding='utf-8') as f:
            content = f.read()
        self.assertIn('<svg ', content)
        self.assertIn('Example Stout', content)

    def test_a4_contains_repeated_labels(self):
        """A4 sheet should contain multiple <g transform> stacked copies."""
        with open(os.path.join(self.out_dir, '1_a4.svg'), encoding='utf-8') as f:
            content = f.read()
        self.assertGreater(content.count('<g transform="translate(0,'), 1)


if __name__ == '__main__':
    unittest.main()
