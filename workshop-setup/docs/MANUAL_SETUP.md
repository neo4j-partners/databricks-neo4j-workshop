# What the automation builds

**Purpose:** the reference inventory for the workshop's Databricks side. What
the dataset contains, what the provisioning creates from it, and what the
numbers should look like when it worked.

This file used to be a step by step UI walkthrough. It is not one any more, and
that is deliberate. `lab/workshop.py` is the course's one definition of the
catalog, the schemas, the volume, the pipeline, the gold tables, the comments
and the grants, and `lab/workspace_init.sh` calls it. A UI walkthrough sitting
beside that produces a second set of objects built by hand, and the last time
this repository held two copies of the table definitions they disagreed on how
many gold tables there are. See [`../README.md`](../README.md) for what creates
what and for the one command that checks a workspace against the course's
manifest.

---

## What lands in the workspace

| Object | Name |
|--------|------|
| Catalog | `databricks-neo4j-workshop` |
| Volume and gold schema | `aircraft` |
| Bronze and silver schema | `aircraft_pipeline` |
| Lab 5 model schema | `agents` |
| Volume | `raw_data`, at `/Volumes/databricks-neo4j-workshop/aircraft/raw_data/` |
| DLT notebook | `/Shared/workshop/dlt_fleet_etl` |
| DLT pipeline | `Fleet Digital Twin ETL` |
| SQL warehouse | `shared_warehouse` |

Bronze and silver stay in `aircraft_pipeline` without `SELECT`, so a participant
browsing Catalog, or picking tables for a Genie space, sees the eight gold
tables and nothing else.

### The eight gold tables

Published into `aircraft` by the `Fleet Digital Twin ETL` pipeline, in the order
a reader meets them: the fleet, what is on it, what it did, then the two
summaries Lab 4 asks Genie about.

| Table | Comment the Genie space reads |
|-------|-------------------------------|
| `aircraft` | Fleet of aircraft with tail numbers, models, and operators |
| `systems` | Aircraft systems including engines, avionics, and hydraulics |
| `sensors` | Sensors installed on aircraft systems |
| `sensor_readings` | Sensor readings at 4-hour intervals over 90 days, 155,520 rows across 288 sensors |
| `flights` | Flight operations with aircraft, route, schedule, and total delay minutes |
| `maintenance_events` | Maintenance events with fault details and severity |
| `fleet_readiness` | Per-aircraft fleet readiness with mission status |
| `sensor_health` | Per-sensor health summary with anomaly detection |

Ten column comments go on top of those, and eight `GRANT SELECT` statements
follow. The comments are the reason a SQL warehouse is provisioned at all: Lab 4
asks the space questions in English, and a space with no comments answers
plausibly rather than correctly. `workshop.genie_statements()` is the list, and
it is the only list.

### Cluster and libraries

The per-student cluster comes from `voclab.py cluster-ensure`, which reads its
runtime, node type, autotermination and library list out of `lab/course.env`.
The values are there rather than restated here so a change to one of them cannot
half-land.

The Neo4j Spark Connector is why the cluster is classic rather than serverless:
it is a Maven library and serverless compute cannot install one. The connector
also requires Dedicated (single user) access mode, which shared modes do not
provide.

---

## File inventory

27 files travel from `workshop-setup/aircraft_digital_twin_data/` into the
volume. `lab/courseware/` symlinks that directory, `dbx-vocareum-upload` follows
the link into the hash-verified archive, and `workshop.provision_data` uploads
each file. A missing manual is a failure rather than a warning, because a run
that uploaded 22 CSVs and no manual provisions cleanly and breaks two labs
later.

### Core data, Lab 2 notebook 01

| File | Size | Records | Description |
|------|------|---------|-------------|
| `nodes_aircraft.csv` | 4 KB | 36 | Fleet inventory |
| `nodes_systems.csv` | 8 KB | 144 | Aircraft systems |
| `nodes_components.csv` | 32 KB | 612 | System components |
| `rels_aircraft_system.csv` | 4 KB | 144 | Aircraft to System links |
| `rels_system_component.csv` | 20 KB | 612 | System to Component links |

### Full dataset, Lab 2 notebook 02

