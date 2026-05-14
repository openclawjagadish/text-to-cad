# Starcloud-4 Space Data Center CAD Prototype

This directory contains a source-controlled concept CAD prototype inspired by the public Starcloud-4 page and local reference screenshots captured during generation.

## Design Interpretation

The model is a lightweight in-orbit modular data center assembly in millimeters:

- `solar_mesh_panel`: a very large, thin, dark rectangular panel with outer rails, cross-grid members, and diagonal lattice beams.
- `main_data_center_module`: a white foreground rectangular data-center bus mounted above the panel, with dark side and rear panels plus raised Starcloud-style marking plaques.
- `compute_module_stack`: six repeated white server/compute modules in a side stack, each with seams, dark backplanes, small corner fasteners, and Starcloud-style markings.
- `docking_port`: a circular ring and dark center mounted on one compute module.
- `tug_capsule`: a nearby white capsule/tug with rounded body, dark nose/window cone, winglets, top docking panel, and forward probe.
- `connector_booms`: small dark rods tying the main module, stack, and tug/dock pose back to the panel architecture.

The geometry is intentionally faceted and low-detail so it remains fast to regenerate locally while still reading as real 3D CAD rather than flat artwork.

## Regeneration

From the repository root:

```bash
python3 examples/starcloud-4/starcloud4_prototype.py
```

This writes:

- `exports/starcloud4_prototype.step` - primary reviewable CAD artifact.
- `exports/starcloud4_prototype.stl` - secondary mesh artifact.
- `exports/starcloud4_prototype_preview.png` - quick rendered preview generated with Pillow when available.

The preferred bundled `skills/cad` build123d workflow was checked first. In this sandbox, `build123d` and `OCP` were not installed, and installing them was blocked by network/DNS restrictions. To keep the prototype reproducible end-to-end, `starcloud4_prototype.py` uses a dependency-light faceted CAD writer and exposes a `gen_step()` source function returning named solid components.

## Verification

The expected verification flow is:

```bash
python3 examples/starcloud-4/starcloud4_prototype.py
python3 -m py_compile examples/starcloud-4/starcloud4_prototype.py
find examples/starcloud-4/exports -type f -maxdepth 1 -print
```

Artifact existence and non-empty file sizes are part of the completion audit.

## TODO

- CAD Explorer review was attempted, but the local Explorer port range `4178-4198` was already unavailable in this environment. Re-run the `dev:ensure` command after freeing or extending the Explorer port range if an interactive browser review is needed.
- Port the faceted fallback generator to the preferred build123d/OCP workflow once the CAD Python dependencies are available locally.
