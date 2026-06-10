"""
Correlated maintenance event generation.

Events are triggered probabilistically when sensor readings exceed model-specific
warning and critical thresholds. The fault type is determined by which sensor
crossed its threshold, and severity follows from how far above the threshold it went.

This produces the causal signal the GDS algorithms need: aircraft with steeper
degradation slopes accumulate more events and form distinct kNN/Louvain clusters.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np

from .config import GeneratorConfig
from .fleet import AircraftNode, ComponentNode, SystemNode
from .sensors import DegradationProfile, egt_values_for_system, vib_values_for_system
from .specs import (
    CORRECTIVE_ACTIONS,
    ENGINE_SPECS,
    SENSOR_FAULT_MAP,
    EngineSpec,
)

# Per-reading probability of generating a maintenance event when above threshold
_WARN_EVENT_PROB = 0.015
_CRIT_EVENT_PROB = 0.060

# Minimum hours between events on the same engine (prevents unrealistic clusters)
_MIN_EVENT_SPACING_HOURS = 72


def _fault_and_severity(
    sensor_type: str,
    value: float,
    warning: float,
    critical: float,
    rng: random.Random,
) -> tuple[str, str]:
    options = SENSOR_FAULT_MAP[sensor_type]
    if value >= critical:
        # Highest severity option for this sensor type
        for fault, sev in options:
            if sev == "CRITICAL":
                return fault, sev
    # Warning level — pick MAJOR or MINOR randomly, weighted toward MAJOR
    above_warn = [o for o in options if o[1] in ("MAJOR", "MINOR")]
    weights = [2 if sev == "MAJOR" else 1 for _, sev in above_warn]
    return rng.choices(above_warn, weights=weights)[0]


def _pick_component(system: SystemNode, rng: random.Random) -> ComponentNode:
    return rng.choice(system.components)


def generate_maintenance_events(
    aircraft: AircraftNode,
    engine_profiles: dict[str, DegradationProfile],  # system_id -> profile
    config: GeneratorConfig,
    event_counter: list[int],  # mutable counter for global event IDs
    rng_np: np.random.Generator,
    rng: random.Random,
) -> list[dict]:
    """
    Scan each engine's sensor series for threshold exceedances and emit
    maintenance events with realistic fault types and corrective actions.
    """
    spec: EngineSpec = ENGINE_SPECS[aircraft.model]
    events: list[dict] = []

    for system in aircraft.systems:
        if system.type != "Engine":
            continue

        profile = engine_profiles.get(system.system_id)
        if profile is None:
            continue

        egt_vals = egt_values_for_system(aircraft, system, profile, config, rng_np)
        vib_vals = vib_values_for_system(aircraft, system, profile, config, rng_np)

        last_event_hour: dict[str, int] = {}  # sensor_type -> last event hour

        for h in range(config.n_hours):
            # Check EGT threshold
            egt = egt_vals[h]
            if egt >= spec.egt_warning:
                p = _CRIT_EVENT_PROB if egt >= spec.egt_critical else _WARN_EVENT_PROB
                last_h = last_event_hour.get("EGT", -_MIN_EVENT_SPACING_HOURS)
                if h - last_h >= _MIN_EVENT_SPACING_HOURS and rng.random() < p:
                    fault, severity = _fault_and_severity(
                        "EGT", egt, spec.egt_warning, spec.egt_critical, rng
                    )
                    events.append(
                        _make_event(aircraft, system, fault, severity, h, config, event_counter, rng)
                    )
                    last_event_hour["EGT"] = h

            # Check Vibration threshold
            vib = vib_vals[h]
            if vib >= spec.vib_warning:
                p = _CRIT_EVENT_PROB if vib >= spec.vib_critical else _WARN_EVENT_PROB
                last_h = last_event_hour.get("Vibration", -_MIN_EVENT_SPACING_HOURS)
                if h - last_h >= _MIN_EVENT_SPACING_HOURS and rng.random() < p:
                    fault, severity = _fault_and_severity(
                        "Vibration", vib, spec.vib_warning, spec.vib_critical, rng
                    )
                    events.append(
                        _make_event(aircraft, system, fault, severity, h, config, event_counter, rng)
                    )
                    last_event_hour["Vibration"] = h

    return events


def _make_event(
    aircraft: AircraftNode,
    system: SystemNode,
    fault: str,
    severity: str,
    hour_offset: int,
    config: GeneratorConfig,
    event_counter: list[int],
    rng: random.Random,
) -> dict:
    event_counter[0] += 1
    event_id = f"ME{event_counter[0]:04d}"
    component = _pick_component(system, rng)
    reported_at = config.start_date + timedelta(hours=hour_offset)
    return {
        ":ID(MaintenanceEvent)": event_id,
        "component_id": component.component_id,
        "system_id": system.system_id,
        "aircraft_id": aircraft.aircraft_id,
        "fault": fault,
        "severity": severity,
        "reported_at": reported_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "corrective_action": CORRECTIVE_ACTIONS.get(fault, "Inspected and cleared"),
    }
