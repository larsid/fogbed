import dataclasses
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Iterable, List, Optional

from fogbed.exceptions import ContainerNotFound, FailInjectionError
from fogbed.experiment import Experiment
from fogbed.experiment.distributed import FogbedDistributedExperiment
from fogbed.experiment.local import FogbedExperiment
from fogbed.fails.agent import CRASH, FailAgent
from fogbed.fails.events import FailEvent, NodeMetrics, compute_metrics
from fogbed.fails.operators import ContainernetOperator
from fogbed.fails.plan import FailPlan, FailTarget, NodeSpec, TargetKind
from fogbed.fails.remote.client import FailWorkerClient
from fogbed.node.container import Container
from fogbed.node.instance import VirtualInstance
from fogbed.node.services.local_docker import LocalDocker

from mininet.log import info


def build_node_spec(container: Container, instance: VirtualInstance) -> NodeSpec:
    return NodeSpec(
        name=container.name,
        switch=instance.switch,
        params=dict(container.params),
        link_params=dict(container.link_params)
    )


def build_targets(instances: Iterable[VirtualInstance]) -> List[FailTarget]:
    targets: List[FailTarget] = []

    for instance in instances:
        specs = [build_node_spec(container, instance) for container in instance]

        for container, spec in zip(instance, specs):
            if(container.fail_model is not None):
                targets.append(FailTarget(TargetKind.NODE, container.name, container.fail_model, [spec]))

        if(instance.fail_model is not None):
            targets.append(FailTarget(TargetKind.INSTANCE, instance.label, instance.fail_model, specs))

    return targets


def find_virtual_instance(instances: Iterable[VirtualInstance], name: str) -> VirtualInstance:
    for instance in instances:
        if(name in instance.containers):
            return instance
    raise ContainerNotFound(f'Container {name} not found.')


