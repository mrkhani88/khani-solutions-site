KHANI SOLUTIONS | STAGE 02 | INTEGRATED HAPS DIURNAL MISSION
Independent public-reference work, 23 October 2026.

VIEW THE RESULTS
  python3 -m http.server 8894
  http://127.0.0.1:8894/Review.html
Online: https://khanisolutions.com/AISolutions/sceye-haps-thermal.html#mission
The browser plays saved native results; it does not rerun OpenModelica.

NATIVE MODEL
Open source/HAPSDiurnal.mo in OMEdit, then IntegratedMission. It contains the
entire connected thermal-energy model and separate subsystem/primitive classes.
Inspect native Diagram/Modelica views and the supplied source-derived SVG maps.
Modelica Standard Library 4.1.0 is required (OpenModelica package manager).
OpenModelica 1.27.1 was executed on Intel.24 lumped thermal nodes; no spatial field.

REPRODUCE ON LINUX / INTEL
From this project root:
  mkdir -p verification/native
  cd verification/native
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 omc ../../source/compile.mos > compile.log 2>&1
  OMP_NUM_THREADS=1 omc ../../source/inspect.mos > inspect.log 2>&1
  cd ../..
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python3 source/run_cases.py
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python3 source/audit_and_export.py
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python3 source/render_assets.py
  python3 source/build_stage_page.py
Requires Python, NumPy >=2, SciPy, Matplotlib and Modelica 4.1.0. Only two compiler jobs
are requested. Default native run is 8 days with 60 s output/max step and tolerance
1e-7. The reference refinement is 30 s and 1e-8. Each case changes one stated factor.
run_cases.py can accept case IDs to rerun only those cases. Simulation runtime
stepSize/tolerance are explicit flags; parameter overrides are separate.

SOURCE AND DATA
source/: native package, compile/introspection/scenario/audit/plot/page code.
inputs/: scenario overrides, component capacities/CAD links, source hierarchy,
         geometric/gas presizing and public primary-reference register.
results/: source-linked summaries, selected final-day CSVs and viewer JSON.
verification/: conservation, topology, repeat-cycle/refinement and run records.
review/: native-connection SVGs and standalone scientific PNG figures.
docs/: full assumptions/equations/limitations and a step-by-step walkthrough.

Full original native eight-day CSVs, logs and case records are separate per-case ZIPs,
linked on the public website under Model&Data downloads. They are deliberately
not duplicated inside this source/report ZIP. Their SHA-256 hashes are recorded
in verification/native-archives.json and the public asset manifest. The archive
CSV bytes are unchanged. Final-day CSVs and viewer JSON are derived excerpts;
viewer temperatures are Celsius, power isW, heaterEnergy isWh, electrical
cumulative energy is kWh and SOC isfraction. The input/output schema notes and
web labels retain these units. Native CSV temperature isK and energy isJ.
Native event records have duplicate timestamps; website interpolation uses
post-event values on a 60 s grid. The summary extrema use original final-day rows.

MODEL BOUNDARIES
All equipment capacities, losses, limits and mission loads are study assumptions.
This is not Sceye production thermal architecture or a flight telemetry replay.
The manufacturer mission context supplies station keeping and solar/battery
operation; no private recruiter,NDA,employer data or meeting information is used.
No selected-cell/part operational/survival limits, physical validation, spatial
hot spots, aerodynamic station-keeping control, pressure/ballonet dynamics,
buoyancy or vehicle mass closure are available. Heaters can saturate and high
sensitivity-case temperatures can invalidate constant-load hardware assumptions.
Numerical completion is not qualification or proof of functioning hardware.

Native original logs/compiled products/rejected development attempts remain on
Intel. Published diagnostic paths are normalized to ${PROJECT_ROOT}; source and
numerical artifacts retain hashes. The prior Stage 01 FreeCAD package remains
available separately on the same website.
