"""
Notebook 04 feature computation using pandas instead of Spark.

Reads nodes_readings.csv, nodes_sensors.csv, nodes_systems.csv, and
nodes_maintenance.csv from aircraft_digital_twin_data_v2/, computes
per-aircraft feature vectors, min-max normalizes, and writes *_norm
properties to Aircraft nodes in Neo4j.
"""

from pathlib import Path

import pandas as pd
from neo4j import Driver
from rich.console import Console

console = Console()

_DATA_DIR = Path(__file__).parent.parent.parent.parent / "aircraft_digital_twin_data_v2"

FEATURE_COLS = [
    "avg_egt",
    "stddev_egt",
    "avg_vibration",
    "stddev_vibration",
    "avg_fuel_flow",
    "total_events",
    "critical_events",
]


def _sensor_features(data_dir: Path) -> pd.DataFrame:
    console.print("  Reading sensor CSVs (nodes_readings is ~114 MB)...")
    readings = pd.read_csv(data_dir / "nodes_readings.csv")
    sensors = pd.read_csv(data_dir / "nodes_sensors.csv").rename(
        columns={":ID(Sensor)": "sensor_id"}
    )
    systems = pd.read_csv(data_dir / "nodes_systems.csv").rename(
        columns={":ID(System)": "system_id"}
    )

    merged = (
        readings.merge(sensors[["sensor_id", "system_id", "type"]], on="sensor_id")
        .merge(systems[["system_id", "aircraft_id"]], on="system_id")
    )

    egt = (
        merged[merged["type"] == "EGT"]
        .groupby("aircraft_id")["value"]
        .agg(avg_egt="mean", stddev_egt="std")
    )
    vibration = (
        merged[merged["type"] == "Vibration"]
        .groupby("aircraft_id")["value"]
        .agg(avg_vibration="mean", stddev_vibration="std")
    )
    fuel_flow = (
        merged[merged["type"] == "FuelFlow"]
        .groupby("aircraft_id")["value"]
        .agg(avg_fuel_flow="mean")
    )

    return egt.join(vibration, how="outer").join(fuel_flow, how="outer").reset_index()


def _maintenance_features(data_dir: Path) -> pd.DataFrame:
    maint = pd.read_csv(data_dir / "nodes_maintenance.csv")
    return (
        maint.groupby("aircraft_id")
        .agg(
            total_events=("fault", "count"),
            critical_events=("severity", lambda x: (x == "CRITICAL").sum()),
        )
        .reset_index()
    )


def _minmax_normalize(df: pd.DataFrame) -> pd.DataFrame:
    for col in FEATURE_COLS:
        lo, hi = df[col].min(), df[col].max()
        df[f"{col}_norm"] = (df[col] - lo) / (hi - lo) if hi > lo else 0.0
    return df


def _write_to_neo4j(driver: Driver, features: pd.DataFrame) -> int:
    norm_cols = [f"{c}_norm" for c in FEATURE_COLS]
    rows = [
        {
            "aircraft_id": row["aircraft_id"],
            "props": {c: float(row[c]) for c in norm_cols},
        }
        for _, row in features.iterrows()
    ]
    records, _, _ = driver.execute_query(
        """
        UNWIND $rows AS row
        MATCH (a:Aircraft {aircraft_id: row.aircraft_id})
        SET a += row.props
        RETURN count(a) AS updated
        """,
        rows=rows,
    )
    return int(records[0]["updated"])


def compute_and_write_features(
    driver: Driver, data_dir: Path = _DATA_DIR
) -> int:
    """Compute *_norm features from CSV and write to Neo4j Aircraft nodes."""
    console.rule("[cyan]Notebook 04 — Aircraft Feature Vectors[/cyan]")

    sensor = _sensor_features(data_dir)
    console.print(f"  Sensor features: {len(sensor)} aircraft")

    maint = _maintenance_features(data_dir)
    console.print(f"  Maintenance features: {len(maint)} aircraft")

    features = sensor.merge(maint, on="aircraft_id", how="outer").fillna(0)
    features = _minmax_normalize(features)

    updated = _write_to_neo4j(driver, features)
    console.print(f"  Written *_norm properties to {updated} Aircraft nodes")
    return updated
