"""Dataset generation commands, registered on the populate-aircraft-db CLI."""

from __future__ import annotations

import csv
import random
import time
from pathlib import Path

import numpy as np
import typer
from rich.console import Console
from rich.table import Table

from .config import GeneratorConfig
from .fleet import AircraftNode, generate_fleet
from .maintenance import generate_maintenance_events
from .operations import generate_operations
from .removals import generate_removals
from .sensors import generate_engine_readings
from .writers import write_csv

console = Console()

# workshop-setup/aircraft_digital_twin_data, relative to this file
_DEFAULT_OUTPUT = Path(__file__).resolve().parents[4] / "aircraft_digital_twin_data"


def _fleet_rows(fleet: list[AircraftNode]) -> tuple[
    list[dict], list[dict], list[dict], list[dict],
    list[dict], list[dict], list[dict],
]:
    """Flatten fleet topology into CSV-ready row lists."""
    aircraft_rows, system_rows, component_rows, sensor_rows = [], [], [], []
    rels_aircraft_system, rels_system_component, rels_system_sensor = [], [], []

    for ac in fleet:
        aircraft_rows.append(
            {
                ":ID(Aircraft)": ac.aircraft_id,
                "tail_number": ac.tail_number,
                "icao24": ac.icao24,
                "model": ac.model,
                "manufacturer": ac.manufacturer,
                "operator": ac.operator,
            }
        )
        for sys in ac.systems:
            system_rows.append(
                {
                    ":ID(System)": sys.system_id,
                    "aircraft_id": ac.aircraft_id,
                    "type": sys.type,
                    "name": sys.name,
                }
            )
            rels_aircraft_system.append(
                {":START_ID(Aircraft)": ac.aircraft_id, ":END_ID(System)": sys.system_id}
            )
            for comp in sys.components:
                component_rows.append(
                    {
                        ":ID(Component)": comp.component_id,
                        "system_id": sys.system_id,
                        "type": comp.type,
                        "name": comp.name,
                    }
                )
                rels_system_component.append(
                    {":START_ID(System)": sys.system_id, ":END_ID(Component)": comp.component_id}
                )
            for sensor in sys.sensors:
                sensor_rows.append(
                    {
                        ":ID(Sensor)": sensor.sensor_id,
                        "system_id": sys.system_id,
                        "type": sensor.type,
                        "name": sensor.name,
                        "unit": sensor.unit,
                    }
                )
                rels_system_sensor.append(
                    {":START_ID(System)": sys.system_id, ":END_ID(Sensor)": sensor.sensor_id}
                )

    return (
        aircraft_rows, system_rows, component_rows, sensor_rows,
        rels_aircraft_system, rels_system_component, rels_system_sensor,
    )


