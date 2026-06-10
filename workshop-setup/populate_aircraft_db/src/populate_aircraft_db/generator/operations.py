"""
Flight operations and delay generation.

Hub airports receive disproportionately more routes, producing a realistic
hub-and-spoke network where PageRank and Betweenness centrality produce
non-trivial rankings.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from .config import GeneratorConfig
from .fleet import AircraftNode
from .specs import AIRPORTS, AirportSpec

# Flights per aircraft per day — drawn uniformly from this range
_FLIGHTS_PER_DAY_RANGE = (3, 6)

# Minimum block time (hours) and range for variation
_MIN_BLOCK_HOURS = 1.0
_MAX_BLOCK_HOURS = 5.5

# Delay causes with realistic weights
_DELAY_CAUSES = ["Weather", "Maintenance", "NAS", "Carrier"]
_DELAY_WEIGHTS = [0.30, 0.25, 0.25, 0.20]

# Delay duration ranges (minutes) by cause
_DELAY_MINUTES: dict[str, tuple[int, int]] = {
    "Weather":     (20, 180),
    "Maintenance": (30, 240),
    "NAS":         (15,  90),
    "Carrier":     (10,  60),
}

# Hub airports get this weight multiplier in route selection
_HUB_WEIGHT = 4.0


def _build_route_weights(airports: list[AirportSpec]) -> list[float]:
    return [_HUB_WEIGHT if ap.is_hub else 1.0 for ap in airports]


def generate_operations(
    fleet: list[AircraftNode],
    config: GeneratorConfig,
    rng: random.Random,
) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    """
    Returns (airport_nodes, flight_nodes, delay_nodes,
             rels_aircraft_flight, rels_flight_departure, rels_flight_arrival,
             rels_flight_delay)

    Actually returns six lists — see return statement.
    """
    airports = AIRPORTS[: config.n_airports]
    airport_weights = _build_route_weights(airports)
    iata_to_id = {ap.iata: ap.airport_id for ap in airports}

    airport_nodes = [
        {
            ":ID(Airport)": ap.airport_id,
            "name": ap.name,
            "city": ap.city,
            "country": ap.country,
            "iata": ap.iata,
            "icao": ap.icao,
            "lat": ap.lat,
            "lon": ap.lon,
        }
        for ap in airports
    ]

    flight_nodes: list[dict] = []
    delay_nodes: list[dict] = []
    rels_aircraft_flight: list[dict] = []
    rels_departure: list[dict] = []
    rels_arrival: list[dict] = []
    rels_delay: list[dict] = []

    flight_counter = 0
    delay_counter = 0

    for aircraft in fleet:
        delay_rate = aircraft.operator_profile.delay_rate
        # Each aircraft starts at a random hub airport
        current_airport = rng.choices(
            [ap for ap in airports if ap.is_hub]
        )[0]

        for day in range(config.n_days):
            n_flights = rng.randint(*_FLIGHTS_PER_DAY_RANGE)
            # Stagger first departure between 06:00 and 09:00
            current_time = config.start_date + timedelta(
                days=day, hours=rng.uniform(6.0, 9.0)
            )

            for _ in range(n_flights):
                # Weighted destination selection — hubs attract more traffic
                candidates = [ap for ap in airports if ap.airport_id != current_airport.airport_id]
                candidate_weights = [_HUB_WEIGHT if ap.is_hub else 1.0 for ap in candidates]
                destination = rng.choices(candidates, weights=candidate_weights)[0]

                flight_counter += 1
                flight_id = f"FL{flight_counter:05d}"
                block_hours = rng.uniform(_MIN_BLOCK_HOURS, _MAX_BLOCK_HOURS)
                departure = current_time
                arrival = departure + timedelta(hours=block_hours)

                flight_number = f"{aircraft.operator[:2].upper()}{rng.randint(100, 999)}"

                flight_nodes.append(
                    {
                        ":ID(Flight)": flight_id,
                        "flight_number": flight_number,
                        "aircraft_id": aircraft.aircraft_id,
                        "operator": aircraft.operator,
                        "origin": current_airport.iata,
                        "destination": destination.iata,
                        "scheduled_departure": departure.strftime("%Y-%m-%dT%H:%M:%S"),
                        "scheduled_arrival": arrival.strftime("%Y-%m-%dT%H:%M:%S"),
                    }
                )
                rels_aircraft_flight.append(
                    {":START_ID(Aircraft)": aircraft.aircraft_id, ":END_ID(Flight)": flight_id}
                )
                rels_departure.append(
                    {":START_ID(Flight)": flight_id, ":END_ID(Airport)": current_airport.airport_id}
                )
                rels_arrival.append(
                    {":START_ID(Flight)": flight_id, ":END_ID(Airport)": destination.airport_id}
                )

                # Delays — probability scaled by operator quality
                if rng.random() < delay_rate:
                    delay_counter += 1
                    cause = rng.choices(_DELAY_CAUSES, weights=_DELAY_WEIGHTS)[0]
                    lo, hi = _DELAY_MINUTES[cause]
                    minutes = rng.randint(lo, hi)
                    delay_id = f"DLY{delay_counter:05d}"
                    delay_nodes.append(
                        {":ID(Delay)": delay_id, "cause": cause, "minutes": minutes}
                    )
                    rels_delay.append(
                        {":START_ID(Flight)": flight_id, ":END_ID(Delay)": delay_id}
                    )

                current_airport = destination
                # Turnaround time: 45–90 minutes on ground
                current_time = arrival + timedelta(minutes=rng.randint(45, 90))

    return (
        airport_nodes,
        flight_nodes,
        delay_nodes,
        rels_aircraft_flight,
        rels_departure,
        rels_arrival,
        rels_delay,
    )
