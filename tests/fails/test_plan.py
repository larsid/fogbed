import json

import pytest

from fogbed.exceptions import FailPlanError
from fogbed.fails.models import AvailabilityFail, AvailabilityMode, CrashFail
from fogbed.fails.plan import FailPlan, FailTarget, NodeSpec, TargetKind


def spec(name: str, switch: str = 's2') -> NodeSpec:
    return NodeSpec(
        name=name,
        switch=switch,
        params={'ip': '10.0.0.1', 'dimage': 'ubuntu:trusty', 'environment': {'A': '1'}},
        link_params={'bw': 10}
    )


def plan() -> FailPlan:
    return FailPlan(
        targets=[
            FailTarget(TargetKind.NODE, 'd1', CrashFail(life_time=20), [spec('d1')]),
            FailTarget(
                TargetKind.INSTANCE,
                'edge',
                AvailabilityFail(0.5, 2, AvailabilityMode.DISCONNECT),
                [spec('d1'), spec('d2')]
            )
        ],
        start_at=1793900000.5,
        seed=42
    )


def test_plan_survives_json_round_trip():
    original = plan()
    restored = FailPlan.from_dict(json.loads(json.dumps(original.to_dict())))

    assert restored == original
    assert restored.targets[1].node_names == ['d1', 'd2']


def test_plan_exposes_node_specs():
    specs = plan().node_specs

    assert set(specs) == {'d1', 'd2'}
    assert specs['d1'].link_params == {'bw': 10}


def test_node_target_must_describe_itself():
    with pytest.raises(FailPlanError):
        FailTarget(TargetKind.NODE, 'd1', CrashFail(), [spec('d2')])


def test_target_rejects_duplicated_nodes():
    with pytest.raises(FailPlanError):
        FailTarget(TargetKind.INSTANCE, 'edge', CrashFail(), [spec('d1'), spec('d1')])


def test_plan_rejects_duplicated_targets():
    target = FailTarget(TargetKind.NODE, 'd1', CrashFail(), [spec('d1')])
    with pytest.raises(FailPlanError):
        FailPlan([target, target])


def test_plan_rejects_conflicting_node_specs():
    with pytest.raises(FailPlanError):
        FailPlan([
            FailTarget(TargetKind.NODE, 'd1', CrashFail(), [spec('d1', 's2')]),
            FailTarget(TargetKind.INSTANCE, 'edge', CrashFail(), [spec('d1', 's3')])
        ])


@pytest.mark.parametrize('data', [
    {},
    {'targets': 'd1'},
    {'targets': [{'kind': 'node'}]},
    {'targets': [{'kind': 'cluster', 'name': 'd1', 'fail_model': CrashFail().to_dict(), 'nodes': []}]},
    {'targets': [{'kind': 'node', 'name': 'd1', 'fail_model': {'kind': 'meteor'}, 'nodes': []}]},
    {'targets': [{'kind': 'node', 'name': 'd1', 'fail_model': CrashFail().to_dict(), 'nodes': [{'name': 'd1', 'switch': 's1', 'params': []}]}]},
    {'targets': [], 'start_at': 'soon'}
])
def test_invalid_plan_dicts_are_rejected(data):
    with pytest.raises(FailPlanError):
        FailPlan.from_dict(data)


def test_empty_plan_is_valid():
    assert FailPlan.from_dict({'targets': []}) == FailPlan()
