from orbit.core.bunch import Bunch
from orbit.lattice import AccLattice
from orbit.lattice import AccNode


class AccModel:
    def __init__(self, verbose: int = 1) -> None:
        self.verbose = verbose
