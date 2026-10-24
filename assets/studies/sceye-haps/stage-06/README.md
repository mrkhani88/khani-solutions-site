# Stratospheric thermal engineering — interview evidence

Independent public-reference portfolio study by Mohammadreza Khani. This is a representative architecture and engineering workflow, not Sceye's internal design or flight qualification evidence.

## Start here

- Main guided page: https://khanisolutions.com/AISolutions/sceye-thermal-interview.html
- Earlier CAD and thermal stages: https://khanisolutions.com/AISolutions/sceye-haps-thermal.html
- Short interview route: `documents/Presenter-Guide.html`
- Standalone clickable requirements matrix: `documents/Job-Requirement-Matrix.html`
- Machine-readable traceability: `inputs/requirements-matrix.json` and `inputs/lifecycle-evidence-registry.json`

The six-step route covers requirements, the connected mission, spatial detail and design trades, test-ready article definition, correlation workflow, and faults/readiness. The 13 job-requirement rows link the same underlying evidence wherever relevant. Evidence status describes this study, not the author's complete employment history.

## What was completed

- A 28-temperature-node native OpenModelica architecture extends the previous model with representative transmitter, beamforming, baseband, edge-server and payload-power functions.
- A conservative 3D finite-volume board-conduction model supplies effective heat paths to the system model. A separate matched-boundary transient comparison checks the reduced representation.
- Nominal, pressure-sensitivity, cold-start, interface/radiator trades, sensor/heater faults, degradation and workload-shedding studies retain both successful and rejected cases. Fixed-boundary payload equilibrium studies are separate from the finite-energy mission.
- Native FreeCAD and STEP geometry, VTK fields, mesh/reduction data, numerical audits, sources and compact CSV histories are included.
- Requirements, interfaces, risk register, environmental test plan, sensor map, uncertainty allocations, blank measurement template and review checklist are supplied.
- A clearly labeled synthetic two-node calibration/held-out exercise demonstrates the analysis procedure. It is independent of the five-terminal assembly and does not validate its physical properties.

## Important result boundaries

The selected study configuration uses a 4.5 m² radiator and a chosen 60 W/K attachment. Its settled nominal payload-case surrogates span approximately 7.14–61.83 °C; the model permits the full requested workload throughout that day, with minimum generic battery SOC about 53.04%. These are results for selected assumptions, not measured service performance. The fixed hot payload case reaches about 67.31 °C against a study-chosen 70 °C screen. That margin is not a qualified uncertainty allowance.

The panel change adds an estimated 3.93 kg to the assumed radiator stack. It is not a complete vehicle mass estimate: installation hardware, flight demand and buoyancy feedback are outside this calculation. Effective PCB conductivity, contacts, capacities, electronic loads and operating screens require actual hardware data before design release.

Large rejected-baseline values exceed the selected constant-property model domain. They identify infeasibility; they are not credible temperatures of functioning hardware. Read the validity notes before comparing those curves with the selected configuration.

**No physical article has been assembled or tested in this study.** The measured-data template is empty. Environmental tests, physical correlation, selected-part allowables and operational qualification remain explicitly unexecuted. `documents/Completion-Boundaries.md` explains what evidence would close each gap.

## Reproduce and inspect

Use the retained stage directory structure. Read `source/engineering/README.md` for the native OpenModelica, spatial solver and FreeCAD command sequence and dependencies. Engineering runs were performed on Intel; compiled executables and bulk native histories remain on that host, with downloadable native archives linked in the website and archive manifest.

`source/correlation/README.md` documents the separate synthetic identification exercise. `source/frontend/README.md` documents the static controls and result schema. The browser views saved outputs; moving a control does not launch a solver.

`manifest.json` records compact file sizes and SHA-256 hashes. The stage ZIP contains the compact engineering and evidence package. Native archive hashes and URLs are recorded separately. Download earlier stage packages from their original study sections for their complete source/CAD/results.

## Delivery record

The durable project folder is the iCloud Khani Workspace project. Public deployment, public asset hash checks and browser verification are recorded in the sibling `Publication-Evidence/Stage-06-Interview-Evidence-R1/` folder. Saving in iCloud does not by itself establish completed cloud upload or offload.
