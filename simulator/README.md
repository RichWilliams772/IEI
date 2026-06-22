# Electrical Diagram Simulator

A simple educational single-line electrical diagram simulator with a continuously running FastAPI backend and a lightweight browser dashboard.

This is not a full transient power-system simulator. It uses readable steady-state relationships so the model is easy to inspect, change, and test.

## What It Simulates

- Source voltage
- Buses
- Step-down and step-up transformer voltage math
- Breaker open/close isolation
- Load and consumer-load power calculations
- Basic meter readings
- Optional asynchronous generator state
- Continuous background stepping at the model sampling rate

## Run It

From the repository root:

```bash
pip install -r simulator/requirements.txt
python -m uvicorn simulator.backend.api:app --host 0.0.0.0 --port 8000
```

Then open:

```text
http://localhost:8000/
```

Other launch options:

```bash
python simulator/run_server.py
```

```bash
simulator/run_server.bat
```

The backend starts the simulation loop automatically. The dashboard polls `/api/model`, `/api/state`, and `/api/simulation/status`.

## Model File

The example system is defined in:

```text
simulator/example_model.json
```

The backend loads this file at startup through `ModelLoader.load_example_model()`.

Current example components:

- `source-1` - Utility Source, 13.8 kV
- `bus-main` - Main Bus, 13.8 kV
- `meter-main` - Main Meter, 13.8 kV
- `transformer-t1` - Transformer, 13.8 kV to 480 V
- `breaker-main` - Main breaker
- `bus-load` - Load Bus, 480 V
- `breaker-load` - Load-side breaker
- `load-panel` - Load Panel, 480 V
- `meter-load` - Load Meter, 480 V
- `load-1` - 100 kW load at 0.9 power factor
- `consumer-load-1` - 200 kW consumer load at 0.85 power factor
- `async-generator-1` - 500 kW asynchronous generator, optional operation

## How Points Are Connected

The simulator uses a very simple single-line connection model:

1. Components are connected left-to-right by their `position.x` value in `example_model.json`.
2. Lower `x` values are upstream. Higher `x` values are downstream.
3. If two components have the same `x`, `position.y` and then `id` are used only for stable ordering.
4. The first source energizes the path.
5. A transformer changes the current path voltage.
6. A closed breaker passes voltage downstream.
7. An open breaker stops voltage for everything downstream of that breaker.
8. Loads consume power only when their section is energized.
9. Meters read the energized section at their point on the line.

This means the `position` field is not just visual. In this basic simulator, it is also the connection order.

### Example Connection Order

The default model behaves like this:

```text
source-1
  -> bus-main
  -> meter-main
  -> transformer-t1
  -> breaker-main
  -> bus-load
  -> breaker-load
  -> load-panel
  -> meter-load
  -> load-1
  -> consumer-load-1
  -> async-generator-1
```

### Breaker Sections

`breaker-main` isolates the entire 480 V load side:

```text
source-1 -> bus-main -> meter-main -> transformer-t1 -> breaker-main [OPEN]
                                                          downstream off
```

When `breaker-main` is open:

- upstream source/main bus/main meter remain energized
- load bus, load breaker, load panel, load meter, loads, and generator are de-energized

`breaker-load` isolates only the final load section:

```text
source-1 -> transformer-t1 -> breaker-main -> bus-load -> breaker-load [OPEN]
                                                                 downstream off
```

When `breaker-load` is open:

- source, main bus, transformer, main breaker, and load bus remain energized
- load panel, load meter, loads, and generator are de-energized

Closing a breaker restores downstream voltage if every upstream breaker is closed and energized.

## Adding Or Moving Simulation Points

To add a new point, add an object to `components` in `example_model.json`.

Required fields:

```json
{
  "id": "bus-new",
  "type": "bus",
  "name": "New Bus",
  "position": {"x": 650, "y": 100},
  "voltage_rating": "480 V"
}
```

Choose `position.x` based on where the point belongs in the single-line sequence:

- put it before a breaker to make it upstream of that breaker
- put it after a breaker to make it downstream of that breaker
- put a meter at the point where you want section readings
- put a load after the breaker that should control it

For example, to add a second load controlled by `breaker-load`, give it an `x` value greater than `breaker-load`:

```json
{
  "id": "load-2",
  "type": "load",
  "name": "Load 50 kW",
  "position": {"x": 850, "y": 180},
  "power_rating": 50,
  "power_factor": 0.95,
  "voltage_rating": "480 V"
}
```

After editing the model, restart the server or call:

```http
POST /api/model/reload
```

## Component Types

### Source

Provides the starting voltage for the single-line path.

