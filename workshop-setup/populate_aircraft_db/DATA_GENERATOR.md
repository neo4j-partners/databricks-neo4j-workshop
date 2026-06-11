# Data Generator Guide

The `generate` command produces the complete synthetic Aircraft Digital Twin dataset as CSV files: fleet topology, sensor telemetry with modeled engine degradation, maintenance events correlated with that degradation, flight operations, and component removals. Generation is fully deterministic for a given seed, runs in a few seconds, and needs no Neo4j connection or `.env` configuration.

The dataset lives in `workshop-setup/aircraft_digital_twin_data/`, alongside the five maintenance manuals the fleet models are paired with. The generator writes the CSVs; the manuals are hand-authored and never touched by generation.

## Quick Start

```bash
cd workshop-setup/populate_aircraft_db
uv sync

# Regenerate the committed workshop dataset (writes to ../aircraft_digital_twin_data)
uv run populate-aircraft-db generate --seed 42 --reading-interval 4

# Check referential integrity of the output
uv run populate-aircraft-db validate-csv
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--aircraft`, `-a` | `36` | Number of aircraft in the fleet |
| `--airports` | `40` | Number of airports, capped at 40 |
| `--days`, `-d` | `90` | Days of sensor telemetry, starting 2024-07-01 |
| `--seed` | `42` | Random seed. Same seed and parameters always reproduce identical files |
| `--reading-interval` | `1` | Hours between readings written to `nodes_readings.csv`. See below |
| `--readings-only` | off | Write only `nodes_readings.csv`; leave every other CSV untouched. See below |
| `--output`, `-o` | `../aircraft_digital_twin_data` | Output directory, created if missing |

## Controlling the size of nodes_readings.csv

Sensor readings dominate the dataset size. The row count is:

```
aircraft x 2 engines x 4 sensors x (days x 24 / reading-interval)
```

| `--reading-interval` | Rows (36 aircraft, 90 days) | File size | Use |
|----------------------|-----------------------------|-----------|-----|
| `1` | 622,080 | ~44 MB | Full-resolution Delta table in Databricks. Too large to commit to git |
| `4` | 155,520 | ~11 MB | The committed workshop dataset |
| `8` | 77,760 | ~5.5 MB | Minimal footprint; degradation trends stay visible but anomaly spikes get sparse |

### How `--reading-interval` works

Sensor series are always generated at hourly resolution internally. The interval only controls which rows are written to the CSV: every Nth hourly reading. This has two important consequences:

1. **Every other CSV is identical regardless of interval.** Maintenance events are triggered by the internal hourly series, so the degradation-to-maintenance correlation is preserved, and files such as `nodes_maintenance.csv` and `nodes_flights.csv` are byte-identical whether you generate at 1-hour or 8-hour intervals.
2. **Reading IDs are stable.** The hourly index is kept in `reading_id`, so a 4-hour file contains IDs `R00001, R00005, R00009, ...`, a strict subset of the hourly file's IDs. Loading a coarser file into a graph that already holds a finer one merges cleanly.

## Regenerating only the readings file

`--readings-only` reruns the full seeded pipeline in memory but writes only `nodes_readings.csv`. Combined with `--reading-interval`, this produces a readings file at any resolution that is exactly consistent with the rest of the dataset:

```bash
# Full hourly readings for a larger sensor_readings Delta table in Databricks,
# written somewhere outside the repo so the committed CSVs stay untouched
uv run populate-aircraft-db generate --readings-only --reading-interval 1 -o /tmp/readings_hourly
```

The seed and fleet parameters must match the original run. Changing `--seed`, `--aircraft`, or `--days` produces a different fleet, which invalidates the other CSVs; regenerate everything in that case.

## What gets generated

| Group | Files | Contents |
|-------|-------|----------|
| Fleet topology | `nodes_aircraft.csv`, `nodes_systems.csv`, `nodes_components.csv`, `nodes_sensors.csv` + 3 `rels_*` files | 36 aircraft across five models, each with 2 Engine systems plus Avionics and Hydraulics. Each engine carries 4 sensors: EGT, Vibration, N1Speed, FuelFlow |
| Sensor readings | `nodes_readings.csv` | Time series per sensor with per-engine degradation slopes and random anomaly spikes |
| Maintenance | `nodes_maintenance.csv` + 3 `rels_*` files | Events triggered probabilistically when readings exceed model-specific warning and critical thresholds. Fault type follows from which sensor crossed; severity from how far |
| Operations | `nodes_airports.csv`, `nodes_flights.csv`, `nodes_delays.csv` + 4 `rels_*` files | 3 to 6 flights per aircraft per day over a hub-and-spoke network; weighted delay causes |
| Removals | `nodes_removals.csv` + 2 `rels_*` files | Component removals with work order, technician, warranty, cost, and shop-visit fields |

