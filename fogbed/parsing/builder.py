from fogbed import Experiment
from fogbed.parsing.factories.distributed import DistributedExperimentFactory
from fogbed.parsing.factories.local import LocalExperimentFactory
from fogbed.parsing.parser import YMLParser


class ExperimentBuilder:
    def __init__(self, filename: str) -> None:
        self.parser = YMLParser(filename)
    
   
    def build(self) -> Experiment:
        if(self.parser.experiment_is_distributed()):
            return DistributedExperimentFactory(
                containers=self.parser.get_containers(),
                instances=self.parser.get_instances(),
                workers=self.parser.get_workers(),
                tunnels=self.parser.get_tunnels()
            ).build()

        return LocalExperimentFactory(
            containers=self.parser.get_containers(),
            instances=self.parser.get_instances(),
            links=self.parser.get_links()
        ).build()
