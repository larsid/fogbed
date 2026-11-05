# Fail Injection
Fogbed can inject failures into containers and virtual instances to evaluate the resilience of fog and edge applications. Fail models are attached with the `fail_model` param and a `FailController` runs them while the experiment is running. The same API works in local and distributed emulation.

## Fail Models
* `CrashFail` - removes the container and its link after `life_time` seconds. The container stays down until the controller is stopped.
* `DisconnectFail` - disables the link of the container after `life_time` seconds and keeps the container state.
* `AvailabilityFail` - divides the time into slots of `slot_time` seconds and keeps the containers up in a fraction of the slots defined by `availability`. The `availability_mode` param defines if the containers are crashed or disconnected.

```py
from fogbed import AvailabilityFail, AvailabilityMode, Container, CrashFail

edge = exp.add_virtual_instance('edge', fail_model=AvailabilityFail(
    availability=0.5, 
    slot_time=2, 
    availability_mode=AvailabilityMode.DISCONNECT
))
d1 = Container('d1', fail_model=CrashFail(life_time=20))
```

A fail model attached to a container affects only that container. A fail model attached to a virtual instance affects the containers of the instance, and the following params define which containers fail.

* `fail_rate` - fraction of the containers affected by `CrashFail` and `DisconnectFail`.
* `split_method` - rounds the number of affected containers up (`SplitMethod.UP`), down (`SplitMethod.DOWN`) or randomly (`SplitMethod.RANDOM`).
* `selection_method` - selects the first containers (`SelectionMethod.SEQUENTIAL`) or random containers (`SelectionMethod.RANDOM`).

With `AvailabilityFail`, the virtual instance takes down random containers in each slot to keep the requested availability.


## Running the Failures
=== "Local"

    ```py title="local.py"
    import time

    from fogbed import (
        AvailabilityFail, AvailabilityMode, Container, CrashFail,
        FailController, FogbedExperiment
    )

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

=== "Distributed"

    ```py title="distributed.py"
    import time

    from fogbed import (
        AvailabilityFail, AvailabilityMode, Container, CrashFail,
        FailController, FogbedDistributedExperiment
    )

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

    fails = FailController(exp, seed=42)

    try:
        exp.start()
        fails.start()
        time.sleep(60)
        print(fails.events())
    finally:
        try:
            fails.stop()
        finally:
            exp.stop()
    ```

The `seed` param makes the random choices reproducible, so an experiment produces the same sequence of failures in local and distributed emulation.

In distributed emulation, each worker receives the fail models of its virtual instances and runs them locally from a common start time. This way the network latency between the machines does not change the timing of the failures.

!!! warning
    In distributed emulation the workers must run the `fogbed worker` command 
    and their clocks should be synchronized with NTP. The controller measures 
    the clock offset of each worker in `start()`, compensates it in the start 
    time and in the events, and logs a warning when the offset is greater than 
    `max_clock_skew` seconds.


## Fail Controller
* `start()` - starts the fail models of the running experiment.
* `stop()` - stops the failures and restores the failed containers. It raises `FailInjectionError` if a container cannot be restored.
* `fail(name, mode)` - crashes (`'crash'`) or disconnects (`'disconnect'`) a container immediately.
* `recover(name)` - recovers a failed container immediately.
* `status()` - returns the state of the fail models and containers. In distributed emulation the state is grouped by worker.
* `events()` - returns the events ordered by time. Each event has the container, the state (`on` or `off`), the action (`crash`, `disconnect`, `recover` or `reconnect`), the timestamp and the source (`local` or the worker address).
* `metrics()` - returns the uptime, downtime, number of failures, availability, MTBF and MTTR of each container between `start()` and `stop()`.


## Recovery
A crashed container is recreated with the same params, IP address, MAC address and switch port, so the flows and ARP tables of the network remain valid. A fail model only recovers the containers that it took down, which means that a crashed container is not recovered by an availability cycle. If a disconnected container receives a crash, the crash takes priority.


## Worker API
The `fogbed worker` command runs the clusternet worker with the following routes.

* `POST /fails` - registers the fail plan of the worker.
* `POST /fails/start` - starts the fail plan at its `start_at` time.
* `POST /fails/stop` - stops the failures and restores the containers.
* `GET /fails/status` - returns the state of the fail models, the containers and the worker clock.
* `GET /fails/events` - returns the events of the worker.
* `POST /containers/<name>/fail` - fails a container immediately with the `crash` or `disconnect` mode.
* `POST /containers/<name>/recover` - recovers a failed container.
