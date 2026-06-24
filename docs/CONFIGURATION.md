# Configuration

Copy `.env.example` to `.env` and fill in all values before running any script.

## Environment Variables

All variables live in `.env`. Copy `.env.example` as a starting point.

### Required (Deployment)

| Variable | Description | Example |
|---|---|---|
| `FTP_HOST` | FTP server hostname | `ftp.your-host.com` |
| `FTP_USER` | FTP username | `your-user` |
| `FTP_PASS` | FTP password | `your-password` |
| `FTP_DIR` | Remote path to web root | `/public_html/beer` |

### Required (Website)

| Variable | Description | Example |
|---|---|---|
| `BREWERY_NAME` | Displayed name of your brewery | `My Brewery` |
| `SITE_URL` | Full URL where the site is hosted | `https://beer.your-domain.com` |

`BREWERY_NAME` appears in the website header and as the recipe author in exported BeerJSON files.  
`SITE_URL` is used for the QR code on each label (`{SITE_URL}?beer={sudnummer}`).

### Optional (Branding)

| Variable | Description | Example |
|---|---|---|
| `LOGO_PNG` | PNG logo filename (must exist in `input/logo/`) | `my-brewery-logo.png` |
| `LOGO_SVG` | SVG logo filename (must exist in `input/logo/`) | `my-brewery-logo.svg` |

Both are copied from `input/logo/` to `web/logo/` on each export run. Omit both if you don't want a logo on the site or labels.

### Optional (InfluxDB Sensor Data)

These variables are only used by `fetch_influxdb.py` — all other scripts ignore them. Skip this entire section if you don't have sensor data.

#### Connection

| Variable | Description | Example |
|---|---|---|
| `INFLUXDB_URL` | InfluxDB v2 base URL | `http://localhost:8086` |
| `INFLUXDB_TOKEN` | InfluxDB v2 API token | `my-token` |
| `INFLUXDB_ORG` | InfluxDB organisation name (often empty) | `` |
| `INFLUXDB_BUCKET` | InfluxDB bucket name | `brewery` |

#### Kettle Temperature (Brew Day)

| Variable | Description | Example |
|---|---|---|
| `INFLUXDB_KETTLE_MEASUREMENT` | Measurement for kettle temp | `mqtt_consumer` |
| `INFLUXDB_KETTLE_TOPIC_TAG` | Tag holding the MQTT topic | `topic` |
| `INFLUXDB_KETTLE_TOPICS` | Comma-separated kettle temp topics | `cave/brewery/temperature/0,...` |
| `INFLUXDB_KETTLE_FIELD` | Field name for kettle temperature | `temperature` |
| `INFLUXDB_KETTLE_SENSOR_LABELS` | Human-readable label per topic suffix | `0=Kettle,1=Ambient` |

#### iSpindel (Fermentation)

| Variable | Description | Example |
|---|---|---|
| `INFLUXDB_ISPINDEL_MEASUREMENT` | Measurement for iSpindel data | `ispindel` |
| `INFLUXDB_ISPINDEL_SOURCE_TAG` | Tag identifying the device | `source` |
| `INFLUXDB_ISPINDEL_TYPE_TAG` | Tag distinguishing reading types | `field` |
| `INFLUXDB_ISPINDEL_VALUE_FIELD` | Field holding the numeric value | `value` |
| `INFLUXDB_ISPINDEL_TEMP_VALUE` | Type-tag value for temperature | `temperature` |
| `INFLUXDB_ISPINDEL_GRAVITY_VALUE` | Type-tag value for gravity | `gravity` |

## Enrichment (Taste Profile, Untappd)

> **The Sudnummer (`n`) is the primary key for every brew in Kleiner Brauhelfer 2.**  
> Find it in KBH2 under *Sudinfo → Sudnummer*. It must match across enrichment files,
> photo filenames, and the `?beer=N` URL parameter.

Edit `input/enrichment/{n}.json` per brew (`n` = Sudnummer):

```json
{
  "untappd_id": "12345",
  "label_color": "#D2CECE",
  "tastes": [
    {"rating": 0.6, "notes": "Bitterkeit"},
    {"rating": 0.3, "notes": "Frucht"},
    {"rating": 0.7, "notes": "Milde"},
    {"rating": 0.5, "notes": "Erde"},
    {"rating": 0.8, "notes": "Würze"}
  ]
}
```

The 5 sensory axes (Bitterkeit, Frucht, Milde, Erde, Würze) default to 0.5 if no enrichment file exists. The remaining 3 axes (Stammwürze, Alkohol, Farbe) are always computed from actual brew measurements.

Changes are picked up automatically on the next deploy run.

## Photos

Drop brew photos into `input/images/` using the naming convention `{n}_{description}.jpg` (or `.png`), where `n` is the Sudnummer:

```
input/images/
├── 18_Brauen.jpg
├── 18_Abfüllung.jpg
├── 25_Jodprobe.jpg
└── ...
```

`export.py` auto-discovers all matching files, copies them to `web/images/`, and embeds the filename list in each brew's BeerJSON under `_brewery.images`. The detail view renders them as a thumbnail grid with a full-screen lightbox (keyboard ← / → / Esc).

## Translations (i18n)

The UI supports 8 languages selectable via a flag-picker dropdown in the header:

| Code | Language |
|------|----------|
| `de` | German |
| `en` | English |
| `fr` | French |
| `it` | Italian |
| `es` | Spanish |
| `nl` | Dutch |
| `da` | Danish |
| `cs` | Czech |

Translation files live in `web/i18n/{code}.json`. **When adding or changing any UI-visible string, update all 8 files.** The deploy script uploads the entire `i18n/` folder automatically.