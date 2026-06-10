// ---- WARNING: This script wipes the DB ----
MATCH (n) DETACH DELETE n;

// Constraints
CREATE CONSTRAINT IF NOT EXISTS FOR (a:Aircraft) REQUIRE a.aircraft_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (s:System) REQUIRE s.system_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Component) REQUIRE c.component_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (sn:Sensor) REQUIRE sn.sensor_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (ap:Airport) REQUIRE ap.airport_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (f:Flight) REQUIRE f.flight_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (d:Delay) REQUIRE d.delay_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (m:MaintenanceEvent) REQUIRE m.event_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (r:Removal) REQUIRE r.removal_id IS UNIQUE;

// Nodes
LOAD CSV WITH HEADERS FROM 'file:///nodes_aircraft.csv' AS row
CREATE (:Aircraft { aircraft_id: row[":ID(Aircraft)"], tail_number: row.tail_number, icao24: row.icao24, model: row.model, manufacturer: row.manufacturer, operator: row.operator });

LOAD CSV WITH HEADERS FROM 'file:///nodes_systems.csv' AS row
CREATE (:System { system_id: row[":ID(System)"], aircraft_id: row.aircraft_id, type: row.type, name: row.name });

LOAD CSV WITH HEADERS FROM 'file:///nodes_components.csv' AS row
CREATE (:Component { component_id: row[":ID(Component)"], system_id: row.system_id, type: row.type, name: row.name });

LOAD CSV WITH HEADERS FROM 'file:///nodes_sensors.csv' AS row
CREATE (:Sensor { sensor_id: row[":ID(Sensor)"], system_id: row.system_id, type: row.type, name: row.name, unit: row.unit });

LOAD CSV WITH HEADERS FROM 'file:///nodes_airports.csv' AS row
CREATE (:Airport { airport_id: row[":ID(Airport)"], name: row.name, city: row.city, country: row.country, iata: row.iata, icao: row.icao, lat: toFloat(row.lat), lon: toFloat(row.lon) });

LOAD CSV WITH HEADERS FROM 'file:///nodes_flights.csv' AS row
CREATE (:Flight { flight_id: row[":ID(Flight)"], flight_number: row.flight_number, aircraft_id: row.aircraft_id, operator: row.operator, origin: row.origin, destination: row.destination, scheduled_departure: row.scheduled_departure, scheduled_arrival: row.scheduled_arrival });

LOAD CSV WITH HEADERS FROM 'file:///nodes_delays.csv' AS row
CREATE (:Delay { delay_id: row[":ID(Delay)"], cause: row.cause, minutes: toInteger(row.minutes) });

LOAD CSV WITH HEADERS FROM 'file:///nodes_maintenance.csv' AS row
CREATE (:MaintenanceEvent { event_id: row[":ID(MaintenanceEvent)"], component_id: row.component_id, system_id: row.system_id, aircraft_id: row.aircraft_id, fault: row.fault, severity: row.severity, reported_at: row.reported_at, corrective_action: row.corrective_action });

LOAD CSV WITH HEADERS FROM 'file:///nodes_removals.csv' AS row
CREATE (:Removal {
  removal_id: row[":ID(RemovalEvent)"],
  RMV_TRK_NO: row.RMV_TRK_NO,
  RMV_REA_TX: row.RMV_REA_TX,
  component_id: row.component_id,
  aircraft_id: row.aircraft_id,
  removal_date: row.removal_date,
  work_order_number: row.work_order_number,
  technician_id: row.technician_id,
  part_number: row.part_number,
  serial_number: row.serial_number,
  time_since_install: toFloat(row.time_since_install),
  flight_hours_at_removal: toInteger(row.flight_hours_at_removal),
  flight_cycles_at_removal: toInteger(row.flight_cycles_at_removal),
  replacement_required: toBoolean(row.replacement_required),
  shop_visit_required: toBoolean(row.shop_visit_required),
  warranty_status: row.warranty_status,
  removal_location: row.removal_location,
  scheduled_maintenance: toBoolean(row.scheduled_maintenance),
  removal_priority: row.removal_priority,
  cost_estimate: toInteger(row.cost_estimate),
  supplier_code: row.supplier_code,
  installation_date: row.installation_date
});

