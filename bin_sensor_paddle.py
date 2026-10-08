"""Separate forked paddle for cylinder_cutout.py; dimensions in millimeters.

Local print coordinates: X=width/pivot axis, Y=length (0..160), Z=height.
The 5 mm plate lies on Z=0. Two 5 mm thick ears flank a 25 mm clear slot.
The pivot is 6 mm from the ear tips. No mechanical stop is included.
Run directly to display with ocp_viewer; import to obtain result/print_part.
"""
from math import asin, degrees, hypot

from build123d import (
    Align, Axis, Box, BuildPart, BuildSketch, Cylinder, Locations,
    Mode, Polygon, Pos, extrude, export_stl,
)

# Paddle and fork dimensions.
total_length = 160.0  # Ear tips to far end, NOT pivot to far end.
end_width = 100.0
paddle_thickness = 5.0
extension_width = 24.0
fork_clearance = 1.0  # Total clearance: 0.5 mm on each side.
ear_thickness = 5.0  # Along X (bolt axis).
ear_height = 16.0  # Above print bed; independent of thickness.
pivot_diameter = 7.0
pivot_from_tip = 6.0
pivot_height = ear_height / 2
fork_depth = 40.0  # Open slot ends here; adjustable for clearance.
ear_root_overlap = 5.0

# Optional mounted pose. Default output is the flat, printable paddle only.
show_mounted = False
mount_angle_deg = 45.0  # Outward angle from cylinder's downward axis.
tip_travel = 5.0  # Assumed total chord travel of far-end center.
# Match these to the mating cylinder script if its pivot position changes.
mount_pivot_y = -32.5
mount_pivot_z = 40.0

fork_width = extension_width + fork_clearance
root_width = fork_width + 2 * ear_thickness
ear_length = fork_depth + ear_root_overlap
centered = (Align.CENTER, Align.CENTER, Align.CENTER)

if not (0 < pivot_from_tip < fork_depth < ear_length < total_length):
    raise ValueError("Require pivot tip offset < fork depth < ear length < total length")
if min(pivot_from_tip, pivot_height, ear_height - pivot_height) <= pivot_diameter / 2:
    raise ValueError("Pivot hole must have material around it")
if end_width < root_width or min(paddle_thickness, ear_thickness, fork_clearance) <= 0:
    raise ValueError("Invalid paddle width, thickness, or fork clearance")

with BuildPart() as paddle:
    # Flared plate: the slot is open from Y=0 to Y=fork_depth.
    with BuildSketch():
        Polygon(
            (-root_width / 2, fork_depth),
            (root_width / 2, fork_depth),
            (end_width / 2, total_length),
            (-end_width / 2, total_length),
            align=None,
        )
    extrude(amount=paddle_thickness)

    # Both ears overlap the plate at their roots to form one solid.
    ear_x = fork_width / 2 + ear_thickness / 2
    with Locations((-ear_x, ear_length / 2, ear_height / 2),
                   (ear_x, ear_length / 2, ear_height / 2)):
        Box(ear_thickness, ear_length, ear_height, align=centered)

    # One coaxial cut creates the two bolt holes.
    with Locations((0, pivot_from_tip, pivot_height)):
        Cylinder(pivot_diameter / 2, root_width + 4,
                 rotation=(0, 90, 0), align=centered, mode=Mode.SUBTRACT)

print_part = paddle.part


def mounted_part(angle_deg=mount_angle_deg):
    """Return paddle placed at the mating cylinder's X-axis pivot."""
    at_pivot = Pos(0, -pivot_from_tip, -pivot_height) * print_part
    return Pos(0, mount_pivot_y, mount_pivot_z) * at_pivot.rotate(
        Axis.X, -90 - angle_deg
    )


# Tip travel is descriptive: it does not add a stop or constrain rotation.
tip_radius = hypot(total_length - pivot_from_tip,
                   paddle_thickness / 2 - pivot_height)
swing_angle_deg = degrees(2 * asin(tip_travel / (2 * tip_radius)))
result = mounted_part() if show_mounted else print_part

if __name__ == "__main__":
    from ocp_viewer import show

    print(f"Tip travel {tip_travel:g} mm corresponds to {swing_angle_deg:.2f} degrees")
    show(result)
    export_stl(result, str("/tmp/bin_paddle.stl"))