def generate(
    aircraft: int = typer.Option(100, "--aircraft", "-a", help="Number of aircraft to generate."),
    airports: int = typer.Option(40, "--airports", help="Number of airports (max 40)."),
    days: int = typer.Option(90, "--days", "-d", help="Days of sensor telemetry."),
    seed: int = typer.Option(42, "--seed", help="Random seed for reproducibility."),
    reading_interval: int = typer.Option(
        1,
        "--reading-interval",
        min=1,
        help=(
            "Hours between readings written to nodes_readings.csv. "
            "Series are always generated hourly internally, so all other "
            "CSVs are identical regardless of interval."
        ),
    ),
    readings_only: bool = typer.Option(
        False,
        "--readings-only",
        help=(
            "Run the full seeded pipeline but write only nodes_readings.csv. "
            "Use with --reading-interval to regenerate the readings file at a "
            "different resolution, consistent with the other CSVs."
        ),
    ),
    output: Path = typer.Option(
        _DEFAULT_OUTPUT, "--output", "-o", help="Output directory for CSV files."
    ),
) -> None:
    """Generate all CSV files for the aircraft digital twin dataset."""
    airports = min(airports, 40)
    output.mkdir(parents=True, exist_ok=True)

    config = GeneratorConfig(
        n_aircraft=aircraft,
        n_airports=airports,
        n_days=days,
        seed=seed,
        output_dir=output,
        reading_interval_hours=reading_interval,
    )

    def _write(rows: list[dict], path: Path) -> None:
        """Write a CSV unless --readings-only suppresses non-readings output."""
        if not readings_only:
            write_csv(rows, path)

    rng = random.Random(seed)
    rng_np = np.random.default_rng(seed)

    t0 = time.time()
    console.print("\n[bold]Aircraft Digital Twin Generator[/bold]")
    console.print(
        f"  Aircraft: {aircraft}  |  Airports: {airports}  |  Days: {days}  |  Seed: {seed}"
    )
    console.print(f"  Reading interval: {reading_interval}h"
                  + ("  |  readings-only mode" if readings_only else ""))
    console.print(f"  Output:   {output.resolve()}\n")

    # ── 1. Fleet topology ───────────────────────────────────────────────────
    console.print("[cyan]Generating fleet topology…[/cyan]")
    fleet = generate_fleet(config)
    (
        aircraft_rows, system_rows, component_rows, sensor_rows,
        rels_ac_sys, rels_sys_comp, rels_sys_sens,
    ) = _fleet_rows(fleet)

    _write(aircraft_rows,  output / "nodes_aircraft.csv")
    _write(system_rows,    output / "nodes_systems.csv")
    _write(component_rows, output / "nodes_components.csv")
    _write(sensor_rows,    output / "nodes_sensors.csv")
    _write(rels_ac_sys,    output / "rels_aircraft_system.csv")
    _write(rels_sys_comp,  output / "rels_system_component.csv")
    _write(rels_sys_sens,  output / "rels_system_sensor.csv")
    console.print(
        f"  [green]✓[/green] {len(aircraft_rows)} aircraft  "
        f"{len(system_rows)} systems  "
        f"{len(component_rows)} components  "
        f"{len(sensor_rows)} sensors"
    )

    # ── 2. Sensor readings + maintenance events ─────────────────────────────
    console.print("[cyan]Generating sensor readings and maintenance events…[/cyan]")

    reading_fields = ["reading_id", "sensor_id", "ts", "value"]
    maintenance_rows: list[dict] = []
    event_counter = [0]
    total_readings = 0

    # Write readings incrementally per aircraft to keep memory bounded
    readings_path = output / "nodes_readings.csv"
    with readings_path.open("w", newline="", encoding="utf-8") as rf:
        rw = csv.DictWriter(rf, fieldnames=reading_fields)
        rw.writeheader()

        for ac_idx, ac in enumerate(fleet):
            engine_profiles: dict[str, object] = {}

            for system in ac.systems:
                if system.type != "Engine":
                    continue

                profile, rows = generate_engine_readings(ac, system, config, rng_np)
                engine_profiles[system.system_id] = profile
                rw.writerows(rows)
                total_readings += len(rows)

            # Maintenance events must always run: they consume the numpy RNG
            # stream between aircraft, keeping readings reproducible across modes.
            ac_events = generate_maintenance_events(
                ac, engine_profiles, config, event_counter, rng_np, rng
            )
            maintenance_rows.extend(ac_events)

            if (ac_idx + 1) % 20 == 0 or ac_idx + 1 == len(fleet):
                console.print(
                    f"  [dim]{ac_idx + 1}/{len(fleet)} aircraft processed — "
                    f"{total_readings:,} readings, {len(maintenance_rows)} events so far[/dim]"
                )

    console.print(
        f"  [green]✓[/green] {total_readings:,} sensor readings  "
        f"{len(maintenance_rows)} maintenance events"
    )

    # Write maintenance nodes and relationships
    rels_comp_event: list[dict] = []
    rels_event_system: list[dict] = []
    rels_event_aircraft: list[dict] = []

    for evt in maintenance_rows:
        rels_comp_event.append(
            {":START_ID(Component)": evt["component_id"], ":END_ID(MaintenanceEvent)": evt[":ID(MaintenanceEvent)"]}
        )
        rels_event_system.append(
            {":START_ID(MaintenanceEvent)": evt[":ID(MaintenanceEvent)"], ":END_ID(System)": evt["system_id"]}
        )
        rels_event_aircraft.append(
            {":START_ID(MaintenanceEvent)": evt[":ID(MaintenanceEvent)"], ":END_ID(Aircraft)": evt["aircraft_id"]}
        )

    _write(maintenance_rows,    output / "nodes_maintenance.csv")
    _write(rels_comp_event,     output / "rels_component_event.csv")
    _write(rels_event_system,   output / "rels_event_system.csv")
    _write(rels_event_aircraft, output / "rels_event_aircraft.csv")

    # ── 3. Flight operations ────────────────────────────────────────────────
    console.print("[cyan]Generating flights, airports, and delays…[/cyan]")
    (
        airport_rows, flight_rows, delay_rows,
        rels_ac_flight, rels_dep, rels_arr, rels_delay,
    ) = generate_operations(fleet, config, rng)

    _write(airport_rows,   output / "nodes_airports.csv")
    _write(flight_rows,    output / "nodes_flights.csv")
    _write(delay_rows,     output / "nodes_delays.csv")
    _write(rels_ac_flight, output / "rels_aircraft_flight.csv")
    _write(rels_dep,       output / "rels_flight_departure.csv")
    _write(rels_arr,       output / "rels_flight_arrival.csv")
    _write(rels_delay,     output / "rels_flight_delay.csv")
    console.print(
        f"  [green]✓[/green] {len(airport_rows)} airports  "
        f"{len(flight_rows):,} flights  "
        f"{len(delay_rows):,} delays"
    )

    # ── 4. Component removals ───────────────────────────────────────────────
    console.print("[cyan]Generating component removals…[/cyan]")
    removal_rows, rels_ac_removal, rels_comp_removal = generate_removals(
        fleet, maintenance_rows, config, rng
    )
    _write(removal_rows,      output / "nodes_removals.csv")
    _write(rels_ac_removal,   output / "rels_aircraft_removal.csv")
    _write(rels_comp_removal, output / "rels_component_removal.csv")
    console.print(f"  [green]✓[/green] {len(removal_rows)} removals")

    # ── Summary ─────────────────────────────────────────────────────────────
    if readings_only:
        console.print(
            f"\n[yellow]readings-only mode:[/yellow] only nodes_readings.csv was written "
            f"({total_readings:,} readings at {reading_interval}h interval)."
        )
    elapsed = time.time() - t0
    _print_summary(config, fleet, total_readings, maintenance_rows, flight_rows, delay_rows, elapsed)


