"""
Shared test helpers.
Adds web/ to sys.path and provides a fixture SQLite creator matching the
minimal KBH2 schema that export.py and generate_labels.py require.
"""
import os
import sqlite3
import sys

# Make web/ importable from any test file that does `import helpers`
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web'))

FIXTURES_DIR  = os.path.join(os.path.dirname(__file__), 'fixtures')
ENRICHMENT_DIR = os.path.join(FIXTURES_DIR, 'enrichment')
LOGO_SVG      = os.path.join(FIXTURES_DIR, 'logo', 'test-logo.svg')


def create_fixture_db(path):
    """
    Write a minimal KBH2-compatible SQLite to `path` with 2 example brews:
      #1 – Example Pale Ale (Status=3, finished, full ingredients + mash)
      #2 – Example Stout   (Status=0, recipe only, minimal data)
    Returns a closed connection (file is flushed and ready to use).
    """
    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.executescript("""
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

    # ── Brew #1: Example Pale Ale (finished) ─────────────────────────
    c.execute("""
        INSERT INTO Sud VALUES (
            1, 1, 'Example Pale Ale', 'American Pale Ale', 3,
            '2024-03-15', '2024-04-01', '2024-01-10',
            20.0, 12.5, 35.0, 5.0, 90.0, 12.0, 5.2, 78.5,
            3.5, 80.0,
            'Clean and citrusy.', '', '', '', '', '', '', '', ''
        )
    """)
    c.executemany("INSERT INTO Malzschuettung VALUES (?,1,?,?,?,?,?)", [
        (1, 'Pale Malt',    90.0, 3.6, 5.0,   0.80),
        (2, 'Crystal 60',   10.0, 0.4, 120.0,  0.72),
    ])
    c.executemany("INSERT INTO Hopfengaben VALUES (?,1,?,?,?,?,?,?,?)", [
        (1, 'Citra',  30.0, 30.0, 60, 3, 1, 12.0),
        (2, 'Mosaic', 20.0, 20.0,  5, 3, 1, 11.5),
    ])
    c.execute("INSERT INTO Hefegaben VALUES (1,1,'US-05',1.0,'Pck',0)")
    c.executemany("INSERT INTO Maischplan VALUES (?,1,?,?,?,?,?)", [
        (1, 'Einmaischen', 0, 75.0, 65.0,  5),
        (2, 'Kombirast',   1, None, 67.0, 60),
        (3, 'Abmaischen',  1, None, 78.0, 10),
    ])
    c.execute("""
        INSERT INTO Bewertungen VALUES (
            1,1,'2024-05-10',4.5, 8,7,8,9,8,9,8,8
        )
    """)

    # ── Brew #2: Example Stout (recipe, not yet brewed) ───────────────
    c.execute("""
        INSERT INTO Sud VALUES (
            2, 2, 'Example Stout', 'Stout', 0,
            NULL, NULL, '2024-06-01',
            20.0, 16.0, 45.0, 5.5, 90.0, 65.0, 0.0, 0.0,
            NULL, NULL,
            '', '', '', '', '', '', '', '', ''
        )
    """)
    c.executemany("INSERT INTO Malzschuettung VALUES (?,2,?,?,?,?,?)", [
        (3, 'Pale Malt',       80.0, 4.0, 5.0,    0.80),
        (4, 'Roasted Barley',  10.0, 0.5, 1000.0, 0.65),
        (5, 'Chocolate Malt',  10.0, 0.5,  900.0, 0.67),
    ])
    c.execute("INSERT INTO Hopfengaben VALUES (3,2,'Magnum',40.0,40.0,60,3,1,14.0)")
    c.execute("INSERT INTO Hefegaben VALUES (2,2,'Nottingham',1.0,'Pck',0)")
    c.executemany("INSERT INTO Maischplan VALUES (?,2,?,?,?,?,?)", [
        (4, 'Einmaischen', 0, 76.0, 66.0,  5),
        (5, 'Kombirast',   1, None, 66.0, 60),
    ])

    conn.commit()
    conn.close()
