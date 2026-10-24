STAGE 06 - RACK LEAK ISOLATION (23 October 2026)
Independent Khani Solutions study. No private employer/client information.

ACCEPTED RESULT
21 native OpenModelica 1.27.1 / MSL 4.1.0 isothermal algebraic steady cases.
Native run: runs/accepted-reduced-r3. Zero-to-one-second output is not a physical
leak/actuator transient. source/audit.py checks every case against a separate
SciPy pressure-flow network, mass and pressure equations and inherited baseline.
The accepted model excludes enthalpy, temperature, compressibility and surge.
Start guesses are 2% offset flow / 1% pressure from independent values; not fixed.
Compiled binaries and bulk build products remain on Intel, not in this bundle.

MODEL BASIS
Ten parallel rack branches, 144.7 L/min target each, inherited Stage 04 manual
settings and two synthetic duty pumps. R05 has a reversible internal leak path
between supply/return isolation. Each open isolation element replaces K=0.5
of the inherited fittings; open-path resistance and reference duty are preserved.
Equivalent round holes 1/3/6 mm, Cd=0.62, atmospheric receiver, reference pressure
held at 300 kPa absolute. An unlimited ideal source supplies makeup equal to
leak loss. This is not finite coolant-inventory depletion or real autofill design.
Positive supply enters R05; positive return leaves it; negative return is backfeed.
R05 supply flow during leakage does not prove useful cooling.
Ideal zero conductance means a tight valve. 1% Kv is an assumed passing fault,
not a catalog leakage class, stroke setting or 1% leak-flow limit.

RESULTS
For 3 mm: leak 7.137 L/min open, 5.734 supply-only, 7.344 return-only,
zero sustained header feed for ideal dual closure, 6.216 with 1% residual Kv.
Stored coolant may still drain after ideal closure. At unchanged speed, nine
healthy racks receive about 153.1-153.5 L/min. Speed reset to 89.332% gives
144.7-145.1 L/min and estimated pump-bank electrical input 6.836 kW, versus
8.088 kW at the unchanged speed. The ten-rack reference was 8.190 kW.
R05 must be offline; nine rack design duties remain, not equal-service 1 MW savings.

EXPOSURE / METER SCREENS
18 saved assumed delay/closure combinations plus interactive browser arithmetic.
Use max steady 100%-speed shutoff pressure at leak height, hold its leak rate
until both valves seal, add assumed drainable inventory. This is not a pressure
transient, measured valve law, pan qualification or surge bound. Fails to bound
indefinite feed from stuck/passing valves. Branch pipes contain 5.965 L; actual
rack/manifold volume unknown; 10 L total drainable inventory is assumed.
Flow-meter differential error is the sum of two +/- reading-error bounds, not
RSS or a statistical confidence interval. No sensor model or timing selected.

REPRODUCE ON INTEL (fresh attempt folder)
Python needs numpy/scipy/matplotlib. omc and MSL 4.1.0 required.
  python3 source/design.py
  python3 source/build_pressure_model.py
  mkdir -p runs/my-fresh-attempt
  cd runs/my-fresh-attempt
  cp ../../model/DataCenterIsolation.mo input_model.mo
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAKEFLAGS=-j2 omc ../../source/run-reduced.mos > run.log 2>&1
  cd ../..
  python3 source/audit.py my-fresh-attempt
  python3 source/build_report.py
  python3 source/package.py
Serve this directory over HTTP to use Report.html; browser fetch generally cannot
load JSON when opened directly with file://. review.css and review.mjs are local.

HISTORICAL DIAGNOSTICS
source/build_model.py, source/build_full_fluid_model.py and source/run_cases.py
are the rejected full-fluid implementation; do not use them to reproduce the
accepted reduced result. They are retained as diagnostic provenance. Original
full native builds and failed attempts are on Intel. Portable logs/models in
verification/solver-attempts have explicit rejected/accepted status. Reduced r2
was rejected despite completion because a one-sided orifice admitted unphysical
isolated-node pressure. Signed smoothing fixes that in accepted reduced r3.

NEXT QUALIFICATION
Select valve/sensor hardware, map all isolation zones, coordinate electrical
shutdown and thermal ride-through, measure inventory and leakage/closure law,
check loss-of-power fail state, then analyze elastic/compressible pressure waves
and test the fault response. No automatic protection has been installed here.
Existing Stage 02 CAD remains the design reference; no new valve hardware CAD.

PUBLIC REFERENCES
See verification/references.json and the linked original publishers in Report.html.
Third-party PDFs are linked, not redistributed. Original private logs retain Intel
absolute paths; the public deliverable replaces those paths with ${PROJECT_ROOT}.