### Why the data is correlated

Each engine draws a degradation slope from its model's range, scaled by the operator's maintenance quality. Steeper slopes push EGT and vibration readings past warning thresholds sooner, which generates more maintenance events for those aircraft. This causal chain is what makes the workshop's analytics meaningful: GDS algorithms cluster aircraft by degradation behavior, and Genie queries over the readings surface the same exceedances that the maintenance events record.

### Relationship to the maintenance manuals

The five fleet models match the five maintenance manuals in the same directory: `MAINTENANCE_A220.md` (A220-300), `MAINTENANCE_A320.md` (A320-200), `MAINTENANCE_A321neo.md` (A321neo), `MAINTENANCE_B737.md` (B737-800), and `MAINTENANCE_E190.md` (E190). The Lab 3 GraphRAG enrichment chunks these manuals and cross-links them to the generated fleet by model, so generated aircraft, systems, and sensors resolve against manual content. Keep the model set unchanged when modifying the generator, or the manuals stop matching.

## Validation

`validate-csv` checks referential integrity across all generated files, for example that every relationship endpoint exists as a node:

```bash
uv run populate-aircraft-db validate-csv                 # checks the default output directory
uv run populate-aircraft-db validate-csv /tmp/my_output  # or any other directory
```

It exits nonzero and lists offending rows if any check fails.

---

# Architecture and Schema Reference

The dataset feeds two complementary databases. Neo4j holds the relationship-rich graph: topology, maintenance, flights, removals. Databricks Delta Lake holds the high-volume sensor telemetry for SQL analytics and Genie natural language queries. Aircraft, systems, and sensors exist in both as join points.

## Dataset summary

Defaults: 36 aircraft, seed 42, 90 days (2024-07-01 to 2024-09-28), 4-hour reading interval.

| Entity | Count | Neo4j | Databricks |
|--------|-------|-------|------------|
| Aircraft | 36 | yes | yes |
| Systems | 144 | yes | yes |
| Components | 612 | yes | no |
| Sensors | 288 | yes | yes |
| Readings | 155,520 | yes | yes |
| Airports | 40 | yes | no |
| Flights | 14,543 | yes | no |
| Delays | 5,541 | yes | no |
| Maintenance events | 286 | yes | no |
| Removals | 165 | yes | no |

Fleet composition: 35 B737-800, 25 A320-200, 20 A321neo, 10 A220-300, 10 E190, spread evenly across four operators (ExampleAir, SkyWays, RegionalCo, NorthernJet).

## When to use which database

| Query type | Use | Why |
|------------|-----|-----|
| Relationship traversals, topology | Neo4j | Graph optimized for connections and pattern matching |
| Time-series aggregations, statistics | Databricks | Delta Lake optimized for temporal data; SQL analytics |
| Natural language sensor questions | Databricks | Genie queries Delta tables |
| Maintenance and flight correlation | Neo4j | Multi-hop relationships |
| Semantic search over manuals | Neo4j | Vector index over enriched manual chunks |

## Neo4j graph schema

### Node types (10)

| Label | Source CSV | Key properties |
|-------|------------|----------------|
| `Aircraft` | `nodes_aircraft.csv` | `aircraft_id`, `tail_number`, `icao24`, `model`, `manufacturer`, `operator` |
| `System` | `nodes_systems.csv` | `system_id`, `aircraft_id`, `type` (Engine, Avionics, Hydraulics), `name` |
| `Component` | `nodes_components.csv` | `component_id`, `system_id`, `type`, `name` |
| `Sensor` | `nodes_sensors.csv` | `sensor_id`, `system_id`, `type` (EGT, Vibration, N1Speed, FuelFlow), `name`, `unit` |
| `Reading` | `nodes_readings.csv` | `reading_id`, `sensor_id`, `ts`, `value` |
| `Airport` | `nodes_airports.csv` | `airport_id`, `name`, `city`, `iata`, `icao`, `lat`, `lon` |
| `Flight` | `nodes_flights.csv` | `flight_id`, `flight_number`, `aircraft_id`, `origin`, `destination`, scheduled times |
| `Delay` | `nodes_delays.csv` | `delay_id`, `cause` (Weather, Maintenance, NAS, Carrier), `minutes` |
| `MaintenanceEvent` | `nodes_maintenance.csv` | `event_id`, `component_id`, `fault`, `severity` (MINOR, MAJOR, CRITICAL), `reported_at`, `corrective_action` |
| `Removal` | `nodes_removals.csv` | `removal_id`, part/serial, work order, technician, warranty, cost, shop-visit fields |

