from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from fogbed.exceptions import FailPlanError
from fogbed.fails.models import FailModel, fail_model_from_dict


@dataclass
class NodeSpec:
    name: str
    switch: str
    params: Dict[str, Any] = field(default_factory=dict)
    link_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'switch': self.switch,
            'params': dict(self.params),
            'link_params': dict(self.link_params)
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'NodeSpec':
        params = data.get('params', {})
        link_params = data.get('link_params', {})

        if(not isinstance(params, dict) or not isinstance(link_params, dict)):
            raise FailPlanError('Node params and link_params must be objects')

        return NodeSpec(str(data['name']), str(data['switch']), dict(params), dict(link_params))


class TargetKind(Enum):
    NODE = 'node'
    INSTANCE = 'instance'


@dataclass
class FailTarget:
    kind: TargetKind
    name: str
    fail_model: FailModel
    nodes: List[NodeSpec]

    def __post_init__(self):
        names = [node.name for node in self.nodes]

        if(len(names) != len(set(names))):
            raise FailPlanError(f'Target {self.name} has duplicated nodes')
        if(self.kind == TargetKind.NODE and names != [self.name]):
            raise FailPlanError(f'Node target {self.name} must describe only itself')

    @property
    def node_names(self) -> List[str]:
        return [node.name for node in self.nodes]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'kind': self.kind.value,
            'name': self.name,
            'fail_model': self.fail_model.to_dict(),
            'nodes': [node.to_dict() for node in self.nodes]
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'FailTarget':
        return FailTarget(
            kind=TargetKind(data['kind']),
            name=str(data['name']),
            fail_model=fail_model_from_dict(data['fail_model']),
            nodes=[NodeSpec.from_dict(node) for node in data['nodes']]
        )


@dataclass
class FailPlan:
    targets: List[FailTarget] = field(default_factory=list)
    start_at: Optional[float] = None
    seed: Optional[int] = None

    def __post_init__(self):
        keys = [(target.kind, target.name) for target in self.targets]
        if(len(keys) != len(set(keys))):
            raise FailPlanError('Fail plan has duplicated targets')

        specs: Dict[str, NodeSpec] = {}
        for target in self.targets:
            for node in target.nodes:
                if(specs.setdefault(node.name, node) != node):
                    raise FailPlanError(f'Node {node.name} has conflicting specs')

    @property
    def node_specs(self) -> Dict[str, NodeSpec]:
        return {node.name: node for target in self.targets for node in target.nodes}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'targets': [target.to_dict() for target in self.targets],
            'start_at': self.start_at,
            'seed': self.seed
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'FailPlan':
        try:
            targets = data['targets']
            if(not isinstance(targets, list)):
                raise FailPlanError('targets must be a list')

            start_at = data.get('start_at')
            seed = data.get('seed')

            return FailPlan(
                targets=[FailTarget.from_dict(target) for target in targets],
                start_at=None if(start_at is None) else float(start_at),
                seed=None if(seed is None) else int(seed)
            )
        except FailPlanError:
            raise
        except KeyError as ex:
            raise FailPlanError(f'Missing fail plan param {ex}')
        except (TypeError, ValueError, AttributeError) as ex:
            raise FailPlanError(f'Invalid fail plan: {ex}')
