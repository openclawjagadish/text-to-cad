# Starship Upper Stage Prototype

Lightweight build123d prototype of a SpaceX Starship-style upper stage.
The model prioritizes a recognizable windward product-render visual: tall
stainless cylindrical body, rounded ogive nose, bold black heat-shield tile
blanket continuing toward the nose and aft skirt, clustered aft engine bells,
large swept forward and aft flaps, raceways, and subtle circumferential panel
seams.

## Scale and Dimensions

- Units: millimeters
- Scale: approximately 1:100
- Main stage radius: 45 mm
- Stainless cylindrical body height: 350 mm
- Nose height: 120 mm
- Aft skirt height: 30 mm
- Overall exported bounding box from inspection: about 126 x 111 x 534 mm
- Coordinate convention: Z-up, vehicle centerline on the global Z axis

This is a visual prototype, not an engineering-accurate vehicle model.  All
major features are closed BREP solids and labeled in the build123d assembly,
including the individual raised heat-shield tiles and swept flap plates.

## Files

- `starship_upper_stage_prototype.py` - build123d source with `gen_step()`
- `exports/starship_upper_stage_prototype.step` - primary CAD artifact
- `exports/starship_upper_stage_prototype.stl` - mesh sidecar
- `exports/starship_upper_stage_prototype_preview.png` - rendered preview
- `exports/.starship_upper_stage_prototype.step.glb` - CAD Explorer topology sidecar used by inspection
## Regeneration

From the repository root:

```bash
.venv/bin/python -m py_compile examples/starship-upper-stage/starship_upper_stage_prototype.py
```

```bash
.venv/bin/python skills/cad/scripts/step \
  examples/starship-upper-stage/starship_upper_stage_prototype.py \
  -o examples/starship-upper-stage/exports/starship_upper_stage_prototype.step \
  --stl starship_upper_stage_prototype.stl
```

```bash
.venv/bin/python skills/cad/scripts/inspect refs \
  examples/starship-upper-stage/exports/starship_upper_stage_prototype.step \
  --facts --planes --positioning
```

```bash
.venv/bin/python skills/cad/scripts/render view \
  examples/starship-upper-stage/exports/starship_upper_stage_prototype.step \
  --camera 270:18:720 \
  --width 1400 \
  --height 900 \
  --preset solid \
  --color-by step \
  --edges thin \
  --no-axes \
  -o examples/starship-upper-stage/exports/starship_upper_stage_prototype_preview.png
```

The STEP export may also create a hidden CAD Explorer GLB topology sidecar when
regenerating locally; it is not required for the checked-in example.