The Lab 3 enrichment adds further node types from the manuals: `Document`, `Chunk`, `AircraftModel`, `SystemReference`, `ComponentReference`, `Fault`, `MaintenanceProcedure`, `OperatingLimit`.

### Relationship types (13)

| Relationship | Pattern | Source CSV |
|--------------|---------|------------|
| `HAS_SYSTEM` | Aircraft → System | `rels_aircraft_system.csv` |
| `HAS_COMPONENT` | System → Component | `rels_system_component.csv` |
| `HAS_SENSOR` | System → Sensor | `rels_system_sensor.csv` |
| `HAS_READING` | Sensor → Reading | derived from `nodes_readings.csv` |
| `HAS_EVENT` | Component → MaintenanceEvent | `rels_component_event.csv` |
| `AFFECTS_SYSTEM` | MaintenanceEvent → System | `rels_event_system.csv` |
| `AFFECTS_AIRCRAFT` | MaintenanceEvent → Aircraft | `rels_event_aircraft.csv` |
| `OPERATES_FLIGHT` | Aircraft → Flight | `rels_aircraft_flight.csv` |
| `DEPARTS_FROM` | Flight → Airport | `rels_flight_departure.csv` |
| `ARRIVES_AT` | Flight → Airport | `rels_flight_arrival.csv` |
| `HAS_DELAY` | Flight → Delay | `rels_flight_delay.csv` |
| `HAS_REMOVAL` | Aircraft → Removal | `rels_aircraft_removal.csv` |
| `REMOVED_COMPONENT` | Removal → Component | `rels_component_removal.csv` |

### Example Cypher

```cypher
// Average EGT in the 7 days before each critical maintenance event
MATCH (a:Aircraft)-[:HAS_SYSTEM]->(s:System {type:'Engine'})
      -[:HAS_SENSOR]->(sn:Sensor {type:'EGT'})
      -[:HAS_READING]->(r:Reading)
MATCH (s)-[:HAS_COMPONENT]->(c)-[:HAS_EVENT]->(m:MaintenanceEvent {severity:'CRITICAL'})
WHERE datetime(r.ts) <= datetime(m.reported_at)
  AND datetime(r.ts) >= datetime(m.reported_at) - duration('P7D')
RETURN a.tail_number, s.name, m.fault, m.reported_at,
       avg(r.value) AS avg_egt_before_event, count(r) AS readings
ORDER BY avg_egt_before_event DESC
```

## Databricks Delta Lake schema

`databricks-setup` (auto_scripts) uploads the CSVs and manuals to a Unity Catalog volume and creates four Delta tables:

| Table | Source CSV | Rows | Purpose |
|-------|------------|------|---------|
| `sensor_readings` | `nodes_readings.csv` | 155,520 | Time-series telemetry: `reading_id`, `sensor_id`, `ts`, `value` |
| `sensors` | `nodes_sensors.csv` | 288 | Sensor metadata so queries can filter by `type = 'EGT'` instead of cryptic IDs |
| `systems` | `nodes_systems.csv` | 144 | Links sensors to aircraft |
| `aircraft` | `nodes_aircraft.csv` | 36 | Tail numbers, models, operators for human-readable filtering |

The join chain `sensor_readings → sensors → systems → aircraft` lets Genie answer questions like "average EGT by aircraft model":

```sql
SELECT a.model, sen.type,
       AVG(r.value) AS avg_value, STDDEV(r.value) AS stddev_value
FROM sensor_readings r
  JOIN sensors sen ON r.sensor_id = sen.sensor_id
  JOIN systems s   ON sen.system_id = s.system_id
  JOIN aircraft a  ON s.aircraft_id = a.aircraft_id
WHERE sen.type = 'EGT'
GROUP BY a.model, sen.type
ORDER BY avg_value DESC
```

## Data realism

The synthetic data mirrors real-world patterns: sensor behavior modeled on NASA turbofan degradation data, maintenance events on FAA service difficulty reports, and flight operations on BTS on-time performance statistics. Referential integrity is guaranteed by `validate-csv`: unique IDs, valid foreign keys, complete time series, values within realistic per-sensor ranges.
