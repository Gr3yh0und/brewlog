#!/usr/bin/env python3
"""
Generate sample data for trying out Brewlog without a real KBH2 database.

Creates:
  input/brauhelfer.sqlite   — 5 diverse example brews
  input/enrichment/{n}.json — taste profiles per brew

Usage:
  python sample/generate_sample_data.py
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)

DB_PATH      = os.path.join(PROJECT_ROOT, 'input', 'brauhelfer.sqlite')
ENRICH_DIR   = os.path.join(PROJECT_ROOT, 'input', 'enrichment')


def create_schema(cur):
    """
    Create the KBH2-compatible schema. Uses the same tables as the real
    brauhelfer.sqlite but with only the columns we actually need for the
    sample data. The Sud table has 67 columns in real KBH2 — we create all
    of them here so the sample DB is compatible with export.py.
    """
    cur.executescript("""
    DROP TABLE IF EXISTS Tags;
    DROP TABLE IF EXISTS Bewertungen;
    DROP TABLE IF EXISTS Hauptgaerverlauf;
    DROP TABLE IF EXISTS Maischplan;
    DROP TABLE IF EXISTS WeitereZutatenGaben;
    DROP TABLE IF EXISTS Hefegaben;
    DROP TABLE IF EXISTS Hopfengaben;
    DROP TABLE IF EXISTS Malzschuettung;
    DROP TABLE IF EXISTS Sud;

    CREATE TABLE Sud (
        ID                           INTEGER PRIMARY KEY,
        Sudnummer                    INTEGER,
        Sudname                      TEXT,
        Kategorie                    TEXT,
        Status                       INTEGER DEFAULT 0,
        Braudatum                    TEXT,
        Abfuelldatum                 TEXT,
        Erstellt                     TEXT,
        Menge                        REAL,
        SW                           REAL,
        IBU                          REAL,
        CO2                          REAL DEFAULT 0,
        Kochdauer                    REAL DEFAULT 90,
        erg_Farbe                    REAL,
        erg_Alkohol                  REAL,
        erg_Sudhausausbeute          REAL,
        SWJungbier                   REAL,
        Vergaerungsgrad              REAL,
        Kommentar                    TEXT DEFAULT '',
        BemerkungBrauen              TEXT DEFAULT '',
        BemerkungMaischplan          TEXT DEFAULT '',
        BemerkungWasseraufbereitung  TEXT DEFAULT '',
        BemerkungZutatenMaischen     TEXT DEFAULT '',
        BemerkungZutatenKochen       TEXT DEFAULT '',
        BemerkungZutatenGaerung      TEXT DEFAULT '',
        BemerkungGaerung             TEXT DEFAULT '',
        BemerkungAbfuellen           TEXT DEFAULT ''
    );
    CREATE TABLE Malzschuettung (
        ID INTEGER PRIMARY KEY, SudID INTEGER,
        Name TEXT, Prozent REAL, erg_Menge REAL, Farbe REAL, Potential REAL
    );
    CREATE TABLE Hopfengaben (
        ID INTEGER PRIMARY KEY, SudID INTEGER,
        Name TEXT, Menge REAL, erg_Menge REAL, Zeit REAL,
        Vorderwuerze INTEGER DEFAULT 3, Pellets INTEGER DEFAULT 1, Alpha REAL
    );
    CREATE TABLE Hefegaben (
        ID INTEGER PRIMARY KEY, SudID INTEGER,
        Name TEXT, Menge REAL, Einheit TEXT, ZugabeNach REAL DEFAULT 0
    );
    CREATE TABLE WeitereZutatenGaben (
        ID INTEGER PRIMARY KEY, SudID INTEGER,
        Name TEXT, Menge REAL, Einheit TEXT,
        Zeitpunkt INTEGER DEFAULT 0, Typ INTEGER DEFAULT 0, Bemerkung TEXT
    );
    CREATE TABLE Maischplan (
        ID INTEGER PRIMARY KEY, SudID INTEGER,
        Name TEXT, Typ INTEGER DEFAULT 1,
        TempWasser REAL, TempRast REAL, DauerRast REAL
    );
    CREATE TABLE Hauptgaerverlauf (
        ID INTEGER PRIMARY KEY, SudID INTEGER,
        Zeitstempel TEXT, Restextrakt REAL, Alc REAL, Temp REAL, Bemerkung TEXT
    );
    CREATE TABLE Bewertungen (
        ID INTEGER PRIMARY KEY, SudID INTEGER,
        Datum TEXT, Sterne REAL,
        Farbe REAL, Schaum REAL, Geruch REAL, Geschmack REAL,
        Antrunk REAL, Haupttrunk REAL, Nachtrunk REAL, Gesamteindruck REAL
    );
    CREATE TABLE Tags (
        ID INTEGER PRIMARY KEY, SudID INTEGER, Key TEXT, Value TEXT
    );
    """)


def insert_brew(cur, sid, snum, data):
    """Insert one complete brew with all sub-tables using named columns."""
    cur.execute("""
        INSERT INTO Sud (
            ID, Sudnummer, Sudname, Kategorie, Status,
            Braudatum, Abfuelldatum, Erstellt,
            Menge, SW, IBU, CO2, Kochdauer,
            erg_Farbe, erg_Alkohol, erg_Sudhausausbeute,
            SWJungbier, Vergaerungsgrad
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, (
        sid, snum, data['name'], data['category'], data['status'],
        data.get('braudatum'), data.get('abfuelldatum'), data.get('erstellt'),
        data['menge'], data['sw'], data['ibu'], data.get('co2', 5.0),
        data.get('kochdauer', 90), data['ebc'], data['abv'],
        data.get('sha', 75.0), data.get('swj', data['sw']),
        data.get('vg', 72.0),
    ))

    # Malzschuettung
    malt_id = sid * 100
    for malt in data['malts']:
        malt_id += 1
        cur.execute("INSERT INTO Malzschuettung VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (malt_id, sid, malt['name'], malt['prozent'],
                     malt['menge'], malt['farbe'], malt['potential']))

    # Hopfengaben
    hop_id = sid * 200
    for hop in data['hops']:
        hop_id += 1
        cur.execute("INSERT INTO Hopfengaben VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (hop_id, sid, hop['name'], hop['menge'],
                     hop['menge'], hop['zeit'], hop.get('vorderwuerze', 3),
                     1,  # Pellets
                     hop['alpha']))

    # Hefegaben
    cur.execute("INSERT INTO Hefegaben VALUES (?, ?, ?, ?, ?, ?)",
                (sid * 300, sid, data['yeast']['name'],
                 data['yeast']['menge'], data['yeast']['einheit'], 0))

    # Maischplan
    step_id = sid * 400
    for step in data['mash']:
        step_id += 1
        cur.execute("INSERT INTO Maischplan VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (step_id, sid, step['name'], step.get('typ', 1),
                     step.get('temp_wasser'), step['temp_rast'], step['dauer']))

    # Hauptgaerverlauf (fermentation log)
    if 'fermentation' in data:
        for i, f in enumerate(data['fermentation']):
            cur.execute("INSERT INTO Hauptgaerverlauf VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (sid * 500 + i, sid, f['zeitstempel'],
                         f['restextrakt'], f['alc'], f['temp'], f.get('bemerkung', '')))

    # Bewertungen
    if 'rating' in data:
        r = data['rating']
        cur.execute("INSERT INTO Bewertungen VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (sid * 600, sid, r['datum'], r['sterne'],
                     r['farbe'], r['schaum'], r['geruch'], r['geschmack'],
                     r['antrunk'], r['haupttrunk'], r['nachtrunk'], r['gesamteindruck']))

    # Tags
    tag_id = sid * 700
    for idx, tag in enumerate(data.get('tags', []), start=1):
        cur.execute("INSERT INTO Tags VALUES (?, ?, ?, ?)",
                    (tag_id + idx, sid, tag['key'], tag['value']))


