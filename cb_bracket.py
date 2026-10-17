import argparse
from dataclasses import dataclass
from math import sqrt
from pathlib import Path

import ocp_viewer
from build123d import (
    Align, Box, BuildLine, BuildPart, BuildSketch, Circle, Line, Locations,
    Mesher, Mode, Part, Plane, Polyline, ThreePointArc, extrude, make_face,
    export_step, export_stl, Axis, fillet, Cylinder,
)


@dataclass(frozen=True)
class Dimensions:
    base_length: float = 191.0  # X
    base_depth: float = 222.0  # Y
    base_thickness: float = 6.0  # Z
    end_plate_thickness: float = 2.5  # X; plates flush with ends of base
    end_plate_width: float = 60.0  # Y
    overall_height: float = 44.0  # from underside of base
    top_corner_radius: float = 26.0  # leaves an 8 mm flat at the top
    hole_diameter: float = 5.5
    hole_y: float = 0.0
    hole_z: float = 36.5  # measured; deliberately not rounded to 35


def make_bracket(d: Dimensions = Dimensions()) -> Part:
    """Base plus two extruded end profiles, each with a through hole."""
    if min(d.base_length, d.base_depth, d.base_thickness,
           d.end_plate_thickness, d.end_plate_width, d.top_corner_radius,
           d.hole_diameter) <= 0:
        raise ValueError('Dimensions must be positive')
    if d.end_plate_thickness * 2 >= d.base_length:
        raise ValueError('End plates must leave a gap between them')
    if d.end_plate_width > d.base_depth:
        raise ValueError('End plates must fit on the base')
    if not (d.top_corner_radius < d.end_plate_width / 2
            and d.top_corner_radius < d.overall_height - d.base_thickness):
        raise ValueError('Corner radius must leave straight sides and a top flat')

    half_base_length = d.base_length / 2
    half_base_depth = d.base_depth / 2

    half_width = d.end_plate_width / 2
    radius = d.top_corner_radius
    flat_half_width = half_width - radius
    shoulder_z = d.overall_height - radius
    diagonal = radius / sqrt(2)

    inch = 25.4

    grid_dimensions = (int(half_base_length / inch), int(half_base_depth / inch))
    grid = [
        ((x * inch, y * inch, 0), (-x * inch, -y * inch, 0), (x * inch, -y * inch, 0), (-x * inch, y * inch, 0))
        for x in range(grid_dimensions[0] + 1)
        for y in range(grid_dimensions[1] + 1)
    ]

    with BuildPart() as bracket:
        Box(d.base_length, d.base_depth, d.base_thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

        with Locations(*grid):
            Cylinder(radius=1.6, height=d.base_thickness * 2, mode=Mode.SUBTRACT)

        fillet(bracket.edges().filter_by(Axis.Z), radius=3.0)

        # Plane.YZ has local coordinates (Y,Z) and normal +X.
        # Both profiles extrude toward +X, ending flush with their base ends.
        for x in (-d.base_length / 2, d.base_length / 2 - d.end_plate_thickness):
            with BuildSketch(Plane.YZ.offset(x)):
                with BuildLine():
                    Polyline((-half_width, d.base_thickness),
                             (half_width, d.base_thickness),
                             (half_width, shoulder_z))
                    ThreePointArc(
                        (half_width, shoulder_z),
                        (flat_half_width + diagonal, shoulder_z + diagonal),
                        (flat_half_width, d.overall_height),
                    )
                    Line((flat_half_width, d.overall_height),
                         (-flat_half_width, d.overall_height))
                    ThreePointArc(
                        (-flat_half_width, d.overall_height),
                        (-flat_half_width - diagonal, shoulder_z + diagonal),
                        (-half_width, shoulder_z),
                    )
                    Line((-half_width, shoulder_z), (-half_width, d.base_thickness))
                make_face()
                with Locations((d.hole_y, d.hole_z)):
                    Circle(d.hole_diameter / 2, mode=Mode.SUBTRACT)
            extrude(amount=d.end_plate_thickness)

    result = bracket.part
    result.label = 'CB bracket'
    if not result.is_valid or len(result.solids()) != 1:
        raise RuntimeError('The chosen dimensions did not produce one valid solid')
    return result


# Ready for IDE viewers or imports. Re-run on save after changing Dimensions.
model = make_bracket()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--show', action='store_true', help='Show in OCP CAD Viewer')
    parser.add_argument('--step', type=Path)
    parser.add_argument('--stl', type=Path)
    parser.add_argument('--3mf', dest='three_mf', type=Path)
    args = parser.parse_args()
    if args.step:
        export_step(model, args.step)
    export_stl(model, "/tmp/cb.stl", tolerance=0.005, angular_tolerance=0.05)
    if args.three_mf:
        mesher = Mesher()
        mesher.add_shape(model)
        mesher.write(args.three_mf)
    print(f'Valid solid; volume: {model.volume:.3f} mm^3')
    ocp_viewer.show(model)


if __name__ == '__main__':
    main()
