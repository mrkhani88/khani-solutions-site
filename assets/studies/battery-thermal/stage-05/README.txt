STAGE 05 - BONDED GRAPHITE SPREADER / PAD-ONLY REFERENCE / CONDUCTIVITY CONTROL
Independent Khani Solutions teaching study. All values are assumptions.
No experimental validation, vendor-grade selection or Apple/Wisk product claim.

REPRODUCE
  python -m pip install -r source/requirements.txt
  python source/run_spreader_study.py
  python source/plot_layout.py
Dependencies are free/open-source Python, NumPy, SciPy, Shapely and Matplotlib.
FreeCAD is optional for CAD rebuilding; it is not needed for the thermal solve.
base_model.py is the unchanged Stage 03 solver and pad_model.py the unchanged
Stage 04 comparison script. Only import them through run_spreader_study.py here.
The frozen Stage 04 pad reference binary must match the reproduced field exactly.

CONFIGURATIONS
before: original Stage 04 pad-only design, 2.2 mm pad to inner back glass.
after: 30 x 50 x .10 mm graphite plus .025 mm adhesive under the same back glass.
control: SAME new geometry, capacities, vertical properties, contacts and sources;
only graphite kxy changes 800 -> 5 W/(m K). It is a numerical diagnostic material.
All retain 2 W cell + 1.75 W package heat, 25 C initial/ambient, heat-on 0..600 s,
then all sources zero until 1800 s. Input at heat-off is 2250 J. Exterior losses
remain on display/back/frame with effective h=8 W/(m2 K). No new ambient sink.
Original capacities are fixed except the shortened pad. Original cell/package/
board/enclosure material properties remain fixed. Case isolation also runs
internally to verify linear source superposition.

STACK / PHYSICAL GEOMETRY
Sheet footprint x=38..68, y=30..80 mm: 1500 mm2, inside the original enclosure.
RF board top z=4.8. Pad top/new graphite bottom z=6.875: pad height 2.075 mm.
Graphite z=6.875..6.975. Adhesive z=6.975..7.0. Original glass bottom stays z=7.
The old 2.2 mm pad therefore shortens by .125 mm to fit the bonded sheet.
Before and new cases use different pad geometry in CAD/VTK/browser, not overlapping
solids. Native R4 CAD has 67 valid non-overlapping solids. Interface areas measured
from native faces: pad->graphite 80 mm2, graphite->adhesive->glass 1500 mm2.
R3 CAD remains unchanged as the geometry input, included in the archive.
Open cad/Battery_Product_R4_Graphite.FCStd or neutral STEP. To rebuild run
source/build_spreader_cad.py with FreeCAD Python; FREECAD_LIB can locate its modules.
The layout figure's section is schematic and explicitly not to scale.

ASSUMED MATERIALS / CONTACTS
Graphite kxy=800, kz=5 W/(m K); rho=1800 kg/m3; cp=700 J/(kg K); mass .270 g.
Adhesive k=.2 W/(m K); rho=1200; cp=1500; mass .045 g. Each bonded interface
R''=.0001 m2 K/W. Pad upper-contact R''=.0002 m2 K/W remains unchanged.
Pad mass changes .3872 -> .3652 g. Net new mass .293 g; capacity increases .2345 J/K.
The graphite and adhesive each have finite capacity and lateral conduction.
Contact paths include half-layer resistances. Internal gaps under the sheet end
at its lower surface, with original air k=.026 plus linearized radiation 4 W/(m2 K).
Covered old direct-to-glass paths are removed. Exclusions for chips, RF board,
pad and board holes are retained; covered regions must partition the sheet area.
No side-face cavity transfer, airflow, nonlinear radiation, bending/compression,
electrical isolation design or resolved through-thickness gradients are modeled.
Each planar control volume has one through-thickness temperature; z gradients
enter as resistances. Package values are not semiconductor junction temperatures.
Glass layer values are not separately resolved exterior skin/touch temperatures.