class FailBackend(ABC):
    @property
    @abstractmethod
    def started_at(self) -> Optional[float]:
        pass

    @property
    @abstractmethod
    def stopped_at(self) -> Optional[float]:
        pass

    @property
    @abstractmethod
    def nodes(self) -> List[str]:
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def status(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def events(self) -> List[FailEvent]:
        pass

    @abstractmethod
    def fail(self, name: str, mode: str = CRASH) -> bool:
        pass

    @abstractmethod
    def recover(self, name: str) -> bool:
        pass

    def metrics(self) -> Dict[str, NodeMetrics]:
        if(self.started_at is None):
            raise FailInjectionError('Fail controller was not started')

        end = self.stopped_at if(self.stopped_at is not None) else time.time()
        return compute_metrics(self.events(), self.started_at, max(end, self.started_at), self.nodes)


class LocalFailController(FailBackend):
    def __init__(self, experiment: Any, seed: Optional[int] = None):
        self.experiment = experiment
        self.seed  = seed
        self.agent = FailAgent(ContainernetOperator(lambda: experiment.net, on_recover=self._bind_docker))

    @property
    def started_at(self) -> Optional[float]:
        return self.agent.started_at

    @property
    def stopped_at(self) -> Optional[float]:
        return self.agent.stopped_at

    @property
    def nodes(self) -> List[str]:
        return list(self.agent.status()['nodes'])

    def start(self):
        if(not self.experiment.net.is_running):
            raise FailInjectionError('The experiment must be started before the fail controller')

        targets = build_targets(self.experiment.get_virtual_instances())
        self.agent.load(FailPlan(targets, seed=self.seed))
        self.agent.start()

    def stop(self):
        self.agent.stop()

    def status(self) -> Dict[str, Any]:
        return self.agent.status()

    def events(self) -> List[FailEvent]:
        return self.agent.events()

    def fail(self, name: str, mode: str = CRASH) -> bool:
        instance = find_virtual_instance(self.experiment.get_virtual_instances(), name)
        spec = build_node_spec(instance.containers[name], instance)
        return self.agent.fail_node(name, mode, spec=spec)

    def recover(self, name: str) -> bool:
        return self.agent.recover_node(name)

    def _bind_docker(self, node: NodeSpec, docker: Any):
        self.experiment.get_docker(node.name).set_docker(LocalDocker(docker))


class RemoteFailController(FailBackend):
    def __init__(self,
        experiment: Any,
        seed: Optional[int] = None,
        start_delay: float = 2.0,
        max_clock_skew: float = 0.5,
        clock_samples: int = 3,
        client_factory: Callable[[str], FailWorkerClient] = FailWorkerClient
    ):
        self.experiment     = experiment
        self.seed           = seed
        self.start_delay    = start_delay
        self.max_clock_skew = max_clock_skew
        self.clock_samples  = max(1, clock_samples)
        self.client_factory = client_factory
        self.clock_offsets: Dict[str, float] = {}
        self._clients: Dict[str, FailWorkerClient] = {}
        self._started_at: Optional[float] = None
        self._stopped_at: Optional[float] = None
        self._nodes: List[str] = []

    @property
    def started_at(self) -> Optional[float]:
        return self._started_at

    @property
    def stopped_at(self) -> Optional[float]:
        return self._stopped_at

    @property
    def nodes(self) -> List[str]:
        return list(self._nodes)

    def start(self):
        if(not self.experiment.is_running):
            raise FailInjectionError('The experiment must be started before the fail controller')

        groups = self._group_targets()
        self.clock_offsets = self.measure_clock_offsets()
        self._warn_clock_skew()

        start_at = time.time() + self.start_delay
        for ip, targets in groups.items():
            worker_start_at = start_at + self.clock_offsets.get(ip, 0.0)
            self._get_client(ip).load_plan(FailPlan(targets, worker_start_at, self.seed))

        for ip in groups:
            self._get_client(ip).start()

        self._started_at = start_at
        self._stopped_at = None
        self._nodes = list(dict.fromkeys(name for targets in groups.values() for target in targets for name in target.node_names))

    def stop(self):
        errors: List[str] = []

        if(self._started_at is not None and self._stopped_at is None):
            self._stopped_at = time.time()

        for ip in self.experiment.workers:
            try:
                self._get_client(ip).stop()
            except Exception as ex:
                errors.append(f'{ex}')

        if(errors):
            raise FailInjectionError('; '.join(errors))

    def status(self) -> Dict[str, Any]:
        return {ip: self._get_client(ip).status() for ip in self.experiment.workers}

    def events(self) -> List[FailEvent]:
        events = [
            dataclasses.replace(event, source=ip, timestamp=event.timestamp - self.clock_offsets.get(ip, 0.0))
            for ip in self.experiment.workers
            for event in self._get_client(ip).events()
        ]
        return sorted(events, key=lambda event: event.timestamp)

    def fail(self, name: str, mode: str = CRASH) -> bool:
        instance = find_virtual_instance(self.experiment.get_virtual_instances(), name)
        spec = build_node_spec(instance.containers[name], instance)
        return self._get_client(self._get_worker_ip(instance)).fail_node(name, mode, spec)

    def recover(self, name: str) -> bool:
        instance = find_virtual_instance(self.experiment.get_virtual_instances(), name)
        return self._get_client(self._get_worker_ip(instance)).recover_node(name)

    def measure_clock_offsets(self) -> Dict[str, float]:
        offsets: Dict[str, float] = {}

        for ip in self.experiment.workers:
            samples = [self._get_client(ip).clock() for _ in range(self.clock_samples)]
            offsets[ip] = min(samples, key=lambda sample: sample.round_trip).offset

        return offsets

    def _warn_clock_skew(self):
        for ip, offset in self.clock_offsets.items():
            if(abs(offset) > self.max_clock_skew):
                info(f'*** Warning: worker {ip} clock differs {offset:.3f}s from the controller, synchronize clocks with NTP for accurate timing\n')

    def _group_targets(self) -> Dict[str, List[FailTarget]]:
        groups: Dict[str, List[FailTarget]] = {ip: [] for ip in self.experiment.workers}

        for instance in self.experiment.get_virtual_instances():
            targets = build_targets([instance])
            if(targets):
                groups[self._get_worker_ip(instance)].extend(targets)

        return groups

    def _get_worker_ip(self, instance: VirtualInstance) -> str:
        ip = instance.get_ip()
        if(ip not in self.experiment.workers):
            raise FailInjectionError(f'Virtual instance {instance.label} is not assigned to a worker')
        return ip

    def _get_client(self, ip: str) -> FailWorkerClient:
        if(ip not in self._clients):
            self._clients[ip] = self.client_factory(self.experiment.workers[ip].net.url)
        return self._clients[ip]


class FailController:
    def __init__(self, experiment: Experiment, seed: Optional[int] = None, **options: Any):
        self.experiment = experiment
        self.backend = self._create_backend(experiment, seed, **options)

    @staticmethod
    def _create_backend(experiment: Experiment, seed: Optional[int], **options: Any) -> FailBackend:
        if(isinstance(experiment, FogbedDistributedExperiment)):
            return RemoteFailController(experiment, seed, **options)
        if(isinstance(experiment, FogbedExperiment)):
            return LocalFailController(experiment, seed)
        raise TypeError(f'Unsupported experiment type: {type(experiment).__name__}')

    def start(self):
        self.backend.start()

    def stop(self):
        self.backend.stop()

    def status(self) -> Dict[str, Any]:
        return self.backend.status()

    def events(self) -> List[FailEvent]:
        return self.backend.events()

    def metrics(self) -> Dict[str, NodeMetrics]:
        return self.backend.metrics()

    def fail(self, name: str, mode: str = CRASH) -> bool:
        return self.backend.fail(name, mode)

    def recover(self, name: str) -> bool:
        return self.backend.recover(name)
