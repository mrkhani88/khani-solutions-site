KHANI SOLUTIONS | DATA-CENTER HYDRAULICS | STAGE 04 | 23 OCTOBER 2026

PURPOSE
Compare pump-speed reduction and static rack balancing against the accepted Stage 03.
Target: exactly 144.7 L/min at each of ten racks, requested rounded heat-duty value.
No CFD, transient thermal solution, hardware selection or physical validation is claimed.

RESULT
Both duty pumps at 94.4821% assumed reference speed; each rack within 0.001 L/min
of target; bank electric input 9.713853 -> 8.189584 kW (15.6917% lower).
Critical R10 balancing valve: chosen actual 15 kPa floor. Other valves add the
path-loss differences. This constrained static result is not global optimization.

FILES
Report.html / review.css / review.mjs: interactive report; serve the folder over HTTP.
model/DataCenterBalancing.mo: complete native MSL package, five named cases.
model/design.json: independent sizing output and explicit per-case settings.
inputs/: unchanged accepted parent model, assumptions, route schedule and baseline.
runs/r5/: accepted native result CSVs, per-case runtime logs, exact model snapshot.
runs/r1/run.log: original compilation/default-initialization attempt and warnings.
runs/r2..r4/: diagnostic attempts. Failures are preserved, not accepted results.
results/: full comparison JSON, CSV tables, scientific SVG/PNG figures.
source/design.py: independent exact-Colebrook sizing and native case generation.
source/run.mos: reproducible native compilation/simulation for all five cases.
source/audit.py: conservation, original baseline and independent numerical checks.
source/build_report.py: report/section generation from accepted result data.
verification/references.json: public technical source-to-claim register.
manifest.json: relative-path size and SHA256 inventory (excludes itself and ZIP).

REPRODUCE ON LINUX / INTEL
Requires OpenModelica 1.27.1 with Modelica Standard Library 4.1.0; Python 3 with
NumPy, SciPy and Matplotlib. The original engineering runs used two compile
workers, one BLAS/OpenMP thread and -O1 C compilation.
1. python3 source/design.py
2. On a fresh extraction, create runs/reproduction (do not overwrite retained runs).
3. cd runs/reproduction
4. OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAKEFLAGS=-j2 omc ../../source/run.mos > run.log 2>&1
5. Compare resulting *_res.csv against runs/r5 and results/rack-comparison.csv.
   source/audit.py points to the accepted runs/r5 by default; change R to the new
   attempt for a fresh audit and preserve the original accepted outputs first.
6. python3 source/build_report.py
7. python3 -m http.server 8892, then open http://127.0.0.1:8892/Report.html

SOLVER PROVENANCE
The first/default homotopy initialization failed for reduced-speed cases. A hybrid
trial also failed (r2/r3); direct nonlinear initialization succeeded (r4).
Accepted r5 reran all five compiled r1 binaries with -noHomotopyOnFirstTry using
the identical SHA256-verified Modelica input. Compiler and physics equations did
not change to force agreement. source/run.mos includes that initialization flag
for future fresh builds. Alias/start/nominal warnings remain in the compiler log.
Public log copies redact only absolute machine paths; numeric outputs are native.
Native compiled binaries/C build products remain on Intel and are not portable
source deliverables. Prior native CAD and diagrams remain in Stage 02 downloads.

ENGINEERING LIMITS
Fixed-property water near 40 C; assumed quadratic equipment maps and fitting K.
Same CAD-derived routing and direct-return topology. Two identical duty pumps;
standby isolated. Pump bank curve H=37s^2-0.5sr-9r^2 m, r=Q/Qnom. The curve is an
assumed test curve, not purchased pump data. Pump hydraulic efficiency 0.75,
motor efficiency 0.90; additional VFD losses and efficiency variation excluded.
0-1 s CSV samples repeat a steady solution, not a startup or control transient.
The numerical bath closes pump-work energy; it is not the physical heat exchanger.
The +20% R05 case changes its equipment resistance coefficient only, not its heat.
Kv is an equivalent hydraulic target, not a selected valve or dial setting.
Manual settings are case-specific; PICV, DPCV, reverse return and control alternatives
are researched here but not simulated or physically qualified.
