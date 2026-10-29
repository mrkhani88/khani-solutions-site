# Vast Haven-1 public-reference engineering study — Stage 01 CAD R1

This is an independent interview study, not Vast manufacturing CAD. Stage 01 is a geometry review checkpoint. No thermal, CFD, structural, thermal-vacuum qualification or mission performance result is claimed.

## Open and inspect

- Open `review/Review.html` through a local HTTP server rooted at this project. Current review: http://127.0.0.1:8893/review/Review.html . Drag to rotate; use cutaway, visibility, search, component inspection and system focus.
- FreeCAD: `cad/Haven1_Public_Reference_R1.FCStd` (native BREP features grouped by subsystem; no external workbench required).
- CAD exchange: `cad/Haven1_Public_Reference_R1.step` and individual `Subsystem_*.step` files.
- Blender: `cad/Haven1_Public_Reference_R1.blend`. GLB is portable visualization geometry in metres.
- STL is a combined component assembly in millimetres. It is NOT a preprocessed CFD fluid domain or a merged watertight vehicle skin.
- `scripts/assembly_spec.json` is the editable dimensional/component master. Run `scripts/create_spec.py` to regenerate that JSON, then run the FreeCAD macro on Intel to rebuild the assembly. Edit the generator when changing persistent parameters.

## Evidence and scope

The exterior uses the published 10.1 m length and 4.4 m barrel diameter, the 1.1 m radial domed window, axial docking, tapered ends and solar-array appearance. Public counts retained: 12 solar wings, four private crew quarters, six CMGs, eight wet-trash containers and eight lab slots. Exact bay, equipment and solar hinge/cell geometry is inferred.

Main native components include structure, exterior protection proxies, docking/window, four solar bank planforms grouped into 12 wings, candidate radiator surfaces, crew quarters/table, lab equipment, avionics/cold plates, power electronics, batteries, six CMGs, ECLSS air-handler/filter/ducts/fans, gas/propellant envelopes and waste containers.

Additional STUDY DESIGN elements include MPPT/charging regulators, BMS, heater controller and heater patches, thermal controller, pump cartridges/accumulator, valves, temperature/flow/pressure sensing, thermal interface layers, insulation zones, equipment rails and water/condensate resource interfaces. Their exact presence, quantities and packaging on the flight vehicle are NOT claimed. This extends the thermal architecture for a later representative study rather than reverse-engineering confidential hardware.

Subsystem colors identify function, not temperature. The illustrative 12 mm shell and 6 mm MLI zone are visualization dimensions, not selected pressure-vessel thickness or a solid-metal representation of insulation. No mass, emissivity, conductivity, heater rating, capacity, loss factor or dissipation may be inferred from these proxies.

Published 80 m3 pressurized / 45 m3 habitable volumes are independent reference values. This first visual reconstruction has not been calibrated to those cabin volumes. Do not use the outer-envelope volume as either pressure-vessel or habitable air volume. Resolve true cabin envelopes, wall/blanket stackups and structural/thermal contacts before analysis.

## Source trail

See `sources/evidence-register.json`, `sources/SOURCE_NOTES.md` and `sources/thermal-coverage-matrix.md`. Original imagery is credited to Vast with watermarks preserved. The documented Vast docking patent is background evidence about docking concepts, not a dimensioned Haven-1 hull blueprint. Public ECLSS publications inform subsystem understanding; unpublished dimensions and inaccessible papers are not treated as known inputs.

## Verification

FreeCAD construction and STEP export/import occur on Intel. `verification/cad-verification.json` records valid positive-volume shapes and persisted native-file reopening. `verification/blender-verification.json` records scene/GLB/renders. `verification/delivery-manifest.json` records delivered file hashes. Numerical geometry checks do not establish physical validation, accurate subsystem packaging or simulation-ready meshing.

## Next stages — not executed

1. Review exterior and component layout; refine pressure/cabin envelopes and avoid clashes or blocked access. Confirm component/loop boundaries and assumption register.
2. Build a full OpenModelica thermal/power-resource network with explicit subsystem models: orbit/sun/eclipse attitude inputs, solar/battery/PDU energy, avionics/payload/battery/crew heat, forced cabin ventilation and humidity, cold plates/coolant loop/radiator, heaters/sensors/controller limits and fault cases. Assign measured/public inputs and bounded assumptions; reconcile the energy balance.
3. Select local FreeCAD geometry for 3D conduction/contacts and OpenFOAM coolant/airflow CFD. Vacuum exterior exchange is radiation/conduction modeling, not conventional atmospheric aerodynamic CFD. Refine cold-plate channels and watertight, named fluid boundaries first.
4. Run controlled baseline/trade/fault cases, numerical sensitivity, and documented correlation/validation planning. Optimization follows a defensible baseline.
5. Prepare an interview deck from the actual CAD views and solved results as stages finish; distinguish simulation evidence, planned tests and physical test evidence.

## Rebuild on Intel

Project directory: `/home/falcon-admin/projects/vast-haven-1/stage-01-cad-r1`.

```
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 xvfb-run -a -s "-screen 0 1600x1000x24" /home/falcon-admin/.local/bin/freecad scripts/build_model.FCMacro
OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 blender -b -t 8 --python scripts/render_blender.py
```

The build uses a private X server and does not alter any existing solver or GUI session. The `.blend` mesh is generated from the same FreeCAD tessellation as the review viewer. Geometry uses world X longitudinal, Y lateral, Z up; native CAD and STL mm, viewer/Blender/GLB metres.
