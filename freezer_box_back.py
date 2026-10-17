from build123d import *
from ocp_viewer import show

if __name__ == "__main__":
    inch = 25.4

    width = 4.5 * inch
    depth = 6.25 * inch
    thickness = 0.1 * inch
    inset = 0.30 * inch

    with BuildPart() as plate:
        Box(width, depth, thickness)

        with Locations((0, 0, thickness)):
            Box(width - inset, depth - inset, thickness, mode=Mode.ADD)

    export_stl(plate.part, "/tmp/freezer.stl")

    show(plate.part)
