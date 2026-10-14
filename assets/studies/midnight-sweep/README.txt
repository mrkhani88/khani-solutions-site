0–20 degrees in 2-degree steps; 100 mph, sea-level, unpowered public-reference exterior.
OpenFOAM v2512 SST RANS on Intel. 2,226,297-cell symmetry half-domain; full lift/drag forces doubled, lateral force cancels when mirrored.
Prescribed body-coordinate inflow U=(V cos alpha,0,V sin alpha). Drag parallel to U; lift perpendicular in XZ plane.
Bounded steady solves: 200 upwind conditioning iterations, then limitedLinearV convection, up to 1000 iterations. Means/ranges over last 200 second-order iterations.
Unsettled cases may receive short backward-time PIMPLE SST URANS checks initialized from steady fields, averaging from 0.03 s, ending at or before 0.4 s. Total unsteady wall-time budget 30 minutes per case. Incomplete averaging windows retain the steady screening field and qualification.
The transient trials were ended cleanly after their measured timestep cost showed that reaching the averaging window would require hours. None reached 0.03 s; all delivered fields are steady screening iterates. Short_Transient_Checks.json records the actual stop times. Case criteria and field basis are in Sweep_Summary.json.
Refined near-body and high-angle wake regions; finer wing/tail/nacelle surfaces. Fifteen tiny fluid cells closed, total removed volume <0.00015 m3; new walls assigned to nearest aircraft patch. Configured quality checks pass; expanded concave-cell diagnostic remains.
No prism layers. Wall-function RANS on surface-refined cells; boundary-layer profiles and skin-friction accuracy unresolved. Not grid/timestep independent.
Generic airfoils and approximate public exterior dimensions. Unknown OEM camber, incidence, twist, trim and CG. No propeller blades/thrust/propwash, asymmetric stall modes, ground effect or structural analysis.
Colors: aerodynamic force density = rho*p_kin*n_fluid - rho*wallShearStress, projected onto lift or drag axes. Units N/m2 = Pa, not CL/CD or structural stress. URANS uses native mean pressure/shear when available. Exact cell values retained; vertex interpolation for display.
Common display limits: lift +/-1800 Pa; drag +/-1000 Pa. Values outside the ranges are clipped only for display.
Surface pressure/viscous traction integrals checked independently against native forces. Plot ranges are iteration/physical-time variation, not confidence intervals.
Stationary geometry/camera; independent cases, not a transient pitching maneuver. Native U or UMean streamlines; cyan around wings/body/tail; purple selected reversing-flow paths where present. Arrowhead speed is presentation only.
1920x1080, 24 fps. Three-second cut and 11-second inspection cut. All cases plotted; displayed case highlighted.
Green lift/amber drag vectors share one scale, with an illustrative anchor, not CG/center of pressure.
Blender source: common editable mesh, 22 lift/drag attributes, CaseIndex 0–10 and ColorMode 0 lift/1 drag. Eleven-second source timeline.
Maximum sampled lift identifies a point on this model's curve. It does not establish Midnight's stall angle or safe envelope.
Original case fields, logs, rejected meshes and repair evidence remain on Intel under the study root.