Important fields:

- `voltage_rating`
- `voltage_db`
- `voltage_default`
- `voltage_upper_limit`
- `voltage_lower_limit`

### Bus

A named point on the line. It receives the current path voltage if energized.

Important fields:

- `voltage_rating`

### Transformer

Changes voltage based on `primary_voltage` and `secondary_voltage`.

The default transformer maps:

- 13.8 kV to 480 V
- 480 V to 13.8 kV when used in reverse math

Important fields:

- `primary_voltage`
- `secondary_voltage`
- `turns_ratio` optional

### Breaker

Passes or blocks the energized path.

Important fields:

- `state`: `true` means closed, `false` means open

### Load

Consumes real power when energized.

Important fields:

- `power_rating` in kW
- `power_factor`
- `voltage_rating`

### Consumer Load

Same basic math as `load`, with optional unexpected draw.

Important fields:

- `power_rating` in kW
- `power_factor`
- `unexpected_draw_multiplier`
- `is_unexpected_draw_active`

### Meter

Reports readings at its point in the line.

Meter output includes:

- `voltage` in V
- `current` in A
- `real_power` in kW
- `reactive_power` in kVAR
- `apparent_power` in kVA
- `power_factor`
- `frequency` in Hz
- `energized`

### Asynchronous Generator

Can be toggled operational. This remains intentionally basic: when operational and energized, it reports configured real/reactive capability.

Important fields:

- `power_rating` in kW
- `is_operational`
- `target_power_factor`
- `reactive_power_capability` in kVAR

## API Endpoints

### Dashboard

```http
GET /
```

Serves the browser dashboard.

### API Info

```http
GET /api
```

Returns basic API metadata.

### Health

```http
GET /health
```

Returns `{"status": "healthy"}`.

### Model

```http
GET /api/model
```

Returns the loaded model.

```http
POST /api/model/reload
```

Reloads `example_model.json`.

### State

```http
GET /api/state
```

Returns current simulation state. The state is updated continuously in the background.

### Simulation Status

```http
GET /api/simulation/status
```

Returns whether the background simulation loop is running and the active sampling rate.

### Manual Step

```http
POST /api/simulate/step
```

Runs one simulation step manually. This is mostly useful for debugging because the loop runs continuously.

### Breakers

```http
POST /api/breakers/{breaker_id}/open
POST /api/breakers/{breaker_id}/close
```

Examples:

```bash
curl -X POST http://localhost:8000/api/breakers/breaker-main/open
curl -X POST http://localhost:8000/api/breakers/breaker-main/close
```

Invalid breaker IDs return `404`.

### Consumer Load Unexpected Draw

```http
POST /api/consumer_load/{consumer_load_id}/unexpected_draw?unexpected_draw_active=true&multiplier=1.5
```

Example:

```bash
curl -X POST "http://localhost:8000/api/consumer_load/consumer-load-1/unexpected_draw?unexpected_draw_active=true&multiplier=1.5"
```

Invalid consumer load IDs return `404`.

### Asynchronous Generator Operation

```http
POST /api/async_generator/{generator_id}/operational?operational=true
```

Example:

```bash
curl -X POST "http://localhost:8000/api/async_generator/async-generator-1/operational?operational=true"
```

Invalid generator IDs return `404`.

## Units In `/api/state`

The backend returns simple, consistent units:

- `voltage`: volts
- `current`: amps
- `real_power`: kW
- `reactive_power`: kVAR
- `apparent_power`: kVA
- `power_factor`: ratio from 0 to 1
- `frequency`: Hz
- `energized`: boolean

## Accessing Points For Logging And ML

Every simulation point is available through the API as JSON. The main endpoint for logging and ML collection is:

```http
GET /api/state
```

Use `/api/model` to get static metadata such as component names, types, positions, and ratings. Use `/api/state` to get live values.

### Recommended Collection Pattern

1. Call `GET /api/model` once when your logger starts.
2. Store the component metadata by `id`.
3. Poll `GET /api/state` at the rate you need.
4. Flatten each component state into one row per timestamp and component.
5. Write those rows to CSV, Parquet, a database, or a message queue.

The simulator runs internally at `sampling_rate_ms`, currently 16 ms in `example_model.json`. Your logger does not need to poll that fast. For ML experiments, 250 ms, 500 ms, or 1 second sampling is usually easier to inspect.

### Stable Point IDs

The current model exposes these point IDs:

```text
source-1
bus-main
meter-main
transformer-t1
breaker-main
bus-load
breaker-load
load-panel
meter-load
load-1
consumer-load-1
async-generator-1
```

