"""Build123d prototype of a Starship-style upper stage.

Units are millimeters.  The model is intentionally lightweight and visual:
roughly 1:100 scale, Z-up, with the stage centerline on the global Z axis.
"""

from __future__ import annotations

from math import cos, radians, sin

from build123d import (
    Axis,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    Cone,
    Cylinder,
    Location,
    Plane,
    Polygon,
    Polyline,
    Spline,
    Torus,
    extrude,
    make_face,
    revolve,
)


def _placed(shape, label: str, color: Color, xyz, rotation=(0, 0, 0)):
    placed = shape.located(Location(xyz, rotation))
    placed.label = label
    placed.color = color
    return placed


def _tangent_plate(
    *,
    label: str,
    color: Color,
    angle_deg: float,
    radius: float,
    z: float,
    tangential_width: float,
    radial_thickness: float,
    height: float,
):
    angle = radians(angle_deg)
    center_radius = radius + radial_thickness / 2
    xyz = (center_radius * cos(angle), center_radius * sin(angle), z)
    rotation = (0, 0, angle_deg - 90)
    return _placed(
        Box(tangential_width, radial_thickness, height),
        label,
        color,
        xyz,
        rotation,
    )


def _ogive_nose(radius: float, height: float, base_z: float):
    """Rounded Starship-like nose profile revolved around the Z axis."""
    with BuildLine() as profile:
        Polyline((0, 0, base_z), (radius, 0, base_z))
        Spline(
            (radius, 0, base_z),
            (radius * 0.98, 0, base_z + height * 0.22),
            (radius * 0.80, 0, base_z + height * 0.58),
            (radius * 0.38, 0, base_z + height * 0.88),
            (0, 0, base_z + height),
            tangents=(
                (0, 0, 1),
                (-0.12, 0, 1),
                (-0.55, 0, 1),
                (-1, 0, 0.55),
                (-1, 0, 0),
            ),
        )
        Polyline((0, 0, base_z + height), (0, 0, base_z))
    return revolve(make_face(profile.edges()), axis=Axis.Z)


def _swept_flap(
    *,
    label: str,
    color: Color,
    angle_deg: float,
    radius: float,
    z: float,
    height: float,
    span: float,
):
    """Broad swept aerodynamic plate; local X is radial, local Z is vertical."""
    with BuildPart() as flap:
        with BuildSketch(Plane.XZ):
            Polygon(
                (0, -height * 0.50),
                (span * 0.90, -height * 0.34),
                (span, height * 0.28),
                (span * 0.18, height * 0.50),
                (-span * 0.10, height * 0.36),
                (-span * 0.03, -height * 0.44),
            )
        extrude(amount=8.0)
    angle = radians(angle_deg)
    flap.part.label = label
    flap.part.color = color
    return flap.part.located(
        Location(
            ((radius + span * 0.42) * cos(angle), (radius + span * 0.42) * sin(angle), z),
            (0, 0, angle_deg),
        )
    )


