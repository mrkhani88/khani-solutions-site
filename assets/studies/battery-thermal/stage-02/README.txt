BATTERY THERMAL MODELING | STAGE 02
Independent Khani Solutions study. Free and open-source software only.

MAIN COMPARISON
The original 0D cell, initial/ambient temperatures, density, heat capacity,
effective surface loss coefficient and timing are unchanged. Only the heat input
changes from 1 W to 2 W. Source is on for 600 s, then off until 1800 s.
Stage 01 peaks at 37.3289 C; Stage 02 peaks at 49.6578 C.
At 1800 s the averages are 26.4761 C and 27.9522 C respectively.

Let theta=T-T_ambient. C*d(theta)/dt=Q-G*theta. With constant C and G and
zero initial temperature rise, doubling Q doubles theta throughout heating and
cooling. It doubles neither the Celsius temperature nor the time constant.
Both cases have tau=C/G=565.36 s. Actual battery properties, nonlinear radiation,
electrical heat generation and thermal contacts can break this exact scaling.

SEPARATE SPATIAL EXTENSION
This extension adds a 2D cell-centered finite-volume conduction model for the
same effective cell. Temperature is uniform through its 4.45 mm thickness.
The planar dimensions are 36 x 78 mm. k_x=k_y=20 W/(m K) are new assumptions.
No k_z-dependent gradient is resolved. There is no simulated enclosure, BMS,
PCB or contact path in this extension. Gray CAD parts are NOT thermally solved.

Two spatial cases use 2 W total: uniform generation and localized generation.
In the localized case 80% of that 2 W is placed in a 12 x 18 mm patch at local
x=21..33 mm, y=57..75 mm. The remaining 20% is spread over the full cell.
This is an illustrative source profile, not a measured cell/fault heat map.

Equation per finite-volume cell:
C_i*d(theta_i)/dt=Q_i-sum_j[G_ij*(theta_i-theta_j)]-G_loss_i*theta_i.
C_i=rho*cp*thickness*dx*dy.
G_x=k_x*thickness*dy/dx; G_y=k_y*thickness*dx/dy.
Both broad faces lose heat with h_eff=8 W/(m2 K). The four edges use that same
effective coefficient, with half-cell conduction resistance in series.
The combined coefficient is not a measured convection boundary; radiation is
not separately added to it. The phone assembly is geometry context only.

NUMERICAL METHOD AND CHECKS
Crank-Nicolson in time with sparse LU factorization; source switch handled at
exactly 600 s. Baseline grid: 24 x 52 = 1248 quadrilateral thermal cells,
1325 corner points; dt=0.5 s. Uniform-source/no-edge-loss limiting case checked
against an analytical slab response. Energy conservation is integrated using
the same trapezoidal fluxes as the update. Refined grid: 48 x 104 = 4992 cells.
Time sensitivity compares 0.5 s with 1.0 s. Actual errors are in summary.json.
These checks verify the numerical model; no physical validation was performed.

FILES AND REPRODUCTION
Run: python3 -m pip install -r source/requirements.txt
Then: python3 source/run_comparison.py
The script creates results/, review/, and evidence/ as needed.
Results include the 0D comparison CSV; spatial min/mean/max CSV; browser fields;
plots; and VTK time collections for both spatial cases, sampled every 60 s.
The website displays stored results sampled every 10 s, not a browser PDE solve.
Open results/vtk/localized/transient.pvd in ParaView for the localized history.
Coordinates in VTK files are metres; Temperature_C is cell data in degrees C.
The VTK HeatSource_W_per_cell_during_heating array describes the on-phase source;
the applied source is zero after 600 s. The thermal mesh is 2D, not a 3D solid mesh.
The web surface map interpolates cell-center values onto the CAD cell surface
and repeats the planar field through thickness, matching this model assumption.
Shared color scale is 25..65 C; focused scale is labeled per-frame for inspecting
local gradients and should not be used to compare absolute heat between cases.

Public method references
https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.factorized.html
https://docs.pybamm.org/en/v25.10.2/source/examples/notebooks/models/thermal-models.html
The model is custom NumPy/SciPy code; PyBaMM is background on model hierarchy,
not the solver used for this stage.
