"""50 mm diameter x 120 mm cylinder with a transverse opening and V notch.

All dimensions are millimeters. Cylinder axis: Z.
Opening: 25 mm along X, 50 mm along Z, through the entire Y direction.
Centered V notch below opening: opening width minus 1 mm, 5 mm deep.
V tip is 5 mm above the cylinder bottom.
Extension: 24 mm wide, concentric R40 outer edge, on the -Y side,
positioned by extension_center_z (default span Z=20 to Z=60).
Opening cuts through all material, including any overlapping extension.
Rear (+Y) is flattened by 2 mm for printing with that face on the bed.
Extension has a centered 7 mm diameter through-hole parallel to X.
The two vertical outer extension edges have configurable fillets.
The outer top and bottom rims spanning X have a separate fillet radius.
A centered 24.5 mm across-flats hex hole connects the bottom to the opening.
Optional test_slice_y keeps only material at Y <= the selected cut position.
Two 4 mm X-axis bores cross both opening sidewalls, positioned from their
front edge (intersection with cylinder) and the rectangular opening's top.
The second bore is 25 mm below the first.
"""

from build123d import (
    Align, Axis, Box, BuildPart, BuildSketch, Circle, Cylinder, GeomType,
    Keep, Locations, Mode, Plane, Rectangle, extrude, fillet, split, export_stl,
)

diameter = 51.0
length = 120.0
opening_width = 25.0
opening_length = 80.0
opening_hole_diameter = 4.1
opening_hole_down_from_top = 24.0
opening_hole_in_from_front = 19.0
opening_second_hole_z_offset = -25.0
v_width = opening_width - 2.0
v_depth = 0.0
bottom_clearance = 0.0
bottom_hex_across_flats = 24.6
cut_overrun = 2.0
extension_width = 24.0
extension_height = 40.0
# Z=0 is the cylinder midpoint; ends are at -length/2 and +length/2.
# This also sets the hole center Z. Decrease to move the extension down.
extension_center_z = 40.0
extension_outer_diameter = 80.0
extension_hole_diameter = 5.1
extension_fillet_radius = 2.0  # Set to 0 to disable.
extension_x_fillet_radius = 2.0  # Outer top/bottom rims; 0 disables.
rear_flat_depth = 2.0

# Optional test-print cut: None = full model; 0.0 = slice at its center.
# XZ plane at this Y coordinate, keeping Y <= test_slice_y (extension side).
# Negative values retain less material; positive values retain more.
test_slice_y: float | None = None

centered = (Align.CENTER, Align.CENTER, Align.CENTER)
v_tip_z = -length / 2 + bottom_clearance
opening_bottom = v_tip_z + v_depth
opening_center_z = opening_bottom + opening_length / 2
# Front edge of each opening sidewall at X = +/- opening_width/2.
opening_front_y = -((diameter / 2) ** 2 - (opening_width / 2) ** 2) ** 0.5
opening_hole_y = opening_front_y + opening_hole_in_from_front
opening_hole_z = opening_bottom + opening_length - opening_hole_down_from_top
rear_flat_y = diameter / 2 - rear_flat_depth
extension_hole_y = -(diameter / 2 + extension_outer_diameter / 2) / 2
extension_bottom_z = extension_center_z - extension_height / 2
extension_hole_z = extension_center_z

