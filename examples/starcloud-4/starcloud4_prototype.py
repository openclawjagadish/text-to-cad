#!/usr/bin/env python3
"""Generate a lightweight CAD prototype of the Starcloud-4 space data center.

The model is intentionally dependency-light so it can regenerate in this repo
without network access.  It emits faceted STEP, STL, and a review PNG from the
same editable Python source.

Units: millimeters.
Origin: center of the solar mesh panel.
XY: nominal solar mesh panel plane.
+Z: hardware side of the panel.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - preview is optional but available here
    Image = ImageDraw = ImageFont = None


Vec = tuple[float, float, float]
Face = list[Vec]

ROOT = Path(__file__).resolve().parent
EXPORT_DIR = ROOT / "exports"
STEP_PATH = EXPORT_DIR / "starcloud4_prototype.step"
STL_PATH = EXPORT_DIR / "starcloud4_prototype.stl"
PNG_PATH = EXPORT_DIR / "starcloud4_prototype_preview.png"


@dataclass
class Solid:
    name: str
    faces: list[Face]
    color: tuple[int, int, int]


def v_add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_scale(a: Vec, s: float) -> Vec:
    return (a[0] * s, a[1] * s, a[2] * s)


def v_dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def v_cross(a: Vec, b: Vec) -> Vec:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def v_len(a: Vec) -> float:
    return sqrt(v_dot(a, a))


def v_norm(a: Vec) -> Vec:
    length = v_len(a)
    if length == 0:
        raise ValueError("cannot normalize zero-length vector")
    return v_scale(a, 1.0 / length)


def basis_from_axis(axis: Vec) -> tuple[Vec, Vec, Vec]:
    w = v_norm(axis)
    seed = (0.0, 0.0, 1.0) if abs(v_dot(w, (0.0, 0.0, 1.0))) < 0.9 else (0.0, 1.0, 0.0)
    u = v_norm(v_cross(seed, w))
    v = v_norm(v_cross(w, u))
    return u, v, w


def box(name: str, center: Vec, size: Vec, color: tuple[int, int, int], axes: tuple[Vec, Vec, Vec] | None = None) -> Solid:
    u, v, w = axes or ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    hx, hy, hz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0

    def p(sx: float, sy: float, sz: float) -> Vec:
        return v_add(center, v_add(v_add(v_scale(u, sx * hx), v_scale(v, sy * hy)), v_scale(w, sz * hz)))

    c = {
        "lll": p(-1, -1, -1),
        "rll": p(1, -1, -1),
        "rrl": p(1, 1, -1),
        "lrl": p(-1, 1, -1),
        "llh": p(-1, -1, 1),
        "rlh": p(1, -1, 1),
        "rrh": p(1, 1, 1),
        "lrh": p(-1, 1, 1),
    }
    faces = [
        [c["lll"], c["lrl"], c["rrl"], c["rll"]],
        [c["llh"], c["rlh"], c["rrh"], c["lrh"]],
        [c["lll"], c["rll"], c["rlh"], c["llh"]],
        [c["rll"], c["rrl"], c["rrh"], c["rlh"]],
        [c["rrl"], c["lrl"], c["lrh"], c["rrh"]],
        [c["lrl"], c["lll"], c["llh"], c["lrh"]],
    ]
    return Solid(name, faces, color)


def cylinder(name: str, p1: Vec, p2: Vec, radius: float, color: tuple[int, int, int], segments: int = 28) -> Solid:
    u, v, _ = basis_from_axis(v_sub(p2, p1))
    ring1: list[Vec] = []
    ring2: list[Vec] = []
    for i in range(segments):
        a = 2.0 * pi * i / segments
        off = v_add(v_scale(u, cos(a) * radius), v_scale(v, sin(a) * radius))
        ring1.append(v_add(p1, off))
        ring2.append(v_add(p2, off))
    faces: list[Face] = [list(reversed(ring1)), ring2]
    for i in range(segments):
        j = (i + 1) % segments
        faces.append([ring1[i], ring1[j], ring2[j], ring2[i]])
    return Solid(name, faces, color)


def cone(name: str, base: Vec, tip: Vec, radius: float, color: tuple[int, int, int], segments: int = 28) -> Solid:
    u, v, _ = basis_from_axis(v_sub(tip, base))
    ring: list[Vec] = []
    for i in range(segments):
        a = 2.0 * pi * i / segments
        ring.append(v_add(base, v_add(v_scale(u, cos(a) * radius), v_scale(v, sin(a) * radius))))
    faces: list[Face] = [list(reversed(ring))]
    for i in range(segments):
        faces.append([ring[i], ring[(i + 1) % segments], tip])
    return Solid(name, faces, color)


def ellipsoid(name: str, center: Vec, radii: Vec, color: tuple[int, int, int], rings: int = 8, segments: int = 24) -> Solid:
    faces: list[Face] = []
    grid: list[list[Vec]] = []
    for r in range(rings + 1):
        phi = -pi / 2.0 + pi * r / rings
        row = []
        for s in range(segments):
            theta = 2.0 * pi * s / segments
            row.append(
                (
                    center[0] + radii[0] * cos(phi) * cos(theta),
                    center[1] + radii[1] * cos(phi) * sin(theta),
                    center[2] + radii[2] * sin(phi),
                )
            )
        grid.append(row)
    for r in range(rings):
        for s in range(segments):
            faces.append([grid[r][s], grid[r][(s + 1) % segments], grid[r + 1][(s + 1) % segments], grid[r + 1][s]])
    return Solid(name, faces, color)


def beam_between(name: str, p1: Vec, p2: Vec, width: float, depth: float, color: tuple[int, int, int]) -> Solid:
    axis = v_sub(p2, p1)
    u = v_norm(axis)
    w = (0.0, 0.0, 1.0)
    v = v_norm(v_cross(w, u))
    center = v_scale(v_add(p1, p2), 0.5)
    return box(name, center, (v_len(axis), width, depth), color, (u, v, w))


def panel_lattice() -> list[Solid]:
    solids: list[Solid] = []
    panel_color = (46, 55, 60)
    rail_color = (122, 136, 139)
    solids.append(box("solar_mesh_panel_thin_dark_membrane", (0, 0, -4), (1850, 1050, 8), panel_color))
    solids.append(box("solar_mesh_panel_outer_frame", (0, -525, 4), (1850, 10, 12), rail_color))
    solids.append(box("solar_mesh_panel_outer_frame", (0, 525, 4), (1850, 10, 12), rail_color))
    solids.append(box("solar_mesh_panel_outer_frame", (-925, 0, 4), (10, 1050, 12), rail_color))
    solids.append(box("solar_mesh_panel_outer_frame", (925, 0, 4), (10, 1050, 12), rail_color))

    for x in range(-800, 901, 160):
        solids.append(box("solar_mesh_panel_longitudinal_grid", (x, 0, 10), (4, 1040, 7), rail_color))
    for y in range(-480, 481, 120):
        solids.append(box("solar_mesh_panel_cross_grid", (0, y, 11), (1840, 4, 7), rail_color))

    for i, y0 in enumerate(range(-470, 471, 145)):
        solids.append(beam_between(f"solar_mesh_panel_diagonal_lattice_a_{i:02d}", (-890, y0, 16), (890, y0 + 260, 16), 4, 6, rail_color))
        solids.append(beam_between(f"solar_mesh_panel_diagonal_lattice_b_{i:02d}", (-890, y0 + 260, 18), (890, y0, 18), 4, 6, rail_color))
    return solids


def main_data_center_module() -> list[Solid]:
    solids = [
        box("main_data_center_module_white_bus", (80, -95, 76), (300, 155, 96), (232, 232, 225)),
        box("main_data_center_module_dark_side_panel", (80, -174, 78), (292, 8, 82), (26, 31, 36)),
        box("main_data_center_module_dark_rear_panel", (-74, -95, 78), (8, 145, 84), (24, 27, 31)),
        box("starcloud_wordmark_plaque_main", (188, -175, 95), (98, 5, 28), (18, 20, 22)),
        box("starcloud_logo_square_main", (116, -176, 95), (28, 6, 28), (18, 20, 22)),
        box("starcloud_logo_swoosh_main", (116, -180, 102), (22, 5, 5), (232, 232, 225)),
    ]
    for sx in (-1, 1):
        for sz in (-1, 1):
            solids.append(cylinder("main_data_center_module_corner_fastener", (226, -181, 78 + sz * 35), (226, -186, 78 + sz * 35), 4, (33, 34, 36), 16))
            solids.append(cylinder("main_data_center_module_corner_fastener", (-66, -181, 78 + sz * 35), (-66, -186, 78 + sz * 35), 4, (33, 34, 36), 16))
    return solids


def compute_module_stack() -> list[Solid]:
    solids: list[Solid] = []
    for row, z in enumerate((60, 170, 280)):
        for col, y in enumerate((165, 312)):
            name = f"compute_module_stack_module_r{row}_c{col}"
            solids.append(box(name, (635, y, z), (230, 95, 88), (232, 231, 224)))
            solids.append(box(f"{name}_dark_backplane", (515, y, z), (10, 88, 76), (28, 31, 35)))
            solids.append(box(f"{name}_panel_seam_horizontal", (636, y, z + 45), (210, 4, 5), (125, 128, 125)))
            solids.append(box(f"{name}_starcloud_marking_plaque", (742, y - 49, z + 8), (82, 5, 25), (23, 25, 27)))
            for dx in (-94, 94):
                for dz in (-35, 35):
                    solids.append(cylinder(f"{name}_corner_fastener", (635 + dx, y - 51, z + dz), (635 + dx, y - 56, z + dz), 3.2, (31, 32, 34), 12))
    solids.append(cylinder("docking_port_outer_ring", (756, 113, 170), (756, 103, 170), 42, (30, 32, 36), 36))
    solids.append(cylinder("docking_port_inner_white_lip", (756, 100, 170), (756, 91, 170), 27, (222, 222, 215), 36))
    solids.append(cylinder("docking_port_dark_center", (756, 88, 170), (756, 78, 170), 16, (18, 19, 22), 36))
    return solids


def connector_booms() -> list[Solid]:
    return [
        cylinder("connector_boom_main_to_panel", (-72, -95, 48), (-210, -95, 22), 9, (24, 27, 31), 16),
        cylinder("connector_boom_compute_to_panel_upper", (515, 312, 115), (410, 260, 22), 7, (24, 27, 31), 16),
        cylinder("connector_boom_compute_to_panel_lower", (515, 165, 115), (405, 150, 22), 7, (24, 27, 31), 16),
        cylinder("proximity_docking_boom_tug_to_port", (445, -335, 90), (645, 85, 150), 5, (35, 37, 40), 12),
    ]


def tug_capsule() -> list[Solid]:
    solids = [
        cylinder("tug_capsule_rounded_body", (-505, -390, 92), (-385, -390, 92), 48, (232, 232, 225), 28),
        ellipsoid("tug_capsule_aft_rounding", (-505, -390, 92), (44, 48, 48), (232, 232, 225), 8, 24),
        cone("tug_capsule_dark_nose_window", (-385, -390, 92), (-335, -390, 92), 48, (20, 23, 27), 28),
        box("tug_capsule_left_winglet", (-455, -448, 82), (82, 12, 42), (44, 50, 54), ((1, 0, 0), (0, 0.55, -0.83), (0, 0.83, 0.55))),
        box("tug_capsule_right_winglet", (-455, -332, 82), (82, 12, 42), (44, 50, 54), ((1, 0, 0), (0, 0.55, 0.83), (0, -0.83, 0.55))),
        box("tug_capsule_top_docking_panel", (-425, -390, 145), (54, 70, 8), (49, 54, 57)),
        cylinder("tug_capsule_forward_docking_probe", (-335, -390, 92), (-292, -390, 92), 8, (36, 38, 42), 16),
    ]
    return solids


def gen_step() -> list[Solid]:
    """Return the editable source model as named solid components."""
    solids: list[Solid] = []
    solids.extend(panel_lattice())
    solids.extend(main_data_center_module())
    solids.extend(compute_module_stack())
    solids.extend(connector_booms())
    solids.extend(tug_capsule())
    return solids


def triangulate(face: Face) -> Iterable[tuple[Vec, Vec, Vec]]:
    for i in range(1, len(face) - 1):
        yield face[0], face[i], face[i + 1]


def normal(tri: tuple[Vec, Vec, Vec]) -> Vec:
    n = v_cross(v_sub(tri[1], tri[0]), v_sub(tri[2], tri[0]))
    length = v_len(n)
    return (0.0, 0.0, 0.0) if length == 0 else v_scale(n, 1.0 / length)


def write_stl(solids: list[Solid], path: Path) -> None:
    with path.open("w", encoding="ascii") as f:
        f.write("solid starcloud4_prototype\n")
        for solid in solids:
            for face in solid.faces:
                for tri in triangulate(face):
                    n = normal(tri)
                    f.write(f"  facet normal {n[0]:.7g} {n[1]:.7g} {n[2]:.7g}\n")
                    f.write("    outer loop\n")
                    for p in tri:
                        f.write(f"      vertex {p[0]:.7g} {p[1]:.7g} {p[2]:.7g}\n")
                    f.write("    endloop\n  endfacet\n")
        f.write("endsolid starcloud4_prototype\n")


class StepWriter:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.next_id = 1

    def add(self, text: str) -> int:
        idx = self.next_id
        self.next_id += 1
        self.lines.append(f"#{idx}={text};")
        return idx

    def point(self, p: Vec) -> int:
        return self.add(f"CARTESIAN_POINT('',({p[0]:.6f},{p[1]:.6f},{p[2]:.6f}))")

    def vertex(self, p: Vec) -> int:
        return self.add(f"VERTEX_POINT('',#{self.point(p)})")

    def face(self, points: Face) -> int:
        verts = ",".join(f"#{self.vertex(p)}" for p in points)
        loop = self.add(f"POLY_LOOP('',({verts}))")
        bound = self.add(f"FACE_OUTER_BOUND('',#{loop},.T.)")
        plane = self.add("PLANE('',#1)")
        return self.add(f"ADVANCED_FACE('',(#{bound}),#{plane},.T.)")


def write_step(solids: list[Solid], path: Path) -> None:
    w = StepWriter()
    w.add("AXIS2_PLACEMENT_3D('',#2,#3,#4)")
    w.add("CARTESIAN_POINT('',(0.0,0.0,0.0))")
    w.add("DIRECTION('',(0.0,0.0,1.0))")
    w.add("DIRECTION('',(1.0,0.0,0.0))")
    context = w.add("GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#6)) GLOBAL_UNIT_ASSIGNED_CONTEXT((#7,#8,#9)) REPRESENTATION_CONTEXT('','')")
    w.add("UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.01),#7,'distance_accuracy_value','')")
    w.add("SI_UNIT(.MILLI.,.METRE.)")
    w.add("SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT()")
    w.add("SI_UNIT($,.RADIAN.) PLANE_ANGLE_UNIT()")
    solid_ids: list[int] = []
    for solid in solids:
        face_ids = [w.face(face) for face in solid.faces if len(face) >= 3]
        shell = w.add(f"CLOSED_SHELL('{solid.name}',({','.join(f'#{i}' for i in face_ids)}))")
        solid_id = w.add(f"MANIFOLD_SOLID_BREP('{solid.name}',#{shell})")
        solid_ids.append(solid_id)
    w.add(f"SHAPE_REPRESENTATION('starcloud4_prototype',({','.join(f'#{i}' for i in solid_ids)}),#{context})")

    with path.open("w", encoding="ascii") as f:
        f.write("ISO-10303-21;\nHEADER;\n")
        f.write("FILE_DESCRIPTION(('Starcloud-4 space data center concept prototype'),'2;1');\n")
        f.write("FILE_NAME('starcloud4_prototype.step','2026-05-14T00:00:00',('OpenAI Codex'),('earthtojake/text-to-cad'),'faceted python generator','faceted python generator','');\n")
        f.write("FILE_SCHEMA(('AUTOMOTIVE_DESIGN_CC2'));\nENDSEC;\nDATA;\n")
        f.write("\n".join(w.lines))
        f.write("\nENDSEC;\nEND-ISO-10303-21;\n")


def project(p: Vec) -> tuple[float, float, float]:
    rz = -0.46
    rx = 0.96
    x = p[0] * cos(rz) - p[1] * sin(rz)
    y = p[0] * sin(rz) + p[1] * cos(rz)
    z = p[2]
    y2 = y * cos(rx) - z * sin(rx)
    z2 = y * sin(rx) + z * cos(rx)
    return x, y2, z2


def write_preview(solids: list[Solid], path: Path) -> None:
    if Image is None:
        return
    width, height = 1600, 1000
    img = Image.new("RGB", (width, height), (8, 10, 16))
    draw = ImageDraw.Draw(img, "RGBA")

    polys = []
    for solid in solids:
        for face in solid.faces:
            pts3 = [project(p) for p in face]
            depth = sum(p[2] for p in pts3) / len(pts3)
            pts2 = [(width / 2 + p[0] * 0.65, height / 2 - p[1] * 0.65) for p in pts3]
            shade = max(0.45, min(1.18, 0.82 + normal(tuple(face[:3]))[2] * 0.25))
            color = tuple(max(0, min(255, int(c * shade))) for c in solid.color)
            polys.append((depth, pts2, color))

    for _, pts, color in sorted(polys, key=lambda item: item[0]):
        draw.polygon(pts, fill=(*color, 218), outline=(12, 14, 18, 85))

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 38)
        small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except Exception:
        font = small = None
    draw.text((880, 526), "Starcloud", fill=(20, 22, 24), font=font)
    for y in (290, 372, 455):
        draw.text((1175, y), "Starcloud", fill=(20, 22, 24), font=small)
    draw.text((52, 44), "Starcloud-4 CAD prototype", fill=(230, 234, 238), font=font)
    draw.text((54, 92), "faceted STEP/STL preview - units: mm", fill=(154, 168, 178), font=small)
    img.save(path)


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    solids = gen_step()
    write_step(solids, STEP_PATH)
    write_stl(solids, STL_PATH)
    write_preview(solids, PNG_PATH)
    tri_count = sum(1 for solid in solids for face in solid.faces for _ in triangulate(face))
    print(f"Generated {len(solids)} named solids and {tri_count} STL triangles")
    print(f"STEP: {STEP_PATH.relative_to(ROOT)}")
    print(f"STL:  {STL_PATH.relative_to(ROOT)}")
    print(f"PNG:  {PNG_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
