import random

import pytest

from fogbed.fails.schedule import InstanceAvailabilitySchedule, NodeAvailabilitySchedule


@pytest.mark.parametrize('availability, cycle', [
    (0.0, [False]),
    (0.25, [True, False, False, False]),
    (0.5, [True, False]),
    (0.7, [True] * 7 + [False] * 3),
    (1.0, [True])
])
def test_node_schedule_follows_cycle(availability, cycle):
    schedule = NodeAvailabilitySchedule(availability)
    slots = len(cycle) * 3

    assert [schedule.is_on(slot) for slot in range(slots)] == cycle * 3


@pytest.mark.parametrize('availability', [0.0, 0.2, 0.25, 1 / 3, 0.5, 0.7, 0.9, 1.0])
def test_node_schedule_reaches_exact_availability_per_cycle(availability):
    schedule = NodeAvailabilitySchedule(availability)
    on_slots = sum(schedule.is_on(slot) for slot in range(schedule.cycle_size * 5))

    assert on_slots / (schedule.cycle_size * 5) == pytest.approx(availability, abs=1e-3)


@pytest.mark.parametrize('nodes, availability', [
    (3, 0.5),
    (3, 0.2),
    (5, 0.7),
    (4, 0.25),
    (2, 1.0),
    (2, 0.0)
])
def test_instance_schedule_reaches_target_availability(nodes, availability):
    names = [f'd{i}' for i in range(nodes)]
    schedule = InstanceAvailabilitySchedule(names, availability, random.Random(0))
    slots = 1000
    down = [len(schedule.down_nodes(slot)) for slot in range(slots)]

    assert 1 - sum(down) / (slots * nodes) == pytest.approx(availability, abs=1e-2)
    assert max(down) - min(down) <= 1
    assert all(0 <= amount <= nodes for amount in down)


def test_instance_schedule_picks_only_known_nodes():
    names = ['d1', 'd2', 'd3']
    schedule = InstanceAvailabilitySchedule(names, 0.5, random.Random(3))

    for slot in range(50):
        assert schedule.down_nodes(slot) <= set(names)


def test_instance_schedule_is_reproducible_with_seed():
    names = ['d1', 'd2', 'd3', 'd4']
    first = InstanceAvailabilitySchedule(names, 0.5, random.Random(9))
    second = InstanceAvailabilitySchedule(names, 0.5, random.Random(9))

    assert [first.down_nodes(slot) for slot in range(20)] == [second.down_nodes(slot) for slot in range(20)]
