STAGE 04 - RF BOARD COOLING PAD: CONTROLLED BEFORE / AFTER
Independent Khani Solutions teaching study, all inputs assumed.
No experimental validation, product qualification, or Apple/Wisk performance claim.

REPRODUCE THE THERMAL COMPARISON
  python -m pip install -r source/requirements.txt
  python source/run_pad_study.py
  python source/plot_layout.py
FreeCAD is not needed for this solve. Python 3.11, NumPy, SciPy, Shapely and
Matplotlib were used. The source tree contains the unchanged Stage 03 solver as
base_model.py plus a pad subclass. The frozen Stage 03 field and summary provide
a reference fixture. Do not run base_model.py directly for this comparison.
The script reruns the original source-isolation cases to check superposition;
the published before/after fields use the COMBINED 3.75 W source in both designs.

REBUILD CAD (OPTIONAL)
Open cad/Battery_Product_R3_RFPad.FCStd in FreeCAD to inspect/edit the native model.
The archive includes cad/Battery_Product_R2.FCStd as the original geometry input.
Run source/build_pad_cad.py with FreeCAD Python; set FREECAD_LIB if needed.
STEP exports contain all 65 assembly solids, or RF_Thermal_Pad.step for just the pad.
Original R1/R2 files and all Stage 01/02/03 source/results remain unchanged.

CONTROLLED CONDITIONS
Before = frozen Stage 03 combined baseline. After changes only the RF pad design:
the covered portion of the RF-to-back air/radiation gap is replaced by the pad,
and its mass, lateral conduction and two resistive contacts are added.
All original node capacities, source rates, exterior losses, remaining gaps,
materials and contacts are identical. No extra sink to ambient is added.
Cell source: 2 W (80% in the existing patch, 20% uniform). Packages total 1.75 W.
Initial/ambient 25 C. Heat on 0..600 s; then zero sources to 1800 s. Input 2250 J.
Exterior combined effective loss coefficient stays 8 W/(m2 K).
Internal air k=.026 W/(m K), fixed linearized inter-part radiation 4 W/(m2 K).

PAD ASSUMPTIONS
Footprint x=47..63, y=54..59 mm: 16 x 5 = 80 mm2 on a clear RF-board strip.
Installed z=4.8..7.0 mm, thickness 2.2 mm. No overlap with U06/U07 packages.
k=3 W/(m K), rho=2200 kg/m3, cp=1000 J/(kg K). Mass .3872 g; capacity .3872 J/K.
Each contact R''=.0002 m2 K/W. Bulk resistance 9.1667 K/W; contacts total 5 K/W.
RF-board and back-cover half-layer resistances add 12.5 K/W: total 26.6667 K/W
between their mid-surface nodes in the steady series equivalent.
The same-footprint old air/radiation path is about 802.73 K/W including half-layers.
The pad is an assumed concept, not a selected commercial part or measured material.
Pressure/compression/tolerances, side transfer to the cavity and nonlinear material
behavior are omitted. Each pad control volume has one unknown through thickness;
interfaces include half-thickness resistances, not resolved internal z gradients.

INTERPRETATION
At 600 s the RF-board maximum falls from 64.6981 to 61.2475 C. U07 effective package
temperature falls from 68.5189 to 65.0443 C. The back-cover layer maximum rises from
48.1045 to 52.0957 C. Cell mean changes slightly: 41.0446 to 40.9426 C.
Back-cover temperature averaged over the fixed pad footprint rises 43.0300->51.0990 C.
Do not confuse a moving component maximum with a fixed-location temperature.
The pad redirects heat into the cover, improving RF temperature but increasing the
local enclosure temperature. Package values are not semiconductor junction values,
and cover layer values are not a resolved exterior touch-surface prediction.
At 600 s RF->pad is .09555 W and pad->cover .09033 W; the difference is pad storage.
Total exterior heat loss at 600 s is nearly unchanged (836.0173 vs 835.8704 J).
Both designs receive 2250 J; improved local cooling does not imply greater total
heat rejection or a cooler whole product at this finite time.

MESH / NUMERICAL CHECKS
Before: 9683 thermal nodes (9676 spatial + 7 lumped packages).
After: 9710 nodes (same original nodes + 27 pad control volumes), 2 mm grid, dt=2 s.
Fine after mesh: 37236 total nodes, 1 mm. Time refinement: dt=1 s.
summary.json records all component maxima/refinement differences and changes in the
predicted cooling effect between coarse and fine grids. Observed differences are
not rigorous numerical bounds or experimental uncertainty estimates.
The before saved float32 field must exactly match the frozen Stage 03 reference.
The source checks source/capacity/exterior-sink and unaffected-link equality.
Energy residual <=1.1e-9 J. Source-superposition error <1.6e-13 K before export.
All contacts are conservative; exterior sinks remain on display/back/frame only.

RESULT FILE GUIDE
viewer_data.json: cases, times, component node indices/capacities and binary schema.
before/after_temperature_float32.bin: little-endian float32 [61 times,9710 nodes].
Before pad nodes are NaN because the pad DOES NOT EXIST. All actual nodes are finite.
No temperature is assigned to that absent geometry. All other baseline nodes retain
their exact Stage 03 values. Before and after use a shared 25..75 C Inferno palette.
thermal_surface_mesh.json: spatial surfaces, FV node lookup and grid boundaries.
assembly_mesh.json: full R3 CAD tessellation including RFPad, dimensions in mm.
component_history.csv: min/capacity-weighted mean/max every 30 s in each design.
heat_flows.csv: signed path flows with explicit positive-from/to components.
energy_history.csv: input, stored energy, exterior loss and residual, both cases.
before/after_mesh_nodes.json: correct case-specific capacities and exterior sinks.
before/after_network_links.csv: conductances once per internal link, positive from->to.
before/after_heat_source_nodes.csv: battery/electronics/combined source vectors;
use combined column for this comparison and switch all power to zero at 600 s.
mesh_nodes.json: after-case nodes, identical to after_mesh_nodes.json.
summary.json: full-precision results, tradeoff, contacts and numerical verification.
evidence/geometry_verification.json: native/STEP validity and pad-clearance checks.

PARAVIEW
Extract results/before_after_vtk.zip and open before/transient.pvd and/or
after/transient.pvd. 31 frames per design, every 60 s. Coordinates are METERS.
VTK cells are layer mid-surface TRIANGLES, not 3D volume elements or individual
thermal control volumes. ThermalNode_ID repeats on triangles belonging to one node.
Before contains 9683 unique node IDs, after 9710. Temperature_C is CellData.
Before Component_ID order: Battery, MainPCB, RFPCB, Midplate, Frame, Display,
BackGlass, U01,U02,U03,U04,U05,U06,U07. After appends RFPad as Component_ID=14.

VISUALIZATION
The browser displays stored results; it does not run the solver or change contacts
when geometry is hidden/exploded. Separate maps show before/after at the same time
and range, with each footprint fitted independently (sizes are not to scale).
Gray context parts have no independent thermal solution. The pad is absent before.

NEXT EXPERIMENT
Vary one pad/contact/enclosure-spreading input at a time, retaining identical heat
loads. Assess board/package cooling together with enclosure temperatures, mass,
assembly feasibility and explicit design requirements. Measure contact/material/
boundary data and reserve an independent experiment before physical validation.