def _print_summary(
    config: GeneratorConfig,
    fleet: list[AircraftNode],
    n_readings: int,
    maintenance_rows: list[dict],
    flight_rows: list[dict],
    delay_rows: list[dict],
    elapsed: float,
) -> None:
    from collections import Counter

    console.print()
    table = Table(title="Generation Complete", show_header=True)
    table.add_column("Entity", style="cyan")
    table.add_column("Count", justify="right")

    table.add_row("Aircraft",           str(len(fleet)))
    table.add_row("Systems",            str(sum(len(ac.systems) for ac in fleet)))
    table.add_row("Components",         str(sum(len(s.components) for ac in fleet for s in ac.systems)))
    table.add_row("Sensors",            str(sum(len(s.sensors) for ac in fleet for s in ac.systems)))
    table.add_row("Sensor Readings",    f"{n_readings:,}")
    table.add_row("Maintenance Events", str(len(maintenance_rows)))
    table.add_row("Airports",           str(config.n_airports))
    table.add_row("Flights",            f"{len(flight_rows):,}")
    table.add_row("Delays",             f"{len(delay_rows):,}")

    console.print(table)

    # Per-model breakdown
    model_counts = Counter(ac.model for ac in fleet)
    console.print("\n[bold]Fleet composition:[/bold]")
    for model, count in sorted(model_counts.items()):
        console.print(f"  {model:<12} {count}")

    # Maintenance severity breakdown
    sev_counts = Counter(row["severity"] for row in maintenance_rows)
    console.print("\n[bold]Maintenance severity:[/bold]")
    for sev in ["CRITICAL", "MAJOR", "MINOR"]:
        console.print(f"  {sev:<10} {sev_counts.get(sev, 0)}")

    # Degradation spread (operator breakdown)
    op_counts = Counter(ac.operator for ac in fleet)
    console.print("\n[bold]Aircraft by operator:[/bold]")
    for op, count in sorted(op_counts.items()):
        console.print(f"  {op:<14} {count}")

    m, s = divmod(int(elapsed), 60)
    elapsed_str = f"{m}m {s:02d}s" if m else f"{s}s"
    console.print(f"\n[green]Done in {elapsed_str}.[/green]")
    console.print(
        "[dim]GDS notes: cross-model kNN clusters are most visible with ≥80 aircraft. "
        "Louvain community count scales with n_aircraft × degradation variance.[/dim]\n"
    )


