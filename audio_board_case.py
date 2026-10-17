"""Parameterized PCB case and slip-fit lid. All dimensions are millimeters.

Install: python -m pip install build123d
Run:     python pcb_case.py
Optional IDE preview: pip install ocp-vscode; set preview = True below.

X = board width, Y = board depth, Z = up. The PCB and mounting pattern
are centered on XY. Case bottom is Z=0; PCB underside is at
base_thickness + standoff_height. Lid is exported flat-side-down for printing.
The two front pockets are independent sketches on the external -Y wall.
"""

from pathlib import Path

import ocp_viewer
from build123d import (
    Align, Box, BuildPart, BuildSketch, Cylinder, Locations, Mode,
    Plane, Pos, Rectangle, export_step, export_stl, extrude,
)

# PCB and centered 2 x 2 mounting-hole pattern
board_width = 127.5
board_depth = 86.25
hole_spacing = (121.0, 80.0)  # center-to-center, X and Y
board_thickness = 1.6  # used to establish enclosure height
hole_pattern_offset_x = 0.0
hole_pattern_offset_y = 0.0

# Clearance from EACH board edge to its corresponding inner wall
width_padding = 2.0
depth_padding = 2.0

# Case
wall_thickness = 2.0
base_thickness = 2.0
clearance_above_board = 15.0  # board top to lid underside

# Four circular risers; pockets are measured down from each riser top.
# At these defaults the pocket reaches the floor, leaving the base intact.
standoff_radius = 4.0
standoff_height = 3.0
standoff_pocket_radius = 2.0
standoff_pocket_depth = 3.0

# Two rectangular pockets on the width-spanning FRONT (-Y) exterior face
face_pocket_width = 5.0
face_pocket_height = 5.0
face_pocket_depth = 1.0  # blind recess; use wall_thickness for openings
face_pocket_edge_distance = 5.0  # outer side edge to NEAREST pocket edge
face_pocket_z_offset = 0.0  # 0 centers on full exterior face height

# Slip-fit lid: plate rests on case rim; locating ring fits inside walls.
# This is a removable cover, without screws or snap catches.
lid_thickness = 2.0
lid_overhang = 0.0  # beyond each outer wall
lid_fit_clearance = 0.25  # gap per side between ring and inner wall
lid_lip_height = 2.0
lid_lip_thickness = 1.2

# Output / optional OCP viewer
output_directory = Path(__file__).resolve().parent / "pcb_case_output"
stl_tolerance = 0.05
stl_angular_tolerance = 0.1
preview = False
preview_gap = 10.0

# Derived dimensions
inner_width = board_width + 2 * width_padding
inner_depth = board_depth + 2 * depth_padding
outer_width = inner_width + 2 * wall_thickness
outer_depth = inner_depth + 2 * wall_thickness
inner_height = standoff_height + board_thickness + clearance_above_board
case_height = base_thickness + inner_height
lip_width = inner_width - 2 * lid_fit_clearance
lip_depth = inner_depth - 2 * lid_fit_clearance
pocket_x = outer_width / 2 - face_pocket_edge_distance - face_pocket_width / 2
pocket_z = case_height / 2 + face_pocket_z_offset
mounting_centers = [
    (hole_pattern_offset_x + sx * hole_spacing[0] / 2,
     hole_pattern_offset_y + sy * hole_spacing[1] / 2)
    for sx in (-1, 1) for sy in (-1, 1)
]