def create_enrichment(snum, data):
    """Write enrichment JSON for one brew."""
    path = os.path.join(ENRICH_DIR, f'{snum}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(ENRICH_DIR, exist_ok=True)

    # Remove existing DB so we start fresh (sample schema differs from real KBH2)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    create_schema(cur)

    # ── Brew #1: Pale Ale (finished) ──────────────────────────────
    insert_brew(cur, 1, 1, {
        'name': 'Sunshine Pale Ale',
        'category': 'American Pale Ale',
        'status': 3,
        'braudatum': '2024-03-15',
        'abfuelldatum': '2024-04-01',
        'erstellt': '2024-01-10',
        'menge': 22.0,
        'sw': 12.5,
        'ibu': 38,
        'ebc': 24,
        'abv': 4.8,
        'malts': [
            {'name': 'Pale Malt',       'prozent': 85, 'menge': 4.25, 'farbe': 4.0,  'potential': 0.80},
            {'name': 'Crystal 40',      'prozent': 10, 'menge': 0.50, 'farbe': 80.0, 'potential': 0.72},
            {'name': 'Carapils',        'prozent': 5,  'menge': 0.25, 'farbe': 3.0,  'potential': 0.78},
        ],
        'hops': [
            {'name': 'Cascade',  'menge': 25, 'zeit': 60, 'alpha': 5.5},
            {'name': 'Centennial', 'menge': 15, 'zeit': 30, 'alpha': 10.0},
            {'name': 'Cascade',  'menge': 15, 'zeit': 0,  'alpha': 5.5, 'vorderwuerze': 4},
        ],
        'yeast': {'name': 'US-05', 'menge': 1, 'einheit': 'Pck'},
        'mash': [
            {'name': 'Einmaischen', 'temp_wasser': 75, 'temp_rast': 65, 'dauer': 5},
            {'name': 'Beta-Rast',   'temp_wasser': None, 'temp_rast': 63, 'dauer': 30},
            {'name': 'Alpha-Rast',  'temp_wasser': None, 'temp_rast': 72, 'dauer': 20},
            {'name': 'Abmaischen',  'temp_wasser': None, 'temp_rast': 78, 'dauer': 10},
        ],
        'fermentation': [
            {'zeitstempel': '2024-03-16', 'restextrakt': 12.0, 'alc': 0.0, 'temp': 18.5},
            {'zeitstempel': '2024-03-18', 'restextrakt': 9.5,  'alc': 1.3, 'temp': 19.0},
            {'zeitstempel': '2024-03-22', 'restextrakt': 7.0,  'alc': 2.6, 'temp': 18.0},
            {'zeitstempel': '2024-03-28', 'restextrakt': 5.2,  'alc': 3.5, 'temp': 16.0},
            {'zeitstempel': '2024-04-05', 'restextrakt': 4.8,  'alc': 3.7, 'temp': 12.0},
        ],
        'rating': {
            'datum': '2024-05-10', 'sterne': 4.5,
            'farbe': 8, 'schaum': 7, 'geruch': 9, 'geschmack': 8,
            'antrunk': 8, 'haupttrunk': 9, 'nachtrunk': 8, 'gesamteindruck': 8,
        },
        'tags': [
            {'key': 'batch', 'value': 'spring-2024'},
            {'key': 'competition', 'value': 'yes'},
        ],
    })
    create_enrichment(1, {
        'untappd_id': '',
        'label_color': '#D4A843',
        'tastes': [
            {'rating': 0.6, 'notes': 'Bitterkeit'},
            {'rating': 0.7, 'notes': 'Frucht'},
            {'rating': 0.5, 'notes': 'Milde'},
            {'rating': 0.3, 'notes': 'Erde'},
            {'rating': 0.4, 'notes': 'Würze'},
        ],
    })

    # ── Brew #2: Stout (recipe, not yet brewed) ───────────────────
    insert_brew(cur, 2, 2, {
        'name': 'Midnight Stout',
        'category': 'Stout',
        'status': 0,
        'erstellt': '2024-06-01',
        'menge': 22.0,
        'sw': 16.0,
        'ibu': 42,
        'ebc': 180,
        'abv': 6.2,
        'malts': [
            {'name': 'Pale Malt',       'prozent': 55, 'menge': 3.30, 'farbe': 4.0,  'potential': 0.80},
            {'name': 'Munich Malt',     'prozent': 15, 'menge': 0.90, 'farbe': 20.0, 'potential': 0.77},
            {'name': 'Chocolate Malt',  'prozent': 12, 'menge': 0.72, 'farbe': 900.0,'potential': 0.00},
            {'name': 'Roasted Barley',  'prozent': 10, 'menge': 0.60, 'farbe': 1000.0,'potential': 0.00},
            {'name': 'Carafa Special III','prozent': 8, 'menge': 0.48, 'farbe': 1200.0,'potential': 0.00},
        ],
        'hops': [
            {'name': 'Tettnang', 'menge': 30, 'zeit': 60, 'alpha': 4.0},
            {'name': 'Willamette', 'menge': 10, 'zeit': 15, 'alpha': 4.5},
        ],
        'yeast': {'name': 'Nottingham', 'menge': 1, 'einheit': 'Pck'},
        'mash': [
            {'name': 'Einmaischen', 'temp_wasser': 72, 'temp_rast': 66, 'dauer': 5},
            {'name': 'Saccharification', 'temp_wasser': None, 'temp_rast': 68, 'dauer': 45},
            {'name': 'Abmaischen', 'temp_wasser': None, 'temp_rast': 76, 'dauer': 10},
        ],
        'tags': [
            {'key': 'season', 'value': 'winter'},
        ],
    })
    create_enrichment(2, {
        'untappd_id': '',
        'label_color': '#2C1810',
        'tastes': [
            {'rating': 0.7, 'notes': 'Bitterkeit'},
            {'rating': 0.2, 'notes': 'Frucht'},
            {'rating': 0.8, 'notes': 'Milde'},
            {'rating': 0.6, 'notes': 'Erde'},
            {'rating': 0.3, 'notes': 'Würze'},
        ],
    })

    # ── Brew #3: Hefeweizen (bottled) ─────────────────────────────
    insert_brew(cur, 3, 3, {
        'name': 'Bavarian Hefeweizen',
        'category': 'Hefeweizen',
        'status': 2,
        'braudatum': '2024-05-20',
        'abfuelldatum': '2024-06-10',
        'erstellt': '2024-05-01',
        'menge': 20.0,
        'sw': 13.0,
        'ibu': 16,
        'ebc': 12,
        'abv': 5.2,
        'malts': [
            {'name': 'Wheat Malt',    'prozent': 70, 'menge': 3.50, 'farbe': 4.0, 'potential': 0.70},
            {'name': 'Pale Malt',     'prozent': 30, 'menge': 1.50, 'farbe': 3.0, 'potential': 0.80},
        ],
        'hops': [
            {'name': 'Hallertau Mittelfrüh', 'menge': 20, 'zeit': 60, 'alpha': 4.0},
        ],
        'yeast': {'name': 'WB-06', 'menge': 1, 'einheit': 'Pck'},
        'mash': [
            {'name': 'Einmaischen', 'temp_wasser': 55, 'temp_rast': 52, 'dauer': 5},
            {'name': 'Protein-Rast', 'temp_wasser': None, 'temp_rast': 52, 'dauer': 20},
            {'name': 'Beta-Rast',   'temp_wasser': None, 'temp_rast': 63, 'dauer': 30},
            {'name': 'Alpha-Rast',  'temp_wasser': None, 'temp_rast': 72, 'dauer': 15},
            {'name': 'Abmaischen',  'temp_wasser': None, 'temp_rast': 78, 'dauer': 5},
        ],
        'fermentation': [
            {'zeitstempel': '2024-05-21', 'restextrakt': 12.5, 'alc': 0.0, 'temp': 20.0},
            {'zeitstempel': '2024-05-25', 'restextrakt': 8.0,  'alc': 2.3, 'temp': 21.0},
            {'zeitstempel': '2024-06-02', 'restextrakt': 5.5,  'alc': 3.7, 'temp': 18.0},
            {'zeitstempel': '2024-06-12', 'restextrakt': 5.0,  'alc': 4.0, 'temp': 8.0},
        ],
        'rating': {
            'datum': '2024-07-01', 'sterne': 4.0,
            'farbe': 7, 'schaum': 9, 'geruch': 8, 'geschmack': 7,
            'antrunk': 8, 'haupttrunk': 8, 'nachtrunk': 7, 'gesamteindruck': 7,
        },
        'tags': [],
    })
    create_enrichment(3, {
        'untappd_id': '',
        'label_color': '#F5DEB3',
        'tastes': [
            {'rating': 0.2, 'notes': 'Bitterkeit'},
            {'rating': 0.8, 'notes': 'Frucht'},
            {'rating': 0.7, 'notes': 'Milde'},
            {'rating': 0.4, 'notes': 'Erde'},
            {'rating': 0.3, 'notes': 'Würze'},
        ],
    })

    # ── Brew #4: IPA (brewed, fermenting) ─────────────────────────
    insert_brew(cur, 4, 4, {
        'name': 'Tropical Haze IPA',
        'category': 'IPA',
        'status': 1,
        'braudatum': '2024-08-10',
        'erstellt': '2024-08-01',
        'menge': 20.0,
        'sw': 15.0,
        'ibu': 60,
        'ebc': 28,
        'abv': 6.5,
        'malts': [
            {'name': 'Pale Malt',    'prozent': 80, 'menge': 4.00, 'farbe': 4.0,  'potential': 0.80},
            {'name': 'Wheat Malt',   'prozent': 10, 'menge': 0.50, 'farbe': 4.0,  'potential': 0.70},
            {'name': 'Munich Malt',  'prozent': 10, 'menge': 0.50, 'farbe': 18.0, 'potential': 0.77},
        ],
        'hops': [
            {'name': 'Mosaic',   'menge': 20, 'zeit': 15, 'alpha': 11.0},
            {'name': 'Citra',    'menge': 30, 'zeit': 0,  'alpha': 13.0, 'vorderwuerze': 4},
            {'name': 'Mango Loco', 'menge': 20, 'zeit': 0, 'alpha': 9.0,  'vorderwuerze': 4},
        ],
        'yeast': {'name': 'Fermentis UCP-05', 'menge': 1, 'einheit': 'Pck'},
        'mash': [
            {'name': 'Einmaischen', 'temp_wasser': 70, 'temp_rast': 65, 'dauer': 5},
            {'name': 'Saccharification', 'temp_wasser': None, 'temp_rast': 67, 'dauer': 50},
            {'name': 'Abmaischen', 'temp_wasser': None, 'temp_rast': 76, 'dauer': 5},
        ],
        'fermentation': [
            {'zeitstempel': '2024-08-11', 'restextrakt': 14.5, 'alc': 0.0, 'temp': 19.0},
            {'zeitstempel': '2024-08-14', 'restextrakt': 10.0, 'alc': 2.3, 'temp': 21.0},
        ],
        'tags': [
            {'key': 'style', 'value': 'hazy-ipa'},
        ],
    })
    create_enrichment(4, {
        'untappd_id': '',
        'label_color': '#FF8C00',
        'tastes': [
            {'rating': 0.5, 'notes': 'Bitterkeit'},
            {'rating': 0.9, 'notes': 'Frucht'},
            {'rating': 0.4, 'notes': 'Milde'},
            {'rating': 0.3, 'notes': 'Erde'},
            {'rating': 0.5, 'notes': 'Würze'},
        ],
    })

    # ── Brew #5: Pilsner (finished) ───────────────────────────────
    insert_brew(cur, 5, 5, {
        'name': 'Golden Pilsner',
        'category': 'Pilsner',
        'status': 3,
        'braudatum': '2024-02-01',
        'abfuelldatum': '2024-03-15',
        'erstellt': '2024-01-15',
        'menge': 24.0,
        'sw': 11.5,
        'ibu': 32,
        'ebc': 8,
        'abv': 4.5,
        'malts': [
            {'name': 'Pilsner Malt', 'prozent': 100, 'menge': 4.80, 'farbe': 3.0, 'potential': 0.78},
        ],
        'hops': [
            {'name': 'Saaz', 'menge': 35, 'zeit': 60, 'alpha': 4.0},
            {'name': 'Saaz', 'menge': 20, 'zeit': 20, 'alpha': 4.0},
        ],
        'yeast': {'name': 'W-L38', 'menge': 2, 'einheit': 'Pck'},
        'mash': [
            {'name': 'Einmaischen', 'temp_wasser': 45, 'temp_rast': 42, 'dauer': 5},
            {'name': 'Protein-Rast', 'temp_wasser': None, 'temp_rast': 52, 'dauer': 15},
            {'name': 'Beta-Rast',   'temp_wasser': None, 'temp_rast': 63, 'dauer': 35},
            {'name': 'Alpha-Rast',  'temp_wasser': None, 'temp_rast': 72, 'dauer': 15},
            {'name': 'Abmaischen',  'temp_wasser': None, 'temp_rast': 76, 'dauer': 5},
        ],
        'fermentation': [
            {'zeitstempel': '2024-02-02', 'restextrakt': 11.0, 'alc': 0.0, 'temp': 10.0},
            {'zeitstempel': '2024-02-06', 'restextrakt': 7.5,  'alc': 1.8, 'temp': 12.0},
            {'zeitstempel': '2024-02-14', 'restextrakt': 5.0,  'alc': 3.2, 'temp': 8.0},
            {'zeitstempel': '2024-03-01', 'restextrakt': 4.2,  'alc': 3.7, 'temp': 0.0,  'bemerkung': 'Lagering'},
            {'zeitstempel': '2024-03-18', 'restextrakt': 4.0,  'alc': 3.8, 'temp': 0.0},
        ],
        'rating': {
            'datum': '2024-04-01', 'sterne': 4.0,
            'farbe': 9, 'schaum': 8, 'geruch': 7, 'geschmack': 8,
            'antrunk': 9, 'haupttrunk': 8, 'nachtrunk': 7, 'gesamteindruck': 8,
        },
        'tags': [
            {'key': 'classic', 'value': 'yes'},
        ],
    })
    create_enrichment(5, {
        'untappd_id': '',
        'label_color': '#FFD700',
        'tastes': [
            {'rating': 0.5, 'notes': 'Bitterkeit'},
            {'rating': 0.3, 'notes': 'Frucht'},
            {'rating': 0.6, 'notes': 'Milde'},
            {'rating': 0.5, 'notes': 'Erde'},
            {'rating': 0.4, 'notes': 'Würze'},
        ],
    })

    conn.commit()
    conn.close()

    print(f"OK: Sample database created at {DB_PATH}")
    print(f"     5 brews with enrichment files in {ENRICH_DIR}")
    print()
    print("Next steps:")
    print("  1. Copy .env.example -> .env and fill in your settings")
    print("  2. Run: python web/export.py")
    print("  3. Test locally: cd web && python -m http.server 8080")


if __name__ == '__main__':
    main()