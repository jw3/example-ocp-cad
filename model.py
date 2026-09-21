import build123d as cad
from build123d import BuildPart, Locations, Mode
from ocp_viewer import show

from util import *

if __name__ == "__main__":
    width = 40
    depth = 40
    thickness = 6

    corner_hole_spacing = 35
    half_spacing = corner_hole_spacing / 2

    corner_holes = [
        (x, y, 0)
        for x in (-half_spacing, half_spacing)
        for y in (-half_spacing, half_spacing)
    ]

    with BuildPart() as plate:
        cad.Box(width, depth, thickness)

        with Locations((0, 0, 0)):
            cad.Cylinder(radius=3, height=thickness, mode=Mode.SUBTRACT)

        with Locations(polar((0, 0), 15, 12)):
            cad.Cylinder(radius=1, height=thickness, mode=Mode.SUBTRACT)

        with Locations(*corner_holes):
            cad.Cylinder(radius=1.5, height=thickness, mode=Mode.SUBTRACT)

    show(plate.part)
