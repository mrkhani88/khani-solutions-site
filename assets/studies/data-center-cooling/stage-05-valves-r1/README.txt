KHANI SOLUTIONS | STAGE 05 | MANUAL BALANCING VS PICVs | 23 OCTOBER 2026

SCOPE
24 steady native OpenModelica cases: six scenarios, two pump policies, two valve
technologies. Same piping, water, pump curve and manual presets as Stage 04.
Reference, R05 equipment resistance +5% and +20%, filter coefficient +25% and
+100%, and combined severe change. Heat loads are not changed or solved.

PICV MODEL
Generic ideal pressure-limited valve. q/q_target=min(1,sqrt(max(dp,0)/35000 Pa)).
Below 35 kPa valve differential it behaves as a synthetic fully-open orifice;
above it the ideal flow plateau is 144.7 L/min. All cases remain below the chosen
414 kPa upper-envelope guard. No vendor size/part is selected or calibrated.
Reference pump duty includes 5 kPa above the minimum (40 kPa at critical valve).
Real valve accuracy, droop, hysteresis, actuator/diaphragm and controller dynamics
are not included. The cited data sheet's +/-5% setpoint accuracy can exceed the
mild-change flow differences. Numerical exactness is not hardware accuracy.

PUMP POLICIES
Fixed: manual speed 94.4821%, PICV speed 98.1131%, each independently commissioned
at equal reference rack flow. Their different head requirements are explicit.
Reset: calculate a new final steady speed; manual seeks minimum rack flow target,
PICV seeks minimum differential +5 kPa reserve. Apply at most 100% speed. Manual
valve settings remain fixed, so increased speed can overfeed other racks. There
is no time-domain feedback controller or claimed settling time.

FILTER INTERPRETATION
The inherited 20 kPa map was already a provisional dirty-filter allowance.
25 and 40 kPa cases increase that reference coefficient; they are not measured
clean/dirty product curves. Actual loss varies with solved total flow squared.
The R05 changes apply only to its equipment coefficient, not its whole branch.

NATIVE PROVENANCE
model/DataCenterValveComparison.mo is the full native package. The compiler builds
two reusable variants in runs/build-r1: ManualNetwork (4185 equations/variables),
PICVNetwork (3925). Original compilation logs are retained. Native runtime overrides
set speedRatio, equipmentNominalPa[5] and filterNominalPa. Every override is checked
against exported results. runs/accepted-r1 contains all 24 original result CSVs,
per-case logs, command records and exact Modelica input. No prior stage overwritten.
The alias/start/nominal compiler warning remains. Direct nonlinear initialization
uses -noHomotopyOnFirstTry, inherited from the accepted Stage 04 workflow.
The 0-1 s CSV export repeats a steady algebraic solution; it is not a transient.
Public logs redact absolute machine paths only; numerical CSVs are unchanged.
Compiler binaries and generated C files remain on Intel; portable sources included.

REPRODUCTION
Requires OpenModelica 1.27.1 with MSL 4.1.0, Python with NumPy/SciPy/Matplotlib.
1. python3 source/design.py
2. python3 source/build_model.py
3. Create runs/build-r1 on a new extraction. From it run:
   OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAKEFLAGS=-j2 omc ../../source/build.mos > build-reproduction.log 2>&1
4. From the stage root: python3 source/run_cases.py reproduction-r1
   This creates a new case directory and refuses to overwrite existing CSVs.
5. Preserve results/ before regenerating audited outputs, then run:
   python3 source/audit.py reproduction-r1 build-reproduction.log
6. python3 source/build_report.py
7. python3 -m http.server 8892 ; open http://127.0.0.1:8892/Report.html

CHECKS AND LIMITS
All native values finite; final export reached; mass/pressure and numerical
pump-work energy closure; 24 independent exact-Colebrook flow comparisons within
0.002%; inherited reference and +20% manual cases reproduce Stage 04. PICV law
regimes, target cap, operating envelope and actual override values checked.
No experimental validation, thermal performance, NPSH, pump switching or water
hammer qualification. Assumed pump H=37s^2-0.5sr-9r^2 m; two duty pumps, standby
isolated; fixed efficiencies 0.75 hydraulic and 0.90 motor. Extra VFD losses and
efficiency-map changes excluded. Under-flow power reductions are not equal-service
energy savings. Higher required PICV minimum pressure can make it worse once the
pump is head-limited; the combined severe case explicitly demonstrates this.

DELIVERABLES
Report.html + review.css + review.mjs: standalone interactive report (serve via HTTP).
results/: JSON, all-case and all-rack CSVs, scientific plots and valve-law figure.
source/: independent sizing, native model builder, build script, case runner,
conservation audit, figures, report generator and website sources.
verification/: audit log and public source-to-model reference register.
inputs/: unchanged prior model, accepted Stage 04 data and CAD route schedule.
manifest.json: SHA256 hashes of deliverables; ZIP includes the inventory.
