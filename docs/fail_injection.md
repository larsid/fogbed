# Fail Injection
Fogbed can inject failures into containers and virtual instances to evaluate the resilience of fog applications. The same API works in local and distributed emulation: fail models are attached with the `fail_model` parameter and a `FailController` runs them while the experiment is running.

## Fail Models
| Model | Behavior |
|---|---|
| `CrashFail` | Removes the container and its link after `life_time` seconds. The node stays down until the controller is stopped. |
| `DisconnectFail` | Disables the container link after `life_time` seconds, keeping the container state. |
| `AvailabilityFail` | Splits time into slots of `slot_time` seconds and keeps the nodes up for an `availability` fraction of the slots, using crash or disconnect according to `availability_mode`. |

When a model is attached to a virtual instance, it applies to the containers of that instance:

- `CrashFail` and `DisconnectFail` select `fail_rate` of the containers. `split_method` rounds the amount up (`UP`), down (`DOWN`) or randomly with the expected value (`RANDOM`), and `selection_method` picks the first containers (`SEQUENTIAL`) or random ones (`RANDOM`).
- `AvailabilityFail` takes down, in each slot, enough random containers to keep the instance availability at the requested value.

When attached to a container, the model applies only to it. For `AvailabilityFail`, the container stays up in the first slots of each cycle, for example 1 of every 2 slots for `availability=0.5`.

```py
from fogbed import AvailabilityFail, AvailabilityMode, Container, CrashFail

edge = exp.add_virtual_instance('edge', fail_model=AvailabilityFail(
    availability=0.5, 
    slot_time=2, 
    availability_mode=AvailabilityMode.DISCONNECT
))
d1 = Container('d1', fail_model=CrashFail(life_time=20))
```

## Local Emulation
```py title="local.py"
import time

from fogbed import (
    AvailabilityFail, AvailabilityMode, Container, CrashFail,
    FailController, FogbedExperiment, setLogLevel
)

setLogLevel('info')

exp  = FogbedExperiment()
fog  = exp.add_virtual_instance('fog')
edge = exp.add_virtual_instance('edge', fail_model=AvailabilityFail(
    availability=0.5, slot_time=2, availability_mode=AvailabilityMode.DISCONNECT))

exp.add_docker(Container('gw'), fog)
exp.add_docker(Container('d1', fail_model=CrashFail(life_time=20)), edge)
exp.add_docker(Container('d2'), edge)
exp.add_link(fog, edge)

fails = FailController(exp, seed=42)

try:
    exp.start()
    fails.start()
    time.sleep(60)
    print(fails.metrics())
finally:
    try:
        fails.stop()
    finally:
        exp.stop()
```

## Distributed Emulation
In distributed emulation, the controller groups the fail models by worker and sends each worker a fail plan with a common start time. Each worker executes its plan locally, so the network latency between the machines does not affect the timing of the failures.

```py title="distributed.py"
exp  = FogbedDistributedExperiment()
fog  = exp.add_virtual_instance('fog')
edge = exp.add_virtual_instance('edge', fail_model=AvailabilityFail(
    availability=0.5, slot_time=2, availability_mode=AvailabilityMode.DISCONNECT))

exp.add_docker(Container('gw'), fog)
exp.add_docker(Container('d1', fail_model=CrashFail(life_time=20)), edge)
exp.add_docker(Container('d2'), edge)

worker1 = exp.add_worker(ip='192.168.0.151')
worker2 = exp.add_worker(ip='192.168.0.152')
worker1.add(fog, reachable=True)
worker2.add(edge, reachable=True)
exp.add_tunnel(worker1, worker2)

fails = FailController(exp, seed=42, start_delay=2.0, max_clock_skew=0.5)

try:
    exp.start()
    fails.start()
    time.sleep(60)
    events = fails.events()
finally:
    try:
        fails.stop()
    finally:
        exp.stop()
```

!!! warning
    The workers must run `fogbed worker`, which serves the fail routes, and 
    their clocks should be synchronized with NTP. The controller measures the 
    clock offset of each worker on `start()`, shifts the start time of each 
    plan and the timestamps of its events by that offset, and logs a warning 
    when it exceeds `max_clock_skew` seconds.

## Controller
| Method | Description |
|---|---|
| `start()` | Schedules the fail models of the running experiment. |
| `stop()` | Cancels the failures and restores every failed node, raising `FailInjectionError` if a node cannot be restored. |
| `fail(name, mode)` | Immediately crashes (`'crash'`) or disconnects (`'disconnect'`) a container. |
| `recover(name)` | Immediately recovers a failed container. |
| `status()` | Returns the state of the fail models and nodes (per worker in distributed mode). |
| `events()` | Returns the transitions of the nodes, ordered by time. |
| `metrics()` | Returns uptime, downtime, failures, availability, MTBF and MTTR of each node. |

The `seed` parameter makes the random choices reproducible, so the same experiment yields the same failure sequence in local and distributed emulation.

Each event records the node, its state (`on` or `off`), the action (`crash`, `disconnect`, `recover` or `reconnect`), the timestamp and the source (`local` or the worker address).

## Recovery Semantics
- A crashed container is recreated with its original parameters, IP and MAC addresses, and switch port, so existing flows and ARP caches remain valid.
- A fail model only recovers the nodes it took down: a crashed container is not revived by an availability cycle.
- A crash takes over a disconnected container.

## Worker Routes
The `fogbed worker` command serves the clusternet routes plus the following ones:

| Method | Route | Description |
|---|---|---|
| POST | `/fails` | Registers the fail plan of the worker. |
| POST | `/fails/start` | Schedules the plan at its `start_at` time. |
| POST | `/fails/stop` | Cancels the failures and restores the nodes. |
| GET | `/fails/status` | Returns the state of the fail models and nodes and the worker clock. |
| GET | `/fails/events` | Returns the event log. |
| POST | `/containers/<name>/fail` | Immediately fails a container (`mode` is `crash` or `disconnect`). |
| POST | `/containers/<name>/recover` | Recovers a failed container. |
