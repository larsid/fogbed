# COVID Device Simulator

A lightweight Python service that emulates a medical IoT device streaming anonymised vital signs to a remote COVID-19 monitoring platform. The simulator is useful for testing integrations, demos, and local development without requiring physical hardware.

---

## Table of contents
- [Project status](#project-status)
- [Features](#features)
- [System overview](#system-overview)
- [Getting started](#getting-started)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Running the simulator](#running-the-simulator)
  - [Docker](#docker)
- [Configuration](#configuration)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Project status
Prototype. The simulator is stable for local testing but has not been hardened for production workloads.

## Features
- Registers a synthetic device with a configurable REST API.
- Periodically publishes randomised vital-sign payloads (temperature, heart rate, blood pressure, respiratory rate).
- Cleans up remote records on shutdown when possible.
- Ships with Docker packaging for easy deployment.

## System overview
```
┌────────────┐     HTTP(S)      ┌─────────────────────┐
│ covid-device├─────────────────► Remote monitoring API│
└────────────┘  JSON payloads   └─────────────────────┘
```

All application logic resides in [`device.py`](device.py).

1. Resolve a device identifier from the `UID` environment variable or generate a UUID4.
2. Register the device by POSTing to `/users` at the configured base `URL`.
3. Enter an update loop, sending PUT requests to `/users/{id}` with fresh vitals every 2–5 seconds.
4. Attempt to delete the remote record (`DELETE /users/{id}`) when the process stops unexpectedly.

### Sample message formats

Registration request (`POST /users`):

```json
{
  "name": "device-1234",
  "temperature": 37.2,
  "heart_rate": 82,
  "blood_pressure": 118,
  "respiratory_rate": 18
}
```

Typical response body:

```json
{
  "data": {
    "id": 42
  }
}
```

Subsequent update request (`PUT /users/{id}`) uses the same schema as registration and targets the identifier provided by the API:

```json
{
  "name": "device-1234",
  "temperature": 36.8,
  "heart_rate": 90,
  "blood_pressure": 110,
  "respiratory_rate": 20
}
```

## Getting started

### Requirements
- Python 3.9+
- [`pip`](https://pip.pypa.io/) for dependency management
- Optional: Docker 20.10+

### Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the simulator
```bash
python device.py
```
The simulator continues until interrupted (Ctrl+C), logging each request to stdout.

### Docker
Build and run the containerised simulator:
```bash
docker build -t covid-device .
docker run --rm \
  -e URL="http://your-api:8000" \
  -e BIND_IP="10.0.0.15" \
  covid-device
```

## Configuration
Configure behaviour with environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `URL`    | Base URL of the monitoring API. | `http://localhost:8000` |
| `UID`    | Fixed identifier for the device. A UUID4 is generated when omitted. | *(generated)* |
| `BIND_IP` | Optional local address used when establishing outbound HTTP connections. Useful when the container must communicate using a specific interface (for example, the emulator-provided 10.x.x.x address). | *(unset)* |
| `INTERVAL_MIN` | Minimum seconds between updates. | `2` |
| `INTERVAL_MAX` | Maximum seconds between updates. | `5` |

When `BIND_IP` is provided the simulator binds its HTTP client to that address before contacting the remote API. This ensures the
source IP of requests originates from the specified network interface, which is particularly helpful when running inside network
emulators that expose multiple IP ranges.

> **Tip:** Use a reverse proxy or tunnelling service when testing against remote APIs.

## Development
1. Clone the repository and create a feature branch.
2. Create/activate a virtual environment and install dependencies (`pip install -r requirements.txt`).
3. Run `python device.py` to verify the simulator communicates with your API.
4. Add or update tests/documentation as required.
5. Submit a pull request.

## Troubleshooting
| Symptom | Resolution |
|---------|------------|
| `ConnectionError` when starting | Ensure the API defined by `URL` is reachable. Update the environment variable or start a local mock server. |
| HTTP 4xx responses | Confirm the target API exposes `/users` endpoints with POST/PUT/DELETE semantics expected by the simulator. |
| Device records remain after exit | The cleanup step only runs on handled exceptions; manually remove stale records if the process is terminated forcefully. |

## Contributing
Issues and pull requests are welcome. Please describe the scenario you are testing and include reproduction steps where possible.

## License
Specify the license that applies to the project (e.g., MIT, Apache 2.0). Update this section when a license is chosen.