def validate(
    directory: Path = typer.Argument(
        _DEFAULT_OUTPUT, help="Directory containing generated CSV files."
    ),
) -> None:
    """Check referential integrity of generated CSV files."""
    console.print(f"\n[bold]Validating CSV files in:[/bold] {directory.resolve()}\n")

    errors: list[str] = []

    def load_ids(filename: str, id_col: str) -> set[str]:
        path = directory / filename
        if not path.exists():
            errors.append(f"Missing file: {filename}")
            return set()
        with path.open() as f:
            return {row[id_col] for row in csv.DictReader(f)}

    def check_fk(filename: str, col: str, valid_ids: set[str], label: str) -> None:
        path = directory / filename
        if not path.exists():
            return
        with path.open() as f:
            for i, row in enumerate(csv.DictReader(f), start=2):
                val = row.get(col)
                if val and val not in valid_ids:
                    errors.append(f"{filename}:{i} — {col}={val!r} not in {label}")

    aircraft_ids  = load_ids("nodes_aircraft.csv",    ":ID(Aircraft)")
    system_ids    = load_ids("nodes_systems.csv",      ":ID(System)")
    component_ids = load_ids("nodes_components.csv",   ":ID(Component)")
    sensor_ids    = load_ids("nodes_sensors.csv",      ":ID(Sensor)")
    airport_ids   = load_ids("nodes_airports.csv",     ":ID(Airport)")
    flight_ids    = load_ids("nodes_flights.csv",      ":ID(Flight)")
    delay_ids     = load_ids("nodes_delays.csv",       ":ID(Delay)")
    event_ids     = load_ids("nodes_maintenance.csv",  ":ID(MaintenanceEvent)")

    check_fk("rels_aircraft_system.csv",  ":START_ID(Aircraft)", aircraft_ids,  "Aircraft")
    check_fk("rels_aircraft_system.csv",  ":END_ID(System)",     system_ids,    "System")
    check_fk("rels_system_component.csv", ":START_ID(System)",   system_ids,    "System")
    check_fk("rels_system_component.csv", ":END_ID(Component)",  component_ids, "Component")
    check_fk("rels_system_sensor.csv",    ":START_ID(System)",   system_ids,    "System")
    check_fk("rels_system_sensor.csv",    ":END_ID(Sensor)",     sensor_ids,    "Sensor")
    check_fk("rels_flight_departure.csv", ":END_ID(Airport)",    airport_ids,   "Airport")
    check_fk("rels_flight_arrival.csv",   ":END_ID(Airport)",    airport_ids,   "Airport")
    check_fk("rels_flight_delay.csv",     ":START_ID(Flight)",   flight_ids,    "Flight")
    check_fk("rels_flight_delay.csv",     ":END_ID(Delay)",      delay_ids,     "Delay")
    check_fk("rels_component_event.csv",  ":END_ID(MaintenanceEvent)", event_ids, "MaintenanceEvent")

    if errors:
        console.print(f"[red]Found {len(errors)} referential integrity error(s):[/red]")
        for e in errors[:20]:
            console.print(f"  [red]✗[/red] {e}")
        if len(errors) > 20:
            console.print(f"  [dim]… and {len(errors) - 20} more[/dim]")
        raise typer.Exit(1)
    else:
        console.print("[green]✓ All referential integrity checks passed.[/green]\n")