Use the `id` field as the stable key in logs and ML datasets. Names are for display and can change more easily.

### Useful State Fields

Each component in `/api/state.components` uses this shape:

```json
{
  "id": "meter-load",
  "type": "meter",
  "name": "Load Meter",
  "state": null,
  "voltage": 480.0,
  "current": 746.2,
  "real_power": 300.0,
  "reactive_power": 172.3,
  "apparent_power": 346.4,
  "power_factor": 0.866,
  "frequency": 60.0,
  "energized": true
}
```

Not every field is meaningful for every component. For example, breakers use `state`, loads use power fields, and meters summarize readings at their point.

### Suggested Flat Log Schema

For logging and ML, flatten nested JSON into rows like this:

```text
timestamp,component_id,type,name,energized,state,voltage,current,real_power,reactive_power,apparent_power,power_factor,frequency
```

Example row:

```text
1719000000.123,meter-load,meter,Load Meter,true,,480.0,746.2,300.0,172.3,346.4,0.866,60.0
```

This row-based format works well for:

- CSV exports
- pandas DataFrames
- time-series databases
- feature generation
- supervised ML labels joined by timestamp

### Minimal Python Logger Example

This example polls `/api/state` once per second and writes one CSV row per component.

```python
import csv
import time
import urllib.request
import json

BASE_URL = "http://localhost:8000"
OUTPUT_FILE = "simulator_points.csv"
INTERVAL_SECONDS = 1.0

FIELDS = [
    "timestamp",
    "component_id",
    "type",
    "name",
    "energized",
    "state",
    "voltage",
    "current",
    "real_power",
    "reactive_power",
    "apparent_power",
    "power_factor",
    "frequency",
]


def get_json(path):
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


with open(OUTPUT_FILE, "a", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=FIELDS)
    if file.tell() == 0:
        writer.writeheader()

    while True:
        state = get_json("/api/state")
        timestamp = state.get("timestamp")

        for component_id, point in state["components"].items():
            writer.writerow({
                "timestamp": timestamp,
                "component_id": component_id,
                "type": point.get("type"),
                "name": point.get("name"),
                "energized": point.get("energized"),
                "state": point.get("state"),
                "voltage": point.get("voltage"),
                "current": point.get("current"),
                "real_power": point.get("real_power"),
                "reactive_power": point.get("reactive_power"),
                "apparent_power": point.get("apparent_power"),
                "power_factor": point.get("power_factor"),
                "frequency": point.get("frequency"),
            })

        file.flush()
        time.sleep(INTERVAL_SECONDS)
```

### Joining State With Model Metadata

For ML, you may want both live values and static model context. Join `/api/state` rows with `/api/model` by component `id`.

Useful static fields from `/api/model`:

- `type`
- `name`
- `position.x`
- `position.y`
- `voltage_rating`
- `power_rating`
- `power_factor`
- breaker default `state`

Example feature ideas:

- voltage by point
- current by meter
- energized state by component
- breaker open/closed state
- load real/reactive/apparent power
- consumer load unexpected draw state
- distance/order from source using `position.x`

### Labeling Events

For simple ML experiments, use API actions to create known events:

```bash
curl -X POST http://localhost:8000/api/breakers/breaker-main/open
curl -X POST http://localhost:8000/api/breakers/breaker-main/close
curl -X POST http://localhost:8000/api/breakers/breaker-load/open
curl -X POST http://localhost:8000/api/breakers/breaker-load/close
curl -X POST "http://localhost:8000/api/consumer_load/consumer-load-1/unexpected_draw?unexpected_draw_active=true&multiplier=1.5"
curl -X POST "http://localhost:8000/api/consumer_load/consumer-load-1/unexpected_draw?unexpected_draw_active=false"
```

Log the time when you trigger each action. That timestamp can become an event label such as:

- `main_breaker_open`
- `load_breaker_open`
- `unexpected_consumer_draw`
- `normal`

### Practical Notes

- Poll `/api/state` for live values.
- Poll `/api/model` only when the model changes.
- Use component `id`, not display `name`, as the dataset key.
- Keep raw logs before feature engineering.
- Store timestamps from `/api/state.timestamp` so all component rows from one sample share the same simulation time.
- If you edit `example_model.json`, call `POST /api/model/reload` before collecting a new dataset.

## Tests

Run:

```bash
python simulator/tests.py
```

The tests cover:

- model loading
- transformer step-down and step-up math
- main and load breaker behavior
- voltage restoration after breaker close
- meter voltage/current/kW/kVAR/kVA/power factor/frequency/energized state
- invalid IDs
- dashboard and API endpoint smoke checks
