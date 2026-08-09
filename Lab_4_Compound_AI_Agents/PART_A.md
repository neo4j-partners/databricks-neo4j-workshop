# Part A: Genie space for Aircraft Sensor Analytics

In this part, you'll create a Databricks AI/BI Genie space that enables natural language queries over your aircraft sensor telemetry data. This Genie will become one of the sub-agents in your multi-agent system.


---

## Step 1: Explore the Lakehouse Data

Your workshop admin has pre-loaded a set of tables into Unity Catalog that represent the Aircraft Digital Twin sensor telemetry. This is the data you will use to create your Genie space — a natural language interface that lets agents query sensor readings, compare fleet metrics, and detect anomalies using SQL under the hood.

1. Click **Catalog** in the left sidebar.
2. Expand **databricks-neo4j-workshop > aircraft**.
3. Browse the available tables:

| Table | Description |
|-------|-------------|
| `aircraft` | Fleet inventory — tail numbers, models, manufacturers, operators |
| `systems` | Aircraft systems — engines, avionics, hydraulics |
| `sensors` | Sensor metadata — EGT, vibration, N1 speed, fuel flow |
| `sensor_readings` | Telemetry readings every 4 hours over 90 days (July–September 2024) |

4. Click on any table (e.g., `sensor_readings`) and select the **Sample Data** tab to preview its contents.

![Lakehouse sensor_readings table in Unity Catalog](images/lakehouse_sensor_readings.png)

These four tables form a join chain — `sensor_readings` → `sensors` → `systems` → `aircraft` — that connects raw telemetry values all the way up to fleet-level metadata. The Genie space you create in the next steps will use this structure to answer natural language questions by generating SQL queries across these tables automatically.

---

## Step 2: Create the Genie space

### 2.1 Navigate to AI/BI Genie

1. In your Databricks workspace, click **New** > **Genie space**
2. Or navigate to **AI/BI** in the left sidebar and click **New Genie space**

### 2.2 Connect Your Data

After clicking **New Genie space**, the **Connect your data** dialog appears. Select All Catalogs ->  `databricks-neo4j-workshop`  -> `aircraft` -> then select `sensor_readings`, `aircraft`, `sensors`, `systems`.

> **Tip:** These tables form a join chain: `sensor_readings` -> `sensors` -> `systems` -> `aircraft`


![Connect your data dialog](images/genie_connect_data.png)

> **Tip:** If you don't see the table under **Recent**, click **All** or use the search bar to find `databricks-neo4j-workshop`.

### 2.3 Configure Basic Settings

Once the Genie space is created, click **Configure** in the top navigation bar, then select the **Settings** tab:

![Genie space Configure > Settings panel](images/configure_basics_genie.png)

1. **Title:** `Aircraft Sensor Analyst [YOUR_INITIALS]`
   - Example: `Aircraft Sensor Analyst RK`
2. **Description:** "Analyzes aircraft engine sensor telemetry including EGT, vibration, N1 speed, and fuel flow metrics"
3. **Default warehouse:** Select a **Serverless SQL Warehouse**

### 2.4 Add Sample Questions

Still on the **Settings** tab, scroll down to **Sample questions**. These train the Genie to understand domain-specific language. Click **+ Add** and enter these examples:

**Time-Series Analytics**

```
What is the average EGT temperature for aircraft N10000 over the last 30 days?
```

**Fleet Comparisons**

```
Compare average EGT temperatures between Boeing 737 and Airbus A320 aircraft
```

**Anomaly Detection**

```
Find sensors with readings above their 95th percentile value
```

**Trend Analysis**

```
Show the trend of EGT temperatures over the 90-day period for aircraft N10000
```

---

## Step 3: Add Instructions

Navigate to **Configure** > **Instructions**. Instructions provide domain knowledge and query conventions. These instructions give the Genie domain knowledge about sensor types, normal ranges, and data conventions so it can generate accurate SQL queries. Enter the following:

```
# Aircraft Sensor Analytics Domain Knowledge

## Sensor Types and Normal Ranges
- EGT (Exhaust Gas Temperature): unit column value °C. The normal range is per model, taken from each maintenance manual's takeoff limits: A320-200 620-680, A220-300 855-890, E190 870-900, B737-800 900-950, A321neo 980-1040. Always filter or group by model before comparing EGT across aircraft.
- Vibration: Normal range 0.05-0.50 inches per second, unit column value ips
- N1Speed (Fan Speed N1): Normal range 85-100, unit column value % RPM
- FuelFlow: unit column value kg/s. The normal range is per model: E190 1.00-1.20, A220-300 1.15-1.35, B737-800 1.20-1.50, A320-200 1.20-1.95, A321neo 1.50-2.00.

## Fleet Information
- Operators: ExampleAir, SkyWays, RegionalCo, NorthernJet
- Models: B737-800 by Boeing, A320-200 by Airbus, A321neo by Airbus, E190 by Embraer, A220-300 by Airbus

## Sensor Configuration
- Each aircraft has 2 engines
- Each engine has 4 sensors: EGT, Vibration, N1Speed, FuelFlow

## Data Conventions
- Timestamps are stored as timestamp type in the `timestamp` column
- Data period: July 1, 2024 to September 28, 2024 (90 days)
- Readings are every 4 hours (6 per day per sensor)

## Sensor ID Format
- Format: AC{aircraft_number}-S{system_number}-SN{sensor_number}
- Example: AC1001-S01-SN01 = Aircraft 1001, Engine 1 (S01), EGT sensor (SN01)
- S01 and S02 are always engines; S03 is Avionics; S04 is Hydraulics
- SN01=EGT, SN02=Vibration, SN03=N1Speed, SN04=FuelFlow

## Engine Names by Model
The `systems` table stores each engine as a system named after its engine model, so these are the exact strings to match on.
- B737-800: CFM56-7B
- A320-200: CFM56-5B
- A321neo: LEAP-1A
- E190: CF34-10E
- A220-300: PW1500G

## Query Conventions
- When asked about "Engine 1", filter by systems where name contains "#1"
- When asked about "Engine 2", filter by systems where name contains "#2"
- Use tail_number for human-readable aircraft references (e.g., N10000)
- Use aircraft_id for internal references (e.g., AC1001)
- Always include units in results (°C, ips, % RPM, kg/s)
```

