DATA-CENTER HYDRAULICS - FIRST STEADY NETWORK - 23 OCTOBER 2026

Software: OpenModelica 1.27.1, Modelica Standard Library 4.1.0.
Open Report.html for the step-by-step result explanation and numerical checks.

RUN THE NATIVE MODEL
Open model/DataCenterHydraulics.mo in OMEdit; load Modelica 4.1.0.
Select DataCenterHydraulics.Baseline, simulate 0 to 1 s with tolerance 1e-8.
This repeats a steady algebraic operating point. It is NOT a startup transient.

Command-line reproduction from this extracted folder:
  mkdir -p runs/reproduction
  cd runs/reproduction
  omc ../../source/run.mos
The script compiles and runs Baseline, FlatGeometryCheck and RaisedHeaderCheck.

RESULTS
Total flow: 25.574113 L/s
Head: 26.349649 m
Differential pressure: 256.386255 kPa
Estimated electric input: 9.713853 kW
Rack flows: 152.799149 to 154.995763 L/min
Nominal rack target: 144.703707 L/min
Independent Colebrook maximum rack-flow difference: 0.00015227%

MODEL SCOPE
MSL Modelica.Fluid.Pipes.StaticPipe, fluid stream connectors and generic loss elements.
Custom explicitly dimensioned equivalent pump bank and lossless rack elevation link.
Two identical duty pumps; standby isolated. No valve/check-valve switching dynamics.
Pump head per duty: H=37 - 0.5*x - 9*x^2 m at speedRatio=1;
x is each duty pump flow divided by 0.01205864223836569 m3/s.
This assumed curve is not a vendor curve or a selected pump.
The Stage 01 15% pressure margin is a selection allowance, not a physical loss.
Assumed hydraulic efficiency 0.75 and motor efficiency 0.90.
Fixed water properties near 40 C: rho 992.2 kg/m3, cp 4179 J/kgK,
mu 0.000653 Pa s. Rack heat load is used only to define the flow target.
Actual rack heating, coolant temperature dynamics and physical HX heat rejection
are not solved. A 0.1 m3 numerical mixed volume at fixed 40 C closes pump-work
energy equations; it does not size the expansion vessel.
Assumed pressure reference: 300 kPa absolute. Device pressure ratings/NPSHR pending.
CDU manifolds are full-flow equivalents; identical pump legs use nParallel=2.
CAD route snapshot in inputs matches the original exported-file SHA in assumptions.json.
Blind header tails are excluded from circulating flow.
Fitting K, rack/valve/filter/HX loss maps are provisional; see assumptions.json.
No vendor qualification, physical validation, controls, faults, water hammer,
structural design or construction readiness follows from these results.

CHECKS
Accepted run: runs/r5. Native compiler equation check and three successful solves.
Mass/pressure closure, finite outputs and final clock checked.
Independent exact-Colebrook network calculation under the same assumptions.
FlatGeometryCheck removes all hydrostatics at unchanged friction lengths.
RaisedHeaderCheck uses 3.0 m (baseline 2.7 m) at unchanged valid pipe lengths.
Both preserve circulation and shift local header pressures as expected.
A 5 m header cannot use these unchanged short vertical routes: a taller design
must lengthen pipes and recalculate friction. Earlier rejected test attempts remain
on Intel; the package contains only the accepted run and its full native log.
Retained compiler note: redundant start/nominal aliases. Accepted outputs are
finite and conserved; no unit inconsistency, height bound or runtime assertion
failure remains in this accepted run.

REGENERATE / AUDIT
python3 source/build_model.py regenerates the Modelica package from inputs.
python3 source/audit_results.py r5 audits accepted CSVs and rebuilds plots.
Requires NumPy, SciPy and Matplotlib for the independent calculation/plots.
python3 source/build_report.py rebuilds the portable HTML report.
Model simulation itself only needs OpenModelica and MSL 4.1.0.

NEXT
Review the initial operating point; then vary speed, balance rack flows and replace
assumed component maps with supplier/test data before adding thermal/control dynamics.
