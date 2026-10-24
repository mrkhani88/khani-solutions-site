KHANI SOLUTIONS | SCEYE PUBLIC-REFERENCE HAPS THERMAL STUDY
Stage 01: evidence, geometry, architecture and numerical verification
23 October 2026 | Independent work by Mohammadreza Khani

START HERE
Open Review.html through a local HTTP server from this folder:
  python3 -m http.server 8892
  http://127.0.0.1:8892/Review.html
The online study is https://khanisolutions.com/AISolutions/sceye-haps-thermal.html
The standalone module loads local CAD data; credited reference photos use the
public website and need Internet. Publisher photographs are separate from this ZIP.

WHAT EXISTS
- Native FreeCAD assembly, STEP, closed reference hull STL and display mesh JSON.
- A 65 m public-reference class, with inferred diameter/proportions. It is not
  ST1/SE2 production CAD. Proposed equipment is outside the helium envelope.
- Tagged avionics, battery/power, payload, propulsion and thermal-control blocks.
- Published source register with evidence boundaries and historical patent context.
- Candidate passive/active architecture, requirements evidence and test plans.
- Standard-atmosphere presizing and a simplified isothermal radiator screen.
- Three actual native OpenModelica benchmarks, CSVs, logs and analytical audit.

WHAT DOES NOT EXIST YET
No solved vehicle mission temperature field, vehicle CFD/FEM, OEM component limits,
selected flight materials, mass/buoyancy calculation, physical correlation or
qualification. No internal layout is represented as recovered proprietary data.
See docs/Design-Basis.txt and docs/Test-and-Integration-Plan.txt for the boundaries.

REPRODUCE ON INTEL / LINUX
FreeCAD 1.1.4 was used in GUI mode with a virtual display and software rendering.
From the project root, substitute the path of your installed FreeCAD executable:
  OMP_NUM_THREADS=1 LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a freecad source/build_vehicle.FCMacro
  OMP_NUM_THREADS=1 LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a freecad source/render_views.FCMacro
  OMP_NUM_THREADS=1 LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a freecad source/reopen_verify.FCMacro
The build macro creates native objects, tagged records, native exports and browser
tessellation. The separate render macro applies explicit side/top/isometric camera
orientations. The verification macro reopens native CAD and imports STEP/STL.
Part features and parameter spreadsheet are editable; the assembly is not an OEM
fully constrained manufacturing model. Display volumes do not establish mass.

OpenModelica 1.27.1 native benchmarks:
  mkdir -p verification/native-acceptance
  cd verification/native-acceptance
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 omc ../../source/acceptance.mos > run.log 2>&1
  cd ../..
  python3 source/audit_acceptance.py
Analytical presizing and report:
  python3 source/first_checks.py
  python3 source/build_study.py
The default bench temperatures are not predicted vehicle/component temperatures.

TRACEABILITY AND THIRD-PARTY MATERIAL
manifest.json covers all packaged original-work artifacts, numerical CSVs, sources,
and MIT Three.js 0.180.0 viewer dependencies. Verify SHA-256 hashes before reuse.
Three.js and OrbitControls retain source/vendor/LICENSE.txt. Publisher image rights
remain with their owners; image credits/source links are on the website and in its
separate reference-images/credits.json. No recruiter email, NDA, private employer
files or meeting details are included. Public logs substitute ${PROJECT_ROOT} for
an absolute Intel root; native CSVs/CAD are byte-identical to the retained results.

NEXT STAGE
Build the repeated day/night OpenModelica mission network. Establish traceable
assumed loss maps, capacities and thermal conductances with sensitivity bounds;
close an independent energy audit before interpreting hot/cold margins. Selected
hardware data and measured tests are required for physical validation/readiness.
