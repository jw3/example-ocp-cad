import build123d as cad
from build123d import BuildPart, Locations, Mode, fillet
from ocp_viewer import show

from util import *

if __name__ == "__main__":
    width = 71.75
    depth = 71.75
    thickness = 7
    corner_post_size = 5
    half_corner_post_size = corner_post_size / 2

    corner_hole_spacing = 35
    half_spacing = corner_hole_spacing / 2
    half_width = width / 2
    half_depth = depth / 2

    corner_holes = [
        (x, y, 0)
        for x in (-half_spacing, half_spacing)
        for y in (-half_spacing, half_spacing)
    ]

    corners = [
        (x, y, 0)
        for x in (-half_width + half_corner_post_size, half_width - half_corner_post_size)
        for y in (-half_depth + half_corner_post_size, half_depth - half_corner_post_size)
    ]

    with BuildPart() as plate:
        cad.Box(width, depth, thickness)

        with Locations((0, 0, 0)):
            cad.Cylinder(radius=3, height=thickness, mode=Mode.SUBTRACT)

        with Locations(polar((0, 0), 15, 12)):
            cad.Cylinder(radius=1, height=thickness, mode=Mode.SUBTRACT)

        with Locations(*corner_holes):
            cad.Cylinder(radius=1.5, height=thickness, mode=Mode.SUBTRACT)

        top_face = plate.faces().sort_by(cad.Axis.Z)[-1]
        fillet(top_face.edges().filter_by(cad.GeomType.LINE), 0.5)

        with Locations(*corners):
            box = cad.Box(corner_post_size, corner_post_size, 30)

    show(plate.part)
