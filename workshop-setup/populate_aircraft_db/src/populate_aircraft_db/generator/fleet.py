"""Generate the static fleet topology: Aircraft, System, Component, Sensor nodes."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from itertools import islice

from .config import GeneratorConfig
from .specs import (
    COMPONENT_TYPES_BY_SYSTEM,
    ENGINE_SPECS,
    MANUFACTURER,
    MODEL_DISTRIBUTION,
    OPERATORS,
    OperatorProfile,
)

# ICAO 24-bit address characters
_ICAO_CHARS = "0123456789abcdef"

# US tail number prefix pool
_TAIL_PREFIXES = list("NNNNN")  # all start with N for US registration


def _icao24(rng: random.Random) -> str:
    return "".join(rng.choices(_ICAO_CHARS, k=6))


def _tail_number(index: int) -> str:
    # N + 5-digit numeric suffix, guaranteed unique
    return f"N{index + 10000:05d}"


@dataclass
class SensorNode:
    sensor_id: str
    system_id: str
    type: str  # EGT | Vibration | N1Speed | FuelFlow
    name: str
    unit: str


@dataclass
class ComponentNode:
    component_id: str
    system_id: str
    type: str
    name: str


@dataclass
class SystemNode:
    system_id: str
    aircraft_id: str
    type: str  # Engine | Avionics | Hydraulics
    name: str
    engine_index: int | None  # 1 or 2 for Engine systems, None otherwise
    sensors: list[SensorNode] = field(default_factory=list)
    components: list[ComponentNode] = field(default_factory=list)


@dataclass
class AircraftNode:
    aircraft_id: str
    tail_number: str
    icao24: str
    model: str
    manufacturer: str
    operator: str
    operator_profile: OperatorProfile
    systems: list[SystemNode] = field(default_factory=list)


_SENSOR_TYPES: list[tuple[str, str, str]] = [
    ("EGT",      "Exhaust Gas Temperature", "C"),
    ("Vibration","Engine Vibration",         "ips"),
    ("N1Speed",  "Fan Speed N1",             "rpm"),
    ("FuelFlow", "Fuel Flow",                "kg/s"),
]

_ENGINE_NAMES: dict[str, list[str]] = {
    "B737-800": ["CFM56-7B #1", "CFM56-7B #2"],
    "A320-200": ["CFM56-5B #1", "CFM56-5B #2"],
    "A321neo":  ["LEAP-1A #1",  "LEAP-1A #2"],
    "E190":     ["CF34-10E #1", "CF34-10E #2"],
    "A220-300": ["PW1500G #1",  "PW1500G #2"],
}


def _build_system(
    aircraft_id: str,
    system_index: int,
    system_type: str,
    system_name: str,
    engine_index: int | None,
) -> SystemNode:
    system_id = f"{aircraft_id}-S{system_index:02d}"
    system = SystemNode(
        system_id=system_id,
        aircraft_id=aircraft_id,
        type=system_type,
        name=system_name,
        engine_index=engine_index,
    )

    # Components
    for comp_index, comp_type in enumerate(
        COMPONENT_TYPES_BY_SYSTEM[system_type], start=1
    ):
        system.components.append(
            ComponentNode(
                component_id=f"{system_id}-C{comp_index:02d}",
                system_id=system_id,
                type=comp_type,
                name=comp_type,
            )
        )

    # Sensors (engines only)
    if system_type == "Engine":
        for sensor_index, (s_type, s_name, s_unit) in enumerate(
            _SENSOR_TYPES, start=1
        ):
            system.sensors.append(
                SensorNode(
                    sensor_id=f"{system_id}-SN{sensor_index:02d}",
                    system_id=system_id,
                    type=s_type,
                    name=s_name,
                    unit=s_unit,
                )
            )

    return system


def _build_aircraft(index: int, model: str, operator: OperatorProfile, rng: random.Random) -> AircraftNode:
    aircraft_id = f"AC{1001 + index}"
    engine_names = _ENGINE_NAMES[model]

    aircraft = AircraftNode(
        aircraft_id=aircraft_id,
        tail_number=_tail_number(index),
        icao24=_icao24(rng),
        model=model,
        manufacturer=MANUFACTURER[model],
        operator=operator.name,
        operator_profile=operator,
    )

    # Two engines
    for i, ename in enumerate(engine_names, start=1):
        aircraft.systems.append(
            _build_system(aircraft_id, i, "Engine", ename, engine_index=i)
        )

    # Avionics and Hydraulics (no sensors)
    aircraft.systems.append(
        _build_system(aircraft_id, 3, "Avionics", "Avionics Suite", engine_index=None)
    )
    aircraft.systems.append(
        _build_system(aircraft_id, 4, "Hydraulics", "Hydraulics System", engine_index=None)
    )

    return aircraft


def generate_fleet(config: GeneratorConfig) -> list[AircraftNode]:
    rng = random.Random(config.seed)

    # Determine model counts from distribution
    models: list[str] = []
    for model, fraction in MODEL_DISTRIBUTION:
        count = round(config.n_aircraft * fraction)
        models.extend([model] * count)
    # Trim or extend to exactly n_aircraft
    models = models[: config.n_aircraft]
    while len(models) < config.n_aircraft:
        models.append(MODEL_DISTRIBUTION[0][0])

    rng.shuffle(models)

    # Assign operators round-robin then shuffle so each gets a similar fleet size
    n_ops = len(OPERATORS)
    operator_assignments = [OPERATORS[i % n_ops] for i in range(config.n_aircraft)]
    rng.shuffle(operator_assignments)

    return [
        _build_aircraft(i, model, op, rng)
        for i, (model, op) in enumerate(zip(models, operator_assignments))
    ]
