import pytest

from fogbed.exceptions import ContainerNotFound, FailInjectionError
from fogbed.fails.operators import ContainernetOperator
from fogbed.fails.plan import NodeSpec
from fakes import FakeNet

from mininet.link import TCLink


SPEC = NodeSpec('d1', 's2', {'ip': '10.0.0.7', 'dimage': 'alpine'}, {'bw': 10})


@pytest.fixture
def net() -> FakeNet:
    fake = FakeNet()
    fake.addDocker('d1')
    fake.addLink('d1', 's2')
    fake.calls.clear()
    return fake


def test_crash_detaches_and_removes_link_and_container(net):
    switch_interface = net.links[0].intf2
    ContainernetOperator(lambda: net).crash(SPEC)

    assert net['s2'].detached == [switch_interface]
    assert net.calls == [('removeLink', 'd1', 's2'), ('removeDocker', 'd1')]
    assert 'd1' not in net


def test_recover_recreates_container_with_original_params(net):
    recovered = []
    operator = ContainernetOperator(lambda: net, on_recover=lambda spec, docker: recovered.append((spec, docker)))
    operator.crash(SPEC)
    net.calls.clear()
    operator.recover(SPEC)

    assert net.calls == [
        ('addDocker', 'd1', {'ip': '10.0.0.7', 'dimage': 'alpine', 'mac': '00:00:00:00:00:02'}),
        ('addLink', 'd1', 's2', {'cls': TCLink, 'bw': 10})
    ]
    assert net['d1'].configured
    assert recovered == [(SPEC, net['d1'])]


def test_recover_rejects_running_container(net):
    with pytest.raises(FailInjectionError):
        ContainernetOperator(lambda: net).recover(SPEC)


def test_disconnect_and_reconnect_toggle_switch_side_interface(net):
    operator = ContainernetOperator(lambda: net)
    operator.disconnect(SPEC)
    operator.reconnect(SPEC)

    assert net.links[0].intf2.status == ['down', 'up']
    assert net.links[0].intf1.status == []
    assert 'd1' in net


def test_missing_container_is_reported(net):
    with pytest.raises(ContainerNotFound):
        ContainernetOperator(lambda: net).disconnect(NodeSpec('d9', 's2'))


def test_missing_link_is_reported(net):
    net.links.clear()
    with pytest.raises(FailInjectionError):
        ContainernetOperator(lambda: net).disconnect(SPEC)


def test_stopped_network_is_rejected(net):
    net.is_running = False
    with pytest.raises(FailInjectionError):
        ContainernetOperator(lambda: net).crash(SPEC)


def test_net_is_resolved_on_every_operation(net):
    nets = [net]
    operator = ContainernetOperator(lambda: nets[0])

    assert operator.exists('d1')
    nets[0] = FakeNet()
    assert not operator.exists('d1')
