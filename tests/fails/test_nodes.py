import json

from fogbed import Container, FogbedDistributedExperiment, VirtualInstance
from fogbed.fails.models import AvailabilityFail, CrashFail


def test_container_keeps_fail_model_out_of_docker_params():
    model = CrashFail(life_time=20)
    container = Container('d1', fail_model=model, link_params={'bw': 10})

    assert container.fail_model is model
    assert 'fail_model' not in container.params
    json.dumps(container.params)


def test_container_without_fail_model():
    assert Container('d1').fail_model is None


def test_virtual_instance_accepts_fail_model():
    model = AvailabilityFail(availability=0.5)

    assert VirtualInstance('edge', fail_model=model).fail_model is model
    assert VirtualInstance('fog').fail_model is None


def test_distributed_experiment_accepts_fail_model_on_virtual_instances():
    model = AvailabilityFail(availability=0.5)
    exp = FogbedDistributedExperiment()
    edge = exp.add_virtual_instance('edge', fail_model=model)

    assert edge.fail_model is model
    assert exp.get_virtual_instance('edge') is edge