---

## Step 4: Test the Genie

### 4.1 Start a Conversation

Click **Start conversation** or go to the chat interface.

### 4.2 Test Basic Queries

Try these progressively complex queries:

**Query 1: Simple Aggregation**
```
What is the average EGT temperature across all sensors?
```
Expected: A single number around 865 degrees Celsius. The fleet mixes models whose EGT bands run from 620-680 on the A320-200 up to 980-1040 on the A321neo, so a fleet-wide average sits between them and is not meaningful on its own.

**Query 2: Filtering by Aircraft**
```
Show the average EGT for aircraft N10000
```
Expected: Average EGT for that specific aircraft

**Query 3: Time-Series Trend**
```
Show daily average EGT for aircraft AC1001 in July 2024
```
Expected: ~30 rows with date and average value

**Query 4: Cross-Table Join**
```
Compare average vibration readings by aircraft model
```
Expected: Results grouped by B737-800, A320-200, A321neo, E190

**Query 5: Statistical Analysis**
```
Find the top 5 sensors with the highest average readings for their type
```
Expected: Top sensors with their average values and types

### 4.3 View the SQL Generation

For each query, click **View Code** to see the generated query is correct:

Example for "Compare average vibration by aircraft model":
```sql
SELECT
    a.model,
    AVG(r.value) as avg_vibration,
    COUNT(*) as reading_count
FROM sensor_readings r
JOIN sensors sen ON r.sensor_id = sen.sensor_id
JOIN systems s ON sen.system_id = s.system_id
JOIN aircraft a ON s.aircraft_id = a.aircraft_id
WHERE sen.type = 'Vibration'
GROUP BY a.model
ORDER BY avg_vibration DESC
```

---

## Step 5: Save and Note the Genie space ID

### 5.1 Save Configuration

Click **Save** to preserve your Genie space configuration.

### 5.2 Record the Genie space ID

Copy the space ID out of the browser address bar. The URL reads
`.../genie/rooms/<SPACE_ID>`, and the ID is the 32-character value after
`rooms/`.

Save it. Lab 5 asks for it as `GENIE_SPACE_ID` in Section 1, and Lab 6 asks for
the same value in Section 2. The space name is not a substitute: every
participant titles their space differently, so nothing downstream looks a space
up by name.

---

## Summary

You've created a Genie space that can:

- Query sensor telemetry readings using natural language
- Aggregate by aircraft, model, operator, or sensor type
- Perform statistical analysis (averages, percentiles, standard deviation)
- Join across the data model to provide context-rich answers
- Understand domain-specific terminology (EGT, N1Speed, etc.)

---

## Additional Sample Queries

Want to add more sample questions to your Genie space or test further? Here are additional queries organized by category:

**Time-Series Analytics**

```
Show daily average vibration readings for Engine 1 on aircraft AC1001
```

```
What was the maximum fuel flow recorded in August 2024?
```

**Fleet Comparisons**

```
Which aircraft has the highest average vibration readings?
```

```
Show fuel flow rates by operator
```

**Anomaly Detection**

```
Show all EGT readings above 950 degrees Celsius for B737-800 aircraft
```

```
Which engines have N1 speed readings outside the normal range of 85-100% RPM?
```

**Trend Analysis**

```
Calculate the 7-day rolling average of vibration for Engine 1 on AC1001
```

---

## Next Steps

Your Genie space answers questions about *how much* and *how often*. Average EGT on a tail number over 30 days, the maximum fuel flow in August, which aircraft vibrates most. Every one of those is an aggregation over timestamped rows, and SQL over the Lakehouse is the right tool for all of them.

Ask it "which component failure delayed which flight" and it has nothing to work with. That question is a traversal: component to maintenance event to flight to delay, following relationships rather than scanning a column. No amount of Genie instruction tuning produces it, because the relationships are in Neo4j and Genie queries Unity Catalog.

Two ways to give an agent both. You build one, you watch the other.

| | What it is | Graph it queries |
|---|---|---|
| **[Lab 5](../Lab_5_LangGraph_Agent)**, you build it | A LangGraph supervisor in Python, routing across Genie, Cypher, and the GraphRAG retrievers from Lab 3, then deployed to Model Serving | **Your own** Aura instance, the one you loaded in Lab 2 and Lab 3 |
| **[Part B](PART_B.md)**, the instructor demonstrates it | The same routing idea with no code, using the Agent Bricks Multi-Agent Supervisor and a governed MCP connection | The instructor's demo instance |

Continue to Lab 5. Part B is the same architecture seen from the other direction: no code, and centrally governed access to Neo4j through Unity Catalog. That contrast is why it is in the workshop. Watching it needs nothing from you, no Aura instance, no MCP connection, and no credentials.