// Relationships
CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_aircraft_system.csv' AS row
  MATCH (a:Aircraft {aircraft_id: row[":START_ID(Aircraft)"]}), (s:System {system_id: row[":END_ID(System)"]})
  CREATE (a)-[:HAS_SYSTEM]->(s)
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_system_component.csv' AS row
  MATCH (s:System {system_id: row[":START_ID(System)"]}), (c:Component {component_id: row[":END_ID(Component)"]})
  CREATE (s)-[:HAS_COMPONENT]->(c)
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_system_sensor.csv' AS row
  MATCH (s:System {system_id: row[":START_ID(System)"]}), (sn:Sensor {sensor_id: row[":END_ID(Sensor)"]})
  CREATE (s)-[:HAS_SENSOR]->(sn)
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_component_event.csv' AS row
  MATCH (c:Component {component_id: row[":START_ID(Component)"]}), (m:MaintenanceEvent {event_id: row[":END_ID(MaintenanceEvent)"]})
  CREATE (c)-[:HAS_EVENT]->(m)
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_component_removal.csv' AS row
  MATCH (c:Component {component_id: row[":START_ID(Component)"]}), (r:Removal {removal_id: row[":END_ID(RemovalEvent)"]})
  CREATE (r)-[:REMOVED_COMPONENT]->(c)
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_aircraft_removal.csv' AS row
  MATCH (a:Aircraft {aircraft_id: row[":START_ID(Aircraft)"]}), (r:Removal {removal_id: row[":END_ID(RemovalEvent)"]})
  CREATE (a)-[:HAS_REMOVAL]->(r)
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_aircraft_flight.csv' AS row
  MATCH (a:Aircraft {aircraft_id: row[":START_ID(Aircraft)"]}), (f:Flight {flight_id: row[":END_ID(Flight)"]})
  CREATE (a)-[:OPERATES_FLIGHT]->(f)
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_flight_departure.csv' AS row
  MATCH (f:Flight {flight_id: row[":START_ID(Flight)"]}), (ap:Airport {airport_id: row[":END_ID(Airport)"]})
  CREATE (f)-[:DEPARTS_FROM]->(ap)
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_flight_arrival.csv' AS row
  MATCH (f:Flight {flight_id: row[":START_ID(Flight)"]}), (ap:Airport {airport_id: row[":END_ID(Airport)"]})
  CREATE (f)-[:ARRIVES_AT]->(ap)
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_flight_delay.csv' AS row
  MATCH (f:Flight {flight_id: row[":START_ID(Flight)"]}), (d:Delay {delay_id: row[":END_ID(Delay)"]})
  CREATE (f)-[:HAS_DELAY]->(d)
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_event_system.csv' AS row
  MATCH (m:MaintenanceEvent {event_id: row[":START_ID(MaintenanceEvent)"]}), (s:System {system_id: row[":END_ID(System)"]})
  CREATE (m)-[:AFFECTS_SYSTEM]->(s)
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'file:///rels_event_aircraft.csv' AS row
  MATCH (m:MaintenanceEvent {event_id: row[":START_ID(MaintenanceEvent)"]}), (a:Aircraft {aircraft_id: row[":END_ID(Aircraft)"]})
  CREATE (m)-[:AFFECTS_AIRCRAFT]->(a)
} IN TRANSACTIONS OF 1000 ROWS;

// ---- Example Queries ----

// 1) Flights delayed due to maintenance and implicated components
MATCH (f:Flight)-[:HAS_DELAY]->(d:Delay {cause:'Maintenance'})
MATCH (a:Aircraft)-[:OPERATES_FLIGHT]->(f)
MATCH (a)-[:HAS_SYSTEM]->(s:System {type:'Engine'})-[:HAS_COMPONENT]->(c)-[:HAS_EVENT]->(m:MaintenanceEvent)
RETURN f.flight_id, a.tail_number, s.name AS engine, c.name AS component, m.fault, m.severity, d.minutes
ORDER BY d.minutes DESC LIMIT 50;

// 2) Sensors monitoring engines
MATCH (s:System {type:'Engine'})-[:HAS_SENSOR]->(sn:Sensor {type:'EGT'})
RETURN s.name AS engine, sn.sensor_id, sn.name ORDER BY engine;

// 3) CRITICAL events by component type
MATCH (:System)-[:HAS_COMPONENT]->(c)-[:HAS_EVENT]->(m:MaintenanceEvent {severity:'CRITICAL'})
RETURN c.type, count(*) AS cnt ORDER BY cnt DESC;

// 4) Component removals by reason with cost analysis
MATCH (r:Removal)-[:REMOVED_COMPONENT]->(c:Component)
RETURN r.RMV_REA_TX AS removal_reason,
       count(*) AS occurrence_count,
       avg(r.cost_estimate) AS avg_cost,
       sum(r.cost_estimate) AS total_cost,
       avg(r.flight_hours_at_removal) AS avg_hours_at_removal
ORDER BY occurrence_count DESC;

// 5) Aircraft with highest removal costs
MATCH (a:Aircraft)-[:HAS_REMOVAL]->(r:Removal)
RETURN a.tail_number, a.model,
       count(r) AS removal_count,
       sum(r.cost_estimate) AS total_removal_cost,
       avg(r.cost_estimate) AS avg_removal_cost
ORDER BY total_removal_cost DESC LIMIT 10;

// 6) Warranty vs out-of-warranty removal analysis
MATCH (r:Removal)-[:REMOVED_COMPONENT]->(:Component)
WITH r.warranty_status AS warranty,
     count(*) AS count,
     avg(r.cost_estimate) AS avg_cost,
     sum(r.cost_estimate) AS total_cost
RETURN warranty, count, avg_cost, total_cost
ORDER BY total_cost DESC;

// 7) Component reliability analysis - time between installation and removal
MATCH (r:Removal)-[:REMOVED_COMPONENT]->(c:Component)
WHERE r.time_since_install IS NOT NULL
RETURN c.type AS component_type,
       avg(r.time_since_install) AS avg_time_to_removal_hours,
       min(r.time_since_install) AS min_time_to_removal,
       max(r.time_since_install) AS max_time_to_removal,
       count(*) AS removal_count
ORDER BY avg_time_to_removal_hours ASC;