RESULTS AT 600 S
Back-cover maximum: pad-only 52.0957 C, graphite 41.0380 C, control 50.0299 C.
RF-board maximum: pad-only 61.2475 C, graphite 55.0210 C, control 59.8801 C.
U07 effective package: pad-only 65.0443 C, graphite 58.6821 C.
Cell mean: pad-only 40.9426 C, graphite 41.0162 C; do not infer all parts cool.
Cover mean barely changes 36.6445 -> 36.6844 C. Area above 40 C grows
1012 -> 1628 mm2 while area above 45 C drops 300 -> 0 mm2. Those thresholds
are map diagnostics, not safety/touch limits. Areas count whole control volumes
whose center values exceed a threshold, not an interpolated contour boundary.
Spread heat over a larger area; assess the peak and the warm area together.
At 600 s RF-pad->graphite is .17597 W. Adhesive->cover is .29142 W across the
whole 1500 mm2 sheet, including heat from neighboring components, not pad alone.
Total exterior loss changes 835.8704 -> 839.9637 J out of 2250 J input.
Local peak reduction is much larger than the change in whole-product heat rejection.

NUMERICAL CHECKS
9710 nodes before; 10460 after/control, including 375 graphite +375 adhesive cells.
40236-node fine new stack; dt=2 s base and 1 s time checks. Both after and control
are grid/time checked. A fine pad reference is independently rerun for effect checks.
Cover reduction is 11.0577 K on the working grid, 11.4948 K on the finer grid.
Observed refinement differences are not rigorous bounds or experimental uncertainty.
Energy conservation, symmetric pairwise conductances, source superposition, equal
control-case masses/sources/vertical links and baseline byte preservation are checked.
Independent exported-network reconstruction, VTK mapping and source-archive rerun
are additionally recorded in project evidence. Physical validation is not performed.

FILE GUIDE
viewer_data.json: time axis, three cases, components, capacities, binary schema.
*_temperature_float32.bin: little-endian float32 [61 times,10460 nodes]. In the
before case ONLY the 750 nonexistent graphite/adhesive nodes are NaN; no assigned T.
thermal_surface_mesh.json: new-stack FV surfaces and node mapping, coordinates mm.
before_pad_mesh.json: actual 2.2 mm pad geometry used in the reference browser view.
assembly_mesh.json: full R4 CAD tessellation. The browser substitutes the proper
case-specific pad thermal surface. Opening/exploding layers changes no thermal path.
Paired maps show pad-only and graphite at matching time/range; each footprint is
fitted independently, so displayed sizes are not to scale. Shared range 25..75 C.
component_history.csv: min/capacity-weighted mean/max for each active component.
heat_flows.csv: signed contact flows, positive-from/to components explicitly named.
energy_history.csv: supplied heat, stored energy, exterior losses and residual.
before/after/control_mesh_nodes.json: case-specific capacities and ambient sinks.
before/after/control_network_links.csv: internal conductances once per link.
before/after/control_heat_source_nodes.csv: three source-isolation vectors. Use
combined_W_during_heating for public comparison; all applied sources zero after 600.
summary.json: full precision results, area diagnostics, flow/energy and verification.

PARAVIEW
Extract results/spreader_comparison_vtk.zip and open each transient.pvd under
before/, after/ or control/. 31 times per configuration, every 60 s. Units METERS.
VTK triangles represent layer mid-surfaces, not 3D volume elements. Temperature_C
is CellData. ThermalNode_ID repeats on triangles of one FV node; do not count
triangles as thermal nodes. Order is in the VTK README. Before has 15 components,
after/control 17 with GraphiteSpreader and SpreaderAdhesive appended.

MATERIAL BACKGROUND
Panasonic FAQ describes high X-Y conductivity in PGS sheets:
https://industrial.panasonic.com/ww/faq/faq0099
This supports the general spreading concept only. This model's combined property
set is independent and assumed; it is not a selected Panasonic product specification.
