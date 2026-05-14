#!/usr/bin/env python3
"""Build123d generator for the Starcloud-4 orbital data-center concept.

Units: millimeters.
Origin: center of the solar mesh panel.
XY: nominal solar mesh panel plane.
+Z: hardware side of the panel.
"""

from __future__ import annotations

from math import acos, degrees, sqrt
from pathlib import Path

from build123d import Box, Compound, Cylinder, Location, Sphere, Torus, export_step


ROOT = Path(__file__).resolve().parent
DEFAULT_STEP_PATH = ROOT / "exports" / "starcloud4_prototype_build123d.step"

Vec = tuple[float, float, float]


def _label(shape, label: str):
    shape.label = label
    return shape


def _box(label: str, center: Vec, size: Vec, rotation: Vec = (0.0, 0.0, 0.0)):
    return _label(Location(center) * Box(size[0], size[1], size[2], rotation=rotation), label)


def _cylinder_between(label: str, p1: Vec, p2: Vec, radius: float):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    length = sqrt(dx * dx + dy * dy + dz * dz)
    if length <= 0.0:
        raise ValueError(f"{label} has zero length")

    direction = (dx / length, dy / length, dz / length)
    center = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0, (p1[2] + p2[2]) / 2.0)
    shape = Cylinder(radius, length)

    axis = (-direction[1], direction[0], 0.0)
    axis_length = sqrt(axis[0] * axis[0] + axis[1] * axis[1] + axis[2] * axis[2])
    if axis_length > 1e-9:
        angle = degrees(acos(max(-1.0, min(1.0, direction[2]))))
        shape = Location((0.0, 0.0, 0.0), axis, angle) * shape
    elif direction[2] < 0.0:
        shape = Location((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0) * shape

    return _label(Location(center) * shape, label)


def _sphere(label: str, center: Vec, radius: float):
    return _label(Location(center) * Sphere(radius), label)


def solar_mesh_panel() -> list:
    panel_length = 1850.0
    panel_width = 1050.0
    parts = [
        _box("solar_mesh_panel_dark_membrane", (0.0, 0.0, -4.0), (panel_length, panel_width, 8.0)),
        _box("solar_mesh_panel_outer_frame_front", (0.0, -525.0, 4.0), (panel_length, 12.0, 16.0)),
        _box("solar_mesh_panel_outer_frame_back", (0.0, 525.0, 4.0), (panel_length, 12.0, 16.0)),
        _box("solar_mesh_panel_outer_frame_left", (-925.0, 0.0, 4.0), (12.0, panel_width, 16.0)),
        _box("solar_mesh_panel_outer_frame_right", (925.0, 0.0, 4.0), (12.0, panel_width, 16.0)),
    ]

    for index, x in enumerate(range(-800, 901, 160)):
        parts.append(_box(f"solar_mesh_panel_longitudinal_grid_{index:02d}", (x, 0.0, 10.0), (4.0, 1040.0, 8.0)))
    for index, y in enumerate(range(-480, 481, 120)):
        parts.append(_box(f"solar_mesh_panel_cross_grid_{index:02d}", (0.0, y, 12.0), (1840.0, 4.0, 8.0)))
    for index, y0 in enumerate(range(-470, 471, 145)):
        parts.append(
            _cylinder_between(
                f"solar_mesh_panel_diagonal_lattice_a_{index:02d}",
                (-890.0, y0, 18.0),
                (890.0, y0 + 260.0, 18.0),
                3.0,
            )
        )
        parts.append(
            _cylinder_between(
                f"solar_mesh_panel_diagonal_lattice_b_{index:02d}",
                (-890.0, y0 + 260.0, 21.0),
                (890.0, y0, 21.0),
                3.0,
            )
        )
    return parts


def main_data_center_module() -> list:
    parts = [
        _box("main_data_center_module_white_bus", (80.0, -95.0, 76.0), (300.0, 155.0, 96.0)),
        _box("main_data_center_module_dark_side_panel", (80.0, -174.0, 78.0), (292.0, 8.0, 82.0)),
        _box("main_data_center_module_dark_rear_panel", (-74.0, -95.0, 78.0), (8.0, 145.0, 84.0)),
        _box("starcloud_wordmark_plaque_main", (188.0, -180.0, 95.0), (98.0, 8.0, 28.0)),
        _box("starcloud_logo_square_main", (116.0, -181.0, 95.0), (28.0, 8.0, 28.0)),
        _box("starcloud_logo_swoosh_main", (116.0, -186.0, 103.0), (22.0, 7.0, 5.0), (0.0, 0.0, 14.0)),
        _box("starcloud_wordmark_bar_main", (188.0, -186.0, 103.0), (72.0, 7.0, 5.0)),
        _box("main_data_center_module_top_radiator", (80.0, -95.0, 128.0), (260.0, 120.0, 8.0)),
    ]
    for ix, x in enumerate((-66.0, 226.0)):
        for iz, z in enumerate((43.0, 113.0)):
            parts.append(
                _cylinder_between(
                    f"main_data_center_module_corner_fastener_{ix}_{iz}",
                    (x, -181.0, z),
                    (x, -190.0, z),
                    4.0,
                )
            )
    return parts


def compute_module_stack() -> list:
    parts = []
    for row, z in enumerate((60.0, 170.0, 280.0)):
        for col, y in enumerate((165.0, 312.0)):
            prefix = f"compute_module_stack_module_r{row}_c{col}"
            parts.extend(
                [
                    _box(prefix, (635.0, y, z), (230.0, 95.0, 88.0)),
                    _box(f"{prefix}_dark_backplane", (515.0, y, z), (10.0, 88.0, 76.0)),
                    _box(f"{prefix}_panel_seam_horizontal", (636.0, y, z + 45.0), (210.0, 4.0, 5.0)),
                    _box(f"{prefix}_starcloud_marking_plaque", (742.0, y - 53.0, z + 8.0), (82.0, 8.0, 25.0)),
                    _box(f"{prefix}_starcloud_wordmark_bar", (742.0, y - 58.0, z + 14.0), (58.0, 6.0, 4.0)),
                ]
            )
            for dx in (-94.0, 94.0):
                for dz in (-35.0, 35.0):
                    parts.append(
                        _cylinder_between(
                            f"{prefix}_corner_fastener",
                            (635.0 + dx, y - 52.0, z + dz),
                            (635.0 + dx, y - 60.0, z + dz),
                            3.2,
                        )
                    )

    parts.extend(
        [
            _label(Location((756.0, 101.0, 170.0)) * Torus(34.0, 8.0, rotation=(90.0, 0.0, 0.0)), "docking_port_outer_ring"),
            _cylinder_between("docking_port_inner_white_lip", (756.0, 100.0, 170.0), (756.0, 91.0, 170.0), 27.0),
            _cylinder_between("docking_port_dark_center", (756.0, 89.0, 170.0), (756.0, 79.0, 170.0), 16.0),
            _cylinder_between("docking_port_alignment_pin_upper", (756.0, 96.0, 205.0), (756.0, 84.0, 205.0), 4.0),
            _cylinder_between("docking_port_alignment_pin_lower", (756.0, 96.0, 135.0), (756.0, 84.0, 135.0), 4.0),
        ]
    )
    return parts


def connector_booms() -> list:
    return [
        _cylinder_between("connector_boom_main_to_panel", (-72.0, -95.0, 48.0), (-210.0, -95.0, 22.0), 9.0),
        _cylinder_between("connector_boom_compute_to_panel_upper", (515.0, 312.0, 115.0), (410.0, 260.0, 22.0), 7.0),
        _cylinder_between("connector_boom_compute_to_panel_lower", (515.0, 165.0, 115.0), (405.0, 150.0, 22.0), 7.0),
        _cylinder_between("proximity_docking_boom_tug_to_port", (445.0, -335.0, 90.0), (645.0, 85.0, 150.0), 5.0),
    ]


def tug_capsule() -> list:
    parts = [
        _cylinder_between("tug_capsule_rounded_body", (-505.0, -390.0, 92.0), (-385.0, -390.0, 92.0), 48.0),
        _sphere("tug_capsule_aft_rounding", (-510.0, -390.0, 92.0), 44.0),
        _cylinder_between("tug_capsule_dark_nose_window", (-385.0, -390.0, 92.0), (-335.0, -390.0, 92.0), 38.0),
        _box("tug_capsule_left_winglet", (-455.0, -448.0, 82.0), (82.0, 12.0, 42.0), (-56.0, 0.0, 0.0)),
        _box("tug_capsule_right_winglet", (-455.0, -332.0, 82.0), (82.0, 12.0, 42.0), (56.0, 0.0, 0.0)),
        _box("tug_capsule_top_docking_panel", (-425.0, -390.0, 145.0), (54.0, 70.0, 8.0)),
        _cylinder_between("tug_capsule_forward_docking_probe", (-335.0, -390.0, 92.0), (-292.0, -390.0, 92.0), 8.0),
        _box("starcloud_marking_plaque_tug", (-425.0, -440.0, 118.0), (68.0, 8.0, 18.0)),
        _box("starcloud_marking_bar_tug", (-425.0, -446.0, 123.0), (46.0, 5.0, 4.0)),
    ]
    return parts


def gen_step() -> Compound:
    """Return the Starcloud-4 concept as a labeled build123d assembly compound."""
    parts = []
    parts.extend(solar_mesh_panel())
    parts.extend(main_data_center_module())
    parts.extend(compute_module_stack())
    parts.extend(connector_booms())
    parts.extend(tug_capsule())
    return Compound(children=parts, label="starcloud4_orbital_data_center")


def main() -> None:
    DEFAULT_STEP_PATH.parent.mkdir(parents=True, exist_ok=True)
    export_step(gen_step(), DEFAULT_STEP_PATH)
    print(f"STEP: {DEFAULT_STEP_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
