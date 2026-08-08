"""Static domain specifications: engine models, operators, airports, fault vocabulary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineSpec:
    engine_type: str
    egt_baseline: float
    egt_noise_std: float
    egt_degradation_range: tuple[float, float]  # (min_slope, max_slope) °C/hour
    egt_warning: float
    egt_critical: float
    vib_baseline: float
    vib_noise_std: float
    vib_degradation_range: tuple[float, float]  # ips/hour
    vib_warning: float
    vib_critical: float
    # Fan shaft speed that reads 100% N1 for this engine. N1Speed is reported as
    # a percentage of it, so the reference is what makes the "% RPM" unit on both
    # Sensor and OperatingLimit mean the same thing.
    n1_reference_rpm: float
    n1_baseline_rpm: float
    n1_noise_std_rpm: float
    fuel_baseline: float
    fuel_noise_std: float


# N1Speed calibration. Each engine's baseline sits at the normal operating rating
# its maintenance manual gives in section 3.3 or 3.4, Max Continuous where the
# manual has that column and top of cruise for the A320. The noise spread is one
# third of the gap up to the manual's Takeoff figure, which is the value the
# matching OperatingLimit row carries as maxValue. Normal running therefore stays
# inside the band and only a three-sigma excursion crosses the limit.
#
#   model      ref rpm  baseline %  takeoff limit %  noise %
#   B737-800     5175       95            104         3.000
#   A320-200     5000       92            104         4.000
#   A321neo      3900       92             97         1.667
#   E190         7400       96            100         1.333
#   A220-300     2800       92            100         2.667
#
# EGT calibration. Every model's EGT series runs on the Takeoff band its manual
# gives in section 3.3 or 3.4, which is the band the matching OperatingLimit row
# carries as minValue and maxValue. Baseline, noise, drift and the warning and
# critical thresholds were all carried across by one affine map per model,
# value -> a * value + b. That map commutes with every comparison in
# maintenance.py and with the spike amplitudes in sensors.py, so the 286
# maintenance events the old thresholds produced survive unchanged. The A320-200
# moved by nothing: its manual is written for the V2500-A1, whose Takeoff column
# reads 620 to 680, and the old baseline already sat inside it.
#
#   model      Takeoff band    a      b      baseline  noise  over max
#   B737-800     900-950      0.800  394.0    920.4    2.80    0.71%
#   A320-200     620-680      1.000    0.0    645.0    3.00    0.47%
#   A321neo     980-1040      1.000  371.0   1005.0    2.80    0.52%
#   E190         870-900      0.400  623.0    879.4    1.28    0.19%
#   A220-300     855-890      0.600  495.0    870.0    1.50    0.43%
#
# FuelFlow calibration. FuelFlow is a plain normal draw with no drift and no
# spikes, and no threshold in maintenance.py reads it. Each baseline sits at the
# midpoint of the manual's Takeoff band and the noise is one sixth of that
# band's width, so three sigma reaches either edge and about one reading in 370
# falls outside.
#
#   model      Takeoff band    baseline  noise   outside band
#   B737-800    1.20-1.50       1.350    0.0500     0.27%
#   A320-200    1.20-1.95       1.575    0.1250     0.25%
#   A321neo     1.50-2.00       1.750    0.0833     0.26%
#   E190        1.00-1.20       1.100    0.0333     0.14%
#   A220-300    1.15-1.35       1.250    0.0333     0.19%
ENGINE_SPECS: dict[str, EngineSpec] = {
    "B737-800": EngineSpec(
        engine_type="CFM56-7B",
        egt_baseline=920.4, egt_noise_std=2.8,
        egt_degradation_range=(0.0016, 0.0112),
        egt_warning=944.4, egt_critical=950.8,
        vib_baseline=0.180, vib_noise_std=0.010,
        vib_degradation_range=(0.00004, 0.00018),
        vib_warning=0.38, vib_critical=0.45,
        n1_reference_rpm=5175.0,
        n1_baseline_rpm=4916.25, n1_noise_std_rpm=155.25,
        fuel_baseline=1.35, fuel_noise_std=0.05,
    ),
    "A320-200": EngineSpec(
        engine_type="CFM56-5B",
        egt_baseline=645.0, egt_noise_std=3.0,
        egt_degradation_range=(0.001, 0.011),
        egt_warning=674.0, egt_critical=682.0,
        vib_baseline=0.150, vib_noise_std=0.008,
        vib_degradation_range=(0.00003, 0.00015),
        vib_warning=0.33, vib_critical=0.40,
        n1_reference_rpm=5000.0,
        n1_baseline_rpm=4600.0, n1_noise_std_rpm=200.0,
        fuel_baseline=1.575, fuel_noise_std=0.125,
    ),
    "A321neo": EngineSpec(
        engine_type="LEAP-1A",
        egt_baseline=1005.0, egt_noise_std=2.8,
        egt_degradation_range=(0.001, 0.010),
        egt_warning=1034.0, egt_critical=1042.0,
        vib_baseline=0.120, vib_noise_std=0.007,
        vib_degradation_range=(0.00002, 0.00012),
        vib_warning=0.29, vib_critical=0.35,
        n1_reference_rpm=3900.0,
        n1_baseline_rpm=3588.0, n1_noise_std_rpm=65.0,
        fuel_baseline=1.75, fuel_noise_std=0.0833,
    ),
    "E190": EngineSpec(
        engine_type="CF34-10E",
        egt_baseline=879.4, egt_noise_std=1.28,
        egt_degradation_range=(0.0008, 0.0052),
        egt_warning=891.8, egt_critical=895.0,
        vib_baseline=0.140, vib_noise_std=0.009,
        vib_degradation_range=(0.00003, 0.00016),
        vib_warning=0.34, vib_critical=0.41,
        n1_reference_rpm=7400.0,
        n1_baseline_rpm=7104.0, n1_noise_std_rpm=98.67,
        fuel_baseline=1.10, fuel_noise_std=0.0333,
    ),
    # PW1500G geared turbofan: the epicyclic gearbox lets the fan turn far slower
    # than a direct-drive fan, so its 100% reference is ~2800 rpm against 3900 to
    # 7400 for the others. The percentages still land in the same band, which is
    # the point of reporting N1 as a percentage.
    "A220-300": EngineSpec(
        engine_type="PW1500G",
        egt_baseline=870.0, egt_noise_std=1.5,
        egt_degradation_range=(0.0006, 0.0054),
        egt_warning=886.2, egt_critical=891.0,
        vib_baseline=0.110, vib_noise_std=0.006,
        vib_degradation_range=(0.00002, 0.00010),
        vib_warning=0.25, vib_critical=0.30,
        n1_reference_rpm=2800.0,
        n1_baseline_rpm=2576.0, n1_noise_std_rpm=74.67,
        fuel_baseline=1.25, fuel_noise_std=0.0333,
    ),
}

# Model allocation across the fleet (proportions must sum to 1.0)
MODEL_DISTRIBUTION: list[tuple[str, float]] = [
    ("B737-800", 0.35),
    ("A320-200", 0.25),
    ("A321neo",  0.20),
    ("E190",     0.10),
    ("A220-300", 0.10),
]

MANUFACTURER: dict[str, str] = {
    "B737-800": "Boeing",
    "A320-200": "Airbus",
    "A321neo":  "Airbus",
    "E190":     "Embraer",
    "A220-300": "Airbus",
}


@dataclass(frozen=True)
class OperatorProfile:
    name: str
    # Multiplies degradation slopes — 1.0 is average, >1.0 means worse maintenance quality
    degradation_multiplier: float
    # Baseline probability that any given flight incurs a delay
    delay_rate: float


OPERATORS: list[OperatorProfile] = [
    OperatorProfile("ExampleAir",  degradation_multiplier=1.00, delay_rate=0.35),
    OperatorProfile("SkyWays",     degradation_multiplier=0.75, delay_rate=0.25),
    OperatorProfile("RegionalCo",  degradation_multiplier=1.50, delay_rate=0.50),
    OperatorProfile("NorthernJet", degradation_multiplier=1.20, delay_rate=0.40),
]


@dataclass(frozen=True)
class AirportSpec:
    airport_id: str
    name: str
    city: str
    country: str
    iata: str
    icao: str
    lat: float
    lon: float
    is_hub: bool  # hubs get more routes and higher flight frequency


AIRPORTS: list[AirportSpec] = [
    AirportSpec("AP001", "John F. Kennedy International Airport",        "New York",        "USA", "JFK", "KJFK",  40.6413, -73.7781, True),
    AirportSpec("AP002", "Los Angeles International Airport",            "Los Angeles",     "USA", "LAX", "KLAX",  33.9416,-118.4085, True),
    AirportSpec("AP003", "O'Hare International Airport",                 "Chicago",         "USA", "ORD", "KORD",  41.9742, -87.9073, True),
    AirportSpec("AP004", "Dallas/Fort Worth International Airport",      "Dallas",          "USA", "DFW", "KDFW",  32.8998, -97.0403, True),
    AirportSpec("AP005", "Hartsfield–Jackson Atlanta International",     "Atlanta",         "USA", "ATL", "KATL",  33.6407, -84.4277, True),
    AirportSpec("AP006", "Denver International Airport",                  "Denver",          "USA", "DEN", "KDEN",  39.8561,-104.6737, True),
    AirportSpec("AP007", "San Francisco International Airport",           "San Francisco",   "USA", "SFO", "KSFO",  37.6213,-122.3790, True),
    AirportSpec("AP008", "Seattle-Tacoma International Airport",          "Seattle",         "USA", "SEA", "KSEA",  47.4502,-122.3088, True),
    AirportSpec("AP009", "Miami International Airport",                   "Miami",           "USA", "MIA", "KMIA",  25.7959, -80.2870, True),
    AirportSpec("AP010", "Boston Logan International Airport",            "Boston",          "USA", "BOS", "KBOS",  42.3656, -71.0096, True),
    AirportSpec("AP011", "Phoenix Sky Harbor International Airport",      "Phoenix",         "USA", "PHX", "KPHX",  33.4373,-112.0078, False),
    AirportSpec("AP012", "Minneapolis–Saint Paul International Airport",  "Minneapolis",     "USA", "MSP", "KMSP",  44.8820, -93.2218, False),
    AirportSpec("AP013", "Detroit Metropolitan Wayne County Airport",     "Detroit",         "USA", "DTW", "KDTW",  42.2162, -83.3554, False),
    AirportSpec("AP014", "Portland International Airport",                "Portland",        "USA", "PDX", "KPDX",  45.5898,-122.5951, False),
    AirportSpec("AP015", "Salt Lake City International Airport",          "Salt Lake City",  "USA", "SLC", "KSLC",  40.7884,-111.9778, False),
    AirportSpec("AP016", "Philadelphia International Airport",            "Philadelphia",    "USA", "PHL", "KPHL",  39.8719, -75.2411, False),
    AirportSpec("AP017", "Tampa International Airport",                   "Tampa",           "USA", "TPA", "KTPA",  27.9755, -82.5332, False),
    AirportSpec("AP018", "Charlotte Douglas International Airport",       "Charlotte",       "USA", "CLT", "KCLT",  35.2141, -80.9431, False),
    AirportSpec("AP019", "Las Vegas Harry Reid International Airport",    "Las Vegas",       "USA", "LAS", "KLAS",  36.0840,-115.1537, False),
    AirportSpec("AP020", "Houston George Bush Intercontinental Airport",  "Houston",         "USA", "IAH", "KIAH",  29.9902, -95.3368, False),
    AirportSpec("AP021", "Washington Dulles International Airport",       "Washington DC",   "USA", "IAD", "KIAD",  38.9445, -77.4558, False),
    AirportSpec("AP022", "Ronald Reagan Washington National Airport",     "Arlington",       "USA", "DCA", "KDCA",  38.8512, -77.0402, False),
    AirportSpec("AP023", "San Diego International Airport",               "San Diego",       "USA", "SAN", "KSAN",  32.7338,-117.1933, False),
    AirportSpec("AP024", "Baltimore Washington International Airport",    "Baltimore",       "USA", "BWI", "KBWI",  39.1754, -76.6683, False),
    AirportSpec("AP025", "Austin-Bergstrom International Airport",        "Austin",          "USA", "AUS", "KAUS",  30.1975, -97.6664, False),
    AirportSpec("AP026", "Nashville International Airport",               "Nashville",       "USA", "BNA", "KBNA",  36.1245, -86.6782, False),
    AirportSpec("AP027", "Raleigh-Durham International Airport",          "Raleigh",         "USA", "RDU", "KRDU",  35.8776, -78.7875, False),
    AirportSpec("AP028", "Kansas City International Airport",             "Kansas City",     "USA", "MCI", "KMCI",  39.2976, -94.7139, False),
    AirportSpec("AP029", "New Orleans Louis Armstrong International",     "New Orleans",     "USA", "MSY", "KMSY",  29.9934, -90.2580, False),
    AirportSpec("AP030", "Cleveland Hopkins International Airport",       "Cleveland",       "USA", "CLE", "KCLE",  41.4117, -81.8498, False),
    AirportSpec("AP031", "Indianapolis International Airport",            "Indianapolis",    "USA", "IND", "KIND",  39.7173, -86.2944, False),
    AirportSpec("AP032", "Pittsburgh International Airport",              "Pittsburgh",      "USA", "PIT", "KPIT",  40.4915, -80.2329, False),
    AirportSpec("AP033", "St. Louis Lambert International Airport",       "St. Louis",       "USA", "STL", "KSTL",  38.7487, -90.3700, False),
    AirportSpec("AP034", "San Jose International Airport",                "San Jose",        "USA", "SJC", "KSJC",  37.3626,-121.9290, False),
    AirportSpec("AP035", "Sacramento International Airport",              "Sacramento",      "USA", "SMF", "KSMF",  38.6954,-121.5908, False),
    AirportSpec("AP036", "Honolulu Daniel K. Inouye International",       "Honolulu",        "USA", "HNL", "PHNL",  21.3187,-157.9224, False),
    AirportSpec("AP037", "Memphis International Airport",                 "Memphis",         "USA", "MEM", "KMEM",  35.0424, -89.9767, False),
    AirportSpec("AP038", "Jacksonville International Airport",            "Jacksonville",    "USA", "JAX", "KJAX",  30.4941, -81.6879, False),
    AirportSpec("AP039", "Milwaukee Mitchell International Airport",      "Milwaukee",       "USA", "MKE", "KMKE",  42.9472, -87.8966, False),
    AirportSpec("AP040", "Albuquerque International Sunport",             "Albuquerque",     "USA", "ABQ", "KABQ",  35.0402,-106.6090, False),
]


# Which sensor type triggers which fault types (fault, severity)
SENSOR_FAULT_MAP: dict[str, list[tuple[str, str]]] = {
    "EGT": [
        ("Overheat", "CRITICAL"),
        ("Overheat", "MAJOR"),
        ("Sensor drift", "MINOR"),
    ],
    "Vibration": [
        ("Vibration exceedance", "CRITICAL"),
        ("Bearing wear", "MAJOR"),
        ("Bearing wear", "MINOR"),
    ],
    "N1Speed": [
        ("Sensor drift", "MINOR"),
        ("Contamination", "MAJOR"),
    ],
    "FuelFlow": [
        ("Fuel starvation", "CRITICAL"),
        ("Contamination", "MAJOR"),
        ("Leak", "MINOR"),
    ],
}

CORRECTIVE_ACTIONS: dict[str, str] = {
    "Overheat":             "Inspected hot section; replaced affected turbine stage and seals",
    "Vibration exceedance": "Balanced rotating assembly; replaced damper pads and inspected bearings",
    "Bearing wear":         "Replaced bearing assembly; flushed and refilled lubrication system",
    "Fuel starvation":      "Cleaned fuel manifold; replaced fuel control unit and high-pressure pump",
    "Contamination":        "Flushed system; replaced filter elements and recalibrated sensors",
    "Sensor drift":         "Replaced sensor unit and recalibrated engine monitoring system",
    "Leak":                 "Located and sealed leak source; pressure-tested and cleared for service",
    "Electrical fault":     "Replaced faulty wiring harness and connector block; re-ran BITE check",
}

COMPONENT_TYPES_BY_SYSTEM: dict[str, list[str]] = {
    "Engine": ["Turbine", "Compressor", "Combustor", "Nozzle", "Control Unit"],
    "Avionics": ["Flight Computer", "Navigation Unit", "Communication Unit"],
    "Hydraulics": ["Pump", "Filter", "Reservoir", "Actuator"],
}
