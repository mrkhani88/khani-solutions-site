STAGE 07 — ADHESIVE THICKNESS UNDER THE LARGEST GRAPHITE SHEET
Independent Khani Solutions teaching model. Inputs are assumptions; no measured
product performance, physical validation or battery safety qualification.

REPRODUCE WITH FREE / OPEN-SOURCE SOFTWARE
1. Install Python 3 and the dependencies: pip install -r source/requirements.txt
2. From this archive root: python source/run_adhesive_study.py
   Runs three physical stacks plus a separate resistance-only diagnostic, with
   mesh/time checks; exports plots, per-case fields, networks, CSV and VTK.
3. python source/verify_exports.py
   Independently rebuilds the exported physical networks, checks all saved fields
   and selected VTK frames, and regenerates the integrated battery energy audit.
4. Optional CAD regeneration: python source/build_adhesive_cad.py with a
   FreeCAD-enabled Python environment; FREECAD_LIB can locate its libraries.
5. Extract results/adhesive_comparison_vtk.zip and open reference/transient.pvd,
   medium/transient.pvd or thick/transient.pvd in ParaView. Coordinates are meters.

CASES AND FIXED CONDITIONS
reference:25µm=.025mm adhesive, RF pad2.075mm, graphite bottomz6.875mm.
medium:50µm=.050mm adhesive, RF pad2.050mm, graphite bottomz6.850mm.
thick:100µm=.100mm adhesive, RF pad2.000mm, graphite bottomz6.800mm.
All:50x70mm footprint [18,30,68,100]mm, graphite.10mm,kxy800/kz5W/mK,
rho1800kg/m3,cp700J/kgK. Adhesive k.2W/mK,rho1200,cp1500. Each bonded
contact R''=.0001m2K/W. Pad contact R''=.0002m2K/W,kpad3W/mK. Outer
cover innerfacez7mm and exteriorz7.8mm fixed. Pad-to-sheet contact80mm2;
each full bonded interface3500mm2. Cell-to-sheet gaps.675/.650/.600mm.
No physical sheet-to-cell contact. Thicker adhesive adds capacity and moves the
sheet inward; the shorter pad and other internal gaps also change. This is not
an isolated adhesive resistance sweep. Adhesive mechanical compression,
manufacturing tolerances and insulation design are not modeled.

25C initial/ambient. Battery heat2W (80% at x27..39,y84..102mm,20% uniform)
plus seven packages totaling1.75W. Heat on0..600s,off600..1800s. Exterior
effective loss8W/m2K only on display/back/frame. Internal air conductionk.026
plus fixed linearized radiation4W/m2K. No new direct ambient sink on buried parts.

RESISTANCE-ONLY DIAGNOSTIC
Keep25µm geometry, capacities, pad, gaps, sources, sinks and all lateral links.
Change only the two adhesive half-thickness terms in vertical links from25µm
half-thickness to100µm equivalent. Other links unchanged. This mathematical
control is not another physical CAD stack; it is excluded from the 3-case viewer
and physical-stack VTK archive. Its full component histories and numerical checks
are in resistance_diagnostic_history.csv and summary.json. It is independently
mesh/time checked. Difference from the fitted100µm stack includes interactions
between geometry and storage changes; it does not isolate capacity alone.

METHOD AND FILE GUIDE
Conservative symmetric layered finite volumes, constant properties, one unknown
through thickness per planar control volume and seven lumped packages. Backward
Euler2s, working grid2mm; independent1s and1mm refinement for every configuration.
Covered internal gap paths are redirected to graphite exactly once. Sheet and
adhesive have their own capacity. Reference field byte-identical to Stage06 large.
source/sweep.json defines the actual thickness cases. inputs.json retains earlier
stage provenance and the2.2mm pre-stack pad input; the spreader constructor fits
that pad to the thickness listed above. Preserved base/pad/spreader modules are
unchanged. Run run_adhesive_study.py for this stage, not the legacy standalone main.

results/summary.json:600s extrema/weighted means, saved-time maxima, warm area,
geometry/material metrics, diagnostic and mesh/time/effect checks.
results/viewer_data.json:case-specific components, capacities, geometry filenames,
installed pad/adhesive thickness and field shapes. Each binary is little-endian
float32 [61times,node]; times0..1800s every30s. Per-case node/surface/assembly
meshes must match its field, even when node counts agree.
results/*_mesh_nodes.json, *_network_links.csv and *_heat_source_nodes.csv:
node capacity/area/thickness/sink, symmetric conductance links and source powers.
results/component_history.csv, heat_flows.csv, energy_history.csv:all physical
configurations. Heat-flow CSV states positive direction. Component mean is
capacity weighted. Layers have no resolved through-thickness or skin gradient.
results/battery_energy_audit.json:independent network reconstruction, integrated
0..600s heat leaving battery by path, solver-consistent end-step quadrature.
Input1200J=cell stored+net outward path energies. Positive is outward.
VTK:31times/case every60s; CellData Temperature_C, ThermalNode_ID,Component_ID.
Multiple visualization triangles share one thermal node; do not sum power or
capacity per triangle. Layer mid-surfaces only, not a3D volume FE mesh.
review/:absolute maps share25..75C; difference maps use one zero-centered scale
and matching x/y control volumes. Solved fields generate plots; published plot regeneration also uses saved float32 fields.
Threshold areas count whole FV cells, not interpolated boundaries or safety limits.
cad/:67-solid native FreeCAD and STEP assemblies for all3physical stacks.
evidence/:geometry/contact/STEP checks, native reopen and exported-network proof.
manifest.json:SHA256 for public files. Complete archive includes source and outputs.

LIMITS
No measured properties or experimental validation; no CFD airflow, nonlinear
radiation, electrochemical model, junction/skin field or mechanical compression.
Only named solved components and specified conductance links participate. Gray
CAD accessories and optional cooling-path candidates do not automatically add
heat paths. Small temperature shifts are model sensitivities, not hardware margins.
