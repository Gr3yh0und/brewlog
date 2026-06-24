import json
import os
import tempfile
import unittest
import unittest.mock

import helpers  # sets up sys.path; must come before web imports
import export as export_module


class TestExport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.db_path  = os.path.join(cls.tmpdir, 'test.sqlite')
        cls.data_dir = os.path.join(cls.tmpdir, 'data')
        cls.img_out  = os.path.join(cls.tmpdir, 'images')
        cls.logo_out = os.path.join(cls.tmpdir, 'logo')

        helpers.create_fixture_db(cls.db_path)

        with unittest.mock.patch.multiple(
            export_module,
            DB_PATH   = cls.db_path,
            ENR_DIR   = helpers.ENRICHMENT_DIR,
            IMG_DIR   = '',
            DATA_DIR  = cls.data_dir,
            IMG_OUT   = cls.img_out,
            LOGO_SRC  = '',
            LOGO_OUT  = cls.logo_out,
            BREWERY_NAME = 'Test Brewery',
            SITE_URL     = 'https://test.example.com',
            LOGO_PNG     = 'test-logo.png',
        ):
            export_module.export()

    # ── index.json ────────────────────────────────────────────────────

    def test_index_json_created(self):
        self.assertTrue(os.path.exists(os.path.join(self.data_dir, 'index.json')))

    def test_index_json_structure(self):
        with open(os.path.join(self.data_dir, 'index.json'), encoding='utf-8') as f:
            idx = json.load(f)
        self.assertIn('config', idx)
        self.assertIn('exportiert', idx)
        self.assertIn('beers', idx)
        self.assertEqual(len(idx['beers']), 2)

    def test_index_config_block(self):
        with open(os.path.join(self.data_dir, 'index.json'), encoding='utf-8') as f:
            cfg = json.load(f)['config']
        self.assertEqual(cfg['brewery_name'], 'Test Brewery')
        self.assertEqual(cfg['site_url'], 'https://test.example.com')
        self.assertEqual(cfg['logo_png'], 'test-logo.png')

    def test_index_beer_fields(self):
        with open(os.path.join(self.data_dir, 'index.json'), encoding='utf-8') as f:
            beers = json.load(f)['beers']
        # Ordered by Sudnummer DESC → brew 2 first
        required = {'sudnummer', 'name', 'category', 'status', 'ebc', 'sw', 'ibu', 'alkohol', 'file'}
        for beer in beers:
            self.assertTrue(required.issubset(beer.keys()), f"Missing keys in {beer}")

    # ── per-brew BeerJSON ─────────────────────────────────────────────

    def test_beerjson_files_created(self):
        for n in (1, 2):
            path = os.path.join(self.data_dir, f'{n}_beerjson.json')
            self.assertTrue(os.path.exists(path), f'Missing: {n}_beerjson.json')

    def test_beerjson_structure(self):
        with open(os.path.join(self.data_dir, '1_beerjson.json'), encoding='utf-8') as f:
            bj = json.load(f)
        self.assertIn('beerjson', bj)
        self.assertAlmostEqual(bj['beerjson']['version'], 2.06)
        recipe = bj['beerjson']['recipes'][0]
        self.assertEqual(recipe['name'], 'Example Pale Ale')
        self.assertEqual(recipe['author'], 'Test Brewery')

    def test_brewery_extension_present(self):
        with open(os.path.join(self.data_dir, '1_beerjson.json'), encoding='utf-8') as f:
            recipe = json.load(f)['beerjson']['recipes'][0]
        self.assertIn('_brewery', recipe)
        sb = recipe['_brewery']
        self.assertEqual(sb['sudnummer'], 1)
        self.assertEqual(sb['status'], 3)
        self.assertIn('label_color', sb)
        self.assertIn('tastes', sb)

    def test_enrichment_applied(self):
        with open(os.path.join(self.data_dir, '1_beerjson.json'), encoding='utf-8') as f:
            sb = json.load(f)['beerjson']['recipes'][0]['_brewery']
        self.assertEqual(sb['untappd_id'], '12345')
        self.assertEqual(sb['label_color'], '#C8A860')
        self.assertEqual(len(sb['tastes']), 5)

    def test_enrichment_stout_values(self):
        with open(os.path.join(self.data_dir, '2_beerjson.json'), encoding='utf-8') as f:
            sb = json.load(f)['beerjson']['recipes'][0]['_brewery']
        self.assertEqual(sb['label_color'], '#1A0A00')
        self.assertEqual(len(sb['tastes']), 5)
        ratings = {t['notes']: t['rating'] for t in sb['tastes']}
        self.assertEqual(ratings['Bitterkeit'], 0.80)
        self.assertEqual(ratings['Frucht'],     0.35)
        self.assertEqual(ratings['Erde'],       0.60)

    def test_ingredients_exported(self):
        with open(os.path.join(self.data_dir, '1_beerjson.json'), encoding='utf-8') as f:
            ing = json.load(f)['beerjson']['recipes'][0]['ingredients']
        self.assertEqual(len(ing['fermentable_additions']), 2)
        self.assertEqual(len(ing['hop_additions']), 2)
        self.assertEqual(len(ing['culture_additions']), 1)

    def test_mash_steps_exported(self):
        with open(os.path.join(self.data_dir, '1_beerjson.json'), encoding='utf-8') as f:
            mash = json.load(f)['beerjson']['recipes'][0]['mash']
        self.assertEqual(len(mash['mash_steps']), 3)


if __name__ == '__main__':
    unittest.main()
