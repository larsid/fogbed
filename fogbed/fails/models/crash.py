

from fogbed.fails import SplitMethod, SelectionMethod
from fogbed.fails.models import FailMode, FailModel


class CrashFail(FailModel):
    """ This fail kills a node or a virtual instance set of nodes after the specified time """
    # Esta falha mata um nó ou um conjunto de nós de uma instância virtual após o tempo especificado
    def __init__(self, fail_rate=0.5, split_method=SplitMethod.UP, life_time=30, selection_method=SelectionMethod.SEQUENTIAL):
        self.fail_rate = fail_rate
        self.selection_method = selection_method
        self.life_time = life_time
        self.split_method = split_method
        super().__init__(FailMode.CRASH)