def gen_step():
    # Approximate 1:100 dimensions from the public Starship visual envelope.
    stage_radius = 45.0
    body_height = 350.0
    nose_height = 120.0
    aft_skirt_height = 30.0
    body_center_z = -30.0
    body_top_z = body_center_z + body_height / 2
    body_bottom_z = body_center_z - body_height / 2
    skirt_center_z = body_bottom_z - aft_skirt_height / 2

    stainless = Color(0.82, 0.84, 0.80, 1.0)
    stainless_bright = Color(0.93, 0.94, 0.90, 1.0)
    stainless_dark = Color(0.44, 0.46, 0.45, 1.0)
    black_tile = Color(0.002, 0.002, 0.002, 1.0)
    tile_grout = Color(0.075, 0.078, 0.080, 1.0)
    dark_metal = Color(0.035, 0.037, 0.040, 1.0)
    seam_color = Color(0.30, 0.31, 0.31, 1.0)

    parts = []

    parts.append(
        _placed(
            Cylinder(stage_radius, body_height),
            "stainless_cylindrical_body",
            stainless,
            (0, 0, body_center_z),
        )
    )
    parts.append(
        _placed(
            _ogive_nose(stage_radius, nose_height, body_top_z),
            "smooth_rounded_ogive_nose",
            stainless,
            (0, 0, 0),
        )
    )
    parts.append(
        _placed(
            Cylinder(stage_radius + 2.5, aft_skirt_height),
            "slightly_flared_aft_engine_skirt",
            stainless_dark,
            (0, 0, skirt_center_z),
        )
    )
    parts.append(
        _placed(
            Torus(major_radius=stage_radius + 0.8, minor_radius=1.2),
            "soft_stainless_nose_body_shoulder",
            stainless_bright,
            (0, 0, body_top_z),
        )
    )

    # Bold windward thermal protection blanket. The individual raised BREP
    # tiles leave real gaps so the rendered thumbnail still shows a grid.
    tile_angles = (202, 218, 234, 250, 266, 282, 298, 314, 330, 346)
    tile_zs = [body_bottom_z + 10 + i * 18 for i in range(22)]
    for zi, z in enumerate(tile_zs):
        for ai, angle in enumerate(tile_angles):
            stagger = 8.0 if zi % 2 else 0.0
            parts.append(
                _tangent_plate(
                    label=f"black_heatshield_tile_{zi:02d}_{ai:02d}",
                    color=black_tile,
                    angle_deg=angle + stagger,
                    radius=stage_radius + 0.7,
                    z=z,
                    tangential_width=13.0,
                    radial_thickness=3.2,
                    height=15.0,
                )
            )

    for zi, z in enumerate((body_top_z + 9, body_top_z + 25, body_top_z + 42, body_top_z + 59)):
        for ai, angle in enumerate((222, 240, 258, 276, 294, 312, 330)):
            parts.append(
                _tangent_plate(
                    label=f"black_tiles_up_rounded_nose_{zi:02d}_{ai:02d}",
                    color=black_tile,
                    angle_deg=angle,
                    radius=stage_radius - zi * 3.2,
                    z=z,
                    tangential_width=12.0,
                    radial_thickness=2.8,
                    height=11.0,
                )
            )

    for ai, angle in enumerate((210, 230, 250, 270, 290, 310, 330)):
        parts.append(
            _tangent_plate(
                label=f"black_tiles_on_aft_skirt_{ai:02d}",
                color=black_tile,
                angle_deg=angle,
                radius=stage_radius + 2.8,
                z=skirt_center_z,
                tangential_width=17.0,
                radial_thickness=3.2,
                height=aft_skirt_height - 4.0,
            )
        )

    for idx, angle in enumerate((198, 354)):
        parts.append(
            _tangent_plate(
                label=f"raised_dark_heatshield_edge_grout_{idx+1}",
                color=tile_grout,
                angle_deg=angle,
                radius=stage_radius + 1.0,
                z=-4.0,
                tangential_width=3.0,
                radial_thickness=3.0,
                height=370.0,
            )
        )

    # Subtle raised raceways, bright reflection bands, and ring seams.
    for idx, angle in enumerate((25, 78)):
        parts.append(
            _tangent_plate(
                label=f"raised_stainless_raceway_{idx+1}",
                color=seam_color,
                angle_deg=angle,
                radius=stage_radius + 0.6,
                z=-25.0,
                tangential_width=3.0,
                radial_thickness=2.0,
                height=280.0,
            )
        )

    for idx, angle in enumerate((120, 155)):
        parts.append(
            _tangent_plate(
                label=f"polished_stainless_vertical_highlight_{idx+1}",
                color=stainless_bright,
                angle_deg=angle,
                radius=stage_radius + 0.8,
                z=-20.0,
                tangential_width=9.0,
                radial_thickness=1.2,
                height=315.0,
            )
        )

    for idx, z in enumerate((-185.0, -90.0, 12.0, 108.0, body_top_z + 8.0)):
        parts.append(
            _placed(
                Cylinder(stage_radius + 1.0, 1.6),
                f"fine_circumferential_panel_seam_{idx+1}",
                seam_color,
                (0, 0, z),
            )
        )

    # Large forward and aft flaps mounted on the heat-shield side shoulders.
    for side, angle in (("port", 224), ("starboard", 316)):
        parts.append(
            _swept_flap(
                label=f"{side}_large_swept_forward_flap",
                color=stainless_dark,
                angle_deg=angle,
                radius=stage_radius,
                z=102.0,
                height=86.0,
                span=30.0,
            )
        )
        parts.append(
            _swept_flap(
                label=f"{side}_large_swept_aft_flap",
                color=stainless_dark,
                angle_deg=angle,
                radius=stage_radius + 2.0,
                z=-168.0,
                height=118.0,
                span=38.0,
            )
        )

    # Six clustered engine bells below the skirt, protruding enough to read in preview.
    engine_positions = (
        (0.0, -18.0),
        (-15.6, 9.0),
        (15.6, 9.0),
        (-24.0, -12.0),
        (24.0, -12.0),
        (0.0, 23.0),
    )
    for idx, (x, y) in enumerate(engine_positions, start=1):
        parts.append(
            _placed(
                Cone(12.5, 5.2, 34.0),
                f"clustered_engine_bell_{idx}",
                dark_metal,
                (x, y, body_bottom_z - aft_skirt_height - 17.0),
                (180, 0, 0),
            )
        )
        parts.append(
            _placed(
                Cylinder(5.2, 8.0),
                f"engine_throat_{idx}",
                dark_metal,
                (x, y, body_bottom_z - aft_skirt_height + 3.0),
            )
        )

    assembly = Compound(label="starship_upper_stage_prototype", children=parts)
    return assembly


if __name__ == "__main__":
    model = gen_step()
    print(f"{model.label}: {len(model.children)} labeled solids")