with BuildPart() as model:
    Cylinder(radius=diameter / 2, height=length, align=centered)

    # Keep a 24 mm wide strip of the negative-Y half of the R40 disk.
    # The portion inside the cylinder overlaps it and fuses on extrusion.
    outer_radius = extension_outer_diameter / 2
    with BuildSketch(Plane.XY.offset(extension_bottom_z)):
        Circle(outer_radius)
        with Locations((0, -outer_radius / 2)):
            Rectangle(extension_width, outer_radius, mode=Mode.INTERSECT)
    extrude(amount=extension_height)

    # Round only the two vertical corners between the sides and outer arc.
    # Select by geometry, so moving the extension along Z preserves selection.
    if extension_fillet_radius > 0:
        outer_edge_y = -(outer_radius ** 2 - (extension_width / 2) ** 2) ** 0.5
        outer_edges = [
            edge for edge in model.edges().filter_by(Axis.Z)
            if abs(abs(edge.center().X) - extension_width / 2) < 1e-5
               and abs(edge.center().Y - outer_edge_y) < 1e-5
        ]
        if len(outer_edges) != 2:
            raise ValueError("Expected two vertical outer extension edges")
        fillet(outer_edges, radius=extension_fillet_radius)

    # The outer rims span X but are circular arcs, not X-parallel lines.
    # Select the R40 arcs at the extension's top and bottom. Tangent
    # propagation also rounds their adjoining vertical-corner blends.
    if extension_x_fillet_radius > 0:
        extension_top_z = extension_bottom_z + extension_height
        rim_edges = [
            edge for edge in model.edges().filter_by(GeomType.CIRCLE)
            if abs(edge.radius - outer_radius) < 1e-5
               and (
                       abs(edge.center().Z - extension_bottom_z) < 1e-5
                       or abs(edge.center().Z - extension_top_z) < 1e-5
               )
        ]
        if len(rim_edges) != 2:
            raise ValueError("Expected two outer extension rim arcs")
        fillet(rim_edges, radius=extension_x_fillet_radius)

    # Cut last so the opening stays through, including the new extension.
    with Locations((0, 0, opening_center_z)):
        Box(
            length=opening_width,
            width=max(diameter, extension_outer_diameter) + 2 * cut_overrun,
            height=opening_length,
            align=centered,
            mode=Mode.SUBTRACT,
        )

    # # XZ sketch coordinates are (X, Z). The V points downward.
    # with BuildSketch(Plane.XZ):
    #     Polygon(
    #         (-v_width / 2, opening_bottom),
    #         (0, v_tip_z),
    #         (v_width / 2, opening_bottom),
    #         align=None,
    #     )
    # extrude(
    #     amount=max(diameter, extension_outer_diameter) / 2 + cut_overrun,
    #     both=True,
    #     mode=Mode.SUBTRACT,
    # )

    # Remove the +Y circular cap, opposite the extension on -Y.
    # MIN alignment starts the cutter exactly at the rear flat plane.
    with Locations((0, rear_flat_y, 0)):
        Box(
            length=diameter + 2 * cut_overrun,
            width=rear_flat_depth + cut_overrun,
            height=length + 2 * cut_overrun,
            align=(Align.CENTER, Align.MIN, Align.CENTER),
            mode=Mode.SUBTRACT,
        )

    # Rotate the cutter's Z axis onto X to bore across the 24 mm width.
    with Locations((0, extension_hole_y, extension_hole_z)):
        Cylinder(
            radius=extension_hole_diameter / 2,
            height=extension_width + 2 * cut_overrun,
            rotation=(0, 90, 0),
            align=centered,
            mode=Mode.SUBTRACT,
        )

    # # Bore upward from below the bottom into the rectangular opening.
    # # With flats normal to X, the 24.5 mm hex fits inside its 25 mm width.
    # # Minor radius is the apothem: half the across-flats dimension.
    # hex_start_z = -length / 2 - cut_overrun
    # with BuildSketch(Plane.XY.offset(hex_start_z)):
    #     RegularPolygon(
    #         radius=bottom_hex_across_flats / 2,
    #         side_count=6,
    #         major_radius=False,
    #         rotation=30,
    #     )
    # extrude(
    #     amount=opening_bottom - hex_start_z + cut_overrun,
    #     mode=Mode.SUBTRACT,
    # )

    # Bore along X through both walls bordering the rectangular opening.
    with Locations(
            (0, opening_hole_y, opening_hole_z),
            (0, opening_hole_y, opening_hole_z + opening_second_hole_z_offset),
    ):
        Cylinder(
            radius=opening_hole_diameter / 2,
            height=diameter + 2 * cut_overrun,
            rotation=(0, 90, 0),
            align=centered,
            mode=Mode.SUBTRACT,
        )

    # Apply last so every feature is included in the test-print slice.
    if test_slice_y is not None:
        test_plane = Plane(
            origin=(0, test_slice_y, 0),
            x_dir=(1, 0, 0),
            z_dir=(0, 1, 0),  # Positive-Y normal; BOTTOM retains negative Y.
        )
        split(bisect_by=test_plane, keep=Keep.BOTTOM)

result = model.part

if __name__ == "__main__":
    from ocp_viewer import show

    show(result)
    export_stl(result, str("/tmp/bin.stl"))
