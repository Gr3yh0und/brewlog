# InfluxDB Fermentation Data

`fetch_influxdb.py` queries your local InfluxDB instance and writes brew-day and fermentation curves to `input/influxdb/{n}.json`. On the next `export.py` run, those files are copied to `web/data/{n}_influxdb.json` and uploaded alongside the BeerJSON files. The detail view fetches them lazily when a brew is opened and renders the charts if data is present — brews without an influxdb file are unaffected.

**Requires:** `pip install influxdb-client` and InfluxDB variables set in `.env`.

## Usage

```powershell
cd web
python fetch_influxdb.py          # all brews
python fetch_influxdb.py 50       # single brew
python fetch_influxdb.py 48 50    # multiple brews
```

## Output Data

Each output file contains three series plus a `units` metadata block:

| Key | Source | Contents | Unit |
|---|---|---|---|
| `brew_day` | `mqtt_consumer` kettle topics | Temperature per sensor for the brew day; each point includes a `label` (e.g. `Kettle` / `Ambient`) | `°C` |
| `ferm_temp` | `ispindel` `field=temperature` | iSpindel1 + iSpindel2 fermentation temp, tagged by `source` | `°C` |
| `ferm_gravity` | `ispindel` `field=gravity` | iSpindel1 + iSpindel2 specific gravity, tagged by `source` | `°P` |

**Brew day window:** the script queries from 1 calendar day *before* the `braudatum` through 60 hours after midnight of that day. This handles the common case where KBH2 records the brew date when the user saves the entry, which can be the morning after the actual brew session.

All series are downsampled to ~200–300 points with an auto-calculated aggregation window. Brews without a `braudatum` or a missing BeerJSON are skipped gracefully. Brews with no InfluxDB data produce empty arrays — `export.py` ignores them silently. Still-fermenting brews use the current time as the fermentation stop.

> Two brews can ferment in parallel (one iSpindel each). Both sources are stored independently; the correct iSpindel for a given brew is identified by overlapping its time range with the fermentation window.

## Configuration

InfluxDB variables in `.env` (all optional):

| Variable | Description | Default |
|---|---|---|
| `INFLUXDB_URL` | InfluxDB v2 base URL | - |
| `INFLUXDB_TOKEN` | InfluxDB v2 API token | - |
| `INFLUXDB_ORG` | InfluxDB organisation name | `` |
| `INFLUXDB_BUCKET` | InfluxDB bucket name | `brewery` |
| `INFLUXDB_KETTLE_MEASUREMENT` | Measurement for kettle temp | `mqtt_consumer` |
| `INFLUXDB_KETTLE_TOPIC_TAG` | Tag holding the MQTT topic | `topic` |
| `INFLUXDB_KETTLE_TOPICS` | Comma-separated kettle temp topics | - |
| `INFLUXDB_KETTLE_FIELD` | Field name for kettle temperature | `temperature` |
| `INFLUXDB_KETTLE_SENSOR_LABELS` | Human-readable label per topic suffix | - |
| `INFLUXDB_ISPINDEL_MEASUREMENT` | Measurement for iSpindel data | `ispindel` |
| `INFLUXDB_ISPINDEL_SOURCE_TAG` | Tag identifying the device | `source` |
| `INFLUXDB_ISPINDEL_TYPE_TAG` | Tag distinguishing reading types | `field` |
| `INFLUXDB_ISPINDEL_VALUE_FIELD` | Field holding the numeric value | `value` |
| `INFLUXDB_ISPINDEL_TEMP_VALUE` | Type-tag value for temperature | `temperature` |
| `INFLUXDB_ISPINDEL_GRAVITY_VALUE` | Type-tag value for gravity | `gravity` |