# Example Queries for Neo4j Aura Agent

Example natural language questions to ask the **Aircraft Digital Twin Analyst** agent in Neo4j Aura. Questions are organized by the exact agent tool they route to.

The agent has 7 tools configured:

| Tool | Type | Description |
|------|------|-------------|
| Aircraft Systems, Components, and Sensors | Cypher Template | Aircraft topology: systems, components, sensors |
| Aircraft Maintenance Events | Cypher Template | Fault history, severity, corrective actions |
| Aircraft Component Removals | Cypher Template | Part removal records with TSN/CSN |
| Aircraft Flight Details | Cypher Template | Flights, routes, delays |
| Sensor Operating Limits with Source | Cypher Template | Operating limits with provenance back to maintenance manuals |
| Search Maintenance Document Chunks | Similarity Search | Semantic search over maintenance manual content |
| Text2Cypher | Text2Cypher | Open-ended questions that generate Cypher on the fly |

---

## 1. Aircraft Systems, Components, and Sensors (Cypher Template)

Returns aircraft topology: systems, their components, and attached sensors.

- "Tell me about aircraft N95040A"
- "What systems does aircraft N30268B have?"
- "Show all sensors on aircraft N54980C"
- "What components are in the CFM56-7B engines on N95040A?"
- "List all Boeing 737-800 aircraft in the fleet"
- "Which aircraft are operated by ExampleAir?"
- "How many components does each system have on N95040A?"
- "What type of avionics suite is installed on N37272D?"
- "Show the engine sensors for N30268B"

---

## 2. Aircraft Maintenance Events (Cypher Template)

Returns maintenance events with fault type, severity, affected system, and corrective action.

- "Show the maintenance summary for N54980C"
- "What critical maintenance events have been reported for N95040A?"
- "List all bearing wear faults across the fleet"
- "Which aircraft have had overheat events on their engines?"
- "Show recent maintenance events for SkyWays aircraft"
- "What corrective actions were taken for vibration exceedance faults?"
- "How many maintenance events does N30268B have by severity?"
- "What faults have affected the hydraulics system on N54980C?"

---

## 3. Aircraft Component Removals (Cypher Template)

Returns component removal records including reason, time since new (TSN), and cycles since new (CSN).

- "What component removals have occurred on N95040A?"
- "Show all removals due to contamination"
- "Which components have been removed with the highest flight cycles?"
- "List component removals for Boeing 737-800 aircraft"
- "What was the reason for the most recent removal on N30268B?"
- "Show turbine removals across the fleet"
- "Which aircraft have had the most component removals?"

---

## 4. Aircraft Flight Details (Cypher Template)

Returns flight operations, routes, and delay information.

- "Show flights operated by aircraft N95040A"
- "What flights depart from JFK?"
- "Which flights were delayed and why?"
- "What are the top routes by flight count?"
- "Show delayed arrivals at LAX"
- "Which aircraft has the most flights with weather delays?"
- "What flights does ExampleAir operate out of ORD?"
- "Show the flight schedule for N54980C"

---

## 5. Sensor Operating Limits with Source (Cypher Template)

Returns sensor operating limits with full provenance: OperatingLimit -> source Chunk -> Document -> Aircraft.

- "What are the sensor operating limits for N30268B?"
- "What is the maximum EGT allowed for the A320-200?"
- "Show the vibration limits for all Boeing 737-800 sensors"
- "What operating limits are defined for N1Speed sensors?"
- "What maintenance manual defines the fuel flow limits for the A321neo?"
- "What is the normal fuel flow range for the B737-800?"
- "Trace the provenance of the EGT operating limit for B737-800"
- "Which sensors on N54980C have operating limits defined?"

---

## 6. Search Maintenance Document Chunks (Similarity Search)

Performs semantic vector search over maintenance manual chunks. Returns scored results with source document and aircraft type.

### Troubleshooting

- "How do I troubleshoot engine vibration?"
- "What are the procedures for an EGT exceedance event?"
- "How do I diagnose a fuel flow anomaly?"
- "What should I check if hydraulic pressure drops?"
- "What are the steps for compressor stall recovery?"

### Operating Limits and Parameters

- "What are the EGT limits during takeoff?"
- "What is the normal vibration range for cruise operations?"
- "What N1 speed limits apply during climb?"
- "What fuel flow rates are expected at idle?"

### Scheduled Maintenance

- "What is the engine inspection schedule?"
- "When should the hydraulic system be serviced?"
- "What are the routine maintenance intervals for the avionics suite?"
- "What lubrication procedures are required for engine bearings?"

### Component-Specific

- "What are the turbine blade inspection criteria?"
- "How often should the combustion chamber be inspected?"
- "What are the filter replacement intervals for the hydraulic system?"
- "What are the known failure modes for the low-pressure compressor?"

---

## 7. Text2Cypher

Open-ended questions the agent answers by generating Cypher on the fly. These go beyond what the Cypher templates cover, typically involving aggregations, comparisons, or cross-domain graph traversals.

### Maintenance Analysis

- "Which aircraft has the most critical maintenance events?"
- "What are the most common fault types across the fleet?"
- "How many maintenance events are there by severity level?"
- "Which components have the highest failure rate?"
- "What faults do aircraft N95040A and N26760M share?"
- "Show all aircraft that had both overheat and vibration exceedance faults"
- "Which engine systems have the most maintenance events?"
- "What is the ratio of critical to minor maintenance events per aircraft model?"

### Flight and Delay Analysis

- "What are the top causes of flight delays?"
- "Which airports have the most delayed arrivals?"
- "How many flights were delayed due to maintenance issues?"
- "What is the average delay time by cause?"
- "Which operator has the most weather-related delays?"
- "Show flights that were delayed more than 60 minutes"
- "Which routes have the highest delay frequency?"

### Topology and Structure

- "Show all components in the hydraulics system"
- "How many sensors are attached to each engine type?"
- "Which aircraft models have the most components?"
- "List all Airbus aircraft with their system counts"
- "What is the complete system hierarchy for the Embraer E190?"

### Cross-Domain Graph Traversals

- "Which sensors have operating limits defined?"
- "Which maintenance manuals apply to Airbus aircraft?"
- "Show operating limits that were extracted from the A320-200 maintenance manual"
- "Find aircraft where maintenance events occurred on components connected to EGT sensors"
- "Which aircraft have had delays on flights within 24 hours of a critical maintenance event?"
