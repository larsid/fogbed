from mininet.node import Docker

DEFAULT_RESOURCES = dict(
    tiny   = {'cu': 0.5,  'mu': 32},
    small  = {'cu': 1.0,  'mu': 128},
    medium = {'cu': 4.0,  'mu': 256},
    large  = {'cu': 8.0,  'mu': 512},
    xlarge = {'cu': 16.0, 'mu': 1024},
)


class ResourceModel(object):
    TINY   = DEFAULT_RESOURCES['tiny']
    SMALL  = DEFAULT_RESOURCES['small']
    MEDIUM = DEFAULT_RESOURCES['medium']
    LARGE  = DEFAULT_RESOURCES['large']
    XLARGE = DEFAULT_RESOURCES['xlarge']

    def __init__(self, max_cu: float, max_mu: float) -> None:
        self.max_cu = max_cu
        self.max_mu = max_mu
        self.allocated_cu = 0
        self.allocated_mu = 0
        self.allocated_containers:dict[str, Docker] = dict()


    def allocate(self, container:Docker):
        pass

    def free(self, container:Docker):
        pass


    def get_compute_units(self, container: Docker)->float:
        return container.params['resources']['cu']


    
class NotEnoughResourcesAvailable(BaseException):
    pass