# A220-300 Maintenance and Troubleshooting Manual

**Document Number:** AMM-A220-2024-001
**Revision:** 1.0
**Effective Date:** October 1, 2024
**Applicability:** A220-300 series aircraft equipped with PW1500G engines
**Operator:** ExampleAir
**Fleet:** N20001, N20002, N20003, N20004, N20005

---

## Document Control

| Rev | Date | Description | Author |
|-----|------|-------------|--------|
| 1.0 | 2024-10-01 | Initial Release | Engineering Division |
| 0.9 | 2024-09-15 | Draft for review | Maintenance Planning |

**NOTICE:** This manual contains proprietary information. Maintenance procedures must be performed by certified personnel only. Always refer to the latest revision of Airbus AMM documentation for authoritative guidance.

---

## Table of Contents

1. [Aircraft Overview](#1-aircraft-overview)
2. [System Architecture](#2-system-architecture)
3. [Engine System - PW1500G](#3-engine-system---pw1500g)
4. [Engine Troubleshooting Procedures](#4-engine-troubleshooting-procedures)
5. [Avionics System](#5-avionics-system)
6. [Hydraulics System](#6-hydraulics-system)
7. [Fault Code Reference](#7-fault-code-reference)
8. [Troubleshooting Decision Trees](#8-troubleshooting-decision-trees)
9. [Scheduled Maintenance Tasks](#9-scheduled-maintenance-tasks)
10. [Appendices](#10-appendices)

---

## 1. Aircraft Overview

### 1.1 General Specifications

| Parameter | Value |
|-----------|-------|
| Aircraft Type | Airbus A220-300 |
| Powerplant | 2x Pratt & Whitney PW1500G Geared Turbofan (GTF) |
| Maximum Takeoff Weight (MTOW) | 70,900 kg (156,200 lb) |
| Maximum Landing Weight (MLW) | 58,500 kg (128,968 lb) |
| Maximum Zero Fuel Weight (MZFW) | 54,200 kg (119,489 lb) |
| Fuel Capacity | 21,805 liters (5,760 US gal) |
| Range | 6,300 km (3,400 nm) |
| Service Ceiling | 41,000 ft |
| Cruise Speed | Mach 0.82 |

### 1.2 Fleet Configuration

The ExampleAir A220-300 fleet consists of five aircraft configured for short to medium-haul operations. Additional operators include SkyWays and NorthernJet.

| Aircraft ID | Registration | ICAO 24 | Entry into Service |
|-------------|--------------|---------|-------------------|
| AC1101 | N20001 | a1b2c3 | March 2022 |
| AC1102 | N20002 | d4e5f6 | June 2022 |
| AC1103 | N20003 | 7a8b9c | October 2022 |
| AC1104 | N20004 | 0d1e2f | February 2023 |
| AC1105 | N20005 | 3a4b5c | May 2023 |

### 1.3 ATA Chapter Reference

This manual covers the following ATA chapters:

| ATA Chapter | System | Reference Section |
|-------------|--------|-------------------|
| ATA 29 | Hydraulic Power | Section 6 |
| ATA 34 | Navigation | Section 5 |
| ATA 71 | Powerplant | Sections 3-4 |
| ATA 72 | Engine | Sections 3-4 |
| ATA 73 | Engine Fuel and Control | Section 3 |
| ATA 77 | Engine Indicating | Section 3 |
| ATA 79 | Oil | Section 3 |

---

## 2. System Architecture

### 2.1 Major System Groups

Each A220-300 aircraft comprises four primary monitored system groups:

```
AIRCRAFT (A220-300)
│
├── ENGINE SYSTEM #1 (PW1500G Left)
│   ├── Fan Module
│   ├── Compressor Stage (High-Pressure)
│   ├── High-Pressure Turbine
│   ├── Main Fuel Pump
│   ├── Thrust Bearing Assembly
│   └── Reduction Gearbox
│
├── ENGINE SYSTEM #2 (PW1500G Right)
│   ├── Fan Module
│   ├── Compressor Stage (High-Pressure)
│   ├── High-Pressure Turbine
│   ├── Main Fuel Pump
│   ├── Thrust Bearing Assembly
│   └── Reduction Gearbox
│
├── AVIONICS SYSTEM
│   ├── Flight Management System (FMS)
│   ├── Air Data and Inertial Reference Unit (ADIRU)
│   └── Navigation Receiver (MMR)
│
└── HYDRAULICS SYSTEM
    ├── Main Hydraulic Pump
    ├── Hydraulic Reservoir
    └── Electrohydraulic Servo Actuators (EHSA)
```

#### 2.1.1 Engine Systems (PW1500G)

The A220-300 is powered by two Pratt & Whitney PW1500G geared turbofan (GTF) engines mounted in underwing nacelles. Each engine produces 23,300 lbf of thrust at takeoff. The defining feature of the PW1500G is its epicyclic planetary reduction gearbox, which decouples the fan shaft from the low-pressure compressor (LPC) shaft. This allows the fan to rotate at approximately 30% lower speed than the LPC, enabling each to operate at its individual aerodynamic optimum — the fan at low speed for maximum propulsive efficiency, and the LPC at higher speed for maximum compression efficiency. The result is a bypass ratio of 12:1, significantly higher than conventional turbofans of comparable thrust class, yielding substantial improvements in specific fuel consumption and noise footprint.

Because of the gearbox architecture, the FADEC monitors two distinct low-pressure shaft speeds: N1 (fan shaft speed) and N1c (LPC shaft speed). These are mechanically coupled through the gearbox at a fixed 3.1:1 ratio but are reported and limit-checked independently. Engine health is continuously monitored via four dedicated sensors per engine measuring exhaust gas temperature (EGT), vibration levels, fan speed (N1), and fuel flow rate. The engine systems account for approximately 68% of all maintenance events in the fleet, with the most common issues being sensor drift, gearbox oil faults, and contamination.

**ATA Reference:** Chapters 71 (Powerplant), 72 (Engine), 73 (Engine Fuel and Control), 77 (Engine Indicating), 79 (Oil)

#### 2.1.2 Avionics System

The avionics system provides flight management, navigation, air data, and inertial reference functions essential for safe aircraft operation. The A220-300 features the Rockwell Collins Pro Line Fusion avionics suite with a fully integrated fly-by-wire (FBW) primary flight control system — a notable distinction within this aircraft class at the time of design. The dual Flight Management Systems (FMS) provide flight planning, 4D navigation, performance calculations, and VNAV/LNAV guidance. Dual Air Data and Inertial Reference Units (ADIRUs) provide redundant altitude, airspeed, attitude, and inertial position data. The Multi-Mode Receiver (MMR) provides VOR/DME, ILS, and GPS position data. All avionics communicate via ARINC 429 digital data buses with comprehensive BITE. Avionics-related maintenance events comprise approximately 11% of fleet issues.

**ATA Reference:** Chapter 34 (Navigation)

#### 2.1.3 Hydraulics System

The A220-300 hydraulic system provides power for primary flight control surface actuation, leading edge devices, trailing edge flaps, landing gear, wheel brakes, thrust reversers, and nose wheel steering. The aircraft employs two primary hydraulic systems designated Left and Right, each operating at 3,000 psi, plus a standby system for emergency backup. A key distinction from conventional hydromechanical designs is the use of electrohydraulic servo actuators (EHSAs) for primary flight control surfaces. EHSAs incorporate integrated position feedback transducers and are commanded directly by the fly-by-wire flight control computers, providing high-bandwidth control with built-in position verification. Hydraulic fluid requires regular monitoring for contamination and proper fluid levels. The hydraulics system represents approximately 21% of maintenance events, with leaks and contamination being the primary concerns.

**ATA Reference:** Chapter 29 (Hydraulic Power)

### 2.2 Engine Health Monitoring

Each PW1500G engine is equipped with four primary monitoring sensors:

| Sensor Type | Parameter | Unit | Location |
|-------------|-----------|------|----------|
| EGT | Exhaust Gas Temperature | °C | Turbine exhaust section |
| Vibration | Engine Vibration | ips (inches/sec) | Fan frame, turbine frame |
| N1Speed | Fan Speed N1 | rpm | Fan shaft (gearbox output) |
| FuelFlow | Fuel Flow | kg/s | Fuel metering valve |

**Sensor Sampling Rate:** Continuous (1 Hz during flight, recorded hourly for trend analysis)

**FADEC Integration:** The PW1500G features Full Authority Digital Engine Control (FADEC) which provides automatic engine parameter management, thrust setting, and fault detection/isolation. The FADEC monitors fan speed (N1) and LPC speed (N1c) as independent parameters. N1Speed in the sensor dataset refers to fan shaft speed (gearbox output). The FADEC also monitors gearbox oil temperature and pressure as first-class parameters distinct from engine oil.

**FADEC Redundancy:** Dual-channel with automatic switchover

### 2.3 Component Identification Schema

Components are identified using the following nomenclature:

```
[Aircraft ID]-[System]-[Component]

Example: AC1101-S01-C03
         │       │    └── Component: High-Pressure Turbine
         │       └─────── System: Engine #1
         └─────────────── Aircraft: AC1101 (N20001)
```

**System Codes:**
- S01: Engine #1 (Left)
- S02: Engine #2 (Right)
- S03: Avionics Suite
- S04: Hydraulics System

---

## 3. Engine System - PW1500G

### 3.1 Engine Specifications

| Parameter | Value |
|-----------|-------|
| Manufacturer | Pratt & Whitney |
| Model | PW1500G |
| Type | Two-spool geared turbofan (GTF) with epicyclic reduction gearbox |
| Thrust Rating | 23,300 lbf (103.6 kN) |
| Bypass Ratio | 12:1 |
| Gear Reduction Ratio | 3.1:1 (fan to LPC) |
| Overall Pressure Ratio | 35:1 |
| Dry Weight | 2,857 kg (6,299 lb) |
| Fan Diameter | 1.87 m (73.5 in) |
| Length | 3.40 m (134 in) |

### 3.2 Component Descriptions

#### 3.2.1 Fan Module
**Part Number:** PW-FM-1500G-100
**ATA Reference:** 72-21

The fan module consists of a single-stage fan with 20 wide-chord hollow titanium blades. Because the fan shaft is driven through the epicyclic reduction gearbox rather than directly from the LPC shaft, the fan is mechanically decoupled from the low-pressure compressor. This decoupling allows the fan to operate at approximately 3,200 rpm at takeoff power while the LPC rotates at approximately 9,900 rpm — a ratio of approximately 3.1:1. The wide-chord hollow blade design increases bypass flow and reduces noise at the lower rotational speed. The fan provides approximately 75% of total engine thrust through the bypass duct.

**Inspection Intervals:**
- Visual inspection: Every 500 flight hours
- Borescope inspection: Every 3,000 flight hours
- Fan blade replacement: On-condition (typically 20,000-25,000 cycles)

**Critical Limits:**
- Fan blade tip clearance: 0.065-0.095 inches cold
- Fan track liner wear limit: 0.120 inches

#### 3.2.2 Compressor Stage (High-Pressure)
**Part Number:** PW-HPC-1500G-200
**ATA Reference:** 72-32

The 8-stage high-pressure compressor (HPC) achieves a pressure ratio of approximately 17:1. Combined with the LPC contribution, the overall engine pressure ratio reaches 35:1. The first two stages feature variable stator vanes (VSV) controlled by the FADEC for optimum performance and stall margin. Note that because the LPC is gearbox-coupled, the HPC sees a different inlet condition profile than in conventional direct-drive turbofans, and VSV scheduling parameters reflect this.

**Common Fault Modes:**
- Compressor stall (vibration exceedance)
- Blade tip erosion (performance degradation)
- Variable stator vane actuator malfunction (sensor drift)
- FOD damage (leading edge nicks and tears)

**Borescope Inspection Points:**
- Stage 1 blades: Leading edge erosion
- Stage 4 blades: Mid-chord cracking
- Stage 8 blades: Tip rub damage

#### 3.2.3 High-Pressure Turbine
**Part Number:** PW-HPT-1500G-300
**ATA Reference:** 72-51

The 2-stage HPT drives the high-pressure compressor through a concentric shaft. Turbine blades feature third-generation single-crystal CMSX-10 alloy construction with ceramic thermal barrier coating (TBC) and advanced film cooling circuits. The nozzle guide vanes use impingement and film cooling. The 2-stage HPT design, compared to the single-stage configuration found in many contemporary engines, allows for higher expansion work per unit of blade stress, contributing to the high overall pressure ratio.

**Operating Limits:**
| Parameter | Normal | Caution | Maximum |
|-----------|--------|---------|---------|
| EGT (Takeoff, 5 min) | < 855°C | 855-880°C | 890°C |
| EGT (Max Continuous) | < 820°C | 820-855°C | 855°C |
| EGT (Start) | — | — | 700°C |

**Note:** PW1500G EGT limits are lower than conventional turbofans of comparable thrust class due to the higher-efficiency combustion cycle and gearbox-enabled LPC aerodynamic optimization. EGT values exceeding these limits have greater consequence given the reduced thermal margin of the high-efficiency combustor design.

**Life-Limited Parts:**
- HPT disk: 20,000 cycles
- HPT blades: On-condition (borescope monitoring)

#### 3.2.4 Main Fuel Pump
**Part Number:** PW-FP-1500G-400
**ATA Reference:** 73-21

The engine-driven fuel pump is a positive displacement gear pump providing metered fuel flow to the combustion chamber through the fuel metering valve (FMV). The electronic engine control (EEC) integrates fuel pump management with the fuel metering valve under FADEC control.

**Flow Rate:** 0.22 - 1.35 kg/s (normal operating range)

**Warning Signs of Degradation:**
- Fluctuating fuel flow readings
- High fuel filter delta-P indication (CAS message)
- Fuel pump inlet pressure low
- Uncommanded thrust changes

#### 3.2.5 Thrust Bearing Assembly
**Part Number:** PW-TB-1500G-500
**ATA Reference:** 72-50

The thrust bearing absorbs axial loads from the high-pressure rotor system. The bearing is a ball-type design with squeeze film damper and oil jet lubrication from the engine oil system. In the GTF architecture, axial loads transmitted through the gearbox must be accounted for in bearing sizing; the thrust bearing is designed to tolerate the additional load path introduced by the gearbox coupling.

**Replacement Criteria:**
- Oil debris analysis: Magnetic chip detector warnings
- Bearing temperature rise > 20°C above baseline
- Vibration increase traceable to bearing frequency
- Oil consumption exceeding 0.4 qt/hr

#### 3.2.6 Reduction Gearbox
**Part Number:** PW-RGB-1500G-600
**ATA Reference:** 72-60

The epicyclic planetary reduction gearbox is the defining component of the GTF architecture. It is located forward of the LPC at the engine inlet and transmits torque from the LPC shaft to the fan shaft at a 3.1:1 reduction ratio. This allows the fan to rotate at approximately 30% of LPC speed, enabling both stages to operate at their individual aerodynamic optima simultaneously.

The gearbox houses a sun gear (LPC shaft-driven), planet gears (typically 5 planetary elements), and a ring gear (connected to the fan shaft). The planet carrier is fixed. The epicyclic arrangement minimizes gearbox diameter while achieving the required torque multiplication. Gearbox weight is approximately 270 kg (595 lb) and represents a significant life-limited component.

See Section 3.5 for detailed gearbox maintenance information.

### 3.3 Normal Operating Parameters

| Parameter | Ground Idle | Flight Idle | Max Continuous | Takeoff |
|-----------|-------------|-------------|----------------|---------|
| N1Speed (% RPM) | 18-24% | 24-30% | 92% | 100% |
| EGT (°C) | 310-380 | 380-440 | 820-855 | 855-890 |
| FuelFlow (kg/s) | 0.09-0.16 | 0.16-0.24 | 0.80-1.10 | 1.15-1.35 |
| Oil Pressure (psi) | 35-60 | 40-70 | 45-75 | 45-75 |
| Oil Temperature (°C) | 50-90 | 60-120 | 80-140 | 80-155 |
| Vibration (ips) | < 0.8 | < 1.2 | < 2.0 | < 2.5 |

**Note on N1Speed:** N1Speed in this table and in the sensor dataset refers to fan shaft speed (gearbox output). N1c (LPC shaft speed) is approximately 3.1 times the fan shaft speed at all power settings and is monitored independently by the FADEC but is not separately captured in the digital twin sensor schema.

**Note on Vibration:** PW1500G vibration limits are lower than conventional turbofans of similar thrust class. The gearbox absorbs fan-rotor excitations before they propagate into the engine core structure, resulting in reduced vibration levels at the engine mounts. Advisory thresholds are set conservatively to detect early gearbox or bearing degradation.

### 3.4 FADEC System

The Full Authority Digital Engine Control (FADEC) provides:

- Automatic engine start sequencing
- Thrust management (N1 limit computation)
- Fuel metering control
- Variable stator vane scheduling
- Transient bleed valve control
- Active clearance control
- Engine limit protection
- Fault detection and isolation
- Gearbox oil pressure and temperature monitoring
- Independent N1 (fan) and N1c (LPC) speed monitoring and limiting

**FADEC Redundancy:** Dual-channel with automatic switchover

**Manual Reversion:** Not available — FADEC failure requires engine shutdown

### 3.5 Reduction Gearbox

#### 3.5.1 Gearbox Oil System

The reduction gearbox uses a dedicated oil supply circuit that is separate from the main engine oil system. This separation is essential because the gearbox oil undergoes different thermal cycling and contamination loading than the main engine bearing oil. The two systems must never be cross-contaminated.

**Gearbox Oil Specification:** PWA 521 Type II (approved alternatives per PW SB 72-600 series)

**Gearbox Oil Capacity:** 3.8 liters (4.0 US qt) usable

**Oil Pressure (normal operating):**
| Power Setting | Minimum (psi) | Normal (psi) | Maximum (psi) |
|---------------|---------------|--------------|---------------|
| Ground Idle | 40 | 50-65 | 85 |
| Flight Idle | 45 | 55-70 | 85 |
| Takeoff | 55 | 65-80 | 90 |

**Oil Temperature (normal operating):**
| Power Setting | Normal (°C) | Caution (°C) | Limit (°C) |
|---------------|-------------|--------------|------------|
| All power | 60-130 | 130-145 | 150 |

**Chip Detector:** A dedicated magnetic chip detector (MCD) is installed in the gearbox oil scavenge circuit downstream of the gearbox sump. This chip detector is polled separately from the main engine oil chip detectors and generates a distinct CAS message (GBX CHIP DET) when activated. Do not conflate gearbox chip detector activations with main engine MCD activations; the fault codes and inspection requirements differ. See ENG-GBX-006 in Section 7.

**Temperature Monitoring:** A dedicated thermocouple monitors gearbox oil outlet temperature. This reading is displayed on the maintenance page and is used by the FADEC for oil system health trending. Sustained operation above 145°C requires investigation before further dispatch; operation above 150°C is not permitted.

#### 3.5.2 Common Gearbox Fault Modes

| Fault Mode | Early Indicators | Detection Method |
|------------|-----------------|------------------|
| Oil starvation | GBX OIL PRESS LOW CAS, rapid oil temp rise | CAS message, maintenance page |
| Planetary gear wear | Elevated Fe/Cu in gearbox oil, vibration change | SOAP analysis, chip detector |
| Sun gear spalling | Metal particles on chip detector | Chip detector activation, SOAP |
| Seal deterioration | Oil level decrease, external seepage | Visual inspection, oil quantity |
| Oil cooler blockage | Oil temp rising with normal pressure | Differential temperature monitoring |

#### 3.5.3 Replacement Criteria

The gearbox is a life-limited component. Hard-time replacement is required regardless of condition. Condition-based removal is required if any of the following are met:

- Chip detector activation (any metallic particles)
- Gearbox oil spectrographic analysis (SOAP) exceeds action limits (see Section 4.3)
- Gearbox oil temperature sustained above 150°C
- Vibration at gearbox mesh frequency exceeds caution limits
- Abnormal noise (growling, clicking) at ground idle
- Oil consumption exceeding 0.25 liters per flight hour

**Gearbox Hard-Time Life Limit:** As specified in the Airworthiness Limitations section of the current PW1500G CMM. Consult current Airbus AMM 72-60-00 for applicable cycle limits.

---

## 4. Engine Troubleshooting Procedures

### 4.1 Sensor Drift

**Fault Code:** ENG-SDR-001
**Severity Classification:** CRITICAL / MAJOR / MINOR
**Fleet Statistics:** Most common fault type (21% of engine events)

#### Symptoms
- Parameter disagree messages on CAS
- Gradual deviation between redundant sensor readings
- Thrust asymmetry indications
- FADEC fault messages

#### Diagnostic Procedure

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Review FADEC fault log via CMS | Identify affected channel and parameter |
| 2 | Compare sensor values (Channel A vs B) | Determine which channel has drifted |
| 3 | Cross-check with independent references | Validate actual engine condition |
| 4 | Perform sensor Built-In Test (BIT) | Confirm sensor hardware status |
| 5 | Check wiring continuity and connections | Rule out intermittent connections |

#### Corrective Actions by Severity

**CRITICAL (Drift > 10% affecting thrust control):**
- Ground aircraft pending sensor replacement
- Replace affected sensor or EEC channel
- Perform engine ground run verification
- Estimated downtime: 8-12 hours

**MAJOR (Drift 5-10%, redundancy compromised):**
- Dispatch with MEL if applicable
- Schedule sensor replacement within 10 days
- Increase monitoring frequency

**MINOR (Drift < 5%, trending):**
- Document in aircraft log
- Schedule calibration check at next maintenance visit
- Continue trend monitoring

### 4.2 Contamination

**Fault Code:** ENG-CNT-002
**Severity Classification:** CRITICAL / MAJOR / MINOR
**Fleet Statistics:** 13% of engine maintenance events

#### Types of Contamination

| Type | Source | Detection Method |
|------|--------|------------------|
| Oil contamination | Bearing seal leak, oil cooler failure | Oil analysis, carbon deposits |
| Fuel contamination | Water, particulates, microbial growth | Fuel filter DP, fuel sample |
| Compressor fouling | Airborne particles, salt, volcanic ash | EGT margin loss, performance |
| Turbine deposits | Combustion byproducts, sulfidation | Borescope, EGT spread |
| Gearbox cross-contamination | Gearbox seal failure | Oil analysis of both circuits |

#### Diagnostic Procedure

| Step | Action | Indicator |
|------|--------|-----------|
| 1 | Review trend data for EGT margin degradation | > 5°C shift indicates fouling |
| 2 | Perform oil spectrographic analysis (both circuits) | Check for wear metals, contamination |
| 3 | Check fuel filter differential pressure | High DP indicates fuel contamination |
| 4 | Borescope HPT nozzle and blades | Visual deposits, coating loss |
| 5 | Perform compressor wash if applicable | Evaluate EGT margin recovery |

#### Corrective Actions

**CRITICAL (Severe contamination affecting operation):**
- Engine removal for shop cleaning
- HPT blade replacement if sulfidation present
- Oil system flush and filter replacement (both engine and gearbox circuits)
- Estimated downtime: 3-5 days

**MAJOR (Moderate contamination):**
- Perform on-wing compressor wash (motoring wash)
- Replace fuel filter element
- Enhanced oil sampling (every 25 FH)
- Monitor EGT margin recovery

**MINOR (Early detection):**
- Schedule compressor wash at next opportunity
- Increase fuel sampling frequency
- Document trend for fleet analysis

### 4.3 Bearing Wear

**Fault Code:** ENG-BRG-003
**Severity Classification:** CRITICAL / MAJOR / MINOR
**Fleet Statistics:** 11% of engine maintenance events

#### Detection Methods
- Magnetic chip detector (MCD) warnings (engine and gearbox circuits)
- Oil spectrographic analysis (SOAP) — both oil circuits
- Vibration trend monitoring
- Oil consumption increase
- Oil temperature rise

#### Oil Analysis Limits (PW1500G Specific — Engine Oil Circuit)

| Metal | Normal (ppm) | Watch (ppm) | Action (ppm) |
|-------|--------------|-------------|--------------|
| Iron (Fe) | < 4 | 4-10 | > 10 |
| Chromium (Cr) | < 1 | 1-3 | > 3 |
| Nickel (Ni) | < 2 | 2-5 | > 5 |
| Silver (Ag) | < 0.5 | 0.5-2 | > 2 |
| Copper (Cu) | < 5 | 5-15 | > 15 |

#### Oil Analysis Limits (PW1500G Specific — Gearbox Oil Circuit)

| Metal | Normal (ppm) | Watch (ppm) | Action (ppm) |
|-------|--------------|-------------|--------------|
| Iron (Fe) | < 6 | 6-15 | > 15 |
| Copper (Cu) | < 8 | 8-20 | > 20 |
| Silver (Ag) | < 1 | 1-3 | > 3 |

**Note:** Gearbox oil action limits differ from main engine oil limits due to the higher normal wear metal baseline associated with gear mesh lubrication.

#### Bearing Identification by Vibration Frequency

| Bearing | Location | N1 Frequency | N1c Frequency |
|---------|----------|--------------|---------------|
| #1 | Fan forward | 1.0 × N1 | — |
| #2 | Fan aft / gearbox | 1.0 × N1 | — |
| #3 | LPC forward | — | 1.0 × N1c |
| #4 (Thrust) | HPC aft | — | 1.0 × N1c |
| #5 | HPT | — | 1.0 × N1c |
| Planetary | Gearbox | Multiple of N1 | Multiple of N1c |

#### Corrective Actions

**CRITICAL (MCD activation or rapid debris increase):**
- Immediate engine shutdown
- Do not motor engine
- Remove engine for teardown inspection
- Estimated downtime: Engine replacement required

**MAJOR (Elevated wear metals, trending):**
- Increase oil sampling to every 25 FH
- Plan engine removal within 200 FH
- Monitor vibration closely
- No power above MCT

**MINOR (Slight increase, stable):**
- Increase sampling frequency to every 50 FH
- Continue normal operations
- Trend monitoring with fleet comparison

### 4.4 Leak Detection

**Fault Code:** ENG-LEAK-004
**Severity Classification:** CRITICAL / MAJOR / MINOR
**Fleet Statistics:** 14% of engine maintenance events

#### Leak Classification

| Class | Rate | Definition | Action |
|-------|------|------------|--------|
| A | Seep | Wetness, no drip | Monitor, clean |
| B | Leak | 1-5 drops/min | Repair within 100 FH |
| C | Heavy | > 5 drops/min | Repair before flight |

#### Common Leak Sources

| System | Location | Visual Indicator |
|--------|----------|------------------|
| Engine oil | Accessory gearbox | Brown/black streaks |
| Engine oil | Turbine rear bearing | Oil in exhaust area |
| Gearbox oil | Gearbox forward sump | Oil forward of fan frame |
| Fuel | Fuel manifold | Fuel odor, staining |
| Fuel | FMV connections | Wet fittings |
| Bleed | Duct connections | Sooting, heat damage |

#### Troubleshooting Procedure

| Step | Action | Inspection Point |
|------|--------|------------------|
| 1 | Perform visual inspection of engine | Note all fluid trails |
| 2 | Clean suspected areas thoroughly | Prepare for leak check |
| 3 | Operate engine at ground idle | Observe for fresh leaks |
| 4 | Apply leak detection solution | Bubble test for pneumatic |
| 5 | UV dye inspection (if oil dye installed) | Pinpoint oil leak source (note: engine and gearbox circuits use different dye colors) |

### 4.5 Vibration Exceedance

**Fault Code:** ENG-VIB-005
**Severity Classification:** CRITICAL / MAJOR / MINOR

#### Vibration Limits (PW1500G)

| Level | N1 (fan) | N1c (LPC) | Alert |
|-------|----------|-----------|-------|
| Normal | < 1.5 ips | < 1.2 ips | None |
| Advisory | 1.5-2.5 ips | 1.2-2.0 ips | ENG VIB (amber) |
| Caution | 2.5-3.5 ips | 2.0-3.0 ips | ENG VIB (amber) |
| Warning | > 3.5 ips | > 3.0 ips | ENG VIB (red) |

**Note:** PW1500G vibration limits are significantly lower than those of conventional turbofans (compare: CFM56-7B warning threshold 4.5 ips N1). The reduction gearbox attenuates fan-rotor excitations before they can propagate into the core structure, so the ambient vibration level at engine mounts is lower in normal operation. Advisory thresholds are set tightly to provide early warning of gearbox anomalies or bearing degradation that might otherwise be masked by the damping effect of the gearbox.

#### Common Root Causes

| Cause | Frequency Signature | Typical Origin |
|-------|--------------------| ---------------|
| Fan imbalance | 1 × N1 | Blade damage, ice |
| Core imbalance | 1 × N1c | HPC blade loss |
| Bearing | 1 × N1 or N1c | Bearing degradation |
| Gear mesh | Multiple of N1/N1c | Gearbox planetary wear |

---

## 5. Avionics System

### 5.1 System Overview

The A220-300 avionics suite is built around the Rockwell Collins Pro Line Fusion platform, featuring large-format display units and fully integrated fly-by-wire primary flight control laws. The FBW system replaces conventional cable-and-pulley primary control runs with electronic signaling from sidestick controllers to flight control computers (FCCs), which command electrohydraulic servo actuators (EHSAs) on all primary surfaces. This architecture is unique in the single-aisle regional jet class.

### 5.2 Component Descriptions

#### 5.2.1 Flight Management System (FMS)
**Part Number:** AVN-FMS-A220-100
**ATA Reference:** 34-61

The dual Rockwell Collins FMS provides:
- 4D flight planning and navigation
- VNAV and LNAV guidance
- Performance calculations (V-speeds, fuel predictions)
- Required Navigation Performance (RNP) capability
- FANS/ATN datalink integration
- Integration with FBW flight control envelope protection

**Common Faults:**
- Navigation database update errors
- CDU display anomalies
- Position initialization failures

#### 5.2.2 Air Data and Inertial Reference Unit (ADIRU)
**Part Number:** AVN-ADC-A220-200
**ATA Reference:** 34-11

Dual ADIRUs provide:
- Barometric altitude computation
- Indicated/calibrated airspeed
- Mach number calculation
- Static air temperature
- Inertial position, velocity, and attitude
- Angle of attack

The ADIRU outputs feed directly into the fly-by-wire flight control computers for envelope protection functions. ADIRU failures must be assessed in the context of the FBW system degradation modes.

**Calibration Requirements:**
- Pitot-static leak test: Every 24 months
- ADIRU accuracy verification: Every 12 months

#### 5.2.3 Navigation Receiver (MMR)
**Part Number:** AVN-NAV-A220-300
**ATA Reference:** 34-51

Dual Multi-Mode Receivers (MMR) providing:
- VOR bearing and distance (VOR/DME)
- ILS localizer and glideslope
- Marker beacon reception
- GPS position with SBAS capability

### 5.3 Avionics Troubleshooting

#### 5.3.1 Sensor Drift (Avionics)

**Fault Code:** AVN-SDR-001

**Diagnostic Steps:**
1. Compare ADIRU outputs (ADIRU 1/2) via maintenance page
2. Cross-check with GPS-derived altitude and airspeed
3. Review BITE fault history for intermittent faults
4. Check pitot-static system for leaks or blockage

**Resolution:**
- Pitot-static leak check and correction
- ADIRU software reload
- ADIRU replacement if hardware fault confirmed

---

## 6. Hydraulics System

### 6.1 System Overview

The A220-300 employs a dual hydraulic system (Left and Right) plus standby, operating at 3,000 psi. Left and Right systems each power their respective primary flight control actuators, with crossover capability for redundancy. All primary flight control surface actuators are electrohydraulic servo actuators (EHSAs) with integrated position feedback transducers, directly commanded by the fly-by-wire flight control computers. This differs fundamentally from conventional hydromechanical actuator designs where cable or rod inputs directly drive actuator control valves.

### 6.2 System Architecture

| System | Power Source | Primary Functions |
|--------|--------------|-------------------|
| Left | EDP (Eng 1), ACMP | Primary flight controls (left surfaces), LE devices, landing gear |
| Right | EDP (Eng 2), ACMP | Primary flight controls (right surfaces), TE flaps, thrust reversers |
| Standby | ACMP | Standby flight controls, LE devices, thrust reversers |

### 6.3 Component Descriptions

#### 6.3.1 Main Hydraulic Pump (Engine-Driven)
**Part Number:** HYD-EDP-A220-100
**ATA Reference:** 29-11

Each engine drives one engine-driven pump (EDP):
- Operating pressure: 3,000 psi nominal
- Flow rate: 24 gpm at 3,000 psi
- Case drain limit: 4 gpm

#### 6.3.2 Hydraulic Reservoir
**Part Number:** HYD-RES-A220-200
**ATA Reference:** 29-21

- Left system reservoir: 4.5 gallons usable
- Right system reservoir: 4.5 gallons usable
- Standby reservoir: 0.7 gallons usable
- Operating temperature: -54°C to +107°C
- Fluid type: Skydrol LD4 or equivalent per AMM approval

#### 6.3.3 Electrohydraulic Servo Actuators (EHSA)
**Part Number:** HYD-EHSA-A220-300
**ATA Reference:** 29-31

Primary flight control surfaces use EHSAs in place of conventional hydromechanical actuators:
- Integrated electrohydraulic servo valve (EHSV) controlled by FCC digital commands
- Integrated linear variable differential transducer (LVDT) for position feedback
- Fail-fixed mode on loss of electrical command
- Maintenance diagnostics via aircraft BITE accessible through CMS

**Note:** EHSA maintenance requires awareness of FBW system interaction. Actuator replacement procedures include FCC re-engagement and control law verification tests. Refer to AMM 27-00-00 for FBW interface requirements.

### 6.4 Hydraulics Troubleshooting

#### 6.4.1 Leak Detection

**Fault Code:** HYD-LEAK-001

**Common Leak Locations:**

| Component | Access | Typical Cause |
|-----------|--------|---------------|
| EDP | Engine cowl | Shaft seal wear |
| ACMP | Equipment bay | Pump seal, fittings |
| Reservoir | Equipment bay | Sight glass gasket |
| EHSA | Wing/fuselage panels | Rod seal wear, EHSV leak |
| Lines | Various | B-nut loosening |

**Leak Check Procedure:**
1. Depressurize hydraulic systems
2. Clean and dry suspected areas
3. Pressurize system using ground cart
4. Inspect for fresh fluid at suspected locations
5. Classify leak severity and document

#### 6.4.2 Contamination

**Fault Code:** HYD-CNT-002

**Contamination Limits (NAS 1638):**

| Level | Class | Action |
|-------|-------|--------|
| Acceptable | 6 or better | Continue operations |
| Marginal | 7-8 | Filter and resample in 100 FH |
| Unacceptable | 9 or worse | Flush system, replace filters |

**Water Content:** Maximum 0.1% by volume

---

## 7. Fault Code Reference

### 7.1 Engine Fault Codes

| Code | Description | Severity | ATA | Primary Action |
|------|-------------|----------|-----|----------------|
| ENG-SDR-001 | Sensor Drift | CRIT/MAJ/MIN | 77 | Identify sensor, verify, replace |
| ENG-CNT-002 | Contamination | CRIT/MAJ/MIN | 72 | Oil/fuel analysis, wash/clean |
| ENG-BRG-003 | Bearing Wear | CRIT/MAJ/MIN | 72 | Oil analysis, vibration check |
| ENG-LEAK-004 | Fluid Leak | CRIT/MAJ/MIN | 79 | Identify source, repair |
| ENG-VIB-005 | Vibration Exceedance | CRIT/MAJ/MIN | 72 | Fan balance, bearing check |
| ENG-GBX-006 | Gearbox Fault | CRIT/MAJ/MIN | 72 | Chip detector, SOAP, oil pressure check |
| ENG-OVH-007 | Overheat | CRIT/MAJ/MIN | 72 | Reduce thrust, borescope |
| ENG-ELF-008 | Electrical Fault | CRIT/MAJ/MIN | 77 | FADEC diagnostics, wiring |

**Note on ENG-GBX-006:** This fault code is unique to GTF-equipped aircraft and does not appear in conventional turbofan maintenance programs. It covers all gearbox-specific fault conditions including chip detector activation, gearbox oil pressure loss, and gearbox oil temperature exceedance.

### 7.2 Avionics Fault Codes

| Code | Description | Severity | ATA | Primary Action |
|------|-------------|----------|-----|----------------|
| AVN-SDR-001 | Sensor Drift | MAJ/MIN | 34 | ADIRU comparison, calibration |
| AVN-ELF-002 | Electrical Fault | MAJ/MIN | 34 | Power check, connector inspect |
| AVN-FMS-003 | FMS Malfunction | MAJ | 34 | Reset, database reload |
| AVN-NAV-004 | NAV Receiver Fault | MIN | 34 | Antenna check, LRU swap |

### 7.3 Hydraulics Fault Codes

| Code | Description | Severity | ATA | Primary Action |
|------|-------------|----------|-----|----------------|
| HYD-LEAK-001 | System Leak | CRIT/MAJ/MIN | 29 | Locate, classify, repair |
| HYD-CNT-002 | Contamination | MAJ/MIN | 29 | Sample analysis, filter |
| HYD-PRS-003 | Low Pressure | CRIT/MAJ | 29 | Pump check, leak check |
| HYD-QTY-004 | Low Quantity | MAJ | 29 | Check level, leak inspect |

### 7.4 Severity Definitions

| Level | Definition | Response Time | MEL Impact |
|-------|------------|---------------|------------|
| CRITICAL | Flight safety affected | Before next flight | No-go item |
| MAJOR | System capability reduced | 1-10 days | Dispatch deviation |
| MINOR | Limited operational impact | Next scheduled mx | Normal dispatch |

---

## 8. Troubleshooting Decision Trees

### 8.1 Engine Vibration Diagnostic Flow

```
START: Engine Vibration Warning/Advisory
│
├─► Is vibration > 3.5 ips (N1 fan) or > 3.0 ips (N1c LPC)?
│   │
│   ├─► YES ─► Reduce thrust immediately
│   │          If vibration persists above warning limits, shutdown engine
│   │          └─► END: Engine shutdown, ground inspection required
│   │
│   └─► NO ─► Continue to next step
│
├─► Analyze vibration frequency spectrum (DFDR/QAR)
│   │
│   ├─► 1×N1 dominant ─► Fan rotor or gearbox output issue
│   │   ├─► Check fan blades for damage, ice, deposits
│   │   ├─► Check gearbox oil pressure and chip detector
│   │   ├─► Perform fan trim balance if imbalance confirmed
│   │   └─► END: Fan service or gearbox investigation
│   │
│   ├─► 1×N1c dominant ─► Core rotor or gearbox input issue
│   │   ├─► Borescope HPC and HPT
│   │   ├─► Check gearbox for planetary gear wear
│   │   ├─► Check oil analysis for bearing wear
│   │   └─► END: Core inspection/repair or gearbox service
│   │
│   ├─► Multiple of N1/N1c ─► Gearbox planetary gear fault
│   │   ├─► Activate gearbox chip detector check
│   │   ├─► Immediate gearbox SOAP sample
│   │   ├─► If metals elevated, plan engine removal
│   │   └─► END: Gearbox inspection (see Section 3.5)
│   │
│   └─► Bearing frequency ─► Bearing degradation
│       ├─► Immediate oil sample for SOAP (engine and gearbox circuits)
│       ├─► If metals elevated, plan engine removal
│       └─► END: Bearing replacement (shop)
│
└─► Vibration transient only?
    │
    ├─► YES ─► Document, monitor for recurrence
    │          Check for icing conditions at time of event
    │          └─► END: Monitoring
    │
    └─► NO ─► Systematic component inspection required
              └─► END: Detailed troubleshooting
```

### 8.2 Sensor Drift Investigation

```
START: Sensor Parameter Disagree / Drift Indication
│
├─► Which parameter is affected?
│   │
│   ├─► EGT ─► Compare EGT probes per FADEC maintenance page
│   │          Check for probe damage, contamination
│   │          Verify harness connections
│   │          └─► Replace probe if > 15°C variance
│   │
│   ├─► N1Speed ─► Compare FADEC channels A and B
│   │              Note: N1Speed is fan shaft speed (gearbox output)
│   │              Check speed sensor tone wheel on fan shaft
│   │              Verify wiring to EEC
│   │              Check gearbox for mechanical fault affecting fan speed
│   │              └─► Replace sensor or EEC channel
│   │
│   ├─► FuelFlow ─► Compare commanded vs actual
│   │               Check fuel flow transmitter
│   │               Verify FMV operation
│   │               └─► Replace transmitter or FMV
│   │
│   └─► Vibration ─► Compare accelerometer outputs
│                   Check mounting and wiring
│                   Note: Gearbox anomalies can cause stepped vibration changes
│                   └─► Replace accelerometer or investigate gearbox
│
└─► Is drift progressive or sudden?
    │
    ├─► Progressive ─► Calibration drift likely
    │                  Schedule replacement at next mx
    │                  └─► END: Scheduled repair
    │
    └─► Sudden ─► Component failure likely
                 Replace before next flight
                 └─► END: Immediate repair
```

### 8.3 Hydraulic Low Pressure Procedure

```
START: HYD SYS PRESS (Left or Right) Warning
│
├─► Check hydraulic quantity
│   │
│   ├─► QUANTITY LOW ─► Leak present
│   │   ├─► Land at nearest suitable airport
│   │   ├─► Do not cycle gear unnecessarily
│   │   ├─► Note: FBW system will degrade gracefully; monitor FCC status
│   │   ├─► After landing, inspect for leak source
│   │   └─► END: Leak repair required
│   │
│   └─► QUANTITY NORMAL ─► Pump issue likely
│
├─► Check pump status (EDP or ACMP)
│   │
│   ├─► EDP ─► Is engine running normally?
│   │   ├─► YES ─► EDP internal failure
│   │   │          Use alternate pump
│   │   │          └─► END: Replace EDP
│   │   │
│   │   └─► NO ─► Engine problem affecting pump drive
│   │            └─► See engine troubleshooting
│   │
│   └─► ACMP ─► Check circuit breaker and power
│               Check motor operation
│               └─► END: Replace ACMP if faulty
│
└─► Pressure restored with alternate pump?
    │
    ├─► YES ─► Primary pump failed
    │          Can dispatch per MEL with restrictions
    │          Note: Verify EHSA functionality on affected surfaces
    │          └─► END: Schedule pump replacement
    │
    └─► NO ─► System blockage or multiple failures
              Do not dispatch
              └─► END: Extensive troubleshooting required
```

### 8.4 Gearbox Oil System Diagnostic Flow

```
START: GBX CHIP DET / GBX OIL PRESS / GBX OIL TEMP CAS Message
│
├─► Which CAS message is active?
│   │
│   ├─► GBX CHIP DET ─► Metal particles detected in gearbox oil
│   │   │
│   │   ├─► Shutdown engine (do not motor)
│   │   ├─► Access gearbox chip detector (AMM 72-60-00)
│   │   ├─► Examine particles: Ferrous vs non-ferrous?
│   │   │   │
│   │   │   ├─► FERROUS (magnetic) ─► Planetary gear or ring gear wear
│   │   │   │   ├─► Collect gearbox SOAP sample
│   │   │   │   ├─► Engine removal required for gearbox teardown
│   │   │   │   └─► END: Engine removal, gearbox replacement
│   │   │   │
│   │   │   └─► NON-FERROUS ─► Bronze/silver indicates bearing cage
│   │   │       ├─► Collect gearbox SOAP sample
│   │   │       ├─► Cross-reference with main engine MCD (not activated?)
│   │   │       ├─► If SOAP action limits exceeded, engine removal required
│   │   │       └─► END: Engine removal if SOAP confirms
│   │   │
│   │   └─► Single isolated particle < 1mm?
│   │       ├─► Re-clean and re-install detector; monitor for recurrence
│   │       ├─► If recurs within 10 FH, treat as confirmed fault
│   │       └─► END: Enhanced monitoring / removal if recurs
│   │
│   ├─► GBX OIL PRESS LOW ─► Low gearbox oil pressure
│   │   │
│   │   ├─► Check gearbox oil quantity (dipstick, access panel forward of fan)
│   │   │   │
│   │   │   ├─► QUANTITY LOW ─► Gearbox oil leak
│   │   │   │   ├─► Inspect forward engine area for gearbox oil seepage
│   │   │   │   ├─► Check gearbox input/output seal areas
│   │   │   │   ├─► Do not dispatch until leak is identified and repaired
│   │   │   │   └─► END: Seal replacement
│   │   │   │
│   │   │   └─► QUANTITY NORMAL ─► Oil pump or pressure regulator fault
│   │   │       ├─► Check gearbox oil pressure regulator valve
│   │   │       ├─► Check gearbox scavenge pump operation
│   │   │       ├─► If no mechanical cause found, replace gearbox oil pump
│   │   │       └─► END: Component replacement
│   │   │
│   │   └─► Was fault transient (appeared and cleared)?
│   │       ├─► Document; inspect gearbox oil filter for debris
│   │       ├─► If filter clean and quantity normal, ground run and monitor
│   │       └─► END: Enhanced monitoring
│   │
│   └─► GBX OIL TEMP HIGH ─► Gearbox oil overtemperature
│       │
│       ├─► Is engine at high power?
│       │   │
│       │   ├─► YES ─► Reduce thrust; observe temperature response
│       │   │   ├─► If temperature decreases > 10°C within 1 minute: transient
│       │   │   │   └─► Document; check oil cooler effectiveness
│       │   │   │
│       │   │   └─► If temperature does not decrease: oil cooling fault
│       │   │       ├─► Shutdown engine
│       │   │       └─► END: Oil cooler inspection/replacement
│       │   │
│       │   └─► NO (ground idle or flight idle) ─► Possible blockage
│       │       ├─► Check gearbox oil filter differential pressure
│       │       ├─► Check oil cooler bypass valve operation
│       │       └─► END: Filter/cooler replacement
│       │
│       └─► Was temperature > 150°C?
│           ├─► YES ─► Do not dispatch; inspect for coking, seal damage
│           │          Gearbox oil drain and refill with approved oil
│           │          └─► END: Engineering disposition required
│           │
│           └─► NO (130-150°C) ─► Caution range; enhanced monitoring
│                                  Schedule gearbox oil service within 25 FH
│                                  └─► END: Scheduled maintenance
```

---

## 9. Scheduled Maintenance Tasks

### 9.1 Engine Inspection Schedule

| Task | Interval | Duration | Personnel |
|------|----------|----------|-----------|
| Fan blade visual inspection | 500 FH | 0.75 hr | 1 mechanic |
| Engine oil service | 50 FH or 7 days | 0.5 hr | 1 mechanic |
| Gearbox oil service | 100 FH or 14 days | 0.75 hr | 1 mechanic |
| Oil filter inspection (engine) | 500 FH | 1.0 hr | 1 mechanic |
| Oil filter inspection (gearbox) | 500 FH | 1.0 hr | 1 mechanic |
| Magnetic chip detector check (engine) | 500 FH | 0.5 hr | 1 mechanic |
| Magnetic chip detector check (gearbox) | 250 FH | 0.5 hr | 1 mechanic |
| Borescope - HPC | 3,000 FH | 3.0 hr | 1 specialist |
| Borescope - Combustor | 3,000 FH | 2.0 hr | 1 specialist |
| Borescope - HPT | 3,000 FH | 2.5 hr | 1 specialist |
| Gearbox oil SOAP analysis | 100 FH | 0.25 hr | 1 mechanic |
| Fuel filter replacement | 1,200 FH | 1.5 hr | 1 mechanic |
| Engine mount inspection | A-check | 2.5 hr | 2 mechanics |
| Thrust reverser inspection | C-check | 12.0 hr | 2 mechanics |

### 9.2 Avionics Inspection Schedule

| Task | Interval | Duration | Personnel |
|------|----------|----------|-----------|
| FMS database update | 28 days | 0.5 hr | 1 technician |
| Pitot-static leak test | 24 months | 4.0 hr | 1 technician |
| ADIRU accuracy check | 12 months | 2.0 hr | 1 technician |
| VOR/ILS accuracy check | 12 months | 2.0 hr | 1 technician |
| BITE fault log review | Weekly | 0.5 hr | 1 technician |
| Antenna inspection | A-check | 1.0 hr | 1 mechanic |

### 9.3 Hydraulics Inspection Schedule

| Task | Interval | Duration | Personnel |
|------|----------|----------|-----------|
| Fluid level check | Daily | 0.25 hr | 1 mechanic |
| Fluid sampling and analysis | 600 FH | 0.5 hr | 1 mechanic |
| System filter replacement | 1,200 FH | 2.0 hr | 1 mechanic |
| EDP inspection | A-check | 2.0 hr | 1 mechanic |
| ACMP functional test | A-check | 1.0 hr | 1 mechanic |
| EHSA inspection and BITE check | C-check | 8.0 hr | 2 mechanics |
| System pressure test | 24 months | 4.0 hr | 2 mechanics |

### 9.4 Common Task Cards

#### Task Card: ENG-TC-001 - Engine Oil Service

**Purpose:** Replenish engine oil to proper level

**Tools Required:**
- Oil dispenser with flexible spout
- Calibrated dipstick (P/N: PW-TOOL-001)
- Lint-free wipes

**Procedure:**
1. Ensure engine has been shut down for minimum 15 minutes (oil drain-back)
2. Open fan cowl oil service door
3. Remove oil tank cap and check level on integral sight glass
4. Add approved oil (PWA 521 Type II) if level below ADD mark
5. Do not overfill — level should be between ADD and FULL
6. Replace cap and verify secure
7. Close service door
8. Record quantity added in aircraft log
9. Do not confuse engine oil service point with gearbox oil service point (see GBX-TC-001)

**Oil Type:** PWA 521 Type II (Mobil Jet Oil 254 or equivalent)

#### Task Card: GBX-TC-001 - Gearbox Oil Service

**Purpose:** Replenish gearbox oil to proper level and collect sample for SOAP analysis

**Reference:** AMM 72-60-00

**Tools Required:**
- Gearbox oil dispenser (separate from engine oil dispenser — do not cross-contaminate)
- Calibrated gearbox dipstick (P/N: PW-TOOL-002)
- Sample bottle (clean, dry, 50ml minimum)
- Sample adapter (P/N: PW-TOOL-003)
- Lint-free wipes
- Gloves and safety glasses

**Warning:** The gearbox oil service point is located forward of the fan frame, accessible through the left forward fan cowl. It is physically distinct from the engine oil service point at the accessory gearbox. Using engine oil in the gearbox or vice versa is a maintenance error that requires gearbox oil drain and refill before return to service.

**Procedure:**
1. Ensure engine has been shut down for minimum 30 minutes (gearbox oil drain-back is slower than main engine oil due to lower sump temperature)
2. Open left forward fan cowl
3. Locate gearbox oil service access panel (labeled GBX OIL — yellow placard)
4. Clean area around service port
5. Connect sample adapter to gearbox SOAP sample port
6. Collect 50ml oil sample in clean bottle before adding oil
7. Label sample: Aircraft registration, Engine position (1 or 2), date, flight hours since last service
8. Remove dipstick and check gearbox oil level
9. Add approved gearbox oil (PWA 521 Type II) if level below ADD mark
10. Replace dipstick and verify secure
11. Replace sample port cap and remove adapter
12. Close forward fan cowl
13. Record quantity added and sample collection in aircraft log
14. Submit SOAP sample to approved laboratory within 48 hours

**Oil Type:** PWA 521 Type II

**Caution:** Gearbox oil consumption exceeding 0.25 liters per flight hour requires investigation per ENG-GBX-006 before further dispatch.

#### Task Card: HYD-TC-001 - Hydraulic Fluid Sample

**Purpose:** Obtain fluid sample for contamination analysis

**Reference:** AMM 29-00-00

**Tools Required:**
- Sample bottle (clean, dry, 100ml minimum)
- Sample valve adapter (P/N: HYD-TOOL-100)
- Gloves and safety glasses

**Procedure:**
1. Ensure hydraulic system depressurized
2. Locate sample port on reservoir (equipment bay)
3. Clean area around sample port
4. Connect adapter and open sample valve
5. Discard first 50ml (flush line)
6. Collect 100ml sample in clean bottle
7. Close valve and disconnect adapter
8. Label sample: Aircraft registration, system (Left/Right), date, hours
9. Submit to approved laboratory within 48 hours

---

## 10. Appendices

### 10.1 Quick Reference - Normal Operating Limits

#### Engine Parameters (PW1500G)

| Parameter | Ground Idle | Flight Idle | Max Continuous | Takeoff (5 min) |
|-----------|-------------|-------------|----------------|-----------------|
| N1Speed (% RPM) | 18-24 | 24-30 | 92 | 100 |
| EGT (°C) | 310-380 | 380-440 | 855 | 890 |
| FuelFlow (kg/s) | 0.09-0.16 | 0.16-0.24 | 0.80-1.10 | 1.15-1.35 |
| Oil Pressure (psi) | 35-60 | 40-70 | 45-75 | 45-75 |
| Oil Temp (°C) | 50-90 | 60-120 | 80-140 | 80-155 |
| Vibration (ips) | < 0.8 | < 1.2 | < 2.0 | < 2.5 |
| GBX Oil Pressure (psi) | 50-65 | 55-70 | 65-80 | 65-80 |
| GBX Oil Temp (°C) | 60-90 | 70-110 | 90-130 | 90-130 |

#### Hydraulic System

| Parameter | Left System | Right System | Standby |
|-----------|-------------|--------------|---------|
| Pressure | 2,800-3,200 psi | 2,800-3,200 psi | 2,800-3,200 psi |
| Quantity | 70-100% | 70-100% | 70-100% |
| Fluid Temp | -40 to +107°C | -40 to +107°C | -40 to +107°C |

### 10.2 Abbreviations and Acronyms

| Abbreviation | Definition |
|--------------|------------|
| ACMP | AC Motor Pump |
| ADIRU | Air Data and Inertial Reference Unit |
| AGB | Accessory Gearbox |
| AMM | Aircraft Maintenance Manual |
| BITE | Built-In Test Equipment |
| CAS | Crew Alerting System |
| CDU | Control Display Unit |
| CMM | Component Maintenance Manual |
| CMS | Central Maintenance System |
| EDP | Engine-Driven Pump |
| EEC | Electronic Engine Control |
| EHSA | Electrohydraulic Servo Actuator |
| EHSV | Electrohydraulic Servo Valve |
| EGT | Exhaust Gas Temperature |
| FADEC | Full Authority Digital Engine Control |
| FBW | Fly-By-Wire |
| FCC | Flight Control Computer |
| FH | Flight Hours |
| FMC | Flight Management Computer |
| FMS | Flight Management System |
| FMV | Fuel Metering Valve |
| FOD | Foreign Object Damage |
| GTF | Geared Turbofan |
| HPC | High Pressure Compressor |
| HPT | High Pressure Turbine |
| LPC | Low Pressure Compressor |
| LPT | Low Pressure Turbine |
| LRU | Line Replaceable Unit |
| LVDT | Linear Variable Differential Transducer |
| MCD | Magnetic Chip Detector |
| MCT | Maximum Continuous Thrust |
| MEL | Minimum Equipment List |
| MMR | Multi-Mode Receiver |
| N1 | Fan Shaft Speed (gearbox output) |
| N1c | LPC Shaft Speed |
| NAV | Navigation |
| OPR | Overall Pressure Ratio |
| SOAP | Spectrometric Oil Analysis Program |
| TBC | Thermal Barrier Coating |
| VSV | Variable Stator Vane |

### 10.3 Reference Documents

| Document | Number | Description |
|----------|--------|-------------|
| Aircraft Maintenance Manual | AMM A220 | Primary maintenance reference |
| Fault Isolation Manual | FIM A220 | Troubleshooting guidance |
| Illustrated Parts Catalog | IPC A220 | Parts identification |
| Component Maintenance Manual | CMM PW1500G | Engine and gearbox overhaul data |
| Service Bulletin Index | SB A220 | Modification tracking |
| Airworthiness Directives | AD List | Mandatory compliance |
| Master Minimum Equipment List | MMEL A220 | Dispatch deviations |

### 10.4 Emergency Contacts

| Function | Contact | Availability |
|----------|---------|--------------|
| AOG Desk | +1-800-555-0220 | 24/7 |
| Engine Support (P&W) | +1-860-555-0190 | 24/7 |
| Airbus Technical Support | +1-314-555-0200 | 24/7 |
| Technical Records | tech.records@exampleair.com | 24/7 |
| Engineering Support | engineering@exampleair.com | 24/7 |
| Parts Supply | parts@exampleair.com | 24/7 |

### 10.5 Fleet Maintenance Statistics Summary

Based on fleet data analysis (July - September 2024):

| Metric | Value |
|--------|-------|
| Total Maintenance Events | 38 |
| Critical Events | 14 (37%) |
| Major Events | 12 (32%) |
| Minor Events | 12 (32%) |
| Engine-Related | 26 (68%) |
| Hydraulics-Related | 8 (21%) |
| Avionics-Related | 4 (11%) |

**Top Fault Types:**
1. Sensor Drift - 8 events (21%)
2. Gearbox Oil Issue - 6 events (16%)
3. Contamination - 5 events (13%)
4. Bearing Wear - 4 events (11%)
5. Vibration Exceedance - 4 events (10%)

**Note:** Gearbox Oil Issue (ENG-GBX-006) is the second most common fault type in the A220-300 fleet and is a GTF-specific maintenance category not present in conventional turbofan fleet data. Enhanced gearbox monitoring intervals have been implemented in response to this trend.

### 10.6 Revision History Log

| Page | Rev | Date | Change Description |
|------|-----|------|--------------------|
| All | 1.0 | 2024-10-01 | Initial release |

---

**END OF DOCUMENT**

*This manual is for demonstration purposes. Always refer to official Airbus documentation for actual maintenance procedures.*
