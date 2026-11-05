import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional

from fogbed.exceptions import ContainerNotFound, FailInjectionError
from fogbed.experiment import Experiment
from fogbed.experiment.local import FogbedExperiment
from fogbed.fails.agent import CRASH, FailAgent
from fogbed.fails.events import FailEvent, NodeMetrics, compute_metrics
from fogbed.fails.operators import ContainernetOperator
from fogbed.fails.plan import FailPlan, FailTarget, NodeSpec, TargetKind
from fogbed.node.container import Container
from fogbed.node.instance import VirtualInstance
from fogbed.node.services.local_docker import LocalDocker


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


class FailController:
    def __init__(self, experiment: Experiment, seed: Optional[int] = None, **options: Any):
        self.experiment = experiment
        self.backend = self._create_backend(experiment, seed, **options)

    @staticmethod
    def _create_backend(experiment: Experiment, seed: Optional[int], **options: Any) -> FailBackend:
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
