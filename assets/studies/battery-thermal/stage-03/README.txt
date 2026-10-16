STAGE 03 - COUPLED BATTERY / PCB / ENCLOSURE
Independent Khani Solutions learning study. All inputs are teaching assumptions.
No experimental validation and no claim of Apple or Wisk product performance.

REPRODUCE
Install free Python 3.11+ and source/requirements.txt dependencies:
  python -m pip install -r source/requirements.txt
  python source/run_model.py
The script creates results/, review/ and evidence/ relative to its own location.
Normal execution runs all three source cases plus mesh/time refinement checks.
--quick skips refinement; a quick-run summary must not be cited as refined.
The reference run used Python 3.11.14, NumPy 1.26.4, SciPy 1.16.3, Shapely 2.1.2.
No FreeCAD Python module is required to rerun the thermal model.

WHAT IS SOLVED
Seven spatial layers: Battery, MainPCB, RFPCB, Midplate, Frame, Display, BackGlass.
Seven lumped package temperatures: U01 to U07. Package values are not junction T.
9,676 planar FV control volumes + 7 lumped nodes, 2 mm nominal grid, 2 s time step.
Spatial layer values are mid-surface temperatures with one unknown through thickness.
Through-thickness paths enter as resistances, not resolved internal temperature fields.
Each link contributes identical opposite heat flow. Backward Euler conserves energy
when exterior loss is integrated with the same endpoint temperature as the update.
No velocity/pressure equations, electrochemistry or mechanical coupling are solved.

SOURCE CASES - 0 TO 600 S, THEN ALL SOURCES OFF TO 1800 S
Battery: 2 W total, 80% in global x=27..39, y=84..102 mm; 20% uniform by area.
Electronics: 1.75 W total, U01=1; U02=.175; U03=.075; U04=.075; U05=.05;
U06=.25; U07=.125 W. These are 25% of original illustrative CAD package loads.
Cases are battery-only, electronics-only and both. All parts start at 25 C.
These are heat-generation rates, not electrical input or measured charging power.

BOUNDARIES / CONTACTS
Only external display/back faces and exposed frame exchange with 25 C ambient,
using a fixed combined effective coefficient of 8 W/(m2 K).
No direct ambient sink is attached to buried battery/PCB/package nodes.
Internal gaps: air conductivity .026 W/(m K) plus fixed radiative conductance
4 W/(m2 K). No airflow or nonlinear radiation is solved.
Cell adhesive .15 mm/.5 W/(m K); PCB pedestal .95 mm/160 and TIM .25 mm/3;
four support annuli; four RF posts; panel perimeter contacts; distributed package
and display contacts. Solid area-specific contact resistance .0002 m2 K/W.
Participating half-layer resistances are included. See source/inputs.json and code.
The topmost modeled surface owns each projected back-gap area; no double count.
Massless links represent adhesive, supports, TIM, pedestal and RF interposers.
Their CAD solids have no independently calculated temperature.
BMS, passives, connectors, camera, haptic, speaker and optional upper SoC bridge
are omitted from the thermal network. Accessory volumes do not displace cavity
transfer paths. The frame thermal mesh omits its small USB cutout; full CAD keeps it.
Gray means no independent solution, not ambient temperature.

FILES
inputs.json: material/contact/source assumptions and scope.
cad_parameters.json: footprint definitions and original illustrative CAD package powers.
run_model.py: complete portable thermal solve, exports, figures and numerical checks.
summary.json: full-precision reference temperatures and numerical verification.
component_history.csv: min/capacity-weighted mean/max every 30 s, for 14 components.
heat_flows.csv: signed contact heat flows with explicit positive-from/to components.
energy_history.csv: supplied heat, stored energy, ambient loss and residual.
mesh_nodes.json: node centroids, planar areas, thicknesses, heat capacity, ambient G.
network_links.csv: each internal conductance once; G*(T_from-T_to) positive from->to.
heat_source_nodes.csv: source power per node during heating; exactly zero after 600 s.
viewer_data.json: time axis, node indices, capacities and float32 field definitions.
*_temperature_float32.bin: little-endian float32, row-major [time,node] temperatures C.
thermal_surface_mesh.json: triangulated spatial layers, node lookup and FV boundaries.
assembly_mesh.json: review tessellation of existing full CAD, in mm; context included.
palette.json: 256 Inferno RGB triples, each channel 0..1. Shared map range 25..75 C.
CAD review surface colors are the saved layer/package values, not a separate solve.
Browser fields use float32, so tiny export roundoff differs from full-precision CSV.

PARAVIEW
Extract results/coupled_vtk.zip, then open cell/transient.pvd,
electronics/transient.pvd or combined/transient.pvd. 31 frames per case, every 60 s.
These are layer MID-SURFACE triangles in assembly coordinates in meters, not 3D
volume elements. CellData has Temperature_C, Component_ID and ThermalNode_ID.
Multiple triangles can share one thermal node. Do not count triangles as FV nodes.
Component_ID order is documented in the VTK archive README.

RESULTS / NUMERICAL LIMITS
At 600 s the cell mean is 35.3789 C (battery only), 30.6657 C (electronics only),
41.0446 C (both). In the combined case cell maximum 47.2529 C; main PCB maximum
51.4134 C; RF PCB maximum 64.6981 C; U07 package 68.5189 C.
Mesh refinement 9,683->37,156 total nodes changes component maxima at 600 s by at
most .308 K. Time refinement 2->1 s changes them by at most .0081 K. These numbers
are observed differences, not rigorous uncertainty bounds or experimental accuracy.
Energy residual <=1.1e-9 J; source superposition <=1.3e-13 K before float32 export.
Independent two-node matrix-exponential benchmark error <.000034 K at dt=.001 s.
The check does not establish physical validity of the assumed interfaces or gaps.

STAGE COMPARISON
Stages 01 and 02 stay unchanged. Stage 03 changes storage, thermal paths and
boundary conditions; its absolute temperatures are not a one-variable comparison
with the previously exposed cell. Within Stage 03, the three source cases share
the exact same geometry/materials/boundaries, so their temperature rises add.

NEXT LEARNING STEP
Change one RF-to-enclosure thermal path while keeping all sources and boundaries
fixed, then compare temperatures, heat split and transient response. Eventually
resolve through-thickness gradients, calibrate against measurements and reserve
an independent experiment for validation.
