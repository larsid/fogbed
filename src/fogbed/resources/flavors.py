class HardwareResources:
    def __init__(self, cu: float, mu: int) -> None:
        self.compute_units = cu
        self.memory_units  = mu
    
    def __str__(self) -> str:
        return f'HardwareResources(cu={self.compute_units}, mu={self.memory_units})'


class Resources:
    TINY   = HardwareResources(cu=0.5,  mu=32)
    SMALL  = HardwareResources(cu=1.0,  mu=128)
    MEDIUM = HardwareResources(cu=4.0,  mu=256)
    LARGE  = HardwareResources(cu=8.0,  mu=512)
    XLARGE = HardwareResources(cu=16.0, mu=1024)
