STAGE 06 — GRAPHITE SIZE AND COVERAGE
Independent Khani Solutions teaching model. All geometry, materials, contacts and heat loads are assumptions. No experimental validation or product/safety qualification.

REPRODUCE (all solver dependencies free and open source)
1. Install Python 3, then: python -m pip install -r source/requirements.txt
2. From the extracted archive root: python source/run_size_study.py
   This reruns three coarse meshes, three fine meshes and three half-time-step cases; creates plots, binaries, CSVs, networks and VTK. Typical runtime is a few minutes, depending on hardware.
3. Run python source/verify_exports.py to independently rebuild the exported networks, check all saved fields and selected VTK frames, and regenerate the integrated battery energy audit.
4. Optional CAD regeneration: python source/build_size_cad.py using a FreeCAD-enabled Python environment; FREECAD_LIB may point to its library directory. Native FCStd input included in cad/. FreeCAD opens all three variants; STEP supports neutral exchange.
5. Open results/size_comparison_vtk.zip in ParaView after extraction, then small/transient.pvd, reference/transient.pvd or large/transient.pvd. Coordinates meters, layer mid-surfaces, Temperature_C CellData. Multiple visualization triangles share one ThermalNode_ID. No resolved through-thickness field.

inputs.json retains the prior stage text and 2.2mm pre-stack pad input for provenance. The spreader constructor fits that pad to2.075mm in every sweep case; sweep.json defines the actual Stage06 footprints.

The preserved base_model.py, pad_model.py and run_spreader_study.py implement the previous stages unchanged. The Stage06 entry point is run_size_study.py. Do not run the old module's standalone main, which expects its original stage-specific reference files.

CONTROLLED COMPARISON
small: [44,30,68,60] mm, 24x30, 720 mm²
reference: [38,30,68,80] mm, 30x50, 1500 mm² (byte-identical Stage05 graphite case)
large: [18,30,68,100] mm, 50x70, 3500 mm²
Fixed lower-right corner (68,30). Growing left/up changes both area and battery coverage. This is not a placement-independent size law. Cell overlap 0/200/1680 mm² is projected gap coupling, not cell-to-sheet physical contact.
Every size: graphite .10 mm (kxy800/kz5 W/mK, rho1800 kg/m³, cp700 J/kgK); adhesive .025 mm (k.2, rho1200, cp1500); bonded-interface R'' .0001 m²K/W each; RF pad 2.075 mm. Pad contact R'' .0002. Pad footprint 16x5 mm, k3. Outer enclosure fixed. Pad and all original capacities identical across sizes; sheet/adhesive capacity grows with area. No extra ambient sink.
25°C initial/ambient; 2W cell plus1.75W electronics; on0..600s, off600..1800s. Cell80% in assumed patch x27..39,y84..102mm,20% uniform. Same exterior8W/m²K effective combined loss on display/back/frame. Internal gaps: airk.026 plus fixed linearized radiation4W/m²K. No CFD airflow or electrochemical solve.

METHOD
Conservative symmetric layered finite-volume conductance graph, constant properties, one temperature through thickness per layer cell; seven lumped packages. Implicit backward Euler, 2mm working grid/1mm refinement,2s timestep/1s refinement. All three isolated/combined source vectors are advanced to verify superposition. Top-surface ownership partitions each covered gap exactly once. New layers have finite heat capacity. Fixed-property linear model.

FILES
source/sweep.json: size locations and growth rule; inputs.json: materials, sources, contacts.
results/summary.json: 600s component extrema/weighted means, all saved-time maxima, cover threshold areas, mass, energy, mesh/time/effect sensitivity.
results/battery_energy_audit.json: independent exported-network reconstruction; integrated heat leaving battery by path using solver-consistent end-step flows,0..600s. Positive is outward. No-path small sheet=zero projected overlap.
results/*_temperature_float32.bin:61 times (0..1800s,30s), little-endian float32 row-major [time,node]. Every size has its own node count; use shape and components in viewer_data.json cases, never reuse another size's indices.
results/*_thermal_surface_mesh.json: display geometry and node mapping, per case; same finite-volume values on top/bottom. Package temperature is uniform. The surfaces do not add separate unknowns.
results/*_assembly_mesh.json: native CAD context meshes, per case. Gray context has no independent thermal result.
results/*_mesh_nodes.json: node centroid, planar area,thickness,capacity,ambient conductance.
results/*_network_links.csv: node pairs, positive symmetric G and path labels.
results/*_heat_source_nodes.csv: three source columns per node.
results/component_history.csv: min,capacity-weighted mean,max per time/component/configuration.
results/heat_flows.csv: instantaneous signed path totals, labels give positive direction.
results/energy_history.csv: input,stored,exterior loss,residual.
review/size_maps.png: shared25–75°C scale and common coordinates, cyan footprints; threshold areas count whole control volumes at centerT, not interpolated contour boundaries or safety limits.
review/battery_difference.png: pointwise Battery-only differences from saved float32 fields at600s, comparing identical thermal nodes; shared -0.5..+0.5K diverging scale, no interpolation. Optional regenerate: python source/plot_battery_difference.py after the solver.
review/size_histories.png and size_layout.png: transients and controlled footprint layout.
cad/: native67-solid assemblies and corresponding STEP for each size.
evidence/geometry_verification.json: validity,no overlaps,STEP volume/count,measured native face contact areas.
manifest.json: SHA256 for public files; complete archive includes all sources and outputs.

NUMERICAL CONSISTENCY IS NOT PHYSICAL VALIDATION
No measured properties, real product CAD, airflow, nonlinear radiation, junction/skin gradient, compression mechanics, graphite bending, tolerance/electrical isolation design or experimental comparison. Small cell shifts are model sensitivities, not demonstrated hardware margins. Sheet size changes mass, bond/gap area and coverage as well as lateral extent. Net heat flow can hide opposite local transfers. A hotter average and a lower maximum can coexist.