def validate_dimensions():
    positive = (
        board_width, board_depth, board_thickness, *hole_spacing,
        wall_thickness, base_thickness, clearance_above_board,
        standoff_radius, standoff_height, standoff_pocket_radius,
        standoff_pocket_depth, face_pocket_width, face_pocket_height,
        face_pocket_depth, lid_thickness, lid_lip_height, lid_lip_thickness,
        stl_tolerance, stl_angular_tolerance,
    )
    if min(positive) <= 0:
        raise ValueError("Dimensions must be positive.")
    if min(width_padding, depth_padding, lid_fit_clearance,
           lid_overhang, face_pocket_edge_distance, preview_gap) < 0:
        raise ValueError("Padding, clearances, overhang and edge distances must be >= 0.")
    if not standoff_pocket_radius < standoff_radius:
        raise ValueError("Riser pocket radius must be smaller than riser radius.")
    if standoff_pocket_depth > standoff_height:
        raise ValueError("Riser pocket depth must not penetrate the case base.")
    if face_pocket_depth > wall_thickness:
        raise ValueError("Front pocket depth must be <= wall thickness.")
    if pocket_x <= face_pocket_width / 2:
        raise ValueError("Front pockets overlap or touch.")
    if not (base_thickness < pocket_z - face_pocket_height / 2
            and pocket_z + face_pocket_height / 2 < case_height - lid_lip_height):
        raise ValueError("Front pockets must clear the floor and lid locating ring.")
    if face_pocket_edge_distance < wall_thickness:
        raise ValueError("Front pockets must clear the side walls.")
    if min(lip_width, lip_depth) <= 2 * lid_lip_thickness:
        raise ValueError("Lid locating ring has no central opening.")
    if lid_lip_height >= clearance_above_board:
        raise ValueError("Lid locating ring must remain above the PCB.")
    for x, y in mounting_centers:
        if abs(x) >= board_width / 2 or abs(y) >= board_depth / 2:
            raise ValueError("Mounting-hole center is outside the board.")
        if (abs(x) + standoff_radius >= inner_width / 2 or
                abs(y) + standoff_radius >= inner_depth / 2):
            raise ValueError("Increase padding so circular risers clear the walls.")


validate_dimensions()
bottom_aligned = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as case_builder:
    Box(outer_width, outer_depth, case_height, align=bottom_aligned)
    with Locations((0, 0, base_thickness)):
        Box(inner_width, inner_depth, inner_height,
            align=bottom_aligned, mode=Mode.SUBTRACT)

    for x, y in mounting_centers:
        with Locations((x, y, base_thickness)):
            Cylinder(standoff_radius, standoff_height, align=bottom_aligned)
        with Locations((x, y, base_thickness + standoff_height - standoff_pocket_depth)):
            Cylinder(standoff_pocket_radius, standoff_pocket_depth,
                     align=bottom_aligned, mode=Mode.SUBTRACT)

    # Each sketch's local X is world X, local Y is world Z, normal is -Y.
    # Negative extrusion therefore cuts inward toward +Y.
    for x in (-pocket_x, pocket_x):
        front_plane = Plane(origin=(x, -outer_depth / 2, pocket_z),
                            x_dir=(1, 0, 0), z_dir=(0, -1, 0))
        with BuildSketch(front_plane):
            Rectangle(face_pocket_width, face_pocket_height)
        extrude(amount=-face_pocket_depth, mode=Mode.SUBTRACT)

with BuildPart() as lid_builder:
    Box(outer_width + 2 * lid_overhang, outer_depth + 2 * lid_overhang,
        lid_thickness, align=bottom_aligned)
    with BuildSketch(Plane.XY.offset(lid_thickness)):
        Rectangle(lip_width, lip_depth)
        Rectangle(lip_width - 2 * lid_lip_thickness,
                  lip_depth - 2 * lid_lip_thickness, mode=Mode.SUBTRACT)
    extrude(amount=lid_lip_height)

case = case_builder.part
lid = lid_builder.part
case.label = "PCB case"
lid.label = "PCB lid (print orientation)"

if __name__ == "__main__":
    output_directory.mkdir(parents=True, exist_ok=True)
    for name, part in (("case", case), ("lid", lid)):
        export_step(part, str(output_directory / f"{name}.step"))
        export_stl(part, str(output_directory / f"{name}.stl"),
                   tolerance=stl_tolerance, angular_tolerance=stl_angular_tolerance)
    print(f"Case outside: {outer_width:g} x {outer_depth:g} x {case_height:g} mm")
    print(f"PCB underside: Z={base_thickness + standoff_height:g} mm")
    print(f"Exported case/lid STL and STEP to {output_directory}")

    ocp_viewer.show(case, Pos(outer_width + lid_overhang + preview_gap, 0, 0) * lid)
