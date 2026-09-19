import build123d as cad
from ocp_viewer import show

if __name__ == '__main__':
    width = 40
    depth = 30
    thickness = 6

    plate = cad.Box(width, depth, thickness)
    hole = cad.Cylinder(radius=3, height=thickness + 2)

    part = plate - hole
    show(part)
