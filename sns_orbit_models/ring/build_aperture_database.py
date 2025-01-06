"""Manually add aperture nodes to SNS ring lattice (read from MAD file)."""

import os
from collections import Counter
from pprint import pprint

from orbit.core.aperture import Aperture
from orbit.core.bunch import Bunch
from orbit.core.collimator import Collimator
from orbit.core.foil import Foil
from orbit.aperture import ApertureLatticeModifications
from orbit.aperture import ApertureLatticeRangeModifications
from orbit.aperture import CircleApertureNode
from orbit.aperture import EllipseApertureNode
from orbit.aperture import RectangleApertureNode
from orbit.aperture import TeapotApertureNode
from orbit.collimation import TeapotCollimatorNode
from orbit.lattice import AccLattice
from orbit.lattice import AccNode
from orbit.foils import TeapotFoilNode
from orbit.rf_cavities import RFNode
from orbit.teapot import teapot
from orbit.teapot import TEAPOT_Lattice
from orbit.teapot import DriftTEAPOT


ENTRANCE = AccNode.ENTRANCE
EXIT = AccNode.EXIT
BODY = AccNode.BODY


# Make bunch
intensity = 2.258e14
turns = 1044.0
NTURNS = 1044
NDUMPS = 4
macrosperturn = 2000
macrosize = intensity / turns / macrosperturn

b = Bunch()
b.mass(0.93827231)
b.macroSize(macrosize)
energy = 1.3  # Gev
b.getSyncParticle().kinEnergy(energy)

lostbunch = Bunch()
lostbunch.addPartAttr("LostParticleAttributes")

paramsDict = {}
paramsDict["bunch"] = b
paramsDict["lostbunch"] = lostbunch


## Make lattice
from sns_orbit_models import SNS_RING

model = SNS_RING(lattice_file="default")
model.add_injection_chicane_apertures_and_displacements()
model.add_apertures()
model.rename_nodes_avoid_duplicates()
lattice = model.lattice


# Build aperture database
# --------------------------------------------------------------------------------------

def is_aperture_node(node: AccNode) -> bool:
    aperture_node_classes = [
        CircleApertureNode,
        EllipseApertureNode,
        RectangleApertureNode,
        TeapotCollimatorNode,
    ]
    return type(node) in aperture_node_classes


class NodeInfo:
    def __init__(self, node: AccNode, index: int, start: float, stop: float) -> None:
        self.node = node
        self.name = node.getName()
        self.length = node.getLength()
        self.type = type(self.node)
        self.class_name = node.__class__.__name__

        self.index = index
        self.start = start
        self.stop = stop


class ChildNodeInfo(NodeInfo):
    def __init__(
        self, node: AccNode, parent_node: AccNode, place: int, subindex: int, **kwargs
    ) -> None:
        super().__init__(node, **kwargs)
        self.parent_node = parent_node
        self.parent_node_info = NodeInfo(parent_node, **kwargs)
        self.place = place
        self.subindex = subindex


class ApertureChildNodeInfo(ChildNodeInfo):
    def __init__(self, node: AccNode, **kwargs) -> None:
        super().__init__(node, **kwargs)

        self.shape = self.node.shape

        self.size_x = self.size_y = None
        if self.shape == 1:
            self.size_x = node.a
            self.size_y = self.size_x
        else:
            self.size_x = node.a
            self.size_y = node.b


class ApertureChildNodeInfoWriter:
    def __init__(self, filename: str, verbose: bool = True) -> None:
        self.filename = filename
        self.verbose = verbose

        self.keys = [
            "index",
            "name",
            "class_name",
            "place",
            "subindex",
            "start",
            "stop",
            "size_x",
            "size_y",
        ]
        self.header = ", ".join(self.keys)
        if self.verbose:
            print(self.header)

        self.file = open(self.filename, "w")
        self.file.write(self.header + "\n")

    def get_line(self, aperture_child_node_info: ApertureChildNodeInfo) -> str:
        line = []
        for key in self.keys:
            line.append(str(getattr(aperture_child_node_info, key)))
        line = ", ".join(line)
        return line

    def write_line(self, aperture_child_node_info: ApertureChildNodeInfo) -> None:
        line = self.get_line(aperture_child_node_info)
        if self.verbose:
            print(line)
        self.file.write(line + "\n")


# Collect node info
nodes = lattice.getNodes()
node_positions = lattice.getNodePositionsDict()
aperture_node_info_list = []
for index, node in enumerate(nodes):
    start, stop = node_positions[node]
    for place in [ENTRANCE, BODY, EXIT]:
        for subindex, child_node in enumerate(node.getChildNodes(place)):
            if is_aperture_node(child_node):
                child_node_info = ApertureChildNodeInfo(
                    node=child_node,
                    index=index,
                    parent_node=node,
                    place=place,
                    subindex=subindex,
                    start=start,
                    stop=stop,
                )
                aperture_node_info_list.append(child_node_info)


# Write data to file
writer = ApertureChildNodeInfoWriter("aperture_node_info_list.txt")
for aperture_node_info in aperture_node_info_list:
    writer.write_line(aperture_node_info)