| File | Size | Records | Description |
|------|------|---------|-------------|
| `nodes_airports.csv` | 4 KB | 40 | Route network airports |
| `nodes_flights.csv` | 1.1 MB | ~14,500 | Flight operations |
| `nodes_delays.csv` | 116 KB | ~5,500 | Delay causes and durations |
| `nodes_maintenance.csv` | 44 KB | ~290 | Maintenance events |
| `nodes_removals.csv` | 16 KB | ~57 | Component removals |
| `rels_aircraft_flight.csv` | 228 KB | ~14,500 | Aircraft to Flight links |
| `rels_aircraft_removal.csv` | 4 KB | ~57 | Aircraft to Removal links |
| `rels_component_event.csv` | 8 KB | ~290 | Component to Event links |
| `rels_component_removal.csv` | 4 KB | ~57 | Removal to Component links |
| `rels_event_aircraft.csv` | 8 KB | ~290 | Event to Aircraft links |
| `rels_event_system.csv` | 8 KB | ~290 | Event to System links |
| `rels_flight_arrival.csv` | 216 KB | ~14,500 | Flight to Airport arrivals |
| `rels_flight_delay.csv` | 100 KB | ~5,500 | Flight to Delay links |
| `rels_flight_departure.csv` | 260 KB | ~14,500 | Flight to Airport departures |

Lab 2 notebook 02 and the GDS appendix are not shipped to Vocareum
participants. Graph Data Science needs Aura Professional and Vocareum
participants are on Aura Free, so shipping either one hands a student a notebook
that cannot run. `VOC_COURSE_NOTEBOOKS` in `lab/course.env` is where that
exclusion is stated.

### Sensor data, Lab 4

| File | Size | Records | Description |
|------|------|---------|-------------|
| `nodes_sensors.csv` | 16 KB | 288 | Sensor metadata |
| `nodes_readings.csv` | 11 MB | 155,520 | Sensor readings every 4 hours over 90 days |
| `rels_system_sensor.csv` | 8 KB | 288 | System to Sensor links |

The readings cover 2024-07-01 to 2024-09-28 at 4-hour intervals: 288 sensors
across 36 aircraft, 4 sensors per engine and 2 engines per aircraft, 540
readings per sensor. The generator writes realistic degradation trends and
anomalies into them, which is what gives Lab 4's `sensor_health` table something
to detect.

| Sensor type | Unit | Description | Typical range |
|-------------|------|-------------|---------------|
| EGT | °C | Exhaust gas temperature | 636-1073 |
| Vibration | ips | Engine vibration | 0.1-2.0 |
| N1Speed | % RPM | Engine fan speed | 75-107 |
| FuelFlow | kg/s | Fuel consumption rate | 1.00-2.09 |

EGT and FuelFlow are calibrated per engine model against that model's takeoff
limits in its maintenance manual, so the ranges above span the whole fleet and no
single aircraft covers them. EGT runs 620-680 on the A320-200 and 980-1040 on the
A321neo. `nodes_operating_limits.csv` carries the band for every model and
parameter, with the manual line each figure came from.

### Maintenance manuals, Lab 3

| File | Size | Description | Required for Lab 3 |
|------|------|-------------|--------------------|
| `MAINTENANCE_A220.md` | ~55 KB | A220-300 maintenance and troubleshooting manual | Optional |
| `MAINTENANCE_A320.md` | ~31 KB | A320-200 maintenance and troubleshooting manual | Yes, used in the notebooks |
| `MAINTENANCE_A321neo.md` | ~41 KB | A321neo maintenance and troubleshooting manual | Optional |
| `MAINTENANCE_B737.md` | ~37 KB | B737-800 maintenance and troubleshooting manual | Optional |
| `MAINTENANCE_E190.md` | ~38 KB | E190 maintenance and troubleshooting manual | Optional |

The Lab 3 notebooks use the A320-200 manual by default. The other four cover the
remaining models in the fleet and back extended exercises. All five upload,
because Lab 3 reads them out of the volume by name and an absent one is a Lab 3
that breaks rather than a manual nobody opened.

---

## Expected counts

Four counts are measured, and they are the CSV record counts the source data
carries into the corresponding gold tables:

| Table | Rows |
|-------|------|
| `aircraft` | 36 |
| `systems` | 144 |
| `sensors` | 288 |
| `sensor_readings` | 155,520 |

The other four gold tables are pipeline output and their row counts have not
been recorded here. Do not infer them from the CSV counts above: `flights`,
`maintenance_events`, `fleet_readiness` and `sensor_health` are the result of
joins and aggregations in `dlt_fleet_etl.py`, and a number written down from a
guess is worse than no number, because the next reader treats it as a
measurement.

`dbx-vocareum-diagnose --expect expected.json` checks presence rather than
counts. Presence is what fails in practice and it is what the gate is for.

---

## Where the dataset comes from

The committed dataset was produced by the generator in
`workshop-setup/populate_aircraft_db/`:

```bash
uv run populate-aircraft-db generate --seed 42 --reading-interval 4
```

`--reading-interval 4` is what keeps `nodes_readings.csv` at 155,520 rows and
about 11 MB, small enough to commit. See
[`../populate_aircraft_db/DATA_GENERATOR.md`](../populate_aircraft_db/DATA_GENERATOR.md)
for the full schema reference and every generator option.
</content>
