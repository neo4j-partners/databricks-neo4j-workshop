# Lab Steps: Data Loading

## Part 2: Load the Knowledge Graph

Data loading is handled in **Lab 2 - Databricks ETL to Neo4j** using:

### Notebook 01: Spark Connector ETL
- Loads Aircraft, System, and Component nodes from CSV files in Unity Catalog
- Uses the Neo4j Spark Connector

### Notebook 02: Full Dataset Load
- Adds Sensors, Airports, Flights, Delays, MaintenanceEvents, and Removals
- Uses the Neo4j Spark Connector

## What You'll Load

| Content | Description |
|---------|-------------|
| Aircraft | Fleet inventory with tail numbers and models |
| Systems | Engines, Avionics, Hydraulics |
| Components | Turbines, Compressors, Pumps |
| Flights | Flight operations with delays |

---

[← Previous](07-lab-steps-1.md) | [Next: Explore the Graph →](09-explore.md)